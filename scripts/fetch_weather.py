import json
import requests
import os

CITIES_FILE = "data/cities_meta.json"
OUTPUT_DIR = "data/cities"

API_URL = "https://api.open-meteo.com/v1/forecast"

def load_cities():
    with open(CITIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["cities"]

def fetch_weather(lat, lon):

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto"
    }

    r = requests.get(API_URL, params=params)
    r.raise_for_status()

    return r.json()

def save_city_weather(city, weather):

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output = {
        "city": city["name_fa"],
        "city_en": city["name_en"],
        "lat": city["lat"],
        "lon": city["lon"],
        "data": weather
    }

    path = f"{OUTPUT_DIR}/{city['id']}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

def main():

    cities = load_cities()

    for city in cities:

        print("Fetching:", city["name_fa"])

        weather = fetch_weather(
            city["lat"],
            city["lon"]
        )

        save_city_weather(city, weather)

    print("Done.")

if __name__ == "__main__":
    main()
