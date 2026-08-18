import requests
import pandas as pd
import random

from datetime import datetime, timedelta
from shapely.geometry import shape


FIRE_URL = (
    "https://portal.data.nsw.gov.au/arcgis/rest/services/"
    "Hosted/NSWFireHistory/FeatureServer/0/query"
)

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_fires(limit=5):

    params = {
        "where": "ignition_date IS NOT NULL",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
        "resultRecordCount": limit,
    }

    response = requests.get(FIRE_URL, params=params, timeout=30)
    response.raise_for_status()

    return response.json()["features"]


def fetch_weather(latitude, longitude, target_date):

    end_date = datetime.strptime(target_date, "%Y-%m-%d")
    start_date = end_date - timedelta(days=30)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": target_date,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],
        "hourly": "relative_humidity_2m",
        "timezone": "Australia/Sydney",
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def days_since_rain(rainfall):

    count = 0

    for value in reversed(rainfall[:-1]):

        if value is not None and value >= 1:
            return count

        count += 1

    return count


def build_weather_features(
    latitude,
    longitude,
    target_date,
    fire_label
):

    weather = fetch_weather(
        latitude,
        longitude,
        target_date
    )

    daily = weather["daily"]

    rainfall = daily["precipitation_sum"]

    humidity = weather["hourly"][
        "relative_humidity_2m"
    ][-24:]

    valid_humidity = [
        x for x in humidity if x is not None
    ]

    target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
    month = target_datetime.month
    day_of_year = target_datetime.timetuple().tm_yday

    if month in (12, 1, 2):
        season = 0
    elif month in (3, 4, 5):
        season = 1
    elif month in (6, 7, 8):
        season = 2
    else:
        season = 3

    return {
        "date": target_date,
        "month": month,
        "day_of_year": day_of_year,
        "season": season,
        "latitude": latitude,
        "longitude": longitude,

        "max_temp":
            daily["temperature_2m_max"][-1],

        "min_temp":
            daily["temperature_2m_min"][-1],

        "avg_humidity":
            round(
                sum(valid_humidity)
                / len(valid_humidity),
                1
            ),

        "max_wind":
            daily["wind_speed_10m_max"][-1],

        "rain_today":
            rainfall[-1],

        "rain_last_7_days":
            round(
                sum(x or 0 for x in rainfall[-8:-1]),
                2
            ),

        "rain_last_30_days":
            round(
                sum(x or 0 for x in rainfall[:-1]),
                2
            ),

        "days_since_rain":
            days_since_rain(rainfall),

        "fire":
            fire_label,
    }

def fire_nearby(latitude, longitude, target_date):

    date = datetime.strptime(target_date, "%Y-%m-%d")

    start = date - timedelta(days=7)
    end = date + timedelta(days=7)

    # ArcGIS timestamps are milliseconds
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    params = {
        "where": (
            f"fire_type = 'Bushfire' "
            f"AND ignition_date >= {start_ms} "
            f"AND ignition_date <= {end_ms}"
        ),

        # ArcGIS expects longitude,latitude
        "geometry": f"{longitude},{latitude}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",

        "spatialRel": "esriSpatialRelIntersects",

        # Search 5 km around our point
        "distance": 5,
        "units": "esriSRUnit_Kilometer",

        "returnCountOnly": "true",
        "f": "json",
    }

    response = requests.get(
        FIRE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    count = result.get("count", 0)

    return count > 0

fires = fetch_fires(500)

rows = []


for fire in fires:

    props = fire["properties"]

    geometry = shape(fire["geometry"])
    centre = geometry.centroid

    latitude = centre.y
    longitude = centre.x

    fire_datetime = datetime.fromtimestamp(
        props["ignition_date"] / 1000
    )

    fire_date = fire_datetime.strftime("%Y-%m-%d")

    print(
        f"Creating FIRE example: "
        f"{props['fire_name']} ({fire_date})"
    )

    # -------------------------
    # FIRE = 1
    # -------------------------

    positive = build_weather_features(
        latitude,
        longitude,
        fire_date,
        1
    )

    rows.append(positive)

       # -------------------------
    # FIRE = 0
    # -------------------------

    negative_found = False
    attempts = 0
    max_attempts = 20

    while not negative_found and attempts < max_attempts:

        attempts += 1

        # Try another year, keeping roughly the same season/day
        year_offset = random.choice(
            [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]
        )

        negative_year = fire_datetime.year + year_offset
        if negative_year < 1941:
          continue

        try:
            negative_datetime = fire_datetime.replace(
                year=negative_year
            )
        except ValueError:
            negative_datetime = fire_datetime.replace(
                year=negative_year,
                day=28
            )

        negative_date = negative_datetime.strftime(
            "%Y-%m-%d"
        )

        print(
            f"Trying NON-FIRE candidate: "
            f"{negative_date}"
        )

        if fire_nearby(
            latitude,
            longitude,
            negative_date
        ):
            print(
                f"REJECTED: fire found near "
                f"{negative_date}"
            )
            continue

        print(
            f"VERIFIED NON-FIRE: "
            f"{negative_date}"
        )

        negative = build_weather_features(
            latitude,
            longitude,
            negative_date,
            0
        )

        rows.append(negative)

        negative_found = True

    if not negative_found:
        print(
            f"WARNING: Could not find verified "
            f"non-fire example after {max_attempts} attempts."
        )


df = pd.DataFrame(rows)

df.to_csv(
    "data/balanced_sample.csv",
    index=False
)

print("\n==============================")
print(df)
print("==============================")

print("\nClass counts:")
print(df["fire"].value_counts())

print(
    "\nSaved to "
    "data/training_dataset_1000.csv"
)
