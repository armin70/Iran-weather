import json
import os

INPUT_FILE = "data/iran_cities.json"
OUTPUT_FILE = "data/cities_meta.json"


def slugify_en(name):
    # موقت: اگر name_en نداشتی
    return name


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    cities = []

    for province, city_list in data.items():
        for c in city_list:
            city = {
                "id": c.get("geonameid"),
                "name_fa": c.get("name"),
                "name_en": c.get("name_en") or slugify_en(c.get("name")),
                "lat": c.get("lat"),
                "lon": c.get("lon"),
            }

            # حذف null ها
            city = {k: v for k, v in city.items() if v is not None}

            cities.append(city)

    output = {"cities": cities}

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("✅ cities_meta.json ساخته شد")


if __name__ == "__main__":
    main()