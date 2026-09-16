import rasterio
from pyproj import Transformer


RASTER_PATH = (
    "/Users/ayubgurung/Downloads/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_108/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_5m.tif"
)

LATITUDE = -30.4834
LONGITUDE = 141.5560


with rasterio.open(
    RASTER_PATH
) as dataset:

    print("Raster CRS:", dataset.crs)
    print("Raster size:", dataset.width, "x", dataset.height)
    print("Raster bounds:", dataset.bounds)

    transformer = Transformer.from_crs(
        "EPSG:4326",
        dataset.crs,
        always_xy=True
    )

    x, y = transformer.transform(
        LONGITUDE,
        LATITUDE
    )

    print("\nTransformed coordinate:")
    print("X:", x)
    print("Y:", y)

    value = next(
        dataset.sample(
            [(x, y)]
        )
    )[0]

    print(
        "\nRaster pixel value:",
        value
    )