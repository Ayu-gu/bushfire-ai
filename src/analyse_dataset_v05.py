import pandas as pd
import matplotlib.pyplot as plt


DATASET_PATH = "data/training_dataset_v05.csv"


# ============================================================
# LOAD DATASET
# ============================================================

df = pd.read_csv(
    DATASET_PATH
)


# ============================================================
# BASIC DATASET HEALTH
# ============================================================

print("\n==============================")
print("BUSHFIRE AI V05 DATASET AUDIT")
print("==============================")

print(f"\nTotal rows: {len(df):,}")

print("\nClass distribution:")
print(
    df["fire"].value_counts()
)

print("\nClass percentages:")
print(
    (
        df["fire"]
        .value_counts(normalize=True)
        * 100
    ).round(2)
)

print(
    f"\nDuplicate rows: "
    f"{df.duplicated().sum():,}"
)

print("\nMissing values:")
print(
    df.isnull().sum()
)


# ============================================================
# DATE COVERAGE
# ============================================================

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

print("\nDate coverage:")

print(
    "Earliest:",
    df["date"].min()
)

print(
    "Latest:",
    df["date"].max()
)

print(
    "Unique dates:",
    df["date"].nunique()
)


# ============================================================
# LOCATION COVERAGE
# ============================================================

print("\nLocation coverage:")

print(
    "Latitude:",
    round(df["latitude"].min(), 4),
    "to",
    round(df["latitude"].max(), 4)
)

print(
    "Longitude:",
    round(df["longitude"].min(), 4),
    "to",
    round(df["longitude"].max(), 4)
)

unique_locations = (
    df[
        [
            "latitude",
            "longitude",
        ]
    ]
    .drop_duplicates()
    .shape[0]
)

print(
    "Unique locations:",
    f"{unique_locations:,}"
)


# ============================================================
# FEATURE SUMMARY
# ============================================================

feature_columns = [
    column
    for column in df.select_dtypes(
        include="number"
    ).columns
    if column not in [
        "source_fire_id",
        "latitude",
        "longitude",
        "fire",
    ]
]

print("\nFeature summary:")

print(
    df[
        feature_columns
    ].describe().round(2)
)


# ============================================================
# FIRE VS NON-FIRE MEANS
# ============================================================

print("\n==============================")
print("FIRE VS NON-FIRE FEATURE MEANS")
print("==============================")

feature_means = (
    df
    .groupby("fire")[
        feature_columns
    ]
    .mean()
    .T
)

feature_means.columns = [
    "Non-Fire",
    "Fire",
]

print(
    feature_means.round(2)
)


# ============================================================
# FEATURE DISTRIBUTIONS
# ============================================================

important_features = [
    "max_temp",
    "min_temp",
    "avg_humidity",
    "max_wind",
    "rain_today",
    "rain_last_7_days",
    "rain_last_30_days",
    "days_since_rain",
]

for feature in important_features:

    if feature not in df.columns:
        continue

    plt.figure(
        figsize=(9, 5)
    )

    fire_values = df.loc[
        df["fire"] == 1,
        feature
    ].dropna()

    non_fire_values = df.loc[
        df["fire"] == 0,
        feature
    ].dropna()

    plt.hist(
        non_fire_values,
        bins=40,
        alpha=0.6,
        label="Non-Fire",
        density=True
    )

    plt.hist(
        fire_values,
        bins=40,
        alpha=0.6,
        label="Fire",
        density=True
    )

    plt.title(
        f"V05 — {feature}"
    )

    plt.xlabel(
        feature
    )

    plt.ylabel(
        "Density"
    )

    plt.legend()

    plt.tight_layout()

    plt.show()


# ============================================================
# CORRELATION MATRIX
# ============================================================

numeric_df = df.select_dtypes(
    include="number"
)

correlation = (
    numeric_df
    .corr()
)

plt.figure(
    figsize=(13, 10)
)

image = plt.imshow(
    correlation,
    aspect="auto"
)

plt.colorbar(
    image,
    label="Correlation"
)

plt.xticks(
    range(len(correlation.columns)),
    correlation.columns,
    rotation=90
)

plt.yticks(
    range(len(correlation.columns)),
    correlation.columns
)

plt.title(
    "Bushfire AI V05 — Feature Correlation"
)

plt.tight_layout()

plt.show()


# ============================================================
# SEASONAL DISTRIBUTION
# ============================================================

df["month"] = (
    df["date"].dt.month
)

monthly_counts = (
    df
    .groupby(
        [
            "month",
            "fire",
        ]
    )
    .size()
    .unstack(
        fill_value=0
    )
)

monthly_counts.plot(
    kind="bar",
    figsize=(11, 6)
)

plt.title(
    "Bushfire AI V05 — Monthly Distribution"
)

plt.xlabel(
    "Month"
)

plt.ylabel(
    "Number of Samples"
)

plt.legend(
    [
        "Non-Fire",
        "Fire",
    ]
)

plt.tight_layout()

plt.show()


# ============================================================
# GEOGRAPHIC DISTRIBUTION
# ============================================================

plt.figure(
    figsize=(10, 8)
)

non_fire = df[
    df["fire"] == 0
]

fire = df[
    df["fire"] == 1
]

plt.scatter(
    non_fire["longitude"],
    non_fire["latitude"],
    s=5,
    alpha=0.3,
    label="Non-Fire"
)

plt.scatter(
    fire["longitude"],
    fire["latitude"],
    s=5,
    alpha=0.3,
    label="Fire"
)

plt.title(
    "Bushfire AI V05 — Geographic Distribution"
)

plt.xlabel(
    "Longitude"
)

plt.ylabel(
    "Latitude"
)

plt.legend()

plt.tight_layout()

plt.show()