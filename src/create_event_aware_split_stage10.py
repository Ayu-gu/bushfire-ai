"""
Stage 10 - Event-aware Train / Validation / Test Split
-------------------------------------------------------

Input:
    final_paired_bushfire_dataset_stage9.csv

Rules:
    - A wildfire event_id may appear in ONE split only.
    - A matched fire/control pair may appear in ONE split only.
    - Both members of every pair stay together.
    - Target approximately:
          Train      70%
          Validation 15%
          Test       15%
    - Deterministic random seed.
    - No ML preprocessing is performed here.
"""

from pathlib import Path

import numpy as np
import pandas as pd


INPUT_FILE = Path(
    "data/final_paired_bushfire_dataset_stage9.csv"
)

OUTPUT_FILE = Path(
    "data/final_paired_bushfire_dataset_stage10_split.csv"
)

SPLIT_FILE = Path(
    "data/stage10_event_split_manifest.csv"
)

SEED = 42

TARGETS = {
    "train": 0.70,
    "validation": 0.15,
    "test": 0.15,
}


# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("=" * 70)
print("STAGE 10 - EVENT-AWARE DATA SPLIT")
print("=" * 70)

print(f"Rows        : {len(df):,}")
print(f"Pairs       : {df['pair_id'].nunique():,}")
print(f"Events      : {df['event_id'].nunique():,}")


# ============================================================
# BASIC INPUT INTEGRITY
# ============================================================

assert len(df) == 18494
assert df["pair_id"].nunique() == 9247
assert df["event_id"].isna().sum() == 0

pair_check = (
    df.groupby("pair_id")
    .agg(
        rows=("fire", "size"),
        fire_sum=("fire", "sum"),
        events=("event_id", "nunique"),
    )
)

assert (pair_check["rows"] == 2).all()
assert (pair_check["fire_sum"] == 1).all()
assert (pair_check["events"] == 1).all()


# ============================================================
# EVENT TABLE
# ============================================================

# One row per event, with number of matched pairs belonging
# to that real wildfire event.
events = (
    df[df["fire"] == 1]
    .groupby("event_id")
    .agg(
        pair_count=("pair_id", "nunique")
    )
    .reset_index()
)

assert events["event_id"].nunique() == len(events)
assert events["pair_count"].sum() == 9247


# ============================================================
# GROUP-AWARE APPROXIMATE 70 / 15 / 15 SPLIT
# ============================================================

rng = np.random.default_rng(SEED)

# Random tie-breaker prevents ordering bias between events
# with the same number of pairs.
events["_random"] = rng.random(len(events))

# Large events are allocated first.
events = (
    events
    .sort_values(
        ["pair_count", "_random"],
        ascending=[False, True]
    )
    .reset_index(drop=True)
)

total_pairs = int(events["pair_count"].sum())

target_pairs = {
    split: total_pairs * fraction
    for split, fraction in TARGETS.items()
}

assigned_pairs = {
    "train": 0,
    "validation": 0,
    "test": 0,
}

assignments = []


for _, row in events.iterrows():

    event_size = int(row["pair_count"])

    # Compare how full each split would be relative
    # to its target after assigning this event.
    scores = {}

    for split in TARGETS:

        projected = (
            assigned_pairs[split]
            + event_size
        )

        scores[split] = (
            projected
            / target_pairs[split]
        )

    # Put the event into the split that would remain
    # least full relative to its target.
    chosen_split = min(
        scores,
        key=scores.get
    )

    assigned_pairs[chosen_split] += event_size

    assignments.append(
        {
            "event_id": row["event_id"],
            "pair_count": event_size,
            "split": chosen_split,
        }
    )


manifest = pd.DataFrame(assignments)

assert len(manifest) == len(events)
assert manifest["event_id"].nunique() == len(events)


# ============================================================
# ATTACH SPLIT TO FULL DATASET
# ============================================================

final = df.merge(
    manifest[
        ["event_id", "split"]
    ],
    on="event_id",
    how="left",
    validate="many_to_one",
)

assert final["split"].isna().sum() == 0


# ============================================================
# LEAKAGE AUDITS
# ============================================================

print("\n" + "=" * 70)
print("LEAKAGE AUDIT")
print("=" * 70)

event_leakage = (
    final.groupby("event_id")
    ["split"]
    .nunique()
)

pair_leakage = (
    final.groupby("pair_id")
    ["split"]
    .nunique()
)

print(
    "Events in multiple splits :",
    int((event_leakage > 1).sum())
)

print(
    "Pairs in multiple splits  :",
    int((pair_leakage > 1).sum())
)

assert (event_leakage == 1).all()
assert (pair_leakage == 1).all()


# ============================================================
# SPLIT STATISTICS
# ============================================================

print("\n" + "=" * 70)
print("SPLIT STATISTICS")
print("=" * 70)

for split in [
    "train",
    "validation",
    "test",
]:

    part = final[
        final["split"] == split
    ]

    pairs = part["pair_id"].nunique()
    events_count = part["event_id"].nunique()

    percentage = (
        pairs
        / total_pairs
        * 100
    )

    fires = int(
        (part["fire"] == 1).sum()
    )

    controls = int(
        (part["fire"] == 0).sum()
    )

    print(
        f"\n{split.upper()}"
    )

    print(
        f"  Rows       : {len(part):,}"
    )

    print(
        f"  Pairs      : {pairs:,} "
        f"({percentage:.2f}%)"
    )

    print(
        f"  Events     : {events_count:,}"
    )

    print(
        f"  Fire       : {fires:,}"
    )

    print(
        f"  Non-fire   : {controls:,}"
    )

    assert fires == controls
    assert len(part) == pairs * 2


# ============================================================
# CROSS-SPLIT INTERSECTION AUDIT
# ============================================================

train_events = set(
    final.loc[
        final["split"] == "train",
        "event_id"
    ]
)

val_events = set(
    final.loc[
        final["split"] == "validation",
        "event_id"
    ]
)

test_events = set(
    final.loc[
        final["split"] == "test",
        "event_id"
    ]
)

print("\n" + "=" * 70)
print("CROSS-SPLIT EVENT INTERSECTIONS")
print("=" * 70)

print(
    "Train ∩ Validation:",
    len(train_events & val_events)
)

print(
    "Train ∩ Test      :",
    len(train_events & test_events)
)

print(
    "Validation ∩ Test :",
    len(val_events & test_events)
)

assert not (train_events & val_events)
assert not (train_events & test_events)
assert not (val_events & test_events)


# ============================================================
# SAVE
# ============================================================

final.to_csv(
    OUTPUT_FILE,
    index=False
)

manifest = manifest.sort_values(
    "event_id"
).reset_index(drop=True)

manifest.to_csv(
    SPLIT_FILE,
    index=False
)

print("\n" + "=" * 70)

print(
    f"Dataset saved : {OUTPUT_FILE}"
)

print(
    f"Manifest saved: {SPLIT_FILE}"
)

print("\n STAGE 10 EVENT-AWARE SPLIT PASSED ")

print("=" * 70)
