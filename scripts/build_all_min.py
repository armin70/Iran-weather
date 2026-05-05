import json
import os
from glob import glob

INPUT_DIR = "data/cities"
OUTPUT_FILE = "data/all.min.json"


def load_city_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_summary(city_json):

    city = city_json.get("city", {})
    current = city_json.get("current", {})
    daily = city_json.get("daily", {})

    temps_max = daily.get("temp_max_c", [])
    temps_min = daily.get("temp_min_c", [])

    result = {
        "id": city.get("id"),
        "city": city.get("name_fa"),
        "city_en": city.get("name_en"),
        "lat": city.get("lat"),
        "lon": city.get("lon"),

        "current_temperature": current.get("temperature_c"),
        "humidity": current.get("humidity_percent"),
        "wind_speed": current.get("wind_speed_kmh"),

        "today_temp_max": temps_max[0] if len(temps_max) > 0 else None,
        "today_temp_min": temps_min[0] if len(temps_min) > 0 else None
    }

    return result


def main():
    files = sorted(glob(os.path.join(INPUT_DIR, "*.json")))
    all_items = []

    for path in files:
        city_json = load_city_file(path)
        all_items.append(build_summary(city_json))

    output = {
        "count": len(all_items),
        "cities": all_items
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Built {OUTPUT_FILE} with {len(all_items)} cities.")


if __name__ == "__main__":
    main()
