import pandas as pd


INPUT_FILE = "data/balanced_sample.csv"
OUTPUT_FILE = "data/training_dataset_v02.csv"


# -------------------------
# LOAD DATA
# -------------------------

df = pd.read_csv(INPUT_FILE)

print("Loaded dataset:", df.shape)


# -------------------------
# DATE FEATURES
# -------------------------

df["date"] = pd.to_datetime(df["date"])

df["month"] = df["date"].dt.month
df["day_of_year"] = df["date"].dt.dayofyear


def get_season(month):
    if month in [12, 1, 2]:
        return 0      # Summer
    elif month in [3, 4, 5]:
        return 1      # Autumn
    elif month in [6, 7, 8]:
        return 2      # Winter
    else:
        return 3      # Spring


df["season"] = df["month"].apply(get_season)


# -------------------------
# REORDER COLUMNS
# -------------------------

columns = [
    "date",
    "month",
    "day_of_year",
    "season",
    "latitude",
    "longitude",
    "max_temp",
    "min_temp",
    "avg_humidity",
    "max_wind",
    "rain_today",
    "rain_last_7_days",
    "rain_last_30_days",
    "days_since_rain",
    "fire",
]

df = df[columns]


# -------------------------
# SAVE
# -------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSaved:", OUTPUT_FILE)
print("Shape:", df.shape)

print("\nClass counts:")
print(df["fire"].value_counts())

print("\nPreview:")
print(df.head())