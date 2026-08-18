import pandas as pd

# Load dataset
df = pd.read_csv("data/balanced_sample.csv")

print("\n==============================")
print("DATASET OVERVIEW")
print("==============================")

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nColumns:")
print(df.columns.tolist())


# --------------------------------
# CLASS BALANCE
# --------------------------------

print("\n==============================")
print("CLASS BALANCE")
print("==============================")

print(df["fire"].value_counts())


# --------------------------------
# MISSING VALUES
# --------------------------------

print("\n==============================")
print("MISSING VALUES")
print("==============================")

print(df.isnull().sum())


# --------------------------------
# DUPLICATES
# --------------------------------

print("\n==============================")
print("DUPLICATE ROWS")
print("==============================")

print(df.duplicated().sum())


# --------------------------------
# BASIC STATISTICS
# --------------------------------

features = [
    "max_temp",
    "min_temp",
    "avg_humidity",
    "max_wind",
    "rain_today",
    "rain_last_7_days",
    "rain_last_30_days",
    "days_since_rain",
]

print("\n==============================")
print("FEATURE STATISTICS")
print("==============================")

print(df[features].describe())


# --------------------------------
# FIRE VS NON-FIRE
# --------------------------------

print("\n==============================")
print("AVERAGE CONDITIONS BY CLASS")
print("==============================")

print(
    df.groupby("fire")[features]
    .mean()
    .round(2)
)


# --------------------------------
# DATE RANGE
# --------------------------------

df["date"] = pd.to_datetime(df["date"])

print("\n==============================")
print("DATE RANGE")
print("==============================")

print("Oldest:", df["date"].min())
print("Newest:", df["date"].max())