import pandas as pd

INPUT_FILE = "data/training_dataset_v02.csv"
OUTPUT_FILE = "data/training_dataset_v04.csv"

df = pd.read_csv(INPUT_FILE)

print("Loaded:", df.shape)

# -------------------------
# INTERACTION FEATURES
# -------------------------

df["temp_humidity_index"] = (
    df["max_temp"] * (100 - df["avg_humidity"]) / 100
)

df["temp_wind_index"] = (
    df["max_temp"] * df["max_wind"]
)

df["dryness_index"] = (
    (df["days_since_rain"] + 1)
    / (df["rain_last_30_days"] + 1)
)

# -------------------------
# SIMPLE VPD APPROXIMATION
# -------------------------
# Saturation vapour pressure using max temperature
# then adjusted by relative humidity.

import math

def calculate_vpd(row):
    temp = row["max_temp"]
    humidity = row["avg_humidity"]

    saturation_vp = 0.6108 * math.exp(
        (17.27 * temp) / (temp + 237.3)
    )

    actual_vp = saturation_vp * (humidity / 100)

    return saturation_vp - actual_vp


df["vpd"] = df.apply(
    calculate_vpd,
    axis=1
)

# -------------------------
# SAVE
# -------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("Saved:", OUTPUT_FILE)
print("Shape:", df.shape)

print("\nNew feature preview:")

print(
    df[
        [
            "max_temp",
            "avg_humidity",
            "max_wind",
            "rain_last_30_days",
            "days_since_rain",
            "temp_humidity_index",
            "temp_wind_index",
            "dryness_index",
            "vpd",
            "fire",
        ]
    ].head()
)