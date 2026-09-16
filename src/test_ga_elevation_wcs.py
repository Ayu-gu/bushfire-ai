import rasterio
import requests


WCS_URL = (
    "https://services.ga.gov.au/gis/services/"
    "DEM_SRTM_1Second_2024/"
    "MapServer/WCSServer"
)

COVERAGE_ID = "1"

LATITUDE = -33.0
LONGITUDE = 150.0

OFFSET = 0.002


def main():

    print("=" * 40)
    print("GA SRTM ELEVATION TEST")
    print("=" * 40)

    min_lon = LONGITUDE - OFFSET
    max_lon = LONGITUDE + OFFSET

    min_lat = LATITUDE - OFFSET
    max_lat = LATITUDE + OFFSET

    bbox = (
        f"{min_lon},"
        f"{min_lat},"
        f"{max_lon},"
        f"{max_lat}"
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
        "width": 20,
        "height": 20,
    }

    response = requests.get(
        WCS_URL,
        params=params,
        timeout=60,
    )

    print(
        "\nRequest URL:"
    )

    print(
        response.url
    )

    print(
        "\nStatus:",
        response.status_code
    )

    if response.status_code != 200:

        print(
            "\nServer response:"
        )

        print(
            response.text[:2000]
        )

        response.raise_for_status()

    print(
        f"\nResponse bytes: "
        f"{len(response.content):,}"
    )

    with rasterio.MemoryFile(
        response.content
    ) as memory_file:

        with memory_file.open() as dataset:

            print(
                "Raster CRS:",
                dataset.crs
            )

            print(
                "Raster size:",
                dataset.width,
                "x",
                dataset.height
            )

            print(
                "Raster bounds:",
                dataset.bounds
            )

            value = next(
                dataset.sample(
                    [
                        (
                            LONGITUDE,
                            LATITUDE,
                        )
                    ]
                )
            )[0]

            print(
                "\nElevation:",
                value,
                "metres"
            )


if __name__ == "__main__":
    main()