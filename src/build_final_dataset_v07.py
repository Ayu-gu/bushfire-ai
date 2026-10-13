import pandas as pd


NEGATIVE_PATH = "data/v07_spatial_negatives_enriched.csv"
V06_PATH = "data/training_dataset_v06.csv"
OUTPUT_PATH = "data/training_dataset_v07.csv"

VEGETATION_COLUMNS = [
    "pct_id",
    "pct_name",
    "vegetation_class",
    "vegetation_formation",
]


def main():
    print("=" * 45)
    print("BUSHFIRE AI - BUILD FINAL V07 DATASET")
    print("=" * 45)

    # Load datasets
    negatives = pd.read_csv(NEGATIVE_PATH)
    v06 = pd.read_csv(V06_PATH)

    print(f"\nV07 negatives loaded: {len(negatives):,}")
    print(f"V06 rows loaded:       {len(v06):,}")

    # Select only the real fire events matched to V07 negatives.
    fires = v06[
        (v06["fire"] == 1)
        & (v06["source_fire_id"].isin(negatives["source_fire_id"]))
    ].copy()

    print(f"Matched fire rows:     {len(fires):,}")

    # Find matched fire events with missing vegetation.
    bad_ids = set(
        fires.loc[
            fires[VEGETATION_COLUMNS].isna().any(axis=1),
            "source_fire_id",
        ]
    )

    print(f"\nPairs excluded for missing vegetation: {len(bad_ids)}")

    if bad_ids:
        print("Excluded source_fire_id values:")
        print(sorted(bad_ids))

    # Remove the complete pair, not only the positive row.
    fires = fires[
        ~fires["source_fire_id"].isin(bad_ids)
    ].copy()

    negatives = negatives[
        ~negatives["source_fire_id"].isin(bad_ids)
    ].copy()

    # Verify one-to-one matching.
    fire_ids = set(fires["source_fire_id"])
    negative_ids = set(negatives["source_fire_id"])

    if fire_ids != negative_ids:
        raise ValueError(
            "Positive and negative source_fire_id sets do not match."
        )

    if fires["source_fire_id"].duplicated().any():
        raise ValueError("Duplicate positive source_fire_id detected.")

    if negatives["source_fire_id"].duplicated().any():
        raise ValueError("Duplicate negative source_fire_id detected.")

    # Use only columns shared by both datasets.
    # This prevents positive-only/negative-only metadata from creating NaNs.
    common_columns = [
        column
        for column in fires.columns
        if column in negatives.columns
    ]

    fires = fires[common_columns].copy()
    negatives = negatives[common_columns].copy()

    # Combine matched positive and negative samples.
    final_df = pd.concat(
        [fires, negatives],
        ignore_index=True,
    )

    # Stable ordering keeps each matched pair together in the saved dataset.
    final_df = final_df.sort_values(
        ["source_fire_id", "fire"]
    ).reset_index(drop=True)

    # Final integrity checks.
    missing_total = int(final_df.isna().sum().sum())
    duplicate_rows = int(final_df.duplicated().sum())

    if missing_total != 0:
        raise ValueError(
            f"Final dataset contains {missing_total} missing values."
        )

    if len(fires) != len(negatives):
        raise ValueError(
            "Final positive and negative counts are not balanced."
        )

    if len(final_df) != 2 * len(fire_ids):
        raise ValueError(
            "Final row count does not match expected pair count."
        )

    # Save final V07 dataset.
    final_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\n" + "=" * 45)
    print("V07 FINAL DATASET COMPLETE")
    print("=" * 45)

    print(f"\nPositive fires:    {len(fires):,}")
    print(f"Negative samples:  {len(negatives):,}")
    print(f"Matched pairs:     {len(fire_ids):,}")
    print(f"Total rows:        {len(final_df):,}")
    print(f"Total columns:     {len(final_df.columns)}")
    print(f"Missing values:    {missing_total}")
    print(f"Duplicate rows:    {duplicate_rows}")

    print("\nClass distribution:")
    print(final_df["fire"].value_counts().sort_index())

    print("\nColumns:")
    for column in final_df.columns:
        print(f"  - {column}")

    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
