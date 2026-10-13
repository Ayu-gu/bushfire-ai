import math
import os

import pandas as pd
import rasterio

from dbfread import DBF
from pyproj import Transformer


# ============================================================
# PATHS
# ============================================================

INPUT_PATH = (
    "data/full_wildfires_2000plus_stage5.csv"
)

OUTPUT_PATH = (
    "data/full_wildfires_2000plus_stage6.csv"
)

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


# ============================================================
# VEGETATION SETTINGS
# ============================================================

NO_PCT_LABEL = "NO_MAPPED_PCT"

VEGETATION_COLUMNS = [
    "pct_id",
    "pct_name",
    "vegetation_class",
    "vegetation_formation",
]


# ============================================================
# LOAD VEGETATION ATTRIBUTE TABLE
# ============================================================

def load_attribute_table():
    print(
        "\nLoading vegetation attribute table..."
    )

    table = DBF(
        DBF_PATH,
        load=True,
        encoding="cp1252",
    )

    lookup = {}

    for record in table:
        raster_value = int(
            record["Value"]
        )

        lookup[raster_value] = {
            "pct_id": record["PCTID"],
            "pct_name": record["PCTName"],
            "vegetation_class": record["vegClass"],
            "vegetation_formation": record["vegForm"],
        }

    print(
        f"Vegetation lookup records: "
        f"{len(lookup):,}"
    )

    return lookup


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("BUSHFIRE AI - FULL WILDFIRE VEGETATION STAGE 6")
    print("=" * 60)

    # --------------------------------------------------------
    # Check required source files
    # --------------------------------------------------------

    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(
            f"Stage 5 dataset not found:\n"
            f"{INPUT_PATH}"
        )

    if not os.path.exists(RASTER_PATH):
        raise FileNotFoundError(
            f"Vegetation raster not found:\n"
            f"{RASTER_PATH}"
        )

    if not os.path.exists(DBF_PATH):
        raise FileNotFoundError(
            f"Vegetation DBF not found:\n"
            f"{DBF_PATH}"
        )

    # --------------------------------------------------------
    # Load Stage 5
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

    # --------------------------------------------------------
    # Input integrity checks
    # --------------------------------------------------------

    if len(df) != 9249:
        raise ValueError(
            f"Expected 9,249 Stage 5 rows, "
            f"found {len(df):,}."
        )

    if (
        df["source_row_id"]
        .duplicated()
        .any()
    ):
        raise ValueError(
            "Duplicate source_row_id detected "
            "in Stage 5 input."
        )

    if df["latitude"].isna().any():
        raise ValueError(
            "Missing latitude detected."
        )

    if df["longitude"].isna().any():
        raise ValueError(
            "Missing longitude detected."
        )

    if df["elevation"].isna().any():
        raise ValueError(
            "Missing elevation detected "
            "in Stage 5 input."
        )

    # Prevent accidental duplicate enrichment.
    existing_vegetation_columns = [
        column
        for column in VEGETATION_COLUMNS
        if column in df.columns
    ]

    if existing_vegetation_columns:
        raise ValueError(
            "Stage 5 already contains vegetation "
            f"columns: {existing_vegetation_columns}"
        )

    # --------------------------------------------------------
    # Load vegetation lookup
    # --------------------------------------------------------

    vegetation_lookup = (
        load_attribute_table()
    )

    # --------------------------------------------------------
    # Prepare unique locations
    # --------------------------------------------------------

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
        f"\nUnique fire locations: "
        f"{len(unique_locations):,}"
    )

    # --------------------------------------------------------
    # Sample vegetation raster
    # --------------------------------------------------------

    location_results = []

    matched_count = 0
    nodata_count = 0
    outside_count = 0
    unknown_value_count = 0

    print(
        "\nOpening local vegetation raster..."
    )

    with rasterio.open(
        RASTER_PATH
    ) as dataset:

        print(
            f"Raster CRS: "
            f"{dataset.crs}"
        )

        print(
            f"Raster size: "
            f"{dataset.width:,} x "
            f"{dataset.height:,}"
        )

        transformer = Transformer.from_crs(
            "EPSG:4326",
            dataset.crs,
            always_xy=True,
        )

        for index, location in enumerate(
            unique_locations.itertuples(
                index=False
            ),
            start=1,
        ):
            x, y = transformer.transform(
                location.longitude,
                location.latitude,
            )

            # ------------------------------------------------
            # Outside raster extent
            # ------------------------------------------------

            inside_raster = (
                dataset.bounds.left
                <= x
                <= dataset.bounds.right
                and
                dataset.bounds.bottom
                <= y
                <= dataset.bounds.top
            )

            if not inside_raster:
                outside_count += 1

                result = {
                    "latitude":
                        location.latitude,

                    "longitude":
                        location.longitude,

                    "pct_id":
                        NO_PCT_LABEL,

                    "pct_name":
                        NO_PCT_LABEL,

                    "vegetation_class":
                        NO_PCT_LABEL,

                    "vegetation_formation":
                        NO_PCT_LABEL,
                }

                location_results.append(
                    result
                )

                continue

            # ------------------------------------------------
            # Sample raster
            # ------------------------------------------------

            sample = next(
                dataset.sample(
                    [(x, y)],
                    masked=True,
                )
            )[0]

            # ------------------------------------------------
            # Raster NoData
            # ------------------------------------------------

            if getattr(
                sample,
                "mask",
                False,
            ):
                nodata_count += 1

                result = {
                    "latitude":
                        location.latitude,

                    "longitude":
                        location.longitude,

                    "pct_id":
                        NO_PCT_LABEL,

                    "pct_name":
                        NO_PCT_LABEL,

                    "vegetation_class":
                        NO_PCT_LABEL,

                    "vegetation_formation":
                        NO_PCT_LABEL,
                }

            else:
                raster_value = int(
                    sample
                )

                vegetation = (
                    vegetation_lookup.get(
                        raster_value
                    )
                )

                # --------------------------------------------
                # Raster value not present in DBF
                # --------------------------------------------

                if vegetation is None:
                    unknown_value_count += 1

                    result = {
                        "latitude":
                            location.latitude,

                        "longitude":
                            location.longitude,

                        "pct_id":
                            NO_PCT_LABEL,

                        "pct_name":
                            NO_PCT_LABEL,

                        "vegetation_class":
                            NO_PCT_LABEL,

                        "vegetation_formation":
                            NO_PCT_LABEL,
                    }

                else:
                    matched_count += 1

                    result = {
                        "latitude":
                            location.latitude,

                        "longitude":
                            location.longitude,

                        **vegetation,
                    }

            location_results.append(
                result
            )

            if (
                index % 1000 == 0
                or index
                == len(unique_locations)
            ):
                print(
                    f"  Processed "
                    f"{index:,}/"
                    f"{len(unique_locations):,}"
                )

    # --------------------------------------------------------
    # Create vegetation lookup dataframe
    # --------------------------------------------------------

    vegetation_df = pd.DataFrame(
        location_results
    )

    if (
        vegetation_df[
            [
                "latitude",
                "longitude",
            ]
        ]
        .duplicated()
        .any()
    ):
        raise ValueError(
            "Duplicate locations detected "
            "in vegetation results."
        )

    # --------------------------------------------------------
    # Merge back into full dataset
    # --------------------------------------------------------

    print(
        "\nMerging vegetation information..."
    )

    original_row_count = len(df)

    df = df.merge(
        vegetation_df,
        on=[
            "latitude",
            "longitude",
        ],
        how="left",
        validate="many_to_one",
    )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    print(
        "\nRunning Stage 6 integrity checks..."
    )

    if len(df) != original_row_count:
        raise ValueError(
            "Row count changed during "
            "vegetation merge."
        )

    if len(df) != 9249:
        raise ValueError(
            f"Expected 9,249 final rows, "
            f"found {len(df):,}."
        )

    duplicate_ids = int(
        df["source_row_id"]
        .duplicated()
        .sum()
    )

    if duplicate_ids != 0:
        raise ValueError(
            f"{duplicate_ids:,} duplicate "
            f"source_row_id values detected."
        )

    missing_by_column = (
        df[VEGETATION_COLUMNS]
        .isna()
        .sum()
    )

    missing_total = int(
        missing_by_column.sum()
    )

    if missing_total != 0:
        print(
            "\nMissing vegetation fields:"
        )

        print(
            missing_by_column
        )

        raise ValueError(
            f"Stage 6 contains "
            f"{missing_total:,} missing "
            f"vegetation values."
        )

    # --------------------------------------------------------
    # Verify elevation survived unchanged
    # --------------------------------------------------------

    if df["elevation"].isna().any():
        raise ValueError(
            "Elevation became missing "
            "during Stage 6."
        )

    # --------------------------------------------------------
    # Calculate final vegetation statistics
    # --------------------------------------------------------

    no_pct_rows = int(
        (
            df["vegetation_class"]
            == NO_PCT_LABEL
        ).sum()
    )

    mapped_rows = (
        len(df) - no_pct_rows
    )

    unique_pct = int(
        df.loc[
            df["pct_id"]
            != NO_PCT_LABEL,
            "pct_id",
        ].nunique()
    )

    unique_classes = int(
        df.loc[
            df["vegetation_class"]
            != NO_PCT_LABEL,
            "vegetation_class",
        ].nunique()
    )

    unique_formations = int(
        df.loc[
            df["vegetation_formation"]
            != NO_PCT_LABEL,
            "vegetation_formation",
        ].nunique()
    )

    # --------------------------------------------------------
    # Save only after validation succeeds
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("STAGE 6 VEGETATION COMPLETE")
    print("=" * 60)

    print(
        f"\nRows:                    "
        f"{len(df):,}"
    )

    print(
        f"Columns:                 "
        f"{len(df.columns)}"
    )

    print(
        f"Unique source IDs:       "
        f"{df['source_row_id'].nunique():,}"
    )

    print(
        f"\nMapped vegetation rows:  "
        f"{mapped_rows:,}"
    )

    print(
        f"No mapped PCT rows:      "
        f"{no_pct_rows:,}"
    )

    print(
        f"\nRaster NoData locations: "
        f"{nodata_count:,}"
    )

    print(
        f"Outside raster:          "
        f"{outside_count:,}"
    )

    print(
        f"Unknown raster values:   "
        f"{unknown_value_count:,}"
    )

    print(
        f"\nUnique mapped PCT IDs:   "
        f"{unique_pct:,}"
    )

    print(
        f"Vegetation classes:      "
        f"{unique_classes:,}"
    )

    print(
        f"Vegetation formations:   "
        f"{unique_formations:,}"
    )

    print(
        "\nVegetation class distribution:"
    )

    print(
        df["vegetation_class"]
        .value_counts()
        .head(20)
        .to_string()
    )

    print(
        f"\nSaved to: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()