import json
import sys

from predict_location import predict_location


def main():

    if len(sys.argv) != 3:
        print(json.dumps({
            "error": "latitude and longitude required"
        }))
        sys.exit(1)

    latitude = float(sys.argv[1])
    longitude = float(sys.argv[2])

    result = predict_location(
        latitude,
        longitude
    )

    print(
        json.dumps(result)
    )


if __name__ == "__main__":
    main()