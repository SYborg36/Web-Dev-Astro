#Contains partially completed code with sections for you to complete
#IT IS MANDATORY TO USE THE RESOURCE PROVIDED
#The starter code is structured into functions and modules. You are required to complete the missing sections while maintaining this modular design.  Further step by step instructions can be found in the appendix A of this assignment brief.
#For extended features implement it within the existing modular structure. The new feature must be triggered using a new command (e.g., /stars, /moon, /sky) and follow the same approach
#Use Git for version control. Maintain a repository on GitHub to track your project's progress and changes. Ensure regular commits for each step with meaningful messages that document your step by stepdevelopment process.

# =========================
# REQUIRED LIBRARIES
# =========================

import requests                 # sends HTTP GET/POST requests to the APIs
import json                     # converts Python dictionaries into JSON text
import time                     # 5-second polling delay + epoch time conversion
from datetime import datetime   # timestamps for the console log
import os                       # reads environment variables (API keys)
from getpass import getpass     # hides the token/key while it is typed in

# python-dotenv loads WEBEX_TOKEN and OPENWEATHER_API_KEY from a local .env file,
# so no secret is ever written in this code or pushed to GitHub.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv is not installed - you will be asked to type your keys in.")

REQUEST_TIMEOUT = 10  # seconds to wait for any API before giving up

# =========================
# CONFIGURATION FUNCTIONS
# =========================
def get_webex_token():
    choice = input("Use hard-coded Webex token? (y/n): ").lower()
    if choice == "n":
        token = getpass("Enter your Webex Access Token: ").strip()
        return f"Bearer {token}"
    else:
        # The "hard-coded" token is read from the .env file instead of the code
        token = os.getenv("WEBEX_TOKEN", "")
        if not token:
            print("WEBEX_TOKEN was not found in the .env file.")
            token = getpass("Enter your Webex Access Token: ").strip()
        return f"Bearer {token}"

def get_api_key(prompt, hardcoded_key):
    # Ask whether to use the stored key (from .env) or type a different one
    choice = input(f"Use hard-coded {prompt}? (y/n): ").lower()
    if choice == "n" or not hardcoded_key:
        if not hardcoded_key:
            print(f"{prompt} was not found in the .env file.")
        return getpass(f"Enter your {prompt}: ").strip()
    return hardcoded_key

# =========================
# WEBEX FUNCTIONS
# =========================
WEBEX_BASE_URL = "https://webexapis.com/v1"

def get_rooms(token):
    url = f"{WEBEX_BASE_URL}/rooms"
    headers = {"Authorization": token}  # token already includes "Bearer "
    try:
        response = requests.get(url, headers=headers, params={"max": 100}, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as error:
        print("Network error while fetching rooms:", error)
        return []

    if response.status_code != 200:
        print("Error fetching rooms:", response.status_code)
        if response.status_code == 401:
            print("Your Webex token is invalid or expired (personal tokens last 12 hours).")
        return []

    return response.json().get("items", [])


def print_rooms(rooms):
    print("\nAvailable Webex rooms:")
    for room in rooms:
        print(f"  - {room.get('title', 'Untitled')}  (type: {room.get('type', 'N/A')})")


def select_room(rooms):
    while True:
        name = input("\nEnter the name of the room to monitor: ").strip()
        if not name:
            continue  # an empty name would match every room, so ask again
        for room in rooms:
            if name.lower() in room["title"].lower():
                print(f"Monitoring room: {room['title']}")
                return room["id"]
        print("Room not found. Please check the name and try again.")


def get_latest_message(token, room_id):
    url = f"{WEBEX_BASE_URL}/messages"
    params = {"roomId": room_id, "max": 1}  # only the newest message is needed
    headers = {"Authorization": token}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        return None, None

    # 429 = Too Many Requests: Webex says how long to wait in the Retry-After header
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "60")
        wait = int(retry_after) if retry_after.isdigit() else 60
        print(f"Rate limited by Webex - waiting {wait} seconds.")
        time.sleep(wait)
        return None, None

    if response.status_code != 200:
        return None, None

    data = response.json().get("items", [])

    if not data:
        return None, None

    latest = data[0]
    return latest.get("id"), latest.get("text", "")


def send_message(token, room_id, message):
    url = f"{WEBEX_BASE_URL}/messages"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    data = {
        "roomId": room_id,
        "text": message
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as error:
        print("Network error while sending message:", error)
        return

    if not response.ok:  # .ok is True for any 2xx success code
        print("Error sending message:", response.status_code)

# =========================
# WEATHER FUNCTIONS
# =========================
GEO_BASE_URL = "https://api.openweathermap.org/geo/1.0"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

def value_or_na(value, unit=""):
    # Shows "N/A" instead of crashing or printing "None" when data is missing
    return "N/A" if value is None else f"{value}{unit}"


def format_epoch(epoch, utc_offset=0):
    # Converts a Unix epoch (seconds since 1 Jan 1970 UTC) into readable text.
    # utc_offset (seconds) shifts the time to the local time of a city.
    if epoch is None:
        return "Unknown"
    return time.strftime("%a %d %b %Y, %H:%M", time.gmtime(epoch + utc_offset))


def get_city_coordinates(city, api_key):
    url = f"{GEO_BASE_URL}/direct"
    params = {"q": city, "limit": 1, "appid": api_key}
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        return None

    if response.status_code != 200:
        print("Geocoding API error:", response.status_code)
        return None

    try:
        data = response.json()
    except ValueError:
        return None
    # The API returns a list; an empty list means no match was found
    return data[0] if isinstance(data, list) and data else None


def get_weather_data(lat, lon, api_key):
    # Fetches raw weather JSON for any coordinates (used by /weather and /iss)
    params = {"lat": lat, "lon": lon, "units": "metric", "appid": api_key}
    try:
        response = requests.get(WEATHER_URL, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        return None

    if response.status_code != 200:
        print("Weather API error:", response.status_code)
        return None

    try:
        return response.json()
    except ValueError:
        return None


def stargazing_verdict(weather):
    # Judges sky conditions using cloud cover %, visibility and rain/snow
    clouds = weather.get("clouds", {}).get("all")
    visibility = weather.get("visibility")
    condition = (weather.get("weather") or [{}])[0].get("main", "")

    if condition in ("Rain", "Drizzle", "Thunderstorm", "Snow"):
        return f"Poor ❌ ({condition.lower()})"
    if clouds is None:
        return "Unknown (no cloud data)"
    if clouds <= 20 and (visibility is None or visibility >= 8000):
        return "Good ✅ (mostly clear skies)"
    if clouds <= 60:
        return "Fair ⚠️ (some cloud cover)"
    return "Poor ❌ (heavy cloud cover)"


def get_weather(city, api_key):
    location = get_city_coordinates(city, api_key)

    if not location:
        return f"Sorry, I couldn't find a city called '{city}'. Check the spelling and try again."

    weather = get_weather_data(location["lat"], location["lon"], api_key)

    if not weather:
        return "Sorry, the weather data could not be retrieved right now. Please try again later."

    main = weather.get("main", {})
    wind = weather.get("wind", {})
    sys_info = weather.get("sys", {})
    description = (weather.get("weather") or [{}])[0].get("description", "Unknown")
    offset = weather.get("timezone", 0)

    return (
        f"🌤️ Weather for {weather.get('name') or location.get('name', city)}, {sys_info.get('country', 'N/A')}\n"
        f"🕒 Local time: {format_epoch(weather.get('dt'), offset)}\n"
        f"🌡️ Temperature: {value_or_na(main.get('temp'), '°C')} (feels like {value_or_na(main.get('feels_like'), '°C')})\n"
        f"☁️ Conditions: {description.capitalize()}, cloud cover {value_or_na(weather.get('clouds', {}).get('all'), '%')}\n"
        f"💧 Humidity: {value_or_na(main.get('humidity'), '%')}\n"
        f"💨 Wind: {value_or_na(wind.get('speed'), ' m/s')}\n"
        f"🌇 Sunset: {format_epoch(sys_info.get('sunset'), offset)}\n"
        f"🔭 Stargazing: {stargazing_verdict(weather)}"
    )

# =========================
# ISS FUNCTIONS
# =========================
ISS_URL = "http://api.open-notify.org/iss-now.json"

def format_coords(lat, lon):
    # Turns -12.49, 98.22 into "12.4900° S, 98.2200° E"
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    return f"{abs(lat):.4f}° {lat_dir}, {abs(lon):.4f}° {lon_dir}"


def reverse_geocode(lat, lon, api_key):
    url = f"{GEO_BASE_URL}/reverse"
    params = {"lat": lat, "lon": lon, "limit": 1, "appid": api_key}

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        return None

    if response.status_code != 200:
        return None

    try:
        data = response.json()
    except ValueError:
        return None
    # The API returns a list; an empty list means no match was found
    return data[0] if isinstance(data, list) and data else None


def get_iss_location(api_key):
    url = ISS_URL

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        return "Sorry, the ISS location service could not be reached. Please try again later."

    if response.status_code != 200:
        return "Sorry, the ISS location could not be retrieved right now."

    # The API returns latitude/longitude as strings, so convert them to numbers
    try:
        data = response.json()
        lat = float(data["iss_position"]["latitude"])
        lon = float(data["iss_position"]["longitude"])
    except (ValueError, KeyError, TypeError):
        return "Sorry, the ISS API returned unexpected data."

    location = reverse_geocode(lat, lon, api_key)

    place = "Over Ocean / No Nearby City"

    if location:
        parts = [location.get("name"), location.get("state"), location.get("country")]
        place = ", ".join(part for part in parts if part)

    # Weather conditions directly below the ISS
    weather = get_weather_data(lat, lon, api_key)
    if weather:
        description = (weather.get("weather") or [{}])[0].get("description", "Unknown")
        temp = value_or_na(weather.get("main", {}).get("temp"), "°C")
        clouds = value_or_na(weather.get("clouds", {}).get("all"), "%")
        weather_line = f"{description.capitalize()}, {temp}, cloud cover {clouds}"
    else:
        weather_line = "N/A"

    return (
        f"🛰️ ISS Current Location\n"
        f"🕒 Time: {format_epoch(data.get('timestamp'))} UTC\n"
        f"📍 Coordinates: {format_coords(lat, lon)}\n"
        f"🌍 Over: {place}\n"
        f"🌤️ Weather below: {weather_line}"
    )

# =========================
# MAIN BOT LOGIC
# =========================
def main():

    token = get_webex_token()

    weather_key = get_api_key(
        "Weather API key",
        "YOUR_OPENWEATHER_API_KEY"
    )

    rooms = get_rooms(token)

    if not rooms:
        print(#complete the print statement )
        return

    print_rooms(rooms)
    room_id = select_room(rooms)

    last_message_id, _ = get_latest_message(token, room_id)

    while True:

        message_id, message_text = get_latest_message(token, room_id)

        if message_id and message_id != last_message_id:

            last_message_id = message_id

            print(#complete the print statement to display the received message text)

            if not message_text.startswith(#complete):
                continue

            if message_text.lower() == "/help":
                send_message(
                    token,
                    room_id,
                    "/weather <city>\n/iss\n/help\n/quit"
                )

            elif message_text.lower().startswith(#complete):

                parts = message_text.split(maxsplit=1)

                if len(parts) < 2:
                    send_message(token, room_id, "Usage: /weather <city>")
                else:
                    city = parts[1]
                    send_message(token, room_id, get_weather(city, weather_key))

            elif message_text.lower() == "#complete":
                send_message(token, room_id, get_iss_location(weather_key))

            elif message_text.lower() == "#complete":
                send_message(token, room_id, "AstroBot shutting down.")
                break

            else:
                send_message(token, room_id, "Unknown command. Use /help")

        time.sleep(5)


if __name__ == '__main__':
    main()
