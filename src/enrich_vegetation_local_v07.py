import pandas as pd
import rasterio

from dbfread import DBF
from pyproj import Transformer


INPUT_PATH = "data/v07_spatial_negatives_land_valid.csv"
OUTPUT_PATH = "data/v07_spatial_negatives_vegetation.csv"

RASTER_PATH = (
    "/Users/ayubgurung/Downloads/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_108/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_5m.tif"
)

DBF_PATH = (
    "/Users/ayubgurung/Downloads/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_108/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_5m.tif.vat.dbf"
)


def load_attribute_table():

    table = DBF(
        DBF_PATH,
        load=True,
        encoding="cp1252"
    )

    lookup = {}

    for record in table:

        value = int(record["Value"])

        lookup[value] = {
            "pct_id": record["PCTID"],
            "pct_name": record["PCTName"],
            "vegetation_class": record["vegClass"],
            "vegetation_formation": record["vegForm"],
        }

    return lookup


def main():

    print("=" * 32)
    print("BUSHFIRE AI V06 LOCAL VEGETATION")
    print("=" * 32)

    df = pd.read_csv(INPUT_PATH)

    print(f"\nDataset rows: {len(df):,}")

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

    print("\nLoading vegetation attribute table...")

    vegetation_lookup = load_attribute_table()

    print(
        f"Vegetation records loaded: "
        f"{len(vegetation_lookup):,}"
    )

    location_results = []

    print("\nOpening local vegetation raster...")

    with rasterio.open(RASTER_PATH) as dataset:

        print(f"Raster CRS: {dataset.crs}")

        transformer = Transformer.from_crs(
            "EPSG:4326",
            dataset.crs,
            always_xy=True
        )

        coordinates = []

        for row in unique_locations.itertuples(
            index=False
        ):

            x, y = transformer.transform(
                row.longitude,
                row.latitude
            )

            coordinates.append(
                (x, y)
            )

        print(
            f"Sampling "
            f"{len(coordinates):,} locations..."
        )

        samples = dataset.sample(coordinates)

        for index, (
            location,
            sample
        ) in enumerate(
            zip(
                unique_locations.itertuples(
                    index=False
                ),
                samples
            ),
            start=1
        ):

            raster_value = int(sample[0])

            vegetation = vegetation_lookup.get(
                raster_value
            )

            if vegetation is None:

                result = {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "pct_id": None,
                    "pct_name": None,
                    "vegetation_class": None,
                    "vegetation_formation": None,
                }

            else:

                result = {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    **vegetation,
                }

            location_results.append(result)

            if (
                index % 500 == 0
                or index
                == len(unique_locations)
            ):
                print(
                    f"Processed "
                    f"{index:,}/"
                    f"{len(unique_locations):,}"
                )

    vegetation_df = pd.DataFrame(
        location_results
    )

    print("\nMerging vegetation data...")

    df = df.merge(
        vegetation_df,
        on=[
            "latitude",
            "longitude",
        ],
        how="left"
    )

    print("\nValidation")
    print("-" * 32)

    print(
        f"Rows after merge: "
        f"{len(df):,}"
    )

    print(
        f"Missing PCT ID: "
        f"{df['pct_id'].isna().sum():,}"
    )

    print(
        f"Missing vegetation class: "
        f"{df['vegetation_class'].isna().sum():,}"
    )

    print(
        f"Missing vegetation formation: "
        f"{df['vegetation_formation'].isna().sum():,}"
    )

    print(
        f"Unique PCT IDs: "
        f"{df['pct_id'].nunique():,}"
    )

    print(
        f"Unique vegetation classes: "
        f"{df['vegetation_class'].nunique():,}"
    )

    print(
        f"Unique vegetation formations: "
        f"{df['vegetation_formation'].nunique():,}"
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n" + "=" * 32)
    print("V06 LOCAL VEGETATION COMPLETE")
    print("=" * 32)

    print(
        f"\nSaved to {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()