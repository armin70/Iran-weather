import requests
import time
import re
import json

# ----------------------------
# CONFIG
# ----------------------------
TOKEN = "1229859473:TgRGJRh7ARWpQpXDP20jmBWmVMhSeiINVlQ"
API_URL = f"https://tapi.bale.ai/bot{TOKEN}"

WEATHER_URL = "https://raw.githubusercontent.com/armin70/Iran-weather/main/data/all.min.json"
CITIES_FILE = "iran_cities.json"

CACHE_TTL = 120

# ----------------------------
# GLOBALS
# ----------------------------
weather_cache = None
last_fetch = 0
user_state = {}
provinces_data = {}

# ----------------------------
# LOAD PROVINCES
# ----------------------------
def load_provinces():
    global provinces_data
    try:
        with open(CITIES_FILE, "r", encoding="utf-8") as f:
            provinces_data = json.load(f)
    except Exception as e:
        print("Error loading provinces:", e)
        provinces_data = {}

# ----------------------------
# HELPERS
# ----------------------------
def normalize_text(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = re.sub(r"[؟?!,.]", "", text)
    return text


def extract_city(text):
    text = normalize_text(text)
    for w in ["هوای", "هوا", "آب‌وهوا", "اب و هوا"]:
        text = text.replace(w, "")
    return text.strip()

# ----------------------------
# API
# ----------------------------
def get_updates(offset=None):
    try:
        return requests.get(
            f"{API_URL}/getUpdates",
            params={"timeout": 30, "offset": offset},
            timeout=35
        ).json()
    except:
        return {}


def send_message(chat_id, text, keyboard=None):
    payload = {"chat_id": chat_id, "text": text}

    if keyboard:
        payload["reply_markup"] = keyboard

    try:
        requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
    except:
        pass

# ----------------------------
# WEATHER
# ----------------------------
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

        if q == fa or q == en or q in fa or q in en:
            return c
    return None

# ----------------------------
# WEATHER FORMAT
# ----------------------------
WEATHER_MAP = {
    0: "☀️ آسمان صاف",
    1: "🌤 کمی ابری",
    2: "⛅ نیمه‌ابری",
    3: "☁️ ابری",
    45: "🌫 مه",
    51: "🌦 نم‌نم باران",
    61: "🌧 بارانی",
    71: "🌨 برفی",
    95: "⛈ طوفانی",
}


def clothing_tip(temp):
    if temp < 10:
        return "🧥 لباس گرم بپوش"
    elif temp < 20:
        return "🧶 لباس نیمه‌گرم"
    elif temp < 30:
        return "👕 معمولی"
    else:
        return "☀️ لباس خنک"


def format_weather(city):
    cu = city["current"]
    to = city["today"]
    tm = city["tomorrow"]
    np = city.get("next_period")

    status = WEATHER_MAP.get(cu["code"], "❓")

    next_part = ""
    if np:
        next_part = (
            f"\n⏱ {np['label']}:\n"
            f"{np['temp']}°C | 🌧 {np['rain']}٪\n"
        )

    return (
        f"📍 {city['city']}\n\n"
        f"🌡 {cu['temp']}°C | 💨 {cu['wind']} km/h\n"
        f"🌧 {cu['rain']}٪ | {status}\n\n"
        f"📅 امروز: {to['tmin']}° / {to['tmax']}°\n"
        f"{next_part}\n"
        f"🌅 فردا: {tm['tmin']}° / {tm['tmax']}°\n\n"
        f"{clothing_tip(cu['temp'])}"
    )

# ----------------------------
# KEYBOARDS
# ----------------------------
def build_province_keyboard():
    keyboard, row = [], []

    for p in sorted(provinces_data.keys()):
        row.append(p)
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return {"keyboard": keyboard, "resize_keyboard": True}


def build_city_keyboard(province):
    keyboard, row = [], []

    cities = provinces_data.get(province, [])

    for c in cities:
        row.append(c["name"])
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append(["⬅️ بازگشت"])

    return {"keyboard": keyboard, "resize_keyboard": True}

# ----------------------------
# MAIN
# ----------------------------
load_provinces()

offset = None

while True:
    updates = get_updates(offset)

    if "result" in updates:
        for update in updates["result"]:
            offset = update["update_id"] + 1

            msg = update.get("message")
            if not msg:
                continue

            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()

            if not text:
                continue

            state = user_state.get(chat_id, {})

            # START
            if text == "/start":
                user_state[chat_id] = {"step": "province"}

                send_message(
                    chat_id,
                    "استان رو انتخاب کن:",
                    build_province_keyboard()
                )
                continue

            # BACK
            if text == "⬅️ بازگشت":
                user_state[chat_id] = {"step": "province"}

                send_message(chat_id, "استان رو انتخاب کن:", build_province_keyboard())
                continue

            data = load_weather()
            if not data:
                send_message(chat_id, "❗ خطا در دریافت داده‌ها")
                continue

            # STEP 1: PROVINCE
            if state.get("step") == "province":
                if text in provinces_data:
                    user_state[chat_id] = {
                        "step": "city",
                        "province": text
                    }

                    send_message(
                        chat_id,
                        f"شهرهای {text}:",
                        build_city_keyboard(text)
                    )
                else:
                    city = find_city(text, data)
                    if city:
                        send_message(chat_id, format_weather(city))
                    else:
                        send_message(chat_id, "❗ نامعتبر")
                continue

            # STEP 2: CITY
            if state.get("step") == "city":
                province = state.get("province")
                cities = [c["name"] for c in provinces_data.get(province, [])]

                if text in cities:
                    city = find_city(text, data)
                    if city:
                        send_message(chat_id, format_weather(city))
                    else:
                        send_message(chat_id, "❗ داده هوا نیست")
                else:
                    send_message(chat_id, "❗ از لیست انتخاب کن")

                continue

    time.sleep(2)