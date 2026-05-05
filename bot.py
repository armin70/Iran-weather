import requests
import time

TOKEN = "1229859473:TgRGJRh7ARWpQpXDP20jmBWmVMhSeiINVlQ"
API_URL = f"https://tapi.bale.ai/bot{TOKEN}"

weather_url = "https://raw.githubusercontent.com/armin70/Iran-weather/main/data/all.min.json"


def get_updates(offset=None):
    url = f"{API_URL}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    r = requests.get(url, params=params)
    return r.json()


def send_message(chat_id, text):
    url = f"{API_URL}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=data)


def get_weather(city):
    data = requests.get(weather_url).json()

    for c in data["cities"]:
        if c["city"] == city:
            return f"""
🌤 آب‌وهوا در {city}

دمای فعلی: {c["current_temperature"]}°C
رطوبت: {c["humidity"]}٪
سرعت باد: {c["wind_speed"]} km/h

حداکثر امروز: {c["today_temp_max"]}°C
حداقل امروز: {c["today_temp_min"]}°C
"""
    return "شهر پیدا نشد."


offset = None

while True:
    updates = get_updates(offset)

    if "result" in updates:
        for update in updates["result"]:
            offset = update["update_id"] + 1

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message.get("text")

            if text == "/start":
                send_message(chat_id, "نام شهر را بفرستید (مثلاً: تهران)")

            else:
                result = get_weather(text)
                send_message(chat_id, result)

    time.sleep(1)
