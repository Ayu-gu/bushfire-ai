import pandas as pd

PATH = "data/final_paired_bushfire_dataset_stage10_split.csv"

df = pd.read_csv(PATH)

# Absolutely no test-set inspection.
df = df[df["split"].isin(["train", "validation"])].copy()

print("=" * 80)
print("STAGE 12F - PAIR-LEVEL VEGETATION PROVENANCE AUDIT")
print("=" * 80)
print(f"Rows inspected : {len(df):,}")
print("Splits         : train + validation")
print("Test inspected : NO")


# ------------------------------------------------------------
# Build one fire/control row per pair
# ------------------------------------------------------------

fire = (
    df[df["fire"] == 1][
        [
            "split",
            "pair_id",
            "vegetation_class",
            "vegetation_formation",
        ]
    ]
    .rename(
        columns={
            "vegetation_class": "fire_class",
            "vegetation_formation": "fire_formation",
        }
    )
)

control = (
    df[df["fire"] == 0][
        [
            "split",
            "pair_id",
            "vegetation_class",
            "vegetation_formation",
        ]
    ]
    .rename(
        columns={
            "vegetation_class": "control_class",
            "vegetation_formation": "control_formation",
        }
    )
)

pairs = fire.merge(
    control,
    on=["split", "pair_id"],
    how="inner",
    validate="one_to_one",
)

print(f"Complete pairs  : {len(pairs):,}")


# ------------------------------------------------------------
# Mapping states
# ------------------------------------------------------------

SPECIAL = {
    "NO_MAPPED_PCT",
    "Not classified",
}


def mapping_state(value):
    if pd.isna(value):
        return "MISSING"

    value = str(value)

    if value == "NO_MAPPED_PCT":
        return "NO_MAPPED_PCT"

    if value == "Not classified":
        return "NOT_CLASSIFIED"

    return "MAPPED_CLASS"


pairs["fire_state"] = pairs["fire_class"].apply(mapping_state)
pairs["control_state"] = pairs["control_class"].apply(mapping_state)

pairs["same_class"] = (
    pairs["fire_class"] == pairs["control_class"]
)

pairs["same_formation"] = (
    pairs["fire_formation"] == pairs["control_formation"]
)


# ------------------------------------------------------------
# Overall transition matrix
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("FIRE -> CONTROL MAPPING-STATE TRANSITIONS")
print("=" * 80)

transition = pd.crosstab(
    pairs["fire_state"],
    pairs["control_state"],
    margins=True,
)

print(transition.to_string())


# ------------------------------------------------------------
# Split-level audit
# ------------------------------------------------------------

for split in ["train", "validation"]:

    part = pairs[pairs["split"] == split].copy()

    print("\n" + "=" * 80)
    print(split.upper())
    print("=" * 80)

    print(f"Pairs: {len(part):,}")

    print(
        f"Same vegetation class     : "
        f"{part['same_class'].mean():.3%} "
        f"({part['same_class'].sum():,}/{len(part):,})"
    )

    print(
        f"Same vegetation formation : "
        f"{part['same_formation'].mean():.3%} "
        f"({part['same_formation'].sum():,}/{len(part):,})"
    )

    print("\nFIRE MAPPING STATE")
    print(
        part["fire_state"]
        .value_counts()
        .to_string()
    )

    print("\nCONTROL MAPPING STATE")
    print(
        part["control_state"]
        .value_counts()
        .to_string()
    )

    print("\nFIRE -> CONTROL TRANSITIONS")

    t = pd.crosstab(
        part["fire_state"],
        part["control_state"],
    )

    print(t.to_string())


# ------------------------------------------------------------
# Special-category directionality
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("SPECIAL CATEGORY DIRECTIONALITY")
print("=" * 80)

checks = [
    (
        "Mapped fire -> NO_MAPPED control",
        (pairs["fire_state"] == "MAPPED_CLASS")
        & (pairs["control_state"] == "NO_MAPPED_PCT"),
    ),
    (
        "NO_MAPPED fire -> mapped control",
        (pairs["fire_state"] == "NO_MAPPED_PCT")
        & (pairs["control_state"] == "MAPPED_CLASS"),
    ),
    (
        "Mapped fire -> NOT_CLASSIFIED control",
        (pairs["fire_state"] == "MAPPED_CLASS")
        & (pairs["control_state"] == "NOT_CLASSIFIED"),
    ),
    (
        "NOT_CLASSIFIED fire -> mapped control",
        (pairs["fire_state"] == "NOT_CLASSIFIED")
        & (pairs["control_state"] == "MAPPED_CLASS"),
    ),
]

for label, mask in checks:
    print(
        f"{label:40s}: "
        f"{mask.sum():,} pairs "
        f"({mask.mean():.3%})"
    )


# ------------------------------------------------------------
# Most common exact class transitions
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("TOP DIFFERENT-CLASS TRANSITIONS")
print("=" * 80)

different = pairs[~pairs["same_class"]].copy()

top_transitions = (
    different
    .groupby(
        ["fire_class", "control_class"],
        dropna=False
    )
    .size()
    .reset_index(name="pairs")
    .sort_values(
        "pairs",
        ascending=False
    )
    .head(25)
)

print(top_transitions.to_string(index=False))


# ------------------------------------------------------------
# Does NO_MAPPED mostly appear on control side?
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("NO_MAPPED_PCT SIDE CHECK")
print("=" * 80)

fire_no_map = (
    pairs["fire_class"] == "NO_MAPPED_PCT"
).sum()

control_no_map = (
    pairs["control_class"] == "NO_MAPPED_PCT"
).sum()

print(f"Fire side NO_MAPPED_PCT    : {fire_no_map:,}")
print(f"Control side NO_MAPPED_PCT : {control_no_map:,}")

if fire_no_map > 0:
    print(
        "Control / fire ratio       : "
        f"{control_no_map / fire_no_map:.2f}x"
    )
else:
    print("Control / fire ratio       : undefined (0 fire cases)")


# ------------------------------------------------------------
# Not-classified side check
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("NOT CLASSIFIED SIDE CHECK")
print("=" * 80)

fire_nc = (
    pairs["fire_class"] == "Not classified"
).sum()

control_nc = (
    pairs["control_class"] == "Not classified"
).sum()

print(f"Fire side Not classified    : {fire_nc:,}")
print(f"Control side Not classified : {control_nc:,}")

if fire_nc > 0:
    print(
        "Control / fire ratio       : "
        f"{control_nc / fire_nc:.2f}x"
    )


# ------------------------------------------------------------
# Final reminder
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("STAGE 12F AUDIT COMPLETE")
print("NO DATA WAS MODIFIED.")
print("NO MODEL WAS TRAINED.")
print("TEST SET REMAINS LOCKED.")
print("=" * 80)
