import os
import time
import math
import random
import requests
import pandas as pd

from datetime import datetime, timedelta
from shapely.geometry import shape


# ============================================================
# CONFIG
# ============================================================

FIRE_URL = (
    "https://portal.data.nsw.gov.au/arcgis/rest/services/"
    "Hosted/NSWFireHistory/FeatureServer/0/query"
)

WEATHER_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)

OUTPUT_FILE = "data/training_dataset_v05.csv"

TARGET_ROWS = 20_000

# Balanced:
# 10,000 FIRE
# 10,000 verified NON-FIRE
TARGET_FIRE_ROWS = TARGET_ROWS // 2

# Keep V05 focused on modern records.
MIN_FIRE_YEAR = 2000

# ArcGIS pagination size.
PAGE_SIZE = 500

# Save regularly so a crash does not destroy progress.
CHECKPOINT_EVERY_PAIRS = 25

# Retry settings for network/API problems.
MAX_API_RETRIES = 5
REQUEST_DELAY_SECONDS = 1.0

# Maximum attempts to find verified non-fire date.
MAX_NEGATIVE_ATTEMPTS = 20


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
                f"\nAPI attempt "
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
                wait_seconds = 60 * attempt
            else:
                wait_seconds = 2 ** attempt
            
            print(
                f"Retrying in "
                f"{wait_seconds} seconds..."
            )

            time.sleep(wait_seconds)

where_clause = (
    "fire_type = 'Bushfire' "
    "AND ignition_date IS NOT NULL "
    "AND ignition_date >= DATE '2000-01-01'"
)


# ============================================================
# FIRE COUNT
# ============================================================

def get_available_fire_count():

    where_clause = (
        "fire_type = 'Bushfire' "
        "AND ignition_date IS NOT NULL "
        "AND ignition_date >= DATE '2000-01-01'"
    )

    params = {
        "where": where_clause,
        "returnCountOnly": "true",
        "f": "json",
    }

    result = request_json(
        FIRE_URL,
        params
    )

    return result.get(
        "count",
        0
    )


# ============================================================
# PAGINATED FIRE FETCH
# ============================================================

def fetch_fire_page(
    offset,
    limit=PAGE_SIZE
):

    where_clause = (
        "fire_type = 'Bushfire' "
        "AND ignition_date IS NOT NULL "
        "AND ignition_date >= DATE '2000-01-01'"
    )

    params = {
        "where": where_clause,

        "outFields": "*",

        "returnGeometry": "true",

        "f": "geojson",

        "resultOffset": offset,

        "resultRecordCount": limit,

        "orderByFields": "objectid ASC",
    }

    result = request_json(
        FIRE_URL,
        params
    )

    return result.get(
        "features",
        []
    )


# ============================================================
# WEATHER
# ============================================================

def fetch_weather(
    latitude,
    longitude,
    target_date
):

    end_date = datetime.strptime(
        target_date,
        "%Y-%m-%d"
    )

    start_date = (
        end_date
        - timedelta(days=30)
    )

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "start_date":
            start_date.strftime(
                "%Y-%m-%d"
            ),

        "end_date":
            target_date,

        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],

        "hourly":
            "relative_humidity_2m",

        "timezone":
            "Australia/Sydney",
    }

    return request_json(
        WEATHER_URL,
        params
    )


# ============================================================
# DATE FEATURES
# ============================================================

def get_season(month):

    if month in [12, 1, 2]:
        return 0

    if month in [3, 4, 5]:
        return 1

    if month in [6, 7, 8]:
        return 2

    return 3


# ============================================================
# RAIN FEATURES
# ============================================================

def days_since_rain(
    rainfall
):

    count = 0

    for value in reversed(
        rainfall[:-1]
    ):

        if (
            value is not None
            and value >= 1
        ):
            return count

        count += 1

    return count


# ============================================================
# VPD
# ============================================================

def calculate_vpd(
    max_temp,
    avg_humidity
):

    saturation_vp = (
        0.6108
        * math.exp(
            (
                17.27
                * max_temp
            )
            /
            (
                max_temp
                + 237.3
            )
        )
    )

    actual_vp = (
        saturation_vp
        * (
            avg_humidity
            / 100
        )
    )

    return (
        saturation_vp
        - actual_vp
    )


# ============================================================
# BUILD ALL V05 FEATURES
# ============================================================

def build_weather_features(
    latitude,
    longitude,
    target_date,
    fire_label,
    source_fire_id
):

    weather = fetch_weather(
        latitude,
        longitude,
        target_date
    )

    daily = weather["daily"]

    rainfall = daily[
        "precipitation_sum"
    ]

    humidity_values = (
        weather["hourly"][
            "relative_humidity_2m"
        ][-24:]
    )

    valid_humidity = [
        value
        for value in humidity_values
        if value is not None
    ]

    if not valid_humidity:
        raise ValueError(
            "No humidity observations available."
        )

    max_temp = (
        daily[
            "temperature_2m_max"
        ][-1]
    )

    min_temp = (
        daily[
            "temperature_2m_min"
        ][-1]
    )

    max_wind = (
        daily[
            "wind_speed_10m_max"
        ][-1]
    )

    if (
        max_temp is None
        or min_temp is None
        or max_wind is None
    ):
        raise ValueError(
            "Required weather values missing."
        )

    avg_humidity = round(
        sum(valid_humidity)
        / len(valid_humidity),
        1
    )

    rain_today = (
        rainfall[-1]
        or 0
    )

    rain_7 = round(
        sum(
            value or 0
            for value
            in rainfall[-8:-1]
        ),
        2
    )

    rain_30 = round(
        sum(
            value or 0
            for value
            in rainfall[:-1]
        ),
        2
    )

    days_dry = days_since_rain(
        rainfall
    )

    target_datetime = datetime.strptime(
        target_date,
        "%Y-%m-%d"
    )

    month = target_datetime.month

    day_of_year = (
        target_datetime
        .timetuple()
        .tm_yday
    )

    season = get_season(
        month
    )

    temp_humidity_index = (
        max_temp
        * (
            100
            - avg_humidity
        )
        / 100
    )

    temp_wind_index = (
        max_temp
        * max_wind
    )

    dryness_index = (
        (days_dry + 1)
        /
        (rain_30 + 1)
    )

    vpd = calculate_vpd(
        max_temp,
        avg_humidity
    )

    return {
        "source_fire_id":
            source_fire_id,

        "state":
            "NSW",

        "date":
            target_date,

        "month":
            month,

        "day_of_year":
            day_of_year,

        "season":
            season,

        "latitude":
            latitude,

        "longitude":
            longitude,

        "max_temp":
            max_temp,

        "min_temp":
            min_temp,

        "avg_humidity":
            avg_humidity,

        "max_wind":
            max_wind,

        "rain_today":
            rain_today,

        "rain_last_7_days":
            rain_7,

        "rain_last_30_days":
            rain_30,

        "days_since_rain":
            days_dry,

        "temp_humidity_index":
            temp_humidity_index,

        "temp_wind_index":
            temp_wind_index,

        "dryness_index":
            dryness_index,

        "vpd":
            vpd,

        "fire":
            fire_label,
    }


# ============================================================
# VERIFY NON-FIRE
# ============================================================

def fire_nearby(
    latitude,
    longitude,
    target_date
):

    date = datetime.strptime(
        target_date,
        "%Y-%m-%d"
    )

    start = (
        date
        - timedelta(days=7)
    )

    end = (
        date
        + timedelta(days=7)
    )

    start_ms = int(
        start.timestamp()
        * 1000
    )

    end_ms = int(
        end.timestamp()
        * 1000
    )

    params = {
        "where": (
            "fire_type = 'Bushfire' "
            f"AND ignition_date >= {start_ms} "
            f"AND ignition_date <= {end_ms}"
        ),

        "geometry":
            f"{longitude},{latitude}",

        "geometryType":
            "esriGeometryPoint",

        "inSR":
            "4326",

        "spatialRel":
            "esriSpatialRelIntersects",

        "distance":
            5,

        "units":
            "esriSRUnit_Kilometer",

        "returnCountOnly":
            "true",

        "f":
            "json",
    }

    result = request_json(
        FIRE_URL,
        params
    )

    return (
        result.get(
            "count",
            0
        )
        > 0
    )


# ============================================================
# LOAD CHECKPOINT
# ============================================================

def load_existing_dataset():

    if not os.path.exists(
        OUTPUT_FILE
    ):

        return pd.DataFrame()

    df = pd.read_csv(
        OUTPUT_FILE
    )

    print(
        f"\n Existing V05 checkpoint found:"
        f" {len(df):,} rows"
    )

    return df


# ============================================================
# SAVE CHECKPOINT
# ============================================================

def save_checkpoint(
    rows
):

    df = pd.DataFrame(
        rows
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"\n CHECKPOINT SAVED:"
        f" {len(df):,}/{TARGET_ROWS:,}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n ==============================")
    print("BUSHFIRE AI — DATASET V05")
    print("==============================\n")

    print(
        f"Target rows: "
        f"{TARGET_ROWS:,}"
    )

    print(
        f"Target FIRE: "
        f"{TARGET_FIRE_ROWS:,}"
    )

    print(
        f"Target NON-FIRE: "
        f"{TARGET_FIRE_ROWS:,}"
    )

    print(
        f"Minimum fire year: "
        f"{MIN_FIRE_YEAR}"
    )

    available_fires = (
        get_available_fire_count()
    )

    print(
        f"\nModern NSW bushfires "
        f"available from API: "
        f"{available_fires:,}"
    )

    if (
        available_fires
        < TARGET_FIRE_ROWS
    ):

        print(
            "\n⚠️ WARNING:"
        )

        print(
            f"We requested "
            f"{TARGET_FIRE_ROWS:,} "
            f"fire examples, but the API "
            f"reports only "
            f"{available_fires:,} "
            f"matching NSW records."
        )

        print(
            "The script will collect as many "
            "valid balanced pairs as possible."
        )


    # -----------------------------------
    # RESUME
    # -----------------------------------

    existing_df = (
        load_existing_dataset()
    )

    if existing_df.empty:

        rows = []

        completed_fire_ids = set()

    else:

        rows = (
            existing_df
            .to_dict(
                "records"
            )
        )

        completed_fire_ids = set(
            existing_df.loc[
                existing_df["fire"] == 1,
                "source_fire_id"
            ]
            .astype(str)
        )


    fire_count = sum(
        1
        for row in rows
        if row["fire"] == 1
    )

    non_fire_count = sum(
        1
        for row in rows
        if row["fire"] == 0
    )

    print(
        f"\nResume status:"
    )

    print(
        f"FIRE:     "
        f"{fire_count:,}"
    )

    print(
        f"NON-FIRE: "
        f"{non_fire_count:,}"
    )

    print(
        f"TOTAL:    "
        f"{len(rows):,}"
    )


    if (
        fire_count
        >= TARGET_FIRE_ROWS
        and non_fire_count
        >= TARGET_FIRE_ROWS
    ):

        print(
            "\n V05 target already complete."
        )

        return


    # -----------------------------------
    # COUNTERS
    # -----------------------------------

    offset = 0

    completed_since_save = 0

    api_failures = 0
    rejected_negatives = 0
    duplicates_skipped = 0


    # -----------------------------------
    # PAGINATE FIRE DATA
    # -----------------------------------

    while (
        fire_count
        < TARGET_FIRE_ROWS
    ):

        print(
            f"\n Fetching fire page "
            f"offset {offset:,}..."
        )

        try:

            fires = fetch_fire_page(
                offset
            )

        except Exception as error:

            print(
                "\n Could not fetch fire page:"
            )

            print(error)

            save_checkpoint(
                rows
            )

            return


        if not fires:

            print(
                "\nNo more fire records returned."
            )

            break


        for fire in fires:

            if (
                fire_count
                >= TARGET_FIRE_ROWS
            ):
                break


            props = fire[
                "properties"
            ]

            source_fire_id = (
                props.get(
                    "OBJECTID"
                )
                or props.get(
                    "objectid"
                )
                or props.get(
                    "ObjectID"
                )
            )

            if source_fire_id is None:

                source_fire_id = (
                    f"{offset}-"
                    f"{props.get('ignition_date')}"
                )

            source_fire_id = str(
                source_fire_id
            )


            # ----------------------------
            # DUPLICATE PROTECTION
            # ----------------------------

            if (
                source_fire_id
                in completed_fire_ids
            ):

                duplicates_skipped += 1

                continue


            # ----------------------------
            # GEOMETRY
            # ----------------------------

            try:

                geometry = shape(
                    fire["geometry"]
                )

                centre = (
                    geometry.centroid
                )

                latitude = centre.y
                longitude = centre.x

            except Exception as error:

                print(
                    f"⚠️ Invalid geometry "
                    f"for fire "
                    f"{source_fire_id}: "
                    f"{error}"
                )

                continue


            # ----------------------------
            # FIRE DATE
            # ----------------------------

            try:

                fire_datetime = (
                    datetime.fromtimestamp(
                        props[
                            "ignition_date"
                        ]
                        / 1000
                    )
                )

            except Exception:

                continue


            if (
                fire_datetime.year
                < MIN_FIRE_YEAR
            ):
                continue


            fire_date = (
                fire_datetime.strftime(
                    "%Y-%m-%d"
                )
            )


            print(
                f"\n FIRE "
                f"{fire_count + 1:,}/"
                f"{TARGET_FIRE_ROWS:,}"
            )

            print(
                f"ID: {source_fire_id}"
            )

            print(
                f"Date: {fire_date}"
            )

            print(
                f"Location: "
                f"{latitude:.4f}, "
                f"{longitude:.4f}"
            )


            # ----------------------------
            # POSITIVE WEATHER
            # ----------------------------

            try:

                positive = (
                    build_weather_features(
                        latitude,
                        longitude,
                        fire_date,
                        1,
                        source_fire_id
                    )
                )

            except Exception as error:

                api_failures += 1

                print(
                    "⚠️ FIRE weather failed:"
                )

                print(error)

                continue


            # ----------------------------
            # FIND VERIFIED NEGATIVE
            # ----------------------------

            negative = None


            for attempt in range(
                1,
                MAX_NEGATIVE_ATTEMPTS + 1
            ):

                candidate_years = [
                     year
                     for year in range(
                          max(
                               1941,
                               fire_datetime.year - 10
                               ),
                          min(
                               datetime.now().year - 1,
                               fire_datetime.year + 10
                               ) + 1
                               )
                     if year != fire_datetime.year
                 ]
                if not candidate_years:
                     continue
                negative_year = random.choice(
                    candidate_years
                )


                try:

                    negative_datetime = (
                        fire_datetime.replace(
                            year=
                                negative_year
                        )
                    )

                except ValueError:

                    negative_datetime = (
                        fire_datetime.replace(
                            year=
                                negative_year,
                            day=28
                        )
                    )


                negative_date = (
                    negative_datetime.strftime(
                        "%Y-%m-%d"
                    )
                )


                try:

                    if fire_nearby(
                        latitude,
                        longitude,
                        negative_date
                    ):

                        rejected_negatives += 1

                        continue

                except Exception as error:

                    api_failures += 1

                    print(
                        "⚠️ Fire verification "
                        "request failed:"
                    )

                    print(error)

                    continue


                try:

                    negative = (
                        build_weather_features(
                            latitude,
                            longitude,
                            negative_date,
                            0,
                            source_fire_id
                        )
                    )

                    break

                except Exception as error:

                    api_failures += 1

                    print(
                        "⚠️ NON-FIRE weather "
                        "failed:"
                    )

                    print(error)


            if negative is None:

                print(
                    "⚠️ Could not create a "
                    "verified NON-FIRE pair."
                )

                continue


            # ----------------------------
            # ONLY SAVE COMPLETE PAIRS
            # ----------------------------

            rows.append(
                positive
            )

            rows.append(
                negative
            )

            completed_fire_ids.add(
                source_fire_id
            )

            fire_count += 1
            non_fire_count += 1

            completed_since_save += 1


            # ----------------------------
            # PROGRESS
            # ----------------------------

            print(
                "\n V05 PROGRESS"
            )

            print(
                f"FIRE:     "
                f"{fire_count:,}/"
                f"{TARGET_FIRE_ROWS:,}"
            )

            print(
                f"NON-FIRE: "
                f"{non_fire_count:,}/"
                f"{TARGET_FIRE_ROWS:,}"
            )

            print(
                f"TOTAL:    "
                f"{len(rows):,}/"
                f"{TARGET_ROWS:,}"
            )

            print(
                f"API failures: "
                f"{api_failures:,}"
            )

            print(
                f"Rejected negatives: "
                f"{rejected_negatives:,}"
            )

            print(
                f"Duplicates skipped: "
                f"{duplicates_skipped:,}"
            )


            # ----------------------------
            # CHECKPOINT
            # ----------------------------

            if (
                completed_since_save
                >= CHECKPOINT_EVERY_PAIRS
            ):

                save_checkpoint(
                    rows
                )

                completed_since_save = 0


        offset += PAGE_SIZE


    # -----------------------------------
    # FINAL SAVE
    # -----------------------------------

    save_checkpoint(
        rows
    )


    print("\n ==============================")
    print("V05 DATASET RUN FINISHED")
    print("==============================")

    print(
        f"FIRE rows: "
        f"{fire_count:,}"
    )

    print(
        f"NON-FIRE rows: "
        f"{non_fire_count:,}"
    )

    print(
        f"TOTAL rows: "
        f"{len(rows):,}"
    )

    print(
        f"\nSaved to:"
        f" {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()