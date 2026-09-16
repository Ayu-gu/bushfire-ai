import pandas as pd

from build_dataset_v07 import (
    fire_nearby,
    random_location_nearby,
    build_weather_features,
)


SOURCE_DATASET = "data/training_dataset_v06.csv"

VALIDATED_SPATIAL_PATH = (
    "data/v07_spatial_negatives_validated.csv"
)

OUTPUT_PATH = (
    "data/v07_spatial_negatives_replacements.csv"
)

TARGET_REPLACEMENTS = 180

MAX_ATTEMPTS_PER_FIRE = 30


def main():

    print("=" * 48)
    print("BUSHFIRE AI V07 REPLACEMENT GENERATOR")
    print("=" * 48)

    source_df = pd.read_csv(
        SOURCE_DATASET
    )

    valid_df = pd.read_csv(
        VALIDATED_SPATIAL_PATH
    )

    fire_df = (
        source_df[
            source_df["fire"] == 1
        ]
        .copy()
        .reset_index(drop=True)
    )

    used_source_ids = set(
        valid_df[
            "source_fire_id"
        ]
        .astype(str)
    )

    available_fires = fire_df[
        ~fire_df[
            "source_fire_id"
        ]
        .astype(str)
        .isin(used_source_ids)
    ].copy()

    print(
        f"\nValidated spatial negatives: "
        f"{len(valid_df):,}"
    )

    print(
        f"Replacement target: "
        f"{TARGET_REPLACEMENTS:,}"
    )

    print(
        f"Unused source fires available: "
        f"{len(available_fires):,}"
    )

    replacements = []

    rejected_candidates = 0
    weather_failures = 0

    for fire_row in (
        available_fires.itertuples(
            index=False
        )
    ):

        if (
            len(replacements)
            >= TARGET_REPLACEMENTS
        ):
            break

        source_fire_id = str(
            fire_row.source_fire_id
        )

        fire_date = str(
            fire_row.date
        )

        replacement_created = False

        for attempt in range(
            1,
            MAX_ATTEMPTS_PER_FIRE + 1
        ):

            latitude, longitude = (
                random_location_nearby(
                    fire_row.latitude,
                    fire_row.longitude
                )
            )

            try:

                nearby_fire = fire_nearby(
                    latitude,
                    longitude,
                    fire_date
                )

            except Exception as error:

                print(
                    f"Fire verification failed: "
                    f"{error}"
                )

                continue

            if nearby_fire:

                rejected_candidates += 1
                continue

            try:

                features = build_weather_features(
                    latitude,
                    longitude,
                    fire_date
                )

            except Exception as error:

                weather_failures += 1

                print(
                    f"Weather lookup failed: "
                    f"{error}"
                )

                continue

            features[
                "source_fire_id"
            ] = source_fire_id

            replacements.append(
                features
            )

            replacement_created = True

            print(
                f"\nReplacement "
                f"{len(replacements)}/"
                f"{TARGET_REPLACEMENTS}"
            )

            print(
                f"Source fire ID: "
                f"{source_fire_id}"
            )

            print(
                f"Date: "
                f"{fire_date}"
            )

            print(
                f"Location: "
                f"{latitude:.4f}, "
                f"{longitude:.4f}"
            )

            print(
                f"Rejected candidates: "
                f"{rejected_candidates}"
            )

            break

        if not replacement_created:

            print(
                f"Could not create replacement "
                f"for source fire "
                f"{source_fire_id}"
            )

    replacement_df = pd.DataFrame(
        replacements
    )

    replacement_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n" + "=" * 48)
    print("V07 REPLACEMENT GENERATION COMPLETE")
    print("=" * 48)

    print(
        f"\nReplacements created: "
        f"{len(replacement_df):,}"
    )

    print(
        f"Rejected candidates: "
        f"{rejected_candidates:,}"
    )

    print(
        f"Weather failures: "
        f"{weather_failures:,}"
    )

    print(
        f"\nSaved to "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()