import pandas as pd
import rasterio

from pyproj import Transformer

from build_dataset_v07 import (
    fire_nearby,
    random_location_nearby,
    build_weather_features,
)


SOURCE_DATASET = "data/training_dataset_v06.csv"

VALID_SPATIAL_PATH = (
    "data/v07_spatial_negatives_vegetation.csv"
)

OUTPUT_PATH = (
    "data/v07_spatial_negatives_land_replacements.csv"
)

TARGET_REPLACEMENTS = 931

MAX_ATTEMPTS_PER_FIRE = 50

RASTER_PATH = (
    "/Users/ayubgurung/Downloads/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_108/"
    "SVTM_NSW_Extant_PCT_vC2_0_M2_2_5m.tif"
)


def build_land_checker():

    dataset = rasterio.open(
        RASTER_PATH
    )

    transformer = Transformer.from_crs(
        "EPSG:4326",
        dataset.crs,
        always_xy=True
    )

    return dataset, transformer


def has_valid_vegetation(
    dataset,
    transformer,
    latitude,
    longitude
):

    x, y = transformer.transform(
        longitude,
        latitude
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
        return False

    value = next(
        dataset.sample(
            [(x, y)]
        )
    )[0]

    if (
        dataset.nodata is not None
        and value == dataset.nodata
    ):
        return False

    if int(value) <= 0:
        return False

    return True


def main():

    print("=" * 52)
    print("BUSHFIRE AI V07 LAND-VALID REPLACEMENTS")
    print("=" * 52)

    source_df = pd.read_csv(
        SOURCE_DATASET
    )

    spatial_df = pd.read_csv(
        VALID_SPATIAL_PATH
    )

    # Keep only rows with valid vegetation from the current
    # spatial-negative dataset.
    good_spatial = spatial_df[
        spatial_df[
            "vegetation_formation"
        ].notna()
    ].copy()

    print(
        f"\nExisting valid spatial rows: "
        f"{len(good_spatial):,}"
    )

    print(
        f"Replacement target: "
        f"{TARGET_REPLACEMENTS:,}"
    )

    fire_df = (
        source_df[
            source_df["fire"] == 1
        ]
        .copy()
        .reset_index(drop=True)
    )

    used_source_ids = set(
        good_spatial[
            "source_fire_id"
        ]
        .astype(str)
    )

    available_fires = fire_df[
        ~fire_df[
            "source_fire_id"
        ]
        .astype(str)
        .isin(
            used_source_ids
        )
    ].copy()

    print(
        f"Unused source fires available: "
        f"{len(available_fires):,}"
    )

    replacements = []

    rejected_land = 0
    rejected_fire = 0
    weather_failures = 0

    dataset, transformer = (
        build_land_checker()
    )

    try:

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

                # ------------------------------------------------
                # FAST LOCAL LAND / VEGETATION CHECK
                # ------------------------------------------------

                if not has_valid_vegetation(
                    dataset,
                    transformer,
                    latitude,
                    longitude
                ):

                    rejected_land += 1
                    continue

                # ------------------------------------------------
                # FIRE-HISTORY CHECK
                # ------------------------------------------------

                try:

                    if fire_nearby(
                        latitude,
                        longitude,
                        fire_date
                    ):

                        rejected_fire += 1
                        continue

                except Exception as error:

                    print(
                        f"Fire verification failed: "
                        f"{error}"
                    )

                    continue

                # ------------------------------------------------
                # WEATHER
                # ------------------------------------------------

                try:

                    features = (
                        build_weather_features(
                            latitude,
                            longitude,
                            fire_date
                        )
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

                features[
                    "negative_type"
                ] = "spatial"

                replacements.append(
                    features
                )

                replacement_created = True

                print(
                    f"\nReplacement "
                    f"{len(replacements):,}/"
                    f"{TARGET_REPLACEMENTS:,}"
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
                    f"Rejected land: "
                    f"{rejected_land:,}"
                )

                print(
                    f"Rejected fire: "
                    f"{rejected_fire:,}"
                )

                break

            if not replacement_created:

                print(
                    f"Could not create valid replacement "
                    f"for source fire "
                    f"{source_fire_id}"
                )

    finally:

        dataset.close()

    replacement_df = pd.DataFrame(
        replacements
    )

    replacement_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n" + "=" * 52)
    print("V07 LAND-VALID REPLACEMENTS COMPLETE")
    print("=" * 52)

    print(
        f"\nReplacements created: "
        f"{len(replacement_df):,}"
    )

    print(
        f"Rejected land candidates: "
        f"{rejected_land:,}"
    )

    print(
        f"Rejected fire candidates: "
        f"{rejected_fire:,}"
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