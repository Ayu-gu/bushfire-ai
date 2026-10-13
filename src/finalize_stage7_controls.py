from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

STAGE6_PATH = Path(
    "data/full_wildfires_2000plus_stage6.csv"
)

ORIGINAL_CONTROLS_PATH = Path(
    "data/full_wildfires_matched_controls_stage7.csv"
)

RECOVERED_CONTROLS_PATH = Path(
    "data/full_wildfires_stage7_recovered_controls.csv"
)

OUTPUT_PATH = Path(
    "data/full_wildfires_matched_controls_stage7_complete.csv"
)

EXPECTED_UNMATCHED = {7483, 33008}

MIN_DISTANCE_KM = 20.0
MAX_DISTANCE_KM = 100.0
MAX_ELEVATION_DIFFERENCE_M = 300.0


# ============================================================
# HELPERS
# ============================================================

def fail(message):
    raise RuntimeError(
        f"\n❌ AUDIT FAILED: {message}"
    )


def main():

    print("=" * 72)
    print(
        "BUSHFIRE AI - STAGE 7 FINALISATION & AUDIT"
    )
    print("=" * 72)

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    print("\nLoading files...")

    positives = pd.read_csv(
        STAGE6_PATH
    )

    original = pd.read_csv(
        ORIGINAL_CONTROLS_PATH
    )

    recovered = pd.read_csv(
        RECOVERED_CONTROLS_PATH
    )

    # --------------------------------------------------------
    # NORMALISE RECOVERY SCHEMA TO ORIGINAL STAGE 7
    # --------------------------------------------------------

    recovered = recovered.rename(
        columns={
            "distance_km":

            "distance_from_source_km",

        "elevation_difference":

            "elevation_difference_m",
            }
    )

    print(
        f"Stage 6 positives:       {len(positives):,}"
    )

    print(
        f"Original Stage 7:        {len(original):,}"
    )

    print(
        f"Recovered controls:      {len(recovered):,}"
    )

    # --------------------------------------------------------
    # BASIC EXPECTATIONS
    # --------------------------------------------------------

    if len(positives) != 9249:
        fail(
            f"Expected 9,249 Stage 6 rows, "
            f"found {len(positives):,}."
        )

    if len(original) != 9240:
        fail(
            f"Expected 9,240 original controls, "
            f"found {len(original):,}."
        )

    if len(recovered) != 7:
        fail(
            f"Expected 7 recovered controls, "
            f"found {len(recovered):,}."
        )

    # --------------------------------------------------------
    # REQUIRED COLUMNS
    # --------------------------------------------------------

    required_control_columns = {
        "source_row_id",
        "event_id",
        "source_date",
        "source_latitude",
        "source_longitude",
        "control_latitude",
        "control_longitude",
        "distance_from_source_km",
        "source_elevation",
        "control_elevation",
        "elevation_difference_m",
        "vegetation_match_type",
        "fire",
        "negative_type",
    }

    for name, df in [
        ("original controls", original),
        ("recovered controls", recovered),
    ]:

        missing_columns = (
            required_control_columns
            - set(df.columns)
        )

        if missing_columns:
            fail(
                f"{name} missing columns: "
                f"{sorted(missing_columns)}"
            )

    # --------------------------------------------------------
    # CHECK DUPLICATES BEFORE MERGE
    # --------------------------------------------------------

    if original[
        "source_row_id"
    ].duplicated().any():

        fail(
            "Original Stage 7 contains duplicate "
            "source_row_id values."
        )

    if recovered[
        "source_row_id"
    ].duplicated().any():

        fail(
            "Recovery file contains duplicate "
            "source_row_id values."
        )

    original_ids = set(
        original[
            "source_row_id"
        ].astype(int)
    )

    recovered_ids = set(
        recovered[
            "source_row_id"
        ].astype(int)
    )

    overlap = (
        original_ids
        & recovered_ids
    )

    if overlap:
        fail(
            "Recovered controls overlap existing "
            f"Stage 7 source IDs: {sorted(overlap)}"
        )

    print(
        "\n✅ No duplicate or overlapping "
        "source IDs."
    )

    # --------------------------------------------------------
    # MERGE
    # --------------------------------------------------------

    controls = pd.concat(
        [
            original,
            recovered,
        ],
        ignore_index=True,
        sort=False,
    )

    print(
        f"\nCombined controls:       "
        f"{len(controls):,}"
    )

    if len(controls) != 9247:
        fail(
            f"Expected 9,247 final controls, "
            f"found {len(controls):,}."
        )

    # --------------------------------------------------------
    # UNIQUE SOURCE PAIRING
    # --------------------------------------------------------

    if controls[
        "source_row_id"
    ].duplicated().any():

        duplicates = (
            controls.loc[
                controls[
                    "source_row_id"
                ].duplicated(
                    keep=False
                ),
                "source_row_id",
            ]
            .astype(int)
            .tolist()
        )

        fail(
            "Duplicate final source pairings: "
            f"{sorted(set(duplicates))}"
        )

    if (
        controls[
            "source_row_id"
        ].nunique()
        != 9247
    ):
        fail(
            "Final controls do not contain "
            "9,247 unique source IDs."
        )

    # --------------------------------------------------------
    # VERIFY AGAINST STAGE 6
    # --------------------------------------------------------

    positive_ids = set(
        positives[
            "source_row_id"
        ].astype(int)
    )

    control_ids = set(
        controls[
            "source_row_id"
        ].astype(int)
    )

    unexpected_ids = (
        control_ids
        - positive_ids
    )

    if unexpected_ids:
        fail(
            "Controls reference source IDs not "
            "present in Stage 6: "
            f"{sorted(unexpected_ids)}"
        )

    missing_ids = (
        positive_ids
        - control_ids
    )

    if missing_ids != EXPECTED_UNMATCHED:
        fail(
            "Unexpected unmatched Stage 6 IDs. "
            f"Expected {sorted(EXPECTED_UNMATCHED)}, "
            f"found {sorted(missing_ids)}"
        )

    print(
        "✅ Exactly two expected unmatched "
        "sources remain:"
    )

    print(
        f"   {sorted(missing_ids)}"
    )

    # --------------------------------------------------------
    # DISTANCE AUDIT
    # --------------------------------------------------------

    distance = pd.to_numeric(
        controls["distance_from_source_km"],
        errors="coerce",
    )

    if distance.isna().any():
        fail(
            "Missing or invalid control distance."
        )

    invalid_distance = (
        (distance < MIN_DISTANCE_KM)
        |
        (distance > MAX_DISTANCE_KM)
    )

    if invalid_distance.any():
        fail(
            f"{invalid_distance.sum()} controls "
            "violate the 20–100 km rule."
        )

    print(
        "✅ All control distances are "
        "20–100 km."
    )

    # --------------------------------------------------------
    # ELEVATION AUDIT
    # --------------------------------------------------------

    source_elevation = pd.to_numeric(
        controls["source_elevation"],
        errors="coerce",
    )

    control_elevation = pd.to_numeric(
        controls["control_elevation"],
        errors="coerce",
    )

    stored_difference = pd.to_numeric(
        controls["elevation_difference_m"],
        errors="coerce",
    )

    if (
        source_elevation.isna().any()
        or
        control_elevation.isna().any()
        or
        stored_difference.isna().any()
    ):
        fail(
            "Missing/invalid elevation values."
        )

    calculated_difference = (
        source_elevation
        - control_elevation
    ).abs()

    if (
        calculated_difference
        > MAX_ELEVATION_DIFFERENCE_M
    ).any():

        fail(
            "At least one control violates "
            "the ±300 m elevation rule."
        )

    elevation_error = (
        calculated_difference
        - stored_difference
    ).abs()

    if (
        elevation_error > 0.05
    ).any():

        fail(
            "Stored elevation_difference does "
            "not match calculated elevation "
            "difference."
        )

    print(
        "✅ All controls satisfy the "
        "±300 m elevation rule."
    )

    # --------------------------------------------------------
    # LABEL AUDIT
    # --------------------------------------------------------

    fire_values = set(
        pd.to_numeric(
            controls["fire"],
            errors="coerce",
        ).dropna()
    )

    if fire_values != {0}:
        fail(
            f"Unexpected fire labels: "
            f"{fire_values}"
        )

    negative_types = set(
        controls[
            "negative_type"
        ].dropna().astype(str)
    )

    if negative_types != {
        "matched_spatial_control"
    }:
        fail(
            "Unexpected negative_type values: "
            f"{negative_types}"
        )

    print(
        "✅ All rows are correctly labelled "
        "non-fire controls."
    )

    # --------------------------------------------------------
    # DATE + EVENT ID AUDIT
    # --------------------------------------------------------

    source_reference = (
        positives[
            [
                "source_row_id",
                "event_id",
                "date",
            ]
        ]
        .copy()
    )

    source_reference[
        "source_row_id"
    ] = source_reference[
        "source_row_id"
    ].astype(int)

    audit = controls.merge(
        source_reference,
        on="source_row_id",
        how="left",
        suffixes=(
            "_control",
            "_positive",
        ),
        validate="one_to_one",
    )

    if audit[
        "date"
    ].isna().any():

        fail(
            "At least one control could not "
            "be linked to its Stage 6 source."
        )

    control_dates = pd.to_datetime(
        audit["source_date"],
        errors="coerce",
    ).dt.normalize()

    positive_dates = pd.to_datetime(
        audit["date"],
        errors="coerce",
    ).dt.normalize()

    if (
        control_dates.isna().any()
        or
        positive_dates.isna().any()
    ):
        fail(
            "Invalid dates detected."
        )

    date_mismatch = (
        control_dates
        != positive_dates
    )

    if date_mismatch.any():
        fail(
            f"{date_mismatch.sum()} controls "
            "have the wrong source date."
        )

    control_event = (
        audit[
            "event_id_control"
        ].fillna("").astype(str)
    )

    positive_event = (
        audit[
            "event_id_positive"
        ].fillna("").astype(str)
    )

    event_mismatch = (
        control_event
        != positive_event
    )

    if event_mismatch.any():
        fail(
            f"{event_mismatch.sum()} controls "
            "have the wrong event_id."
        )

    print(
        "✅ Source dates and event IDs match "
        "Stage 6."
    )

    # --------------------------------------------------------
    # COORDINATE AUDIT
    # --------------------------------------------------------

    coordinate_columns = [
        "source_latitude",
        "source_longitude",
        "control_latitude",
        "control_longitude",
    ]

    for column in coordinate_columns:

        numeric = pd.to_numeric(
            controls[column],
            errors="coerce",
        )

        if numeric.isna().any():
            fail(
                f"Invalid coordinates in "
                f"{column}."
            )

    print(
        "✅ All source/control coordinates "
        "are populated."
    )

    # --------------------------------------------------------
    # VEGETATION AUDIT
    # --------------------------------------------------------

    allowed_match_types = {
        "CLASS",
        "FORMATION",
        "DIFFERENT",
        "NO_MAPPED_PCT",
    }

    actual_match_types = set(
        controls[
            "vegetation_match_type"
        ].dropna().astype(str)
    )

    unexpected_match_types = (
        actual_match_types
        - allowed_match_types
    )

    if unexpected_match_types:
        fail(
            "Unexpected vegetation match types: "
            f"{sorted(unexpected_match_types)}"
        )

    print(
        "✅ Vegetation match types are valid."
    )

    # --------------------------------------------------------
    # FINAL SORT
    # --------------------------------------------------------

    controls[
        "source_row_id"
    ] = controls[
        "source_row_id"
    ].astype(int)

    controls = controls.sort_values(
        "source_row_id"
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # SAVE ONLY AFTER ALL AUDITS PASS
    # --------------------------------------------------------

    controls.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    coverage = (
        len(controls)
        / len(positives)
        * 100
    )

    print(
        "\n" + "=" * 72
    )

    print(
        "🔥 STAGE 7 FINAL AUDIT PASSED"
    )

    print(
        "=" * 72
    )

    print(
        f"Stage 6 positives:       "
        f"{len(positives):,}"
    )

    print(
        f"Final matched controls:  "
        f"{len(controls):,}"
    )

    print(
        f"Unmatched positives:     "
        f"{len(missing_ids):,}"
    )

    print(
        f"Matching coverage:       "
        f"{coverage:.4f}%"
    )

    print(
        "\nUnmatched source IDs:"
    )

    for source_id in sorted(
        missing_ids
    ):
        print(
            f"  {source_id}"
        )

    print(
        f"\nFinal Stage 7 file:\n"
        f"  {OUTPUT_PATH}"
    )

    print(
        "\nOriginal Stage 7 and recovery "
        "files were NOT modified."
    )

    print(
        "\nStage 7 can now be frozen "
        "before Stage 8."
    )


if __name__ == "__main__":
    main()