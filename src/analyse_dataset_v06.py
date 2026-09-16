import pandas as pd


DATA_PATH = "data/training_dataset_v06.csv"


def main():

    print("=" * 40)
    print("BUSHFIRE AI V06 DATASET AUDIT")
    print("=" * 40)

    df = pd.read_csv(DATA_PATH)

    print(f"\nTotal rows: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")

    # --------------------------------------------------------
    # CLASS BALANCE
    # --------------------------------------------------------

    print("\n" + "=" * 40)
    print("CLASS BALANCE")
    print("=" * 40)

    print(df["fire"].value_counts())

    print("\nPercentages:")
    print(
        df["fire"]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
    )

    # --------------------------------------------------------
    # MISSING VALUES
    # --------------------------------------------------------

    print("\n" + "=" * 40)
    print("MISSING VALUES")
    print("=" * 40)

    missing = df.isna().sum()
    missing = missing[missing > 0]

    if len(missing) == 0:
        print("No missing values.")
    else:
        print(missing)

    # --------------------------------------------------------
    # ELEVATION
    # --------------------------------------------------------

    print("\n" + "=" * 40)
    print("ELEVATION")
    print("=" * 40)

    print(df["elevation"].describe())

    print("\nMean elevation by class:")

    print(
        df.groupby("fire")["elevation"]
        .mean()
        .round(2)
    )

    # --------------------------------------------------------
    # VEGETATION
    # --------------------------------------------------------

    print("\n" + "=" * 40)
    print("VEGETATION SUMMARY")
    print("=" * 40)

    print(
        f"Unique PCT IDs: "
        f"{df['pct_id'].nunique()}"
    )

    print(
        f"Unique vegetation classes: "
        f"{df['vegetation_class'].nunique()}"
    )

    print(
        f"Unique vegetation formations: "
        f"{df['vegetation_formation'].nunique()}"
    )

    print("\nTop vegetation formations:")

    print(
        df["vegetation_formation"]
        .value_counts()
        .head(20)
    )

    # --------------------------------------------------------
    # FIRE RATE BY VEGETATION FORMATION
    # --------------------------------------------------------

    print("\n" + "=" * 40)
    print("FIRE RATE BY VEGETATION FORMATION")
    print("=" * 40)

    formation_stats = (
        df.groupby("vegetation_formation")
        .agg(
            samples=("fire", "size"),
            fires=("fire", "sum"),
            fire_rate=("fire", "mean")
        )
    )

    formation_stats["fire_rate"] = (
        formation_stats["fire_rate"] * 100
    ).round(2)

    formation_stats = (
        formation_stats
        .sort_values(
            "samples",
            ascending=False
        )
    )

    print(formation_stats)

    # --------------------------------------------------------
    # FIRE RATE BY VEGETATION CLASS
    # --------------------------------------------------------

    print("\n" + "=" * 40)
    print("TOP VEGETATION CLASSES")
    print("=" * 40)

    class_stats = (
        df.groupby("vegetation_class")
        .agg(
            samples=("fire", "size"),
            fires=("fire", "sum"),
            fire_rate=("fire", "mean")
        )
    )

    class_stats["fire_rate"] = (
        class_stats["fire_rate"] * 100
    ).round(2)

    class_stats = (
        class_stats
        .sort_values(
            "samples",
            ascending=False
        )
    )

    print(class_stats.head(30))

    # --------------------------------------------------------
    # MISSING VEGETATION ROWS
    # --------------------------------------------------------

    print("\n" + "=" * 40)
    print("MISSING VEGETATION ROWS")
    print("=" * 40)

    missing_vegetation = df[
        df["pct_id"].isna()
    ]

    if len(missing_vegetation) == 0:

        print("None.")

    else:

        columns = [
            "latitude",
            "longitude",
            "elevation",
            "fire"
        ]

        print(
            missing_vegetation[
                columns
            ].to_string(index=False)
        )

    print("\n" + "=" * 40)
    print("AUDIT COMPLETE")
    print("=" * 40)


if __name__ == "__main__":
    main()