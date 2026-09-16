import math
import os
import random
import time

import pandas as pd
import requests

from datetime import datetime, timedelta


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_DATASET = "data/training_dataset_v06.csv"

SPATIAL_OUTPUT = "data/v07_spatial_negatives.csv"

TARGET_SPATIAL_NEGATIVES = 5000

FIRE_URL = (
    "https://portal.data.nsw.gov.au/arcgis/rest/services/"
    "Hosted/NSWFireHistory/FeatureServer/0/query"
)

WEATHER_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)

REQUEST_DELAY_SECONDS = 1.0
MAX_API_RETRIES = 5

MIN_DISTANCE_KM = 20
MAX_DISTANCE_KM = 100

FIRE_CHECK_RADIUS_KM = 5
MAX_LOCATION_ATTEMPTS = 30

CHECKPOINT_EVERY = 25

RANDOM_SEED = 42


# ============================================================
# REPRODUCIBILITY
# ============================================================

random.seed(
    RANDOM_SEED
)


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
                status_code = (
                    error.response.status_code
                )

            if status_code == 429:
                wait_seconds = 60 * attempt

            elif status_code in [
                500,
                502,
                503,
                504,
            ]:
                wait_seconds = 15 * attempt

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
# RANDOM LOCATION AROUND FIRE
# ============================================================

def random_location_nearby(
    latitude,
    longitude
):

    distance_km = random.uniform(
        MIN_DISTANCE_KM,
        MAX_DISTANCE_KM
    )

    bearing = random.uniform(
        0,
        2 * math.pi
    )

    earth_radius_km = 6371.0

    lat1 = math.radians(
        latitude
    )

    lon1 = math.radians(
        longitude
    )

    angular_distance = (
        distance_km
        / earth_radius_km
    )

    lat2 = math.asin(
        math.sin(lat1)
        * math.cos(angular_distance)
        +
        math.cos(lat1)
        * math.sin(angular_distance)
        * math.cos(bearing)
    )

    lon2 = lon1 + math.atan2(
        math.sin(bearing)
        * math.sin(angular_distance)
        * math.cos(lat1),

        math.cos(angular_distance)
        -
        math.sin(lat1)
        * math.sin(lat2)
    )

    return (
        math.degrees(lat2),
        math.degrees(lon2)
    )


# ============================================================
# VERIFY NO FIRE NEAR CANDIDATE
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

    start_date = start.strftime(
        "%Y-%m-%d"
    )

    end_date = end.strftime(
        "%Y-%m-%d"
    )

    where_clause = (
        "fire_type = 'Bushfire' "
        "AND ignition_date IS NOT NULL "
        f"AND ignition_date >= DATE '{start_date}' "
        f"AND ignition_date <= DATE '{end_date}'"
    )

    params = {
        "where":
            where_clause,

        "geometry":
            f"{longitude},{latitude}",

        "geometryType":
            "esriGeometryPoint",

        "inSR":
            "4326",

        "spatialRel":
            "esriSpatialRelIntersects",

        "distance":
            FIRE_CHECK_RADIUS_KM,

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

    count = result.get(
        "count",
        0
    )

    return count > 0


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
        "latitude":
            latitude,

        "longitude":
            longitude,

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
# FEATURE HELPERS
# ============================================================

def get_season(
    month
):

    if month in [
        12,
        1,
        2,
    ]:
        return 0

    if month in [
        3,
        4,
        5,
    ]:
        return 1

    if month in [
        6,
        7,
        8,
    ]:
        return 2

    return 3


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
# BUILD WEATHER FEATURES
# ============================================================

def build_weather_features(
    latitude,
    longitude,
    target_date
):

    weather = fetch_weather(
        latitude,
        longitude,
        target_date
    )

    daily = weather[
        "daily"
    ]

    rainfall = daily[
        "precipitation_sum"
    ]

    max_temp = daily[
        "temperature_2m_max"
    ][-1]

    min_temp = daily[
        "temperature_2m_min"
    ][-1]

    max_wind = daily[
        "wind_speed_10m_max"
    ][-1]

    humidity = weather[
        "hourly"
    ][
        "relative_humidity_2m"
    ][-24:]

    valid_humidity = [
        value
        for value in humidity
        if value is not None
    ]

    if (
        max_temp is None
        or min_temp is None
        or max_wind is None
        or not valid_humidity
    ):
        raise ValueError(
            "Required weather data missing."
        )

    avg_humidity = (
        sum(valid_humidity)
        / len(valid_humidity)
    )

    rain_today = (
        rainfall[-1]
        or 0
    )

    rain_7 = sum(
        value or 0
        for value in rainfall[-8:-1]
    )

    rain_30 = sum(
        value or 0
        for value in rainfall[:-1]
    )

    dry_days = days_since_rain(
        rainfall
    )

    date = datetime.strptime(
        target_date,
        "%Y-%m-%d"
    )

    month = date.month

    day_of_year = (
        date.timetuple().tm_yday
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
        (dry_days + 1)
        /
        (rain_30 + 1)
    )

    vpd = calculate_vpd(
        max_temp,
        avg_humidity
    )

    return {
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
            round(
                avg_humidity,
                1
            ),

        "max_wind":
            max_wind,

        "rain_today":
            rain_today,

        "rain_last_7_days":
            round(
                rain_7,
                2
            ),

        "rain_last_30_days":
            round(
                rain_30,
                2
            ),

        "days_since_rain":
            dry_days,

        "temp_humidity_index":
            temp_humidity_index,

        "temp_wind_index":
            temp_wind_index,

        "dryness_index":
            dryness_index,

        "vpd":
            vpd,

        "fire":
            0,

        "negative_type":
            "spatial",
    }


# ============================================================
# CHECKPOINT
# ============================================================

def load_existing():

    if not os.path.exists(
        SPATIAL_OUTPUT
    ):
        return pd.DataFrame()

    if os.path.getsize(
        SPATIAL_OUTPUT
    ) == 0:
        return pd.DataFrame()

    return pd.read_csv(
        SPATIAL_OUTPUT
    )


def save_checkpoint(
    rows
):

    df = pd.DataFrame(
        rows
    )

    df.to_csv(
        SPATIAL_OUTPUT,
        index=False
    )

    print(
        f"\nCheckpoint saved: "
        f"{len(df):,}/"
        f"{TARGET_SPATIAL_NEGATIVES:,}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 44)
    print("BUSHFIRE AI V07 SPATIAL NEGATIVES")
    print("=" * 44)

    source_df = pd.read_csv(
        SOURCE_DATASET
    )

    fire_df = (
        source_df[
            source_df["fire"] == 1
        ]
        .copy()
        .reset_index(drop=True)
    )

    existing_df = load_existing()

    if existing_df.empty:

        rows = []
        completed_ids = set()

    else:

        rows = (
            existing_df
            .to_dict("records")
        )

        completed_ids = set(
            existing_df[
                "source_fire_id"
            ]
            .astype(str)
        )

    print(
        f"\nAvailable fires: "
        f"{len(fire_df):,}"
    )

    print(
        f"Spatial negatives already saved: "
        f"{len(rows):,}"
    )

    rejected_fire = 0
    failed_weather = 0
    failed_candidates = 0

    completed_since_save = 0

    for fire_row in (
        fire_df.itertuples(
            index=False
        )
    ):

        if (
            len(rows)
            >= TARGET_SPATIAL_NEGATIVES
        ):
            break

        source_fire_id = str(
            fire_row.source_fire_id
        )

        if (
            source_fire_id
            in completed_ids
        ):
            continue

        fire_date = str(
            fire_row.date
        )

        candidate_created = False

        for attempt in range(
            1,
            MAX_LOCATION_ATTEMPTS + 1
        ):

            latitude, longitude = (
                random_location_nearby(
                    fire_row.latitude,
                    fire_row.longitude
                )
            )

            try:

                if fire_nearby(
                    latitude,
                    longitude,
                    fire_date
                ):

                    rejected_fire += 1
                    continue

            except Exception:

                failed_candidates += 1
                continue

            try:

                features = (
                    build_weather_features(
                        latitude,
                        longitude,
                        fire_date
                    )
                )

            except Exception as error:

                failed_weather += 1

                print(
                    f"Weather lookup failed: "
                    f"{error}"
                )

                continue

            features[
                "source_fire_id"
            ] = source_fire_id

            rows.append(
                features
            )

            completed_ids.add(
                source_fire_id
            )

            candidate_created = True
            completed_since_save += 1

            print(
                f"\nSpatial negative "
                f"{len(rows):,}/"
                f"{TARGET_SPATIAL_NEGATIVES:,}"
            )

            print(
                f"Source fire ID: "
                f"{source_fire_id}"
            )

            print(
                f"Date: "
                f"{fire_date}"
            )

            print(
                f"Location: "
                f"{latitude:.4f}, "
                f"{longitude:.4f}"
            )

            print(
                f"Rejected fire candidates: "
                f"{rejected_fire:,}"
            )

            print(
                f"Weather failures: "
                f"{failed_weather:,}"
            )

            break

        if not candidate_created:

            failed_candidates += 1

        if (
            completed_since_save
            >= CHECKPOINT_EVERY
        ):

            save_checkpoint(
                rows
            )

            completed_since_save = 0

    save_checkpoint(
        rows
    )

    print("\n" + "=" * 44)
    print("V07 SPATIAL NEGATIVE RUN FINISHED")
    print("=" * 44)

    print(
        f"\nSpatial negatives: "
        f"{len(rows):,}"
    )

    print(
        f"Rejected fire candidates: "
        f"{rejected_fire:,}"
    )

    print(
        f"Weather failures: "
        f"{failed_weather:,}"
    )

    print(
        f"Failed candidates: "
        f"{failed_candidates:,}"
    )


if __name__ == "__main__":
    main()