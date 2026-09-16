import math
import requests
import torch
import torch.nn as nn
import numpy as np

from fetch_bom_observations import find_nearest_station
from datetime import datetime, timedelta


MODEL_PATH = "models/bushfire_model_v04.pth"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


# -----------------------------------
# DEVICE
# -----------------------------------

device = torch.device(
    "mps" if torch.backends.mps.is_available()
    else "cpu"
)

#print("Using device:", device)


# -----------------------------------
# MODEL
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

scaler_mean = np.array(
    checkpoint["scaler_mean"]
)

scaler_scale = np.array(
    checkpoint["scaler_scale"]
)

#print("Model loaded successfully.")


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


def calculate_days_since_rain(
    rainfall_values
):

    count = 0

    for value in reversed(
        rainfall_values[:-1]
    ):

        if value is not None and value >= 1:
            return count

        count += 1

    return count


# -----------------------------------
# WEATHER
# -----------------------------------

def fetch_recent_weather(
    latitude,
    longitude
):

    end_date = datetime.now()

    start_date = (
        end_date
        - timedelta(days=30)
    )

    params = {
    "latitude": latitude,
    "longitude": longitude,

    "current": [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    ],

    "daily": [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "wind_speed_10m_max",
    ],

    "hourly": [
        "relative_humidity_2m",
    ],

    "past_days": 30,
    "forecast_days": 1,

    "timezone": "Australia/Sydney",
}

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# -----------------------------------
# PREDICT LOCATION
# -----------------------------------

def predict_location(
    latitude,
    longitude
):
    
    # Actual current observation from nearest BOM station
    bom_weather = find_nearest_station(
        latitude,
        longitude
    )

    # Weather data used for AI model features    
    weather = fetch_recent_weather(
        latitude,
        longitude
    )

    daily = weather["daily"]

    current = weather["current"]

    current_temp = current["temperature_2m"]
    current_humidity = current["relative_humidity_2m"]
    current_wind = current["wind_speed_10m"]

    rainfall = daily[
        "precipitation_sum"
    ]

    max_temp = daily[
        "temperature_2m_max"
    ][-1]

    min_temp = daily[
        "temperature_2m_min"
    ][-1]

    max_wind = daily[
        "wind_speed_10m_max"
    ][-1]

    rain_today = rainfall[-1]

    rain_last_7_days = sum(
        x or 0
        for x in rainfall[-8:-1]
    )

    rain_last_30_days = sum(
        x or 0
        for x in rainfall[:-1]
    )

    days_since_rain = (
        calculate_days_since_rain(
            rainfall
        )
    )

    humidity_values = weather[
        "hourly"
    ]["relative_humidity_2m"][-24:]

    valid_humidity = [
        x
        for x in humidity_values
        if x is not None
    ]

    avg_humidity = (
        sum(valid_humidity)
        / len(valid_humidity)
    )

    now = datetime.now()

    month = now.month
    day_of_year = (
        now.timetuple().tm_yday
    )

    season = get_season(
        month
    )

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

    scaled_data = (
        input_data - scaler_mean
    ) / scaler_scale

    input_tensor = torch.tensor(
        scaled_data,
        dtype=torch.float32
    ).unsqueeze(0).to(device)

    with torch.no_grad():
         # -----------------------------------
         # CAPTURE REAL NEURAL ACTIVATIONS
         # -----------------------------------
         
         layer1_raw = model.network[0](input_tensor)
         layer1 = model.network[1](layer1_raw)
         
         layer2_raw = model.network[2](layer1)
         layer2 = model.network[3](layer2_raw)
         
         layer3_raw = model.network[4](layer2)
         layer3 = model.network[5](layer3_raw)
         
         logits = model.network[6](layer3)
         
         probability = torch.sigmoid(
             logits
         ).item()

    risk_score = (
        probability * 100
    )

    if risk_score < 30:
        risk_level = "LOW"

    elif risk_score < 50:
        risk_level = "MODERATE"

    elif risk_score < 70:
        risk_level = "HIGH"

    else:
        risk_level = "VERY HIGH"

    activations = {
        "input": input_tensor.squeeze(0).cpu().tolist(),
        "layer1": layer1.squeeze(0).cpu().tolist(),
        "layer2": layer2.squeeze(0).cpu().tolist(),
        "layer3": layer3.squeeze(0).cpu().tolist(),
        "output": probability,
    }

    return {
        "activations": activations,
        "latitude": latitude,
        "longitude": longitude,

        "current_temp": bom_weather.get("temperature"),
        "current_humidity": bom_weather.get("humidity"),
        "current_wind": bom_weather.get("wind_speed"),
        "weather_source": "Bureau of Meteorology",
        "weather_station": bom_weather.get("station_name"),
        "weather_station_distance_km": bom_weather.get("distance_km"),
        "weather_observation_time": bom_weather.get("observation_time"),

        "max_temp": max_temp,
        "min_temp": min_temp,
        "avg_humidity":
            round(avg_humidity, 1),
        "max_wind": max_wind,
        "rain_today": rain_today,
        "rain_last_7_days":
            round(rain_last_7_days, 1),
        "rain_last_30_days":
            round(rain_last_30_days, 1),
        "days_since_rain":
            days_since_rain,
        "risk_score":
            round(risk_score, 2),
        "risk_level":
            risk_level,
    }


# -----------------------------------
# TEST LOCATION
# -----------------------------------
if __name__ == "__main__":

    result = predict_location(
        latitude=-31.9539,
        longitude=141.4539
    )

    print("\n==============================")
    print("BUSHFIRE AI LOCATION RESULT")
    print("==============================")

    for key, value in result.items():
        print(f"{key}: {value}")