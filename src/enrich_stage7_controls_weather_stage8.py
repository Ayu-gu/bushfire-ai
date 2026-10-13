"""
Stage 8 - Historical weather enrichment for matched controls
------------------------------------------------------------

Input:
    data/full_wildfires_matched_controls_stage7_complete.csv

For each matched non-fire control:
    - Use control latitude/longitude
    - Use the corresponding source wildfire date
    - Request 31 days of historical weather from Open-Meteo
    - Cache raw API responses separately from Stage 4
    - Reuse the exact Stage 4 weather feature calculations
    - Save progress incrementally

IMPORTANT:
    Stage 4 weather cache is NEVER reused because the same
    source_row_id refers to a different geographic location.
"""

from pathlib import Path
from datetime import datetime, timedelta
import json
import time

import pandas as pd
import requests

from enrich_full_wildfires_weather_stage4 import (
    build_weather_features,
)


# ============================================================
# PATHS / SETTINGS
# ============================================================

INPUT_FILE = Path(
    "data/full_wildfires_matched_controls_stage7_complete.csv"
)

OUTPUT_FILE = Path(
    "data/full_wildfires_controls_stage8.csv"
)

CACHE_DIR = Path(
    "data/weather_cache_stage8_controls"
)

FAILURE_LOG = Path(
    "data/weather_failures_stage8.csv"
)

WEATHER_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)

REQUEST_TIMEOUT = 60
MAX_RETRIES = 5
REQUEST_DELAY = 1.0
TEST_LIMIT = None

# Save output periodically during the full run.
CHECKPOINT_EVERY = 100


# ============================================================
# CACHE
# ============================================================

def cache_path(source_row_id):
    return (
        CACHE_DIR
        / f"{source_row_id}.json"
    )


def load_cached_weather(source_row_id):
    path = cache_path(
        source_row_id
    )

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
            f"Warning: invalid Stage 8 cache "
            f"for {source_row_id}. "
            f"Re-downloading."
        )

        return None


def save_weather_cache(
    source_row_id,
    weather
):
    path = cache_path(
        source_row_id
    )

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

def fetch_control_weather(
    source_row_id,
    latitude,
    longitude,
    target_date
):
    """
    Fetch 31 days of historical weather for the
    CONTROL location.

    Window:
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
# SAVE HELPERS
# ============================================================

def save_results(results):
    """
    Save all completed Stage 8 rows.

    The results list includes rows loaded from a previous
    checkpoint plus rows completed during this run.
    """
    if not results:
        return

    result_df = pd.DataFrame(
        results
    )

    # Protect against accidental duplicate controls.
    result_df = (
        result_df
        .drop_duplicates(
            subset=["source_row_id"],
            keep="last"
        )
        .sort_values(
            "source_row_id"
        )
    )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False
    )


def save_failures(failures):
    if not failures:
        if FAILURE_LOG.exists():
            FAILURE_LOG.unlink()

        return

    pd.DataFrame(
        failures
    ).to_csv(
        FAILURE_LOG,
        index=False
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 65)
    print(
        "STAGE 8 - MATCHED CONTROL HISTORICAL WEATHER"
    )
    print("=" * 65)

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
        f"Stage 7 controls: "
        f"{len(df):,}"
    )

    required_columns = {
        "source_row_id",
        "event_id",
        "source_date",
        "control_latitude",
        "control_longitude",
    }

    missing_columns = (
        required_columns
        - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Stage 7 is missing required "
            f"columns: {sorted(missing_columns)}"
        )

    if TEST_LIMIT is not None:
        work_df = df.head(
            TEST_LIMIT
        ).copy()

        print(
            f"SMOKE TEST MODE: "
            f"{len(work_df):,} controls"
        )

    else:
        work_df = df.copy()

        print(
            "FULL DATASET MODE"
        )

    # ========================================================
    # RESUME EXISTING PROGRESS
    # ========================================================

    results = []
    failures = []

    completed_ids = set()

    if OUTPUT_FILE.exists():
        existing_df = pd.read_csv(
            OUTPUT_FILE
        )

        if not existing_df.empty:
            existing_df = (
                existing_df
                .drop_duplicates(
                    subset=["source_row_id"],
                    keep="last"
                )
            )

            completed_ids = set(
                existing_df[
                    "source_row_id"
                ]
                .astype(int)
                .tolist()
            )

            results = (
                existing_df
                .to_dict(
                    orient="records"
                )
            )

        print(
            f"Existing completed controls: "
            f"{len(completed_ids):,}"
        )

    # Only process controls that have not already
    # been successfully enriched.
    work_df = work_df[
        ~work_df["source_row_id"]
        .astype(int)
        .isin(completed_ids)
    ].copy()

    print(
        f"Controls remaining this run: "
        f"{len(work_df):,}"
    )

    cached_count = 0
    downloaded_count = 0

    for number, (_, row) in enumerate(
        work_df.iterrows(),
        start=1
    ):
        source_row_id = int(
            row["source_row_id"]
        )

        target_date = str(
            row["source_date"]
        )

        latitude = float(
            row["control_latitude"]
        )

        longitude = float(
            row["control_longitude"]
        )

        print(
            f"[{number:04d}/{len(work_df):04d}] "
            f"ID {source_row_id} | "
            f"{target_date} | "
            f"{latitude:.4f}, "
            f"{longitude:.4f}",
            end=" "
        )

        try:
            weather, from_cache = (
                fetch_control_weather(
                    source_row_id,
                    latitude,
                    longitude,
                    target_date
                )
            )

            # EXACT Stage 4 feature calculation.
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

            save_results(
                results
            )

            save_failures(
                failures
            )

            print(
                "Current progress saved."
            )

            break

        except Exception as error:
            print(
                f"-> FAILED: {error}"
            )

            failures.append({
                "source_row_id":
                    source_row_id,

                "source_date":
                    target_date,

                "control_latitude":
                    latitude,

                "control_longitude":
                    longitude,

                "error":
                    str(error),
            })

        if (
            number % CHECKPOINT_EVERY == 0
        ):
            save_results(
                results
            )

            save_failures(
                failures
            )

            print(
                f"--- checkpoint saved "
                f"at {number:,} rows ---"
            )

    save_results(
        results
    )

    save_failures(
        failures
    )

    print()
    print("=" * 65)
    print("STAGE 8 SUMMARY")
    print("=" * 65)

    print(
        f"Requested controls: "
        f"{len(work_df):,}"
    )

    print(
        f"Successful: "
        f"{len(results):,}"
    )

    print(
        f"Downloaded: "
        f"{downloaded_count:,}"
    )

    print(
        f"Loaded from cache: "
        f"{cached_count:,}"
    )

    print(
        f"Failed: "
        f"{len(failures):,}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
