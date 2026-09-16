import pandas as pd
import rasterio

from pyproj import Transformer


INPUT_PATH = (
    "data/v07_missing_vegetation_audit.csv"
)

OUTPUT_PATH = (
    "data/v07_missing_vegetation_diagnosed.csv"
)

RASTER_PATH = (
    "/Users/ayubgurung/Downloads/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_108/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_5m.tif"
)


def main():

    print("=" * 52)
    print("V07 MISSING VEGETATION DIAGNOSTIC")
    print("=" * 52)

    df = pd.read_csv(
        INPUT_PATH
    )

    print(
        f"\nRows to diagnose: "
        f"{len(df):,}"
    )

    results = []

    with rasterio.open(
        RASTER_PATH
    ) as dataset:

        print(
            f"Raster CRS: "
            f"{dataset.crs}"
        )

        transformer = Transformer.from_crs(
            "EPSG:4326",
            dataset.crs,
            always_xy=True
        )

        for index, row in enumerate(
            df.itertuples(index=False),
            start=1
        ):

            x, y = transformer.transform(
                row.longitude,
                row.latitude
            )

            inside_bounds = (
                dataset.bounds.left
                <= x
                <= dataset.bounds.right
                and
                dataset.bounds.bottom
                <= y
                <= dataset.bounds.top
            )

            if not inside_bounds:

                status = "outside_raster_bounds"
                raster_value = None

            else:

                sample = next(
                    dataset.sample(
                        [(x, y)]
                    )
                )[0]

                raster_value = int(
                    sample
                )

                if (
                    dataset.nodata is not None
                    and raster_value
                    == dataset.nodata
                ):

                    status = "nodata"

                elif raster_value == 0:

                    status = "not_classified"

                else:

                    status = "valid_raster_value"

            result = row._asdict()

            result[
                "raster_x"
            ] = x

            result[
                "raster_y"
            ] = y

            result[
                "inside_raster_bounds"
            ] = inside_bounds

            result[
                "raster_value"
            ] = raster_value

            result[
                "diagnostic_status"
            ] = status

            results.append(
                result
            )

            if (
                index % 100 == 0
                or index == len(df)
            ):

                print(
                    f"Checked "
                    f"{index:,}/"
                    f"{len(df):,}"
                )

    result_df = pd.DataFrame(
        results
    )

    print("\n" + "=" * 52)
    print("DIAGNOSTIC RESULTS")
    print("=" * 52)

    print(
        result_df[
            "diagnostic_status"
        ]
        .value_counts(
            dropna=False
        )
    )

    print(
        "\nExamples outside raster bounds:"
    )

    outside = result_df[
        result_df[
            "diagnostic_status"
        ]
        == "outside_raster_bounds"
    ]

    if len(outside) > 0:

        print(
            outside[
                [
                    "latitude",
                    "longitude",
                    "date",
                    "source_fire_id",
                ]
            ]
            .head(20)
            .to_string(
                index=False
            )
        )

    print(
        "\nExamples not classified:"
    )

    unclassified = result_df[
        result_df[
            "diagnostic_status"
        ]
        == "not_classified"
    ]

    if len(unclassified) > 0:

        print(
            unclassified[
                [
                    "latitude",
                    "longitude",
                    "date",
                    "source_fire_id",
                ]
            ]
            .head(20)
            .to_string(
                index=False
            )
        )

    result_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n" + "=" * 52)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 52)

    print(
        f"\nSaved to "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
    