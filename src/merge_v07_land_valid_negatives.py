import pandas as pd


OLD_PATH = "data/v07_spatial_negatives_vegetation.csv"

REPLACEMENT_PATH = (
    "data/v07_spatial_negatives_land_replacements.csv"
)

OUTPUT_PATH = (
    "data/v07_spatial_negatives_land_valid.csv"
)


def main():

    print("=" * 50)
    print("V07 LAND-VALID SPATIAL NEGATIVE MERGE")
    print("=" * 50)

    old_df = pd.read_csv(
        OLD_PATH
    )

    replacements = pd.read_csv(
        REPLACEMENT_PATH
    )

    # Keep only original negatives that successfully
    # received vegetation information.
    valid_old = old_df[
        old_df["vegetation_formation"].notna()
    ].copy()

    print(
        f"\nValid original rows: "
        f"{len(valid_old):,}"
    )

    print(
        f"Replacement rows: "
        f"{len(replacements):,}"
    )

    # Drop old vegetation columns before merging because
    # we'll enrich ALL 5,000 again from the local raster.
    vegetation_columns = [
        "pct_id",
        "pct_name",
        "vegetation_class",
        "vegetation_formation",
    ]

    valid_old = valid_old.drop(
        columns=[
            c
            for c in vegetation_columns
            if c in valid_old.columns
        ],
        errors="ignore",
    )

    replacements = replacements.drop(
        columns=[
            c
            for c in vegetation_columns
            if c in replacements.columns
        ],
        errors="ignore",
    )

    combined = pd.concat(
        [
            valid_old,
            replacements,
        ],
        ignore_index=True,
        sort=False,
    )

    print(
        f"Combined rows: "
        f"{len(combined):,}"
    )

    print(
        "\nMissing values:"
    )

    print(
        combined.isna().sum()
    )

    duplicates = combined.duplicated(
        subset=[
            "latitude",
            "longitude",
            "date",
        ]
    ).sum()

    print(
        f"\nDuplicate location/date: "
        f"{duplicates:,}"
    )

    if len(combined) != 5000:
        raise RuntimeError(
            f"Expected 5,000 rows, "
            f"got {len(combined):,}"
        )

    combined.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\n" + "=" * 50)
    print("MERGE COMPLETE")
    print("=" * 50)

    print(
        f"\nSaved to "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()