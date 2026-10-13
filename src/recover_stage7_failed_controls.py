import random
import pandas as pd

import generate_full_wildfires_matched_controls_stage7 as s7


FAILED_PATH = "data/full_wildfires_stage7_failed_sources.csv"
RECOVERY_PATH = "data/full_wildfires_stage7_recovered_controls.csv"

MAX_RECOVERY_ATTEMPTS = 1000
RANDOM_SEED = 4207


def main():

    print("=" * 68)
    print("BUSHFIRE AI - STAGE 7 FAILED CONTROL RECOVERY")
    print("=" * 68)

    random.seed(RANDOM_SEED)

    sources = pd.read_csv(s7.INPUT_PATH)
    sources["date"] = pd.to_datetime(sources["date"])

    failed = pd.read_csv(FAILED_PATH)

    failed_ids = set(
        failed["source_row_id"].tolist()
    )

    recovery_sources = sources[
        sources["source_row_id"].isin(failed_ids)
    ].copy()

    print(
        f"\nFailed sources requested: {len(failed_ids):,}"
    )

    print(
        f"Sources found in Stage 6: "
        f"{len(recovery_sources):,}"
    )

    if len(recovery_sources) != len(failed_ids):
        raise RuntimeError(
            "Not all failed source IDs were found in Stage 6."
        )

    print("\nLoading vegetation lookup...")

    vegetation_lookup = s7.load_vegetation_lookup()

    vegetation_sampler = s7.VegetationSampler(
        s7.VEGETATION_RASTER,
        vegetation_lookup,
    )

    print("Indexing elevation tiles...")

    elevation_sampler = s7.ElevationSampler(
        s7.ELEVATION_TILE_DIR
    )

    print("Loading fire polygons...")

    fires = s7.load_fire_polygons()

    fire_checker = s7.FirePerimeterChecker(
        fires
    )

    recovered_rows = []
    still_failed = []

    try:

        for source in recovery_sources.itertuples(
            index=False
        ):

            print(
                "\n" + "-" * 68
            )

            print(
                f"Recovering source "
                f"{source.source_row_id}"
            )

            print(
                f"Date: {source.date.date()} | "
                f"Elevation: "
                f"{float(source.elevation):.1f} m"
            )

            accepted = None

            local_rejections = {
                "outside_vegetation_raster": 0,
                "unknown_vegetation_value": 0,
                "missing_elevation": 0,
                "elevation_mismatch": 0,
                "fire_perimeter": 0,
            }

            for attempt in range(
                1,
                MAX_RECOVERY_ATTEMPTS + 1,
            ):

                (
                    candidate_lat,
                    candidate_lon,
                    distance_km,
                ) = s7.random_location_nearby(
                    float(source.latitude),
                    float(source.longitude),
                )

                (
                    candidate_vegetation,
                    vegetation_status,
                ) = vegetation_sampler.sample(
                    candidate_lat,
                    candidate_lon,
                )

                if candidate_vegetation is None:
                     
                     if vegetation_status in local_rejections:
                          local_rejections[
                               vegetation_status
                          ] += 1
                          
                          continue

                candidate_elevation = (
                    elevation_sampler.sample(
                        candidate_lat,
                        candidate_lon,
                    )
                )

                if candidate_elevation is None:
                    local_rejections[
                        "missing_elevation"
                    ] += 1
                    continue

                elevation_difference = abs(
                    float(source.elevation)
                    - float(candidate_elevation)
                )

                if (
                    elevation_difference
                    > s7.MAX_ELEVATION_DIFFERENCE_M
                ):
                    local_rejections[
                        "elevation_mismatch"
                    ] += 1
                    continue

                if (
                    fire_checker
                    .candidate_near_relevant_fire(
                        candidate_lat,
                        candidate_lon,
                        source.date,
                    )
                ):
                    local_rejections[
                        "fire_perimeter"
                    ] += 1
                    continue

                match_type = s7.vegetation_match_type(
                    source,
                    candidate_vegetation,
                    )

                accepted = {
                    "source_row_id":
                        source.source_row_id,

                    "event_id":
                        source.event_id,

                    "source_date":
                        source.date.strftime(
                            "%Y-%m-%d"
                        ),

                    "source_latitude":
                        float(source.latitude),

                    "source_longitude":
                        float(source.longitude),

                    "control_latitude":
                        candidate_lat,

                    "control_longitude":
                        candidate_lon,

                    "distance_km":
                        distance_km,

                    "source_elevation":
                        float(source.elevation),

                    "control_elevation":
                        float(candidate_elevation),

                    "elevation_difference":
                        elevation_difference,

                    "source_pct_id":
                        source.pct_id,

                    "source_pct_name":
                        source.pct_name,

                    "source_vegetation_class":
                        source.vegetation_class,

                    "source_vegetation_formation":
                        source.vegetation_formation,

                    "control_pct_id":
                        candidate_vegetation[
                            "pct_id"
                        ],

                    "control_pct_name":
                        candidate_vegetation[
                            "pct_name"
                        ],

                    "control_vegetation_class":
                        candidate_vegetation[
                            "vegetation_class"
                        ],

                    "control_vegetation_formation":
                        candidate_vegetation[
                            "vegetation_formation"
                        ],

                    "vegetation_match_type":
                        match_type,

                    "generation_attempt":
                        attempt,

                    "fire":
                        0,

                    "negative_type":
                        "matched_spatial_control",
                }

                break

            if accepted is not None:

                recovered_rows.append(accepted)

                print(
                    f"✅ RECOVERED on attempt "
                    f"{accepted['generation_attempt']}"
                )

                print(
                    f"   Distance: "
                    f"{accepted['distance_km']:.2f} km"
                )

                print(
                    f"   Elevation difference: "
                    f"{accepted['elevation_difference']:.1f} m"
                )

                print(
                    f"   Vegetation: "
                    f"{accepted['vegetation_match_type']}"
                )

            else:

                still_failed.append(
                    source.source_row_id
                )

                print(
                    "❌ STILL FAILED after "
                    f"{MAX_RECOVERY_ATTEMPTS:,} attempts"
                )

            print(
                "   Rejections:",
                local_rejections,
            )

    finally:

        vegetation_sampler.close()
        elevation_sampler.close()

    recovered_df = pd.DataFrame(
        recovered_rows
    )

    recovered_df.to_csv(
        RECOVERY_PATH,
        index=False,
    )

    print("\n" + "=" * 68)
    print("RECOVERY FINISHED")
    print("=" * 68)

    print(
        f"Requested:       "
        f"{len(recovery_sources):,}"
    )

    print(
        f"Recovered:       "
        f"{len(recovered_df):,}"
    )

    print(
        f"Still failed:    "
        f"{len(still_failed):,}"
    )

    print(
        f"Saved recovery:  "
        f"{RECOVERY_PATH}"
    )

    if still_failed:
        print(
            "\nStill-failed source IDs:"
        )

        for source_id in still_failed:
            print(
                f"  {source_id}"
            )

    else:
        print(
            "\n🔥 ALL FAILED SOURCES RECOVERED."
        )


if __name__ == "__main__":
    main()