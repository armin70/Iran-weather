import json
import os
import glob
from datetime import datetime, timedelta

CITIES_DIR = "data/cities"
OUTPUT_FILE = "data/all.min.json"


def find_next_period_label(now_hour):
    if 5 <= now_hour < 12:
        return "تا ظهر"
    elif 12 <= now_hour < 17:
        return "تا عصر"
    elif 17 <= now_hour < 21:
        return "تا شب"
    else:
        return "تا صبح"


def filter_next_hours(hourly, start_time, end_time):
    result = []
    for entry in hourly:
        t = datetime.fromisoformat(entry["time"])
        if start_time <= t <= end_time:
            result.append(entry)
    return result


def build_next_period(city_data):
    hourly = city_data.get("hourly", {})
    
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rains = hourly.get("precipitation_probability", [])
    codes = hourly.get("weather_code", [])
    winds = hourly.get("wind_speed_10m", [])

    if not times:
        return None

    now_time = datetime.fromisoformat(city_data["current_weather"]["time"])
    now_hour = now_time.hour

    # برچسب بازه
    label = find_next_period_label(now_hour)

    # زمان پایان بازه
    if 5 <= now_hour < 12:
        end_hour = 12
    elif 12 <= now_hour < 17:
        end_hour = 17
    elif 17 <= now_hour < 21:
        end_hour = 21
    else:
        end_hour = 6
        if now_hour > 21:
            end_time = (now_time + timedelta(days=1)).replace(hour=6, minute=0)
        else:
            end_time = now_time.replace(hour=6, minute=0)
    # زمان شروع بازه
    start_time = now_time

    # اگر عصر/ظهر/صبح:
    if label != "تا صبح":
        end_time = now_time.replace(hour=end_hour, minute=0)

    # داده‌های hourly را ترکیب کنیم
    hourly_entries = []
    for i, t in enumerate(times):
        hourly_entries.append({
            "time": t,
            "temp": temps[i],
            "rain": rains[i],
            "code": codes[i],
            "wind": winds[i]
        })

    next_hours = filter_next_hours(hourly_entries, start_time, end_time)

    if not next_hours:
        return None

    avg_temp = sum(h["temp"] for h in next_hours) / len(next_hours)
    max_rain = max(h["rain"] for h in next_hours)
    common_code = max(
        set([h["code"] for h in next_hours]),
        key=[h["code"] for h in next_hours].count
    )

    return {
        "label": label,
        "temp": round(avg_temp, 1),
        "rain": max_rain,
        "code": common_code
    }


def build_summary(city):

    data = city.get("data", {})

    current = data.get("current_weather", {})
    daily = data.get("daily", {})
    today = 0
    tomorrow = 1

    next_period = build_next_period(data)

    return {
        "id": city.get("id"),
        "city": city.get("city"),
        "city_en": city.get("city_en"),
        "lat": city.get("lat"),
        "lon": city.get("lon"),

        "current": {
            "temp": current.get("temperature"),
            "wind": current.get("windspeed"),
            "code": current.get("weathercode"),
            "rain": data.get("hourly", {}).get("precipitation_probability", [0])[0]
        },

        "today": {
            "tmax": daily.get("temperature_2m_max", [None])[today],
            "tmin": daily.get("temperature_2m_min", [None])[today],
            "rain": daily.get("precipitation_probability_max", [None])[today],
            "code": daily.get("weather_code", [None])[today]
        },

        "next_period": next_period,

        "tomorrow": {
            "tmax": daily.get("temperature_2m_max", [None])[tomorrow],
            "tmin": daily.get("temperature_2m_min", [None])[tomorrow],
            "rain": daily.get("precipitation_probability_max", [None])[tomorrow],
            "code": daily.get("weather_code", [None])[tomorrow]
        }
    }


def main():

    files = glob.glob(os.path.join(CITIES_DIR, "*.json"))
    all_items = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                city_json = json.load(f)

            item = build_summary(city_json)
            all_items.append(item)

        except Exception as e:
            print("Error processing:", file_path, e)

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, separators=(",", ":"))

    print("Built:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
