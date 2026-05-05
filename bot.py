import requests
import time
import re

TOKEN = "1229859473:TgRGJRh7ARWpQpXDP20jmBWmVMhSeiINVlQ"

API_URL = f"https://tapi.bale.ai/bot{TOKEN}"

WEATHER_URL = "https://raw.githubusercontent.com/armin70/Iran-weather/main/data/all.min.json"

weather_cache = None
last_fetch = 0
CACHE_TTL = 30


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def normalize_text(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = re.sub(r"[؟?!,.]", "", text)
    return text


def extract_city_from_text(text):
    text = normalize_text(text)

    # حذف کلمات اضافی
    words_to_remove = ["هوای", "هوا", "weather", "آب‌وهوا", "اب و هوا"]
    for w in words_to_remove:
        text = text.replace(w, "")

    return text.strip()


# ---------------------------------------------------------------
# API
# ---------------------------------------------------------------

def get_updates(offset=None):
    url = f"{API_URL}/getUpdates"
    params = {"timeout": 30, "offset": offset}
    try:
        r = requests.get(url, params=params, timeout=35)
        return r.json()
    except:
        return {}


def send_message(chat_id, text, keyboard=None):
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    if keyboard:
        payload["reply_markup"] = keyboard

    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass


# ---------------------------------------------------------------
# Weather
# ---------------------------------------------------------------

def load_weather():
    global weather_cache, last_fetch

    now = time.time()

    if weather_cache and now - last_fetch < CACHE_TTL:
        return weather_cache

    try:
        r = requests.get(WEATHER_URL, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()

        if isinstance(data, list):
            weather_cache = data
            last_fetch = now
            return data
    except:
        return None

    return None


def find_city(query, data):
    q = normalize_text(query)

    for c in data:
        fa = normalize_text(c["city"])
        en = normalize_text(c["city_en"])

        if q == fa or q == en:
            return c

    return None


# ---------------------------------------------------------------
# BUILD CITY KEYBOARD (Dropdown-like)
# ---------------------------------------------------------------

def build_city_keyboard(cities):
    keyboard = []
    row = []

    for i, c in enumerate(cities):
        row.append(c["city"])
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "selective": True
    }


# ---------------------------------------------------------------
# Weather Formatting (PREMIUM VERSION)
# ---------------------------------------------------------------

def format_weather(c):
    # انتخاب آیکون بر اساس دما
    temp = c['temp']
    if temp <= 0:
        icon = "❄️"
    elif temp <= 10:
        icon = "🌥️"
    elif temp <= 20:
        icon = "⛅"
    elif temp <= 30:
        icon = "🌤️"
    else:
        icon = "🔥"

    return (
        f"{icon} وضعیت جوی شهر {c['city']}\n\n"
        f"🌡 دمای فعلی: {c['temp']}°C\n"
        f"🔺 بیشینه امروز: {c['tmax']}°C\n"
        f"🔻 کمینه امروز: {c['tmin']}°C\n"
        f"💨 سرعت باد: {c['wind']} km/h\n"
        f"🌧 احتمال بارش: {c['rain']}٪\n\n"
        f"🕒 آخرین به‌روزرسانی داده‌ها: لحظات اخیر\n"
        f"——————————————\n"
        f"برای بررسی شهر دیگر، فقط نام آن را بفرستید.\n"
        f"یا از لیست شهرها استفاده کنید."
    )


def get_weather(text):
    city_query = extract_city_from_text(text)

    if not city_query:
        return "نام شهر را وارد کنید."

    data = load_weather()

    if not data:
        return "❗ خطا در دریافت اطلاعات هواشناسی."

    city = find_city(city_query, data)

    if not city:
        return "❗ شهر پیدا نشد.\nمثال: تهران یا Shiraz"

    return format_weather(city)


# ---------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------

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

            if not text or text.strip() == "":
                continue

            text = text.strip()

            # /start
            if text == "/start":
                data = load_weather()

                if not data:
                    send_message(chat_id, "❗ خطا در بارگذاری لیست شهرها")
                    continue

                keyboard = build_city_keyboard(data)

                send_message(
                    chat_id,
                    "سلام 🌦\n"
                    "از لیست زیر یک شهر را انتخاب کنید یا نام آن را تایپ کنید:",
                    keyboard
                )
                continue

            # Normal message → search
            reply = get_weather(text)
            send_message(chat_id, reply)

    time.sleep(1)
