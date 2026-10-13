"""
Stage 4 - Historical weather enrichment
---------------------------------------

Input:
    data/full_wildfires_2000plus_stage3.csv

Test mode:
    First 50 wildfire records only.

For each wildfire:
    - Request 31 days of historical weather from Open-Meteo
    - Save the raw API response locally
    - Calculate the same weather features used by V07
    - Write an enriched Stage 4 test CSV

The raw cache makes the process resumable.
"""

from pathlib import Path
from datetime import datetime, timedelta
import json
import math
import time

import pandas as pd
import requests


# ============================================================
# PATHS / SETTINGS
# ============================================================

INPUT_FILE = Path(
    "data/full_wildfires_2000plus_stage3.csv"
)

OUTPUT_FILE = Path(
    "data/full_wildfires_2000plus_stage4.csv"
)

CACHE_DIR = Path(
    "data/weather_cache_stage4"
)

FAILURE_LOG = Path(
    "data/weather_failures_stage4.csv"
)

WEATHER_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)

RETRY_OUTPUT_FILE = Path(
    "data/weather_recovered_stage4.csv"
)

RETRY_FAILURE_LOG = Path(
    "data/weather_failures_stage4_retry.csv"
)

TEST_LIMIT = None

REQUEST_TIMEOUT = 60
MAX_RETRIES = 5

REQUEST_DELAY = 1.0


# ============================================================
# HELPERS
# ============================================================

def get_season(month):
    if month in [12, 1, 2]:
        return 0

    if month in [3, 4, 5]:
        return 1

    if month in [6, 7, 8]:
        return 2

    return 3


def days_since_rain(rainfall):
    """
    Same logic used in V07.

    The final rainfall value is the target/fire day,
    so rainfall[:-1] checks only previous days.
    """

    count = 0

    for value in reversed(rainfall[:-1]):
        if value is not None and value >= 1:
            return count

        count += 1

    return count


def calculate_vpd(max_temp, avg_humidity):
    """
    Same VPD calculation used in V07.
    """

    saturation_vp = (
        0.6108
        * math.exp(
            (17.27 * max_temp)
            / (max_temp + 237.3)
        )
    )

    actual_vp = (
        saturation_vp
        * (avg_humidity / 100)
    )

    return saturation_vp - actual_vp


# ============================================================
# CACHE
# ============================================================

def cache_path(source_row_id):
    return CACHE_DIR / f"{source_row_id}.json"


def load_cached_weather(source_row_id):
    path = cache_path(source_row_id)

    if not path.exists():
        return None

    try:
        with path.open(
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception:
        print(
            f"Warning: invalid cache file "
            f"for {source_row_id}. Re-downloading."
        )

        return None


def save_weather_cache(
    source_row_id,
    weather
):
    path = cache_path(source_row_id)

    with path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            weather,
            file,
            indent=2
        )


# ============================================================
# OPEN-METEO REQUEST
# ============================================================

def fetch_weather(
    source_row_id,
    latitude,
    longitude,
    target_date
):
    """
    Return cached weather if available.

    Otherwise request 31 days:
        target date - 30 days
        through target date.
    """

    cached = load_cached_weather(
        source_row_id
    )

    if cached is not None:
        return cached, True

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

        "start_date": start_date.strftime(
            "%Y-%m-%d"
        ),

        "end_date": target_date,

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

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):
        try:
            response = requests.get(
                WEATHER_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            # Retry rate limits / server errors.
            if (
                response.status_code == 429
                or response.status_code >= 500
            ):
                wait_seconds = (
                    2 ** (attempt - 1)
                )

                print(
                    f"HTTP {response.status_code}. "
                    f"Retry {attempt}/{MAX_RETRIES} "
                    f"in {wait_seconds}s..."
                )

                time.sleep(
                    wait_seconds
                )

                continue

            response.raise_for_status()

            weather = response.json()

            if "daily" not in weather:
                raise ValueError(
                    "API response has no daily data."
                )

            if "hourly" not in weather:
                raise ValueError(
                    "API response has no hourly data."
                )

            save_weather_cache(
                source_row_id,
                weather
            )

            time.sleep(
                REQUEST_DELAY
            )

            return weather, False

        except Exception as error:
            last_error = error

            if attempt < MAX_RETRIES:
                wait_seconds = (
                    2 ** (attempt - 1)
                )

                print(
                    f"Request failed: {error}. "
                    f"Retrying in "
                    f"{wait_seconds}s..."
                )

                time.sleep(
                    wait_seconds
                )

    raise RuntimeError(
        f"Weather request failed after "
        f"{MAX_RETRIES} attempts: "
        f"{last_error}"
    )


# ============================================================
# FEATURE BUILDING
# ============================================================

def build_weather_features(
    weather,
    target_date
):
    """
    Reproduce V07 weather feature logic.
    """

    daily = weather["daily"]

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

    # V07 used the final 24 hourly humidity
    # readings for the target day.
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

    if len(rainfall) != 31:
        raise ValueError(
            f"Expected 31 rainfall days, "
            f"received {len(rainfall)}."
        )

    avg_humidity = (
        sum(valid_humidity)
        / len(valid_humidity)
    )

    rain_today = (
        rainfall[-1]
        if rainfall[-1] is not None
        else 0
    )

    # Same slices as V07.
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
            100 - avg_humidity
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
        "month": month,
        "day_of_year": day_of_year,
        "season": season,

        "max_temp": max_temp,
        "min_temp": min_temp,
        "avg_humidity": avg_humidity,
        "max_wind": max_wind,

        "rain_today": rain_today,
        "rain_last_7_days": rain_7,
        "rain_last_30_days": rain_30,
        "days_since_rain": dry_days,

        "temp_humidity_index":
            temp_humidity_index,

        "temp_wind_index":
            temp_wind_index,

        "dryness_index":
            dryness_index,

        "vpd":
            vpd,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("STAGE 4 WEATHER ENRICHMENT - FULL DATASET")
    print("=" * 60)

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: "
            f"{INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"Stage 3 rows: "
        f"{len(df):,}"
    )

    required_columns = {
        "source_row_id",
        "event_id",
        "date",
        "latitude",
        "longitude",
    }

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    # Retry only rows that failed during the first Stage 4 run
    failed_df = pd.read_csv(FAILURE_LOG)

    failed_ids = set(
        failed_df["source_row_id"]
        .astype(int)
        .tolist()
        )
    test_df = df[
        df["source_row_id"]
        .astype(int)
        .isin(failed_ids)
        ].copy()

    print(
        f"Retry mode: {len(test_df):,} "
        f"previously failed rows selected."
        )
    
    print(
        f"Test rows: "
        f"{len(test_df):,}"
    )

    results = []
    failures = []

    cached_count = 0
    downloaded_count = 0

    for number, (_, row) in enumerate(
        test_df.iterrows(),
        start=1
    ):
        source_row_id = int(
            row["source_row_id"]
        )

        target_date = str(
            row["date"]
        )

        latitude = float(
            row["latitude"]
        )

        longitude = float(
            row["longitude"]
        )

        print(
            f"[{number:02d}/{len(test_df)}] "
            f"ID {source_row_id} | "
            f"{target_date} | "
            f"{latitude:.4f}, "
            f"{longitude:.4f}",
            end=" "
        )

        try:
            weather, from_cache = (
                fetch_weather(
                    source_row_id,
                    latitude,
                    longitude,
                    target_date
                )
            )

            features = (
                build_weather_features(
                    weather,
                    target_date
                )
            )

            enriched = (
                row.to_dict()
            )

            enriched.update(
                features
            )

            results.append(
                enriched
            )

            if from_cache:
                cached_count += 1
                print("-> CACHE")
            else:
                downloaded_count += 1
                print("-> OK")

        except KeyboardInterrupt:
            print(
                "\nStopped safely by user."
            )
            break

        except Exception as error:
            print(
                f"-> FAILED: {error}"
            )

            failures.append({
                "source_row_id":
                    source_row_id,

                "date":
                    target_date,

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "error":
                    str(error),
            })

    # Save successful rows.
    if results:
        result_df = pd.DataFrame(
            results
        )

        result_df.to_csv(
            RETRY_OUTPUT_FILE,
            index=False
        )

        print()
        print(
            f"Saved enriched rows: "
            f"{len(result_df):,}"
        )

        print(
            f"Output: {RETRY_OUTPUT_FILE}"
        )

    # Save failures.
    if failures:
        failure_df = pd.DataFrame(
            failures
        )

        failure_df.to_csv(
            RETRY_FAILURE_LOG,
            index=False
        )

        print(
            f"Failures saved: "
            f"{RETRY_FAILURE_LOG}"
        )

    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(
        f"Downloaded: {downloaded_count}"
    )

    print(
        f"Loaded from cache: "
        f"{cached_count}"
    )

    print(
        f"Failed: {len(failures)}"
    )

    print(
        f"Successful: {len(results)}"
    )


if __name__ == "__main__":
    main()