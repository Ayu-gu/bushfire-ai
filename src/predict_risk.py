import math
import torch
import torch.nn as nn
import numpy as np


MODEL_PATH = "models/bushfire_model_v04.pth"


# -----------------------------------
# DEVICE
# -----------------------------------

device = torch.device(
    "mps" if torch.backends.mps.is_available()
    else "cpu"
)

print("Using device:", device)


# -----------------------------------
# MODEL ARCHITECTURE
# Must match training exactly
# -----------------------------------

class BushfireModel(nn.Module):

    def __init__(self):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(15, 32),
            nn.ReLU(),

            nn.Linear(32, 16),
            nn.ReLU(),

            nn.Linear(16, 8),
            nn.ReLU(),

            nn.Linear(8, 1),
        )

    def forward(self, x):
        return self.network(x)


# -----------------------------------
# LOAD SAVED MODEL
# -----------------------------------

checkpoint = torch.load(
    MODEL_PATH,
    map_location=device,
    weights_only=False
)

model = BushfireModel().to(device)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model.eval()

features = checkpoint["features"]

scaler_mean = np.array(
    checkpoint["scaler_mean"]
)

scaler_scale = np.array(
    checkpoint["scaler_scale"]
)

print("Model loaded successfully.")
print("Features:", features)


# -----------------------------------
# HELPERS
# -----------------------------------

def get_season(month):

    if month in [12, 1, 2]:
        return 0

    elif month in [3, 4, 5]:
        return 1

    elif month in [6, 7, 8]:
        return 2

    else:
        return 3


def calculate_vpd(
    max_temp,
    avg_humidity
):

    saturation_vp = (
        0.6108
        * math.exp(
            (17.27 * max_temp)
            / (max_temp + 237.3)
        )
    )

    actual_vp = (
        saturation_vp
        * (avg_humidity / 100)
    )

    return saturation_vp - actual_vp


# -----------------------------------
# PREDICTION FUNCTION
# -----------------------------------

def predict_fire_risk(
    month,
    day_of_year,
    max_temp,
    min_temp,
    avg_humidity,
    max_wind,
    rain_today,
    rain_last_7_days,
    rain_last_30_days,
    days_since_rain,
):

    season = get_season(month)

    temp_humidity_index = (
        max_temp
        * (100 - avg_humidity)
        / 100
    )

    temp_wind_index = (
        max_temp
        * max_wind
    )

    dryness_index = (
        (days_since_rain + 1)
        / (rain_last_30_days + 1)
    )

    vpd = calculate_vpd(
        max_temp,
        avg_humidity
    )

    input_data = np.array([
        month,
        day_of_year,
        season,
        max_temp,
        min_temp,
        avg_humidity,
        max_wind,
        rain_today,
        rain_last_7_days,
        rain_last_30_days,
        days_since_rain,
        temp_humidity_index,
        temp_wind_index,
        dryness_index,
        vpd,
    ], dtype=np.float32)

    # Apply SAME scaling as training
    scaled_data = (
        input_data - scaler_mean
    ) / scaler_scale

    input_tensor = torch.tensor(
        scaled_data,
        dtype=torch.float32
    ).unsqueeze(0).to(device)

    with torch.no_grad():

        logits = model(
            input_tensor
        )

        probability = torch.sigmoid(
            logits
        ).item()

    risk_score = probability * 100

    if risk_score < 30:
        risk_level = "LOW"

    elif risk_score < 50:
        risk_level = "MODERATE"

    elif risk_score < 70:
        risk_level = "HIGH"

    else:
        risk_level = "VERY HIGH"

    return (
        risk_score,
        risk_level
    )


# -----------------------------------
# TEST EXAMPLE
# -----------------------------------

risk_score, risk_level = predict_fire_risk(

    month=1,
    day_of_year=15,

    max_temp=38.0,
    min_temp=22.0,

    avg_humidity=20.0,

    max_wind=35.0,

    rain_today=0.0,
    rain_last_7_days=0.5,
    rain_last_30_days=4.0,

    days_since_rain=18,
)


print("\n==============================")
print("BUSHFIRE AI PREDICTION")
print("==============================")

print(
    f"Risk score: "
    f"{risk_score:.2f}%"
)

print(
    f"Risk level: "
    f"{risk_level}"
)