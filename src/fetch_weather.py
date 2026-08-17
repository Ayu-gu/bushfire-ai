import requests

latitude = -34.23620809785823
longitude = 149.98523759294704
date = "2015-01-02"

url = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": latitude,
    "longitude": longitude,
    "start_date": date,
    "end_date": date,
    "daily": [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "wind_speed_10m_max"
    ],
    "hourly": [
        "relative_humidity_2m"
    ],
    "timezone": "Australia/Sydney"
}

print("Fetching historical weather...")

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()

data = response.json()

print("\nLocation:", latitude, longitude)
print("Date:", date)

print("\nDAILY WEATHER")
print("Maximum temperature:", data["daily"]["temperature_2m_max"][0], "°C")
print("Minimum temperature:", data["daily"]["temperature_2m_min"][0], "°C")
print("Rainfall:", data["daily"]["precipitation_sum"][0], "mm")
print("Maximum wind:", data["daily"]["wind_speed_10m_max"][0], "km/h")

humidity_values = [
    value for value in data["hourly"]["relative_humidity_2m"]
    if value is not None
]

average_humidity = sum(humidity_values) / len(humidity_values)

print("Average humidity:", round(average_humidity, 1), "%")