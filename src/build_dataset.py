import requests
import pandas as pd

from datetime import datetime, timedelta
from shapely.geometry import shape


FIRE_URL = (
    "https://portal.data.nsw.gov.au/arcgis/rest/services/"
    "Hosted/NSWFireHistory/FeatureServer/0/query"
)

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_fires(limit=5):
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
        "resultRecordCount": limit,
    }

    response = requests.get(
        FIRE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()["features"]


def fetch_weather(latitude, longitude, fire_date):

    end_date = datetime.strptime(
        fire_date,
        "%Y-%m-%d"
    )

    start_date = end_date - timedelta(days=30)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),

        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],

        "hourly": [
            "relative_humidity_2m",
        ],

        "timezone": "Australia/Sydney",
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def calculate_days_since_rain(rainfall_values):

    # Ignore current day
    previous_days = rainfall_values[:-1]

    days_since_rain = 0

    for rainfall in reversed(previous_days):

        if rainfall is not None and rainfall >= 1.0:
            return days_since_rain

        days_since_rain += 1

    return days_since_rain


fires = fetch_fires(5)

rows = []


for fire in fires:

    properties = fire["properties"]

    if not properties.get("ignition_date"):
        continue

    if not fire.get("geometry"):
        continue

    geometry = shape(fire["geometry"])

    centre = geometry.centroid

    latitude = centre.y
    longitude = centre.x

    fire_date = datetime.fromtimestamp(
        properties["ignition_date"] / 1000
    ).strftime("%Y-%m-%d")

    print(f"Processing: {properties['fire_name']}")

    weather = fetch_weather(
        latitude,
        longitude,
        fire_date
    )

    daily = weather["daily"]

    rainfall = daily["precipitation_sum"]

    # Today's weather
    max_temp = daily["temperature_2m_max"][-1]
    min_temp = daily["temperature_2m_min"][-1]
    max_wind = daily["wind_speed_10m_max"][-1]
    rainfall_today = rainfall[-1]

    # Historical rainfall
    rain_last_7_days = sum(
        value or 0
        for value in rainfall[-8:-1]
    )

    rain_last_30_days = sum(
        value or 0
        for value in rainfall[:-1]
    )

    days_since_rain = calculate_days_since_rain(
        rainfall
    )

    # Humidity from final 24 hours
    humidity_values = weather["hourly"][
        "relative_humidity_2m"
    ][-24:]

    valid_humidity = [
        value
        for value in humidity_values
        if value is not None
    ]

    avg_humidity = (
        sum(valid_humidity) / len(valid_humidity)
        if valid_humidity
        else None
    )

    row = {

        "fire_name": properties["fire_name"],
        "date": fire_date,

        "latitude": latitude,
        "longitude": longitude,

        "max_temp": max_temp,
        "min_temp": min_temp,
        "avg_humidity": round(avg_humidity, 1)
        if avg_humidity is not None
        else None,

        "max_wind": max_wind,

        "rain_today": rainfall_today,

        "rain_last_7_days": round(
            rain_last_7_days,
            2
        ),

        "rain_last_30_days": round(
            rain_last_30_days,
            2
        ),

        "days_since_rain": days_since_rain,

        "area_ha": properties["area_ha"],

        "ignition_cause": properties[
            "ignition_cause"
        ],

        "fire": 1,
    }

    rows.append(row)


df = pd.DataFrame(rows)

df.to_csv(
    "data/training_sample.csv",
    index=False
)

print("\n================================")
print(df)
print("================================")

print(
    "\nDataset saved to "
    "data/training_sample.csv"
)