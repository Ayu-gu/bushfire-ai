import requests
from datetime import datetime
from shapely.geometry import shape

URL = "https://portal.data.nsw.gov.au/arcgis/rest/services/Hosted/NSWFireHistory/FeatureServer/0/query"

params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "true",
    "f": "geojson",
    "resultRecordCount": 5
}

print("Fetching NSW fire data...")

response = requests.get(URL, params=params, timeout=30)
response.raise_for_status()

data = response.json()

print("Number of fires returned:", len(data["features"]))

for fire in data["features"]:
    properties = fire["properties"]

    # Convert fire boundary into a geometry object
    geometry = shape(fire["geometry"])

    # Get centre point of the fire boundary
    centre = geometry.centroid

    longitude = centre.x
    latitude = centre.y

    # Convert Unix milliseconds into normal date
    timestamp = properties["ignition_date"]
    ignition_date = datetime.fromtimestamp(
        timestamp / 1000
    ).strftime("%Y-%m-%d")

    print("\n-----------------------------")
    print("Fire:", properties["fire_name"])
    print("Date:", ignition_date)
    print("Cause:", properties["ignition_cause"])
    print("Area:", round(properties["area_ha"], 2), "hectares")
    print("Latitude:", latitude)
    print("Longitude:", longitude)