import json
import requests
import os
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CITIES_FILE = os.path.join(BASE_DIR, "data", "cities_meta.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "cities")

API_URL = "https://api.open-meteo.com/v1/forecast"

# استفاده از session برای سرعت و پایداری بهتر
session = requests.Session()


def load_cities():
    with open(CITIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # اگر فایل به صورت لیست بود
    if isinstance(data, list):
        return data

    # اگر ساختار {"cities": [...]} داشت
    if isinstance(data, dict) and "cities" in data:
        return data["cities"]

    raise ValueError("Invalid cities file format")


def fetch_weather(lat, lon, retries=3):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "temperature_2m,precipitation_probability,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        "forecast_days": 2,
        "timezone": "auto"
    }

    for attempt in range(1, retries + 1):
        try:
            r = session.get(API_URL, params=params, timeout=(10, 30))
            r.raise_for_status()
            return r.json()

        except Exception as e:
            print(f"  ⚠️ Attempt {attempt} failed:", e)
            if attempt < retries:
                time.sleep(attempt * 2)
            else:
                print("  ❌ Giving up for this city.")
                return None


def save_city_weather(city, weather):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output = {
        "city": city["name_fa"],
        "city_en": city["name_en"],
        "lat": city["lat"],
        "lon": city["lon"],
        "id": city["id"],
        "data": weather
    }

    path = os.path.join(OUTPUT_DIR, f"{city['id']}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def main():
    cities = load_cities()
    failed = []

    for city in cities:
        print("Fetching:", city["name_fa"])

        weather = fetch_weather(city["lat"], city["lon"])

        if weather is None:
            print("  ⚠️ Skipped due to error")
            failed.append(city["name_fa"])
            continue

        save_city_weather(city, weather)

        # جلوگیری از overload روی API
        time.sleep(0.3)

    print("Done.")
    print("Failed cities:", failed)


if __name__ == "__main__":
    main()