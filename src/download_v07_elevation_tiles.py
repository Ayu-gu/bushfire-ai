import math
import os

import pandas as pd
import rasterio
import requests

from rasterio.merge import merge


INPUT_PATH = (
    "data/v07_spatial_negatives_vegetation.csv"
)

TILE_DIR = (
    "data/elevation_tiles_v07"
)

OUTPUT_PATH = (
    "data/v07_spatial_negatives_enriched.csv"
)

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


def tile_bounds(latitude, longitude):

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
        max_lat
    )


def tile_name(bounds):

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


def download_tile(
    bounds,
    output_path
):

    min_lon, min_lat, max_lon, max_lat = (
        bounds
    )

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
        "service":
            "WCS",

        "request":
            "GetCoverage",

        "version":
            "1.0.0",

        "coverage":
            COVERAGE_ID,

        "bbox":
            bbox,

        "crs":
            "EPSG:4326",

        "response_crs":
            "EPSG:4326",

        "format":
            "GeoTIFF",

        "width":
            width,

        "height":
            height,
    }

    response = requests.get(
        WCS_URL,
        params=params,
        timeout=180,
    )

    response.raise_for_status()

    with open(
        output_path,
        "wb"
    ) as file:

        file.write(
            response.content
        )


def main():

    print("=" * 44)
    print("BUSHFIRE AI V07 ELEVATION TILES")
    print("=" * 44)

    os.makedirs(
        TILE_DIR,
        exist_ok=True
    )

    df = pd.read_csv(
        INPUT_PATH
    )

    print(
        f"\nRows: "
        f"{len(df):,}"
    )

    required_tiles = {}

    for row in df.itertuples(
        index=False
    ):

        bounds = tile_bounds(
            row.latitude,
            row.longitude
        )

        name = tile_name(
            bounds
        )

        required_tiles[
            name
        ] = bounds

    print(
        f"Unique DEM tiles required: "
        f"{len(required_tiles):,}"
    )

    downloaded_paths = []

    for index, (
        name,
        bounds
    ) in enumerate(
        required_tiles.items(),
        start=1
    ):

        path = os.path.join(
            TILE_DIR,
            name
        )

        if os.path.exists(
            path
        ):

            print(
                f"Tile "
                f"{index}/"
                f"{len(required_tiles)} "
                f"cached: "
                f"{name}"
            )

        else:

            print(
                f"Downloading tile "
                f"{index}/"
                f"{len(required_tiles)} "
                f"{name}"
            )

            download_tile(
                bounds,
                path
            )

        downloaded_paths.append(
            path
        )

    print(
        "\nSampling elevation..."
    )

    tile_datasets = {}

    elevations = []

    try:

        for row in df.itertuples(
            index=False
        ):

            bounds = tile_bounds(
                row.latitude,
                row.longitude
            )

            name = tile_name(
                bounds
            )

            if name not in tile_datasets:

                path = os.path.join(
                    TILE_DIR,
                    name
                )

                tile_datasets[
                    name
                ] = rasterio.open(
                    path
                )

            dataset = tile_datasets[
                name
            ]

            value = next(
                dataset.sample(
                    [
                        (
                            row.longitude,
                            row.latitude
                        )
                    ]
                )
            )[0]

            elevations.append(
                float(value)
            )

    finally:

        for dataset in (
            tile_datasets.values()
        ):

            dataset.close()

    df[
        "elevation"
    ] = elevations

    print(
        f"\nMissing elevation: "
        f"{df['elevation'].isna().sum():,}"
    )

    print(
        f"Elevation range: "
        f"{df['elevation'].min():.1f} "
        f"to "
        f"{df['elevation'].max():.1f} metres"
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n" + "=" * 44)
    print("V07 ELEVATION COMPLETE")
    print("=" * 44)

    print(
        f"\nSaved to "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()