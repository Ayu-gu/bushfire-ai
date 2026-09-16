import pandas as pd

from build_dataset_v07 import fire_nearby


INPUT_PATH = "data/v07_spatial_negatives.csv"

VALID_OUTPUT_PATH = (
    "data/v07_spatial_negatives_validated.csv"
)

REJECTED_OUTPUT_PATH = (
    "data/v07_spatial_negatives_rejected.csv"
)


def main():

    print("=" * 48)
    print("BUSHFIRE AI V07 SPATIAL REVALIDATION")
    print("=" * 48)

    df = pd.read_csv(
        INPUT_PATH
    )

    print(
        f"\nRows to validate: "
        f"{len(df):,}"
    )

    valid_rows = []
    rejected_rows = []

    for index, row in enumerate(
        df.itertuples(index=False),
        start=1
    ):

        nearby_fire = fire_nearby(
            row.latitude,
            row.longitude,
            row.date
        )

        if nearby_fire:

            rejected_rows.append(
                row._asdict()
            )

        else:

            valid_rows.append(
                row._asdict()
            )

        if (
            index % 100 == 0
            or index == len(df)
        ):

            print(
                f"Checked "
                f"{index:,}/"
                f"{len(df):,} "
                f"| Valid: "
                f"{len(valid_rows):,} "
                f"| Rejected: "
                f"{len(rejected_rows):,}"
            )

    valid_df = pd.DataFrame(
        valid_rows
    )

    rejected_df = pd.DataFrame(
        rejected_rows
    )

    valid_df.to_csv(
        VALID_OUTPUT_PATH,
        index=False
    )

    rejected_df.to_csv(
        REJECTED_OUTPUT_PATH,
        index=False
    )

    print("\n" + "=" * 48)
    print("V07 REVALIDATION COMPLETE")
    print("=" * 48)

    print(
        f"\nOriginal rows: "
        f"{len(df):,}"
    )

    print(
        f"Valid spatial negatives: "
        f"{len(valid_df):,}"
    )

    print(
        f"Rejected spatial negatives: "
        f"{len(rejected_df):,}"
    )

    print(
        f"\nSaved valid rows to "
        f"{VALID_OUTPUT_PATH}"
    )

    print(
        f"Saved rejected rows to "
        f"{REJECTED_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()