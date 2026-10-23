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
        print("Weather API
