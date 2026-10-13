"""
Stage 9 - Build final paired bushfire modelling dataset
-------------------------------------------------------

Combines:
    Stage 6 wildfire observations
    Stage 8 matched non-fire controls

Rules:
    - Preserve Stage 6 and Stage 8 unchanged.
    - Exclude wildfire observations without a valid matched control.
    - One positive + one negative per source_row_id.
    - Standardise both classes to the same modelling schema.
    - Do not include control-generation metadata as model features.
"""

from pathlib import Path
import pandas as pd


STAGE6_FILE = Path(
    "data/full_wildfires_2000plus_stage6.csv"
)

STAGE8_FILE = Path(
    "data/full_wildfires_controls_stage8.csv"
)

OUTPUT_FILE = Path(
    "data/final_paired_bushfire_dataset_stage9.csv"
)


# ============================================================
# LOAD
# ============================================================

stage6 = pd.read_csv(STAGE6_FILE)
stage8 = pd.read_csv(STAGE8_FILE)

print("=" * 70)
print("STAGE 9 - FINAL PAIRED DATASET")
print("=" * 70)

print(f"Stage 6 wildfire rows : {len(stage6):,}")
print(f"Stage 8 control rows  : {len(stage8):,}")


# ============================================================
# VALID MATCHED IDS
# ============================================================

matched_ids = set(
    stage8["source_row_id"]
    .astype(int)
)

positive = stage6[
    stage6["source_row_id"]
    .astype(int)
    .isin(matched_ids)
].copy()

negative = stage8.copy()

print(
    f"Matched positives     : "
    f"{len(positive):,}"
)

print(
    f"Matched negatives     : "
    f"{len(negative):,}"
)


# ============================================================
# STANDARDISE POSITIVE ROWS
# ============================================================

positive_final = pd.DataFrame({

    "source_row_id":
        positive["source_row_id"].astype(int),

    "event_id":
        positive["event_id"],

    "pair_id":
        positive["source_row_id"].astype(int),

    "date":
        positive["date"],

    "latitude":
        positive["latitude"],

    "longitude":
        positive["longitude"],

    "fire":
        1,

    "month":
        positive["month"],

    "day_of_year":
        positive["day_of_year"],

    "season":
        positive["season"],

    "max_temp":
        positive["max_temp"],

    "min_temp":
        positive["min_temp"],

    "avg_humidity":
        positive["avg_humidity"],

    "max_wind":
        positive["max_wind"],

    "rain_today":
        positive["rain_today"],

    "rain_last_7_days":
        positive["rain_last_7_days"],

    "rain_last_30_days":
        positive["rain_last_30_days"],

    "days_since_rain":
        positive["days_since_rain"],

    "temp_humidity_index":
        positive["temp_humidity_index"],

    "temp_wind_index":
        positive["temp_wind_index"],

    "dryness_index":
        positive["dryness_index"],

    "vpd":
        positive["vpd"],

    "elevation":
        positive["elevation"],

    "pct_id":
        positive["pct_id"],

    "pct_name":
        positive["pct_name"],

    "vegetation_class":
        positive["vegetation_class"],

    "vegetation_formation":
        positive["vegetation_formation"],
})


# ============================================================
# STANDARDISE NEGATIVE ROWS
# ============================================================

negative_final = pd.DataFrame({

    "source_row_id":
        negative["source_row_id"].astype(int),

    "event_id":
        negative["event_id"],

    "pair_id":
        negative["source_row_id"].astype(int),

    "date":
        negative["source_date"],

    "latitude":
        negative["control_latitude"],

    "longitude":
        negative["control_longitude"],

    "fire":
        0,

    "month":
        negative["month"],

    "day_of_year":
        negative["day_of_year"],

    "season":
        negative["season"],

    "max_temp":
        negative["max_temp"],

    "min_temp":
        negative["min_temp"],

    "avg_humidity":
        negative["avg_humidity"],

    "max_wind":
        negative["max_wind"],

    "rain_today":
        negative["rain_today"],

    "rain_last_7_days":
        negative["rain_last_7_days"],

    "rain_last_30_days":
        negative["rain_last_30_days"],

    "days_since_rain":
        negative["days_since_rain"],

    "temp_humidity_index":
        negative["temp_humidity_index"],

    "temp_wind_index":
        negative["temp_wind_index"],

    "dryness_index":
        negative["dryness_index"],

    "vpd":
        negative["vpd"],

    "elevation":
        negative["control_elevation"],

    "pct_id":
        negative["control_pct_id"],

    "pct_name":
        negative["control_pct_name"],

    "vegetation_class":
        negative["control_vegetation_class"],

    "vegetation_formation":
        negative["control_vegetation_formation"],
})


# ============================================================
# COMBINE
# ============================================================

final = pd.concat(
    [
        positive_final,
        negative_final,
    ],
    ignore_index=True,
)


# Stable ordering:
# each fire immediately followed by its matched control.
final = (
    final
    .sort_values(
        ["pair_id", "fire"],
        ascending=[True, False]
    )
    .reset_index(drop=True)
)


# ============================================================
# AUDIT
# ============================================================

print("\n" + "=" * 70)
print("FINAL DATASET AUDIT")
print("=" * 70)

print(
    f"Total rows           : "
    f"{len(final):,}"
)

print(
    f"Unique pairs         : "
    f"{final['pair_id'].nunique():,}"
)

print("\nClass distribution:")
print(
    final["fire"]
    .value_counts()
    .sort_index()
)

pair_counts = (
    final.groupby("pair_id")
    ["fire"]
    .agg(["count", "sum"])
)

bad_pairs = pair_counts[
    (pair_counts["count"] != 2)
    | (pair_counts["sum"] != 1)
]

print(
    f"\nInvalid pairs        : "
    f"{len(bad_pairs):,}"
)

print(
    f"Duplicate class rows : "
    f"{final.duplicated(['pair_id', 'fire']).sum():,}"
)

print(
    f"Total null values    : "
    f"{int(final.isna().sum().sum()):,}"
)

print(
    f"Columns              : "
    f"{len(final.columns)}"
)


# ============================================================
# STRICT INTEGRITY CHECKS
# ============================================================

assert len(positive_final) == 9247
assert len(negative_final) == 9247
assert len(final) == 18494

assert final["pair_id"].nunique() == 9247

assert (
    final["fire"]
    .value_counts()
    .to_dict()
    == {1: 9247, 0: 9247}
)

assert len(bad_pairs) == 0

assert (
    final
    .duplicated(
        ["pair_id", "fire"]
    )
    .sum()
    == 0
)


# ============================================================
# SAVE
# ============================================================

final.to_csv(
    OUTPUT_FILE,
    index=False
)

print(
    f"\nSaved: {OUTPUT_FILE}"
)

print("\n STAGE 9 BUILD PASSED ")
