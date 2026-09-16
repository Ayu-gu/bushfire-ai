import json
import os
import time

import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = "data/training_dataset_v06_elevation.csv"
CACHE_PATH = "data/vegetation_cache_v06.json"
OUTPUT_PATH = "data/training_dataset_v06.csv"

TEST_LOCATIONS = None

IDENTIFY_URL = (
    "https://mapprod3.environment.nsw.gov.au/"
    "arcgis/rest/services/VIS/"
    "SVTM_NSW_Extant_PCT/MapServer/identify"
)

REQUEST_DELAY_SECONDS = 1.0
MAX_API_RETRIES = 5


# ============================================================
# REQUEST WITH RETRY
# ============================================================

def request_json(
    url,
    params,
    timeout=30
):

    for attempt in range(
        1,
        MAX_API_RETRIES + 1
    ):

        try:

            time.sleep(
                REQUEST_DELAY_SECONDS
            )

            response = requests.get(
                url,
                params=params,
                timeout=timeout
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as error:

            print(
                f"API attempt "
                f"{attempt}/{MAX_API_RETRIES} failed:"
            )

            print(error)

            if attempt == MAX_API_RETRIES:
                raise

            status_code = None

            if (
                hasattr(error, "response")
                and error.response is not None
            ):
                status_code = error.response.status_code

            if status_code == 429:
                wait_seconds = 30 * attempt
            else:
                wait_seconds = 2 ** attempt

            print(
                f"Retrying in "
                f"{wait_seconds} seconds..."
            )

            time.sleep(
                wait_seconds
            )


# ============================================================
# CACHE
# ============================================================

def load_cache():

    if not os.path.exists(
        CACHE_PATH
    ):
        return {}

    with open(
        CACHE_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_cache(
    cache
):

    with open(
        CACHE_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            cache,
            file,
            indent=2
        )


# ============================================================
# COORDINATE KEY
# ============================================================

def coordinate_key(
    latitude,
    longitude
):

    return (
        f"{latitude:.6f},"
        f"{longitude:.6f}"
    )


# ============================================================
# VEGETATION LOOKUP
# ============================================================

def fetch_vegetation(
    latitude,
    longitude
):

    geometry = (
        f"{longitude},"
        f"{latitude}"
    )

    map_extent = (
        f"{longitude - 0.05},"
        f"{latitude - 0.05},"
        f"{longitude + 0.05},"
        f"{latitude + 0.05}"
    )

    params = {
        "geometry":
            geometry,

        "geometryType":
            "esriGeometryPoint",

        "sr":
            4326,

        "layers":
            "all:0",

        "tolerance":
            3,

        "mapExtent":
            map_extent,

        "imageDisplay":
            "800,600,96",

        "returnGeometry":
            "false",

        "f":
            "json",
    }

    result = request_json(
        IDENTIFY_URL,
        params
    )

    results = result.get(
        "results",
        []
    )

    if not results:
        return {
            "pct_id": None,
            "vegetation_class": None,
            "vegetation_formation": None,
        }

    attributes = results[0].get(
        "attributes",
        {}
    )

    pct_id = attributes.get(
        "PCTID"
    )

    vegetation_class = attributes.get(
        "vegClass"
    )

    vegetation_formation = attributes.get(
        "vegForm"
    )

    return {
        "pct_id": pct_id,
        "vegetation_class":
            vegetation_class,
        "vegetation_formation":
            vegetation_formation,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n==============================")
    print("BUSHFIRE AI V06 VEGETATION")
    print("==============================")

    df = pd.read_csv(
        DATASET_PATH
    )

    unique_locations = (
        df[
            [
                "latitude",
                "longitude",
                
            ]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    
    if TEST_LOCATIONS is not None:
        unique_locations = unique_locations.head(
            TEST_LOCATIONS
            
        )

    print(
        f"\nTesting locations: "
        f"{len(unique_locations):,}"
    )

    cache = load_cache()

    print(
        f"Cached locations: "
        f"{len(cache):,}"
    )

    for index, row in (
        unique_locations.iterrows()
    ):

        latitude = float(
            row["latitude"]
        )

        longitude = float(
            row["longitude"]
        )

        key = coordinate_key(
            latitude,
            longitude
        )

        if key in cache:

            print(
                f"Location "
                f"{index + 1}/"
                f"{len(unique_locations)} "
                f"already cached"
            )

            continue

        print(
            f"Location "
            f"{index + 1}/"
            f"{len(unique_locations)} "
            f"| {latitude:.4f}, "
            f"{longitude:.4f}"
        )

        try:

            vegetation = (
                fetch_vegetation(
                    latitude,
                    longitude
                )
            )

        except Exception as error:

            print(
                "Vegetation lookup failed:"
            )

            print(error)

            continue

        cache[key] = vegetation

        save_cache(
            cache
        )


    # ========================================================
    # BUILD TEST OUTPUT
    # ========================================================

    test_df = (
        df
        .merge(
            unique_locations,
            on=[
                "latitude",
                "longitude",
            ],
            how="inner"
        )
        .copy()
    )


    def lookup(
        row
    ):

        key = coordinate_key(
            float(row["latitude"]),
            float(row["longitude"])
        )

        return cache.get(
            key,
            {}
        )


    vegetation_data = (
        test_df.apply(
            lookup,
            axis=1
        )
    )


    test_df[
        "pct_id"
    ] = vegetation_data.apply(
        lambda value:
            value.get(
                "pct_id"
            )
    )

    test_df[
        "vegetation_class"
    ] = vegetation_data.apply(
        lambda value:
            value.get(
                "vegetation_class"
            )
    )

    test_df[
        "vegetation_formation"
    ] = vegetation_data.apply(
        lambda value:
            value.get(
                "vegetation_formation"
            )
    )


    # ========================================================
    # REPORT
    # ========================================================

    print("\n==============================")
    print("VEGETATION TEST COMPLETE")
    print("==============================")

    print(
        f"\nRows in output: "
        f"{len(test_df):,}"
    )

    print(
        f"PCT values present: "
        f"{test_df['pct_id'].notna().sum():,}"
    )

    print(
        f"Missing PCT values: "
        f"{test_df['pct_id'].isna().sum():,}"
    )

    print(
        "\nVegetation formations:"
    )

    print(
        test_df[
            "vegetation_formation"
        ]
        .value_counts(
            dropna=False
        )
        .head(20)
    )


    # ========================================================
    # SAVE
    # ========================================================

    test_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(
        f"\nSaved to "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()