import math
import os
import time

import pandas as pd
import rasterio
import requests


# ============================================================
# PATHS
# ============================================================

INPUT_PATH = (
    "data/full_wildfires_2000plus_stage4_complete.csv"
)

TILE_DIR = (
    "data/elevation_tiles_v07"
)

OUTPUT_PATH = (
    "data/full_wildfires_2000plus_stage5.csv"
)


# ============================================================
# GEOSCIENCE AUSTRALIA DEM
# ============================================================

WCS_URL = (
    "https://services.ga.gov.au/gis/services/"
    "DEM_SRTM_1Second_2024/"
    "MapServer/WCSServer"
)

COVERAGE_ID = "1"

TILE_SIZE_DEGREES = 0.25

ARC_SECONDS_PER_DEGREE = 3600
DEM_ARC_SECONDS = 1

PIXELS_PER_DEGREE = (
    ARC_SECONDS_PER_DEGREE
    // DEM_ARC_SECONDS
)


# ============================================================
# TILE HELPERS
# ============================================================

def tile_bounds(latitude, longitude):
    """
    Return the 0.25-degree DEM tile containing a coordinate.
    """

    min_lon = (
        math.floor(
            longitude / TILE_SIZE_DEGREES
        )
        * TILE_SIZE_DEGREES
    )

    min_lat = (
        math.floor(
            latitude / TILE_SIZE_DEGREES
        )
        * TILE_SIZE_DEGREES
    )

    max_lon = (
        min_lon + TILE_SIZE_DEGREES
    )

    max_lat = (
        min_lat + TILE_SIZE_DEGREES
    )

    return (
        min_lon,
        min_lat,
        max_lon,
        max_lat,
    )


def tile_name(bounds):
    """
    Convert tile bounds to the same filename convention
    used by the existing V07 elevation cache.
    """

    min_lon, min_lat, _, _ = bounds

    lon_code = int(
        round(min_lon * 100)
    )

    lat_code = int(
        round(min_lat * 100)
    )

    return (
        f"tile_{lat_code}_{lon_code}.tif"
    )


# ============================================================
# TILE VALIDATION
# ============================================================

def validate_tile(path):
    """
    Check that a GeoTIFF exists and Rasterio can open it.
    """

    if not os.path.exists(path):
        return False

    if os.path.getsize(path) == 0:
        return False

    try:
        with rasterio.open(path) as dataset:
            if dataset.width <= 0:
                return False

            if dataset.height <= 0:
                return False

            if dataset.count < 1:
                return False

        return True

    except Exception:
        return False


# ============================================================
# TILE DOWNLOAD
# ============================================================

def download_tile(bounds, output_path):
    """
    Download one 0.25-degree SRTM DEM tile from
    Geoscience Australia's WCS service.
    """

    min_lon, min_lat, max_lon, max_lat = bounds

    bbox = (
        f"{min_lon},"
        f"{min_lat},"
        f"{max_lon},"
        f"{max_lat}"
    )

    width = int(
        TILE_SIZE_DEGREES
        * PIXELS_PER_DEGREE
    )

    height = int(
        TILE_SIZE_DEGREES
        * PIXELS_PER_DEGREE
    )

    params = {
        "service": "WCS",
        "request": "GetCoverage",
        "version": "1.0.0",
        "coverage": COVERAGE_ID,
        "bbox": bbox,
        "crs": "EPSG:4326",
        "response_crs": "EPSG:4326",
        "format": "GeoTIFF",
        "width": width,
        "height": height,
    }

    # Download to a temporary file first.
    # This prevents an interrupted request from leaving
    # a corrupt .tif that looks cached on the next run.
    temp_path = output_path + ".part"

    if os.path.exists(temp_path):
        os.remove(temp_path)

    response = requests.get(
        WCS_URL,
        params=params,
        timeout=180,
    )

    response.raise_for_status()

    with open(temp_path, "wb") as file:
        file.write(response.content)

    if not validate_tile(temp_path):
        if os.path.exists(temp_path):
            os.remove(temp_path)

        raise ValueError(
            "Downloaded file is not a valid DEM GeoTIFF."
        )

    os.replace(
        temp_path,
        output_path,
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("BUSHFIRE AI - FULL WILDFIRE ELEVATION STAGE 5")
    print("=" * 60)

    os.makedirs(
        TILE_DIR,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Load Stage 4 complete dataset
    # --------------------------------------------------------

    df = pd.read_csv(
        INPUT_PATH
    )

    print(
        f"\nInput rows: "
        f"{len(df):,}"
    )

    print(
        f"Input columns: "
        f"{len(df.columns)}"
    )

    if len(df) != 9249:
        raise ValueError(
            f"Expected 9,249 Stage 4 rows, "
            f"found {len(df):,}."
        )

    if df["source_row_id"].duplicated().any():
        raise ValueError(
            "Duplicate source_row_id detected "
            "in Stage 4 input."
        )

    if df["latitude"].isna().any():
        raise ValueError(
            "Missing latitude detected."
        )

    if df["longitude"].isna().any():
        raise ValueError(
            "Missing longitude detected."
        )

    # --------------------------------------------------------
    # Determine required DEM tiles
    # --------------------------------------------------------

    required_tiles = {}

    for row in df.itertuples(
        index=False
    ):
        bounds = tile_bounds(
            row.latitude,
            row.longitude,
        )

        name = tile_name(
            bounds
        )

        required_tiles[name] = bounds

    print(
        f"\nUnique DEM tiles required: "
        f"{len(required_tiles):,}"
    )

    cached_count = 0
    missing_tiles = []

    for name, bounds in required_tiles.items():
        path = os.path.join(
            TILE_DIR,
            name,
        )

        if validate_tile(path):
            cached_count += 1
        else:
            missing_tiles.append(
                (name, bounds)
            )

    print(
        f"Valid cached tiles:       "
        f"{cached_count:,}"
    )

    print(
        f"Tiles to download:        "
        f"{len(missing_tiles):,}"
    )

    # --------------------------------------------------------
    # Download only missing/invalid tiles
    # --------------------------------------------------------

    if missing_tiles:
        print(
            "\nDownloading missing DEM tiles..."
        )

    for index, (
        name,
        bounds,
    ) in enumerate(
        missing_tiles,
        start=1,
    ):
        path = os.path.join(
            TILE_DIR,
            name,
        )

        print(
            f"[{index}/{len(missing_tiles)}] "
            f"{name}"
        )

        max_attempts = 3
        success = False

        for attempt in range(
            1,
            max_attempts + 1,
        ):
            try:
                download_tile(
                    bounds,
                    path,
                )

                success = True
                break

            except Exception as error:
                print(
                    f"  Attempt "
                    f"{attempt}/{max_attempts} "
                    f"failed: {error}"
                )

                if attempt < max_attempts:
                    time.sleep(2)

        if not success:
            raise RuntimeError(
                f"Failed to download "
                f"{name} after "
                f"{max_attempts} attempts."
            )

    # --------------------------------------------------------
    # Validate ALL required tiles
    # --------------------------------------------------------

    print(
        "\nValidating complete DEM coverage..."
    )

    invalid_tiles = []

    for name in required_tiles:
        path = os.path.join(
            TILE_DIR,
            name,
        )

        if not validate_tile(path):
            invalid_tiles.append(
                name
            )

    if invalid_tiles:
        print(
            "\nInvalid/missing tiles:"
        )

        for name in invalid_tiles:
            print(
                f"  - {name}"
            )

        raise RuntimeError(
            f"{len(invalid_tiles)} required "
            f"DEM tiles are unavailable."
        )

    print(
        f"DEM tile coverage: "
        f"{len(required_tiles):,}/"
        f"{len(required_tiles):,} "
        f"tiles"
    )

    # --------------------------------------------------------
    # Sample elevation
    # --------------------------------------------------------

    print(
        "\nSampling elevation for "
        "all fire observations..."
    )

    tile_datasets = {}

    elevations = []

    try:
        for index, row in enumerate(
            df.itertuples(index=False),
            start=1,
        ):
            bounds = tile_bounds(
                row.latitude,
                row.longitude,
            )

            name = tile_name(
                bounds
            )

            if name not in tile_datasets:
                path = os.path.join(
                    TILE_DIR,
                    name,
                )

                tile_datasets[name] = (
                    rasterio.open(path)
                )

            dataset = tile_datasets[
                name
            ]

            sampled = next(
                dataset.sample(
                    [
                        (
                            row.longitude,
                            row.latitude,
                        )
                    ],
                    masked=True,
                )
            )[0]

            # Rasterio masked values represent NoData.
            if getattr(
                sampled,
                "mask",
                False,
            ):
                elevation = float("nan")

            else:
                elevation = float(
                    sampled
                )

                if not math.isfinite(
                    elevation
                ):
                    elevation = float(
                        "nan"
                    )

            elevations.append(
                elevation
            )

            if (
                index % 1000 == 0
                or index == len(df)
            ):
                print(
                    f"  Sampled "
                    f"{index:,}/"
                    f"{len(df):,}"
                )

    finally:
        for dataset in (
            tile_datasets.values()
        ):
            dataset.close()

    df["elevation"] = elevations

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    print(
        "\nRunning Stage 5 integrity checks..."
    )

    missing_elevation = int(
        df["elevation"]
        .isna()
        .sum()
    )

    nonfinite_elevation = int(
        (~df["elevation"].apply(
            math.isfinite
        )).sum()
    )

    duplicate_ids = int(
        df["source_row_id"]
        .duplicated()
        .sum()
    )

    if missing_elevation != 0:
        raise ValueError(
            f"{missing_elevation:,} rows "
            f"have missing elevation."
        )

    if nonfinite_elevation != 0:
        raise ValueError(
            f"{nonfinite_elevation:,} rows "
            f"have invalid elevation."
        )

    if duplicate_ids != 0:
        raise ValueError(
            f"{duplicate_ids:,} duplicate "
            f"source_row_id values detected."
        )

    if len(df) != 9249:
        raise ValueError(
            "Stage 5 row count changed "
            "unexpectedly."
        )

    # --------------------------------------------------------
    # Save only after every validation passes
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\n" + "=" * 60)
    print("STAGE 5 ELEVATION COMPLETE")
    print("=" * 60)

    print(
        f"\nRows:                "
        f"{len(df):,}"
    )

    print(
        f"Columns:             "
        f"{len(df.columns)}"
    )

    print(
        f"Unique source IDs:   "
        f"{df['source_row_id'].nunique():,}"
    )

    print(
        f"Missing elevation:   "
        f"{missing_elevation:,}"
    )

    print(
        f"Elevation minimum:   "
        f"{df['elevation'].min():.1f} m"
    )

    print(
        f"Elevation maximum:   "
        f"{df['elevation'].max():.1f} m"
    )

    print(
        f"Elevation mean:      "
        f"{df['elevation'].mean():.1f} m"
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()