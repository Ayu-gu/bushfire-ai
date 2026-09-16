import json
import os
import time

import pandas as pd
import requests


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_PATH = "data/training_dataset_v05.csv"
OUTPUT_PATH = "data/training_dataset_v06_elevation.csv"
CACHE_PATH = "data/elevation_cache_v06.json"

ELEVATION_URL = (
    "https://api.open-meteo.com/v1/elevation"
)

BATCH_SIZE = 25
REQUEST_DELAY_SECONDS = 5.0
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
# FETCH ELEVATION BATCH
# ============================================================

def fetch_elevation_batch(
    coordinates
):

    latitudes = [
        str(latitude)
        for latitude, _
        in coordinates
    ]

    longitudes = [
        str(longitude)
        for _, longitude
        in coordinates
    ]

    params = {
        "latitude":
            ",".join(latitudes),

        "longitude":
            ",".join(longitudes),
    }

    result = request_json(
        ELEVATION_URL,
        params
    )

    elevations = result.get(
        "elevation"
    )

    if elevations is None:
        raise RuntimeError(
            "Elevation response "
            "did not contain elevation data."
        )

    if not isinstance(
        elevations,
        list
    ):
        elevations = [
            elevations
        ]

    if len(elevations) != len(
        coordinates
    ):
        raise RuntimeError(
            "Elevation result count "
            "does not match coordinate count."
        )

    return elevations


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n==============================")
    print("BUSHFIRE AI V06 ELEVATION")
    print("==============================")

    df = pd.read_csv(
        DATASET_PATH
    )

    print(
        f"\nDataset rows: "
        f"{len(df):,}"
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

    print(
        f"Unique locations: "
        f"{len(unique_locations):,}"
    )

    cache = load_cache()

    print(
        f"Cached locations: "
        f"{len(cache):,}"
    )

    missing_coordinates = []

    for _, row in (
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

        if key not in cache:

            missing_coordinates.append(
                (
                    latitude,
                    longitude
                )
            )

    print(
        f"Locations requiring lookup: "
        f"{len(missing_coordinates):,}"
    )


    # ========================================================
    # BATCH LOOKUPS
    # ========================================================

    total_missing = len(
        missing_coordinates
    )

    for start_index in range(
        0,
        total_missing,
        BATCH_SIZE
    ):

        batch = (
            missing_coordinates[
                start_index:
                start_index
                + BATCH_SIZE
            ]
        )

        batch_number = (
            start_index
            // BATCH_SIZE
            + 1
        )

        total_batches = (
            total_missing
            + BATCH_SIZE
            - 1
        ) // BATCH_SIZE

        print(
            f"\nBatch "
            f"{batch_number}/"
            f"{total_batches}"
        )

        print(
            f"Locations: "
            f"{len(batch)}"
        )

        try:

            elevations = (
                fetch_elevation_batch(
                    batch
                )
            )

        except Exception as error:

            print(
                "Elevation batch failed:"
            )

            print(error)

            save_cache(
                cache
            )

            raise


        for (
            coordinate,
            elevation
        ) in zip(
            batch,
            elevations
        ):

            latitude = coordinate[0]
            longitude = coordinate[1]

            key = coordinate_key(
                latitude,
                longitude
            )

            cache[key] = elevation


        save_cache(
            cache
        )

        print(
            f"Cached locations: "
            f"{len(cache):,}"
        )


    # ========================================================
    # ATTACH ELEVATION
    # ========================================================

    def lookup_elevation(
        row
    ):

        key = coordinate_key(
            float(row["latitude"]),
            float(row["longitude"])
        )

        return cache.get(
            key
        )


    df["elevation"] = df.apply(
        lookup_elevation,
        axis=1
    )


    # ========================================================
    # VALIDATE
    # ========================================================

    missing_elevation = (
        df["elevation"]
        .isna()
        .sum()
    )

    print("\n==============================")
    print("V06 ELEVATION COMPLETE")
    print("==============================")

    print(
        f"\nRows: "
        f"{len(df):,}"
    )

    print(
        f"Missing elevation: "
        f"{missing_elevation:,}"
    )

    print(
        f"Elevation range: "
        f"{df['elevation'].min()} "
        f"to "
        f"{df['elevation'].max()} metres"
    )


    if missing_elevation > 0:

        raise RuntimeError(
            "Elevation enrichment "
            "contains missing values."
        )


    # ========================================================
    # SAVE DATASET
    # ========================================================

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(
        f"\nSaved to "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()