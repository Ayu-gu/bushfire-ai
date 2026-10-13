import math
import pandas as pd

import generate_full_wildfires_matched_controls_stage7 as s7


SOURCE_PATH = "data/full_wildfires_2000plus_stage6.csv"
OUTPUT_PATH = "data/full_wildfires_stage7_final_2_controls.csv"

TARGET_IDS = {7483, 33008}

# Systematic search:
# 20, 22, 24 ... 100 km
DISTANCE_STEP_KM = 2.0

# 0°, 2°, 4° ... 358°
BEARING_STEP_DEGREES = 2.0


def destination_point(
    latitude,
    longitude,
    distance_km,
    bearing_degrees,
):
    """
    Calculate a destination coordinate from a source
    coordinate, distance and bearing.
    """

    earth_radius_km = 6371.0088

    lat1 = math.radians(latitude)
    lon1 = math.radians(longitude)

    bearing = math.radians(
        bearing_degrees
    )

    angular_distance = (
        distance_km / earth_radius_km
    )

    lat2 = math.asin(
        math.sin(lat1)
        * math.cos(angular_distance)
        +
        math.cos(lat1)
        * math.sin(angular_distance)
        * math.cos(bearing)
    )

    lon2 = lon1 + math.atan2(
        math.sin(bearing)
        * math.sin(angular_distance)
        * math.cos(lat1),

        math.cos(angular_distance)
        -
        math.sin(lat1)
        * math.sin(lat2),
    )

    return (
        math.degrees(lat2),
        math.degrees(lon2),
    )


def main():

    print("=" * 72)
    print(
        "BUSHFIRE AI - FINAL SYSTEMATIC "
        "STAGE 7 RECOVERY"
    )
    print("=" * 72)

    sources = pd.read_csv(
        SOURCE_PATH
    )

    sources["date"] = pd.to_datetime(
        sources["date"]
    )

    targets = sources[
        sources["source_row_id"].isin(
            TARGET_IDS
        )
    ].copy()

    print(
        f"\nTarget sources found: "
        f"{len(targets)}/{len(TARGET_IDS)}"
    )

    if len(targets) != len(TARGET_IDS):
        raise RuntimeError(
            "Could not find both target sources."
        )

    print(
        "\nLoading vegetation lookup..."
    )

    vegetation_lookup = (
        s7.load_vegetation_lookup()
    )

    vegetation_sampler = (
        s7.VegetationSampler(
            s7.VEGETATION_RASTER,
            vegetation_lookup,
        )
    )

    print(
        "\nIndexing elevation tiles..."
    )

    elevation_sampler = (
        s7.ElevationSampler(
            s7.ELEVATION_TILE_DIR
        )
    )

    print(
        "\nLoading fire polygons..."
    )

    fires = s7.load_fire_polygons()

    fire_checker = (
        s7.FirePerimeterChecker(
            fires
        )
    )

    recovered = []
    still_failed = []

    try:

        for source in targets.itertuples(
            index=False
        ):

            print(
                "\n" + "-" * 72
            )

            print(
                f"Source: "
                f"{source.source_row_id}"
            )

            print(
                f"Date: "
                f"{source.date.date()}"
            )

            print(
                f"Location: "
                f"{source.latitude:.6f}, "
                f"{source.longitude:.6f}"
            )

            print(
                f"Elevation: "
                f"{float(source.elevation):.1f} m"
            )

            rejection_counts = {
                "outside_vegetation_raster": 0,
                "unknown_vegetation_value": 0,
                "missing_elevation": 0,
                "elevation_mismatch": 0,
                "fire_perimeter": 0,
            }

            candidates_checked = 0
            accepted = None

            distance = (
                s7.MIN_DISTANCE_KM
            )

            while (
                distance
                <= s7.MAX_DISTANCE_KM
                + 1e-9
            ):

                bearing = 0.0

                while bearing < 360.0:

                    candidates_checked += 1

                    (
                        candidate_lat,
                        candidate_lon,
                    ) = destination_point(
                        float(
                            source.latitude
                        ),
                        float(
                            source.longitude
                        ),
                        distance,
                        bearing,
                    )

                    (
                        candidate_vegetation,
                        vegetation_status,
                    ) = (
                        vegetation_sampler
                        .sample(
                            candidate_lat,
                            candidate_lon,
                        )
                    )

                    if (
                        candidate_vegetation
                        is None
                    ):

                        if (
                            vegetation_status
                            in rejection_counts
                        ):
                            rejection_counts[
                                vegetation_status
                            ] += 1

                        bearing += (
                            BEARING_STEP_DEGREES
                        )

                        continue

                    candidate_elevation = (
                        elevation_sampler
                        .sample(
                            candidate_lat,
                            candidate_lon,
                        )
                    )

                    if (
                        candidate_elevation
                        is None
                    ):
                        rejection_counts[
                            "missing_elevation"
                        ] += 1

                        bearing += (
                            BEARING_STEP_DEGREES
                        )

                        continue

                    elevation_difference = abs(
                        float(
                            candidate_elevation
                        )
                        -
                        float(
                            source.elevation
                        )
                    )

                    if (
                        elevation_difference
                        >
                        s7.MAX_ELEVATION_DIFFERENCE_M
                    ):
                        rejection_counts[
                            "elevation_mismatch"
                        ] += 1

                        bearing += (
                            BEARING_STEP_DEGREES
                        )

                        continue

                    if (
                        fire_checker
                        .candidate_near_relevant_fire(
                            candidate_lat,
                            candidate_lon,
                            source.date,
                        )
                    ):
                        rejection_counts[
                            "fire_perimeter"
                        ] += 1

                        bearing += (
                            BEARING_STEP_DEGREES
                        )

                        continue

                    match_type = (
                        s7.vegetation_match_type(
                            source,
                            candidate_vegetation,
                        )
                    )

                    if match_type is None:
                        raise RuntimeError(
                            "Unexpected vegetation "
                            "match result."
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
                            float(
                                source.latitude
                            ),

                        "source_longitude":
                            float(
                                source.longitude
                            ),

                        "control_latitude":
                            candidate_lat,

                        "control_longitude":
                            candidate_lon,

                        "distance_km":
                            distance,

                        "source_elevation":
                            float(
                                source.elevation
                            ),

                        "control_elevation":
                            float(
                                candidate_elevation
                            ),

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
                            candidates_checked,

                        "fire":
                            0,

                        "negative_type":
                            (
                                "matched_spatial_control"
                            ),
                    }

                    break

                if accepted is not None:
                    break

                distance += (
                    DISTANCE_STEP_KM
                )

            if accepted is None:

                still_failed.append(
                    source.source_row_id
                )

                print(
                    "\n❌ NO VALID CONTROL FOUND"
                )

            else:

                recovered.append(
                    accepted
                )

                print(
                    "\n✅ CONTROL FOUND"
                )

                print(
                    f"Distance: "
                    f"{accepted['distance_km']:.2f} km"
                )

                print(
                    f"Elevation difference: "
                    f"{accepted['elevation_difference']:.1f} m"
                )

                print(
                    f"Vegetation: "
                    f"{accepted['vegetation_match_type']}"
                )

            print(
                f"Candidates checked: "
                f"{candidates_checked:,}"
            )

            print(
                "Rejections:",
                rejection_counts,
            )

    finally:

        vegetation_sampler.close()
        elevation_sampler.close()

    recovered_df = pd.DataFrame(
        recovered
    )

    recovered_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "\n" + "=" * 72
    )

    print(
        "FINAL SYSTEMATIC RECOVERY FINISHED"
    )

    print(
        "=" * 72
    )

    print(
        f"Requested:     "
        f"{len(targets)}"
    )

    print(
        f"Recovered:     "
        f"{len(recovered_df)}"
    )

    print(
        f"Still failed:  "
        f"{len(still_failed)}"
    )

    print(
        f"Saved:         "
        f"{OUTPUT_PATH}"
    )

    if still_failed:

        print(
            "\nStill unresolved:"
        )

        for source_id in still_failed:
            print(
                f"  {source_id}"
            )

    else:

        print(
            "\n🔥 BOTH FINAL CONTROLS RECOVERED."
        )


if __name__ == "__main__":
    main()