import pandas as pd


INPUT_PATH = "data/v07_spatial_negatives_vegetation.csv"
OUTPUT_PATH = "data/v07_missing_vegetation_audit.csv"


def main():

    print("=" * 50)
    print("V07 MISSING VEGETATION AUDIT")
    print("=" * 50)

    df = pd.read_csv(INPUT_PATH)

    print(f"\nTotal rows: {len(df):,}")

    # Find rows where vegetation lookup failed
    missing = df[
        df["vegetation_formation"].isna()
    ].copy()

    print(
        f"Missing vegetation rows: "
        f"{len(missing):,}"
    )

    print(
        f"Percentage: "
        f"{len(missing) / len(df) * 100:.2f}%"
    )

    print("\n" + "=" * 50)
    print("COORDINATE RANGE")
    print("=" * 50)

    print(
        f"Latitude: "
        f"{missing['latitude'].min():.4f} "
        f"to "
        f"{missing['latitude'].max():.4f}"
    )

    print(
        f"Longitude: "
        f"{missing['longitude'].min():.4f} "
        f"to "
        f"{missing['longitude'].max():.4f}"
    )

    print("\n" + "=" * 50)
    print("LONGITUDE DISTRIBUTION")
    print("=" * 50)

    bins = [
        140,
        145,
        150,
        151,
        152,
        153,
        154,
        155,
        160,
    ]

    missing["longitude_band"] = pd.cut(
        missing["longitude"],
        bins=bins,
        include_lowest=True
    )

    print(
        missing[
            "longitude_band"
        ].value_counts().sort_index()
    )

    print("\n" + "=" * 50)
    print("MOST EASTERN MISSING LOCATIONS")
    print("=" * 50)

    columns = [
        "latitude",
        "longitude",
        "date",
        "source_fire_id",
    ]

    available_columns = [
        column
        for column in columns
        if column in missing.columns
    ]

    print(
        missing.sort_values(
            "longitude",
            ascending=False
        )[
            available_columns
        ].head(30).to_string(
            index=False
        )
    )

    print("\n" + "=" * 50)
    print("MOST WESTERN MISSING LOCATIONS")
    print("=" * 50)

    print(
        missing.sort_values(
            "longitude"
        )[
            available_columns
        ].head(20).to_string(
            index=False
        )
    )

    missing.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n" + "=" * 50)
    print("AUDIT COMPLETE")
    print("=" * 50)

    print(
        f"\nSaved missing rows to "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()