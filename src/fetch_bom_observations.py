from urllib.request import urlopen
import xml.etree.ElementTree as ET
import math


BOM_URL = (
    "ftp://ftp.bom.gov.au/"
    "anon/gen/fwo/IDN60920.xml"
)


def fetch_bom_observations():

    with urlopen(
        BOM_URL,
        timeout=30
    ) as response:
        data = response.read()

    root = ET.fromstring(data)

    stations = []

    for station in root.findall(".//station"):

        lat = station.get("lat")
        lon = station.get("lon")

        if not lat or not lon:
            continue

        station_data = {
            "station_name": station.get("stn-name"),
            "description": station.get("description"),
            "latitude": float(lat),
            "longitude": float(lon),
            "bom_id": station.get("bom-id"),
        }

        period = station.find("period")

        if period is None:
            continue

        station_data["observation_time"] = (
            period.get("time-local")
        )

        # IMPORTANT:
        # elements are nested inside <level>
        for element in period.findall(".//element"):

            element_type = element.get("type")
            value = element.text

            if value is None:
                continue

            if element_type == "air_temperature":
                station_data["temperature"] = float(value)

            elif element_type == "apparent_temp":
                station_data["apparent_temp"] = float(value)

            elif element_type == "rel-humidity":
                station_data["humidity"] = float(value)

            elif element_type == "wind_spd_kmh":
                station_data["wind_speed"] = float(value)

            elif element_type == "wind_dir":
                station_data["wind_direction"] = value

            elif element_type == "rainfall":
                station_data["rainfall"] = float(value)

            elif element_type == "maximum_air_temperature":
                station_data["max_temp"] = float(value)

            elif element_type == "minimum_air_temperature":
                station_data["min_temp"] = float(value)

        stations.append(station_data)

    return stations


def distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):

    radius = 6371

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radius * c


def find_nearest_station(
    latitude,
    longitude
):

    stations = fetch_bom_observations()

    usable_stations = [
        station
        for station in stations
        if "temperature" in station
    ]

    if not usable_stations:
        raise RuntimeError(
            "No usable BOM stations found."
        )

    nearest = min(
        usable_stations,
        key=lambda station: distance_km(
            latitude,
            longitude,
            station["latitude"],
            station["longitude"],
        )
    )

    nearest["distance_km"] = round(
        distance_km(
            latitude,
            longitude,
            nearest["latitude"],
            nearest["longitude"],
        ),
        1
    )

    return nearest


if __name__ == "__main__":

    result = find_nearest_station(
        latitude=-35.2809,
        longitude=149.1300
    )

    print("\n==============================")
    print("NEAREST BOM OBSERVATION")
    print("==============================")

    for key, value in result.items():
        print(f"{key}: {value}")