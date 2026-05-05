import json
import os
import glob

CITIES_DIR = "data/cities"
OUTPUT_FILE = "data/all.min.json"


def build_summary(city):

    current = city.get("data", {}).get("current_weather", {})
    daily = city.get("data", {}).get("daily", {})

    return {
        "id": city.get("id"),
        "city": city.get("city"),
        "city_en": city.get("city_en"),
        "lat": city.get("lat"),
        "lon": city.get("lon"),
        "temp": current.get("temperature"),
        "wind": current.get("windspeed"),
        "tmax": daily.get("temperature_2m_max", [None])[0],
        "tmin": daily.get("temperature_2m_min", [None])[0],
        "rain": daily.get("precipitation_probability_max", [None])[0],
    }


def main():

    files = glob.glob(os.path.join(CITIES_DIR, "*.json"))

    all_items = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                city_json = json.load(f)

            summary = build_summary(city_json)
            all_items.append(summary)

        except Exception as e:
            print("Error processing:", file_path, e)

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, separators=(",", ":"))

    print("Built:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
