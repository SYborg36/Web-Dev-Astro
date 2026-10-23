# 🚀 Space Bot API Investigation Sheet

**Total Marks: 40**  
**TASK 1: Collect Required API Documentation**

This investigation sheet helps you gather key technical information from the three APIs required for the Space Bot project: **Webex Messaging API**, **ISS Current Location API**, **Weather API** and a **Geocoding API** , plus the Python time module. Also furhter investigate the application of Web Architecture and MVC design pattern in development of the Bot

---

##  Webex Messaging API (4 marks)

| Criteria | Details |
|---------|---------|
| API Base URL | `https://webexapis.com/v1` |
| Authentication Method | **Bearer token** (OAuth 2.0 access token) sent in the `Authorization` HTTP header. For development I used the *Personal Access Token* from developer.webex.com, which expires 12 hours after signing in to the portal, so it is never hard-coded in the script (it is loaded from a `.env` file). |
| Endpoint to list rooms | `GET /rooms` → `https://webexapis.com/v1/rooms` (optional query params: `max`, `type`, `sortBy`) |
| Endpoint to get messages | `GET /messages?roomId={roomId}&max=1` → returns the newest message first in `items[0]` |
| Endpoint to send message | `POST /messages` with a JSON body containing `roomId` and `text` (or `markdown`) |
| Required headers | `Authorization: Bearer <access_token>` on every request; `Content-Type: application/json` on POST requests |
| Sample full GET or POST request | See the `curl` examples below ↓ |

**Sample GET request – latest message in a room**

```bash
curl -X GET "https://webexapis.com/v1/messages?roomId=<ROOM_ID>&max=1" \
     -H "Authorization: Bearer <YOUR_WEBEX_TOKEN>"
```

**Sample POST request – send a message to a room**

```bash
curl -X POST "https://webexapis.com/v1/messages" \
     -H "Authorization: Bearer <YOUR_WEBEX_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"roomId": "<ROOM_ID>", "text": "Hello from AstroBot 🚀"}'
```

**Sample JSON response – `GET /rooms`** (IDs shortened)

```json
{
  "items": [
    {
      "id": "Y2lzY29zcGFyazovL3VzL1JPT00v...",
      "title": "Astro Club Room",
      "type": "group",
      "isLocked": false,
      "lastActivity": "2026-10-22T21:15:03.120Z",
      "creatorId": "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8...",
      "created": "2026-10-22T20:58:41.512Z",
      "isPublic": false,
      "isReadOnly": false
    }
  ]
}
```

**Sample JSON response – `GET /messages?roomId=...&max=1`**

```json
{
  "items": [
    {
      "id": "Y2lzY29zcGFyazovL3VzL01FU1NBR0Uv...",
      "roomId": "Y2lzY29zcGFyazovL3VzL1JPT00v...",
      "roomType": "group",
      "text": "/weather London",
      "personId": "Y2lzY29zcGFyazovL3VzL1BFT1BMRS8...",
      "personEmail": "student@example.com",
      "created": "2026-10-22T21:15:03.120Z"
    }
  ]
}
```

---

##  ISS Current Location API (2 marks)

| Criteria | Details |
|---------|---------|
| API Base URL | `http://api.open-notify.org` (HTTP only – no authentication or API key required) |
| Endpoint for current ISS location | `GET /iss-now.json` → `http://api.open-notify.org/iss-now.json` |
| Sample response format (example JSON) | See below ↓ |

```json
{
  "message": "success",
  "timestamp": 1792704600,
  "iss_position": {
    "latitude": "-12.4931",
    "longitude": "98.2275"
  }
}
```

**Notes from the documentation / testing**

- `timestamp` is a **Unix epoch** (seconds since 1 Jan 1970 UTC) and must be converted to a readable date/time.
- `latitude` and `longitude` are returned as **strings**, so they are converted with `float()` before being passed to the reverse geocoding API.
- The documentation asks clients to poll **no more than about once every 5 seconds** – this matches the 5-second polling loop in the bot.
- The API is served over plain HTTP, so the response is not encrypted (acceptable here because it contains no sensitive data and no key is sent).

---

##  Geocoding API (4 marks)

| Criteria | Details |
|---------|---------|
| Provider used (Choose one) | **OpenWeatherMap Geocoding API** – chosen because it uses the same API key as the Weather API, so the bot only has to manage one key for both services. |
| API Base URL | `https://api.openweathermap.org/geo/1.0` |
| Endpoint for geocoding | `GET /direct?q={city name},{state code},{country code}&limit={n}&appid={API key}` (city name → lat/lon) |
| Endpoint for reverse geocoding | `GET /reverse?lat={lat}&lon={lon}&limit={n}&appid={API key}` (lat/lon → place name) |
| Authentication method | API key passed as the `appid` **query parameter** |
| Required query parameters | **Direct:** `q`, `appid` (`limit` optional, max 5). **Reverse:** `lat`, `lon`, `appid` (`limit` optional) |
| Sample request with latitude/longitude | `https://api.openweathermap.org/geo/1.0/reverse?lat=51.9022&lon=-0.2026&limit=1&appid=YOUR_API_KEY` |
| Sample JSON response (formatted example) | See below ↓ |

```json
[
  {
    "name": "Stevenage",
    "local_names": {
      "en": "Stevenage"
    },
    "lat": 51.9016663,
    "lon": -0.2027155,
    "country": "GB",
    "state": "England"
  }
]
```

**Notes:** the response is a JSON **array** (list), not an object, so the bot reads the first result with `data[0]`. When the coordinates are over the ocean the API returns an empty list `[]`, which the bot handles by showing *"Over Ocean / No Nearby City"*.

---


##  Weather API (3 marks)

| Criteria | Details |
|---------|---------|
| API Provider (Choose one) | **OpenWeatherMap – Current Weather Data API** (free tier) |
| API Base URL | `https://api.openweathermap.org/data/2.5` |
| Endpoint for current weather | `GET /weather?lat={lat}&lon={lon}&units=metric&appid={API key}` |
| Authentication method | API key passed as the `appid` **query parameter** |
| Required query parameters | `lat`, `lon`, `appid` (required); `units=metric` (optional – returns °C and m/s instead of Kelvin) |
| Sample JSON response (formatted example) | See below ↓ |

```json
{
  "coord": { "lon": -0.2027, "lat": 51.9017 },
  "weather": [
    { "id": 803, "main": "Clouds", "description": "broken clouds", "icon": "04n" }
  ],
  "base": "stations",
  "main": {
    "temp": 9.4,
    "feels_like": 7.9,
    "temp_min": 8.6,
    "temp_max": 10.1,
    "pressure": 1012,
    "humidity": 84
  },
  "visibility": 10000,
  "wind": { "speed": 3.6, "deg": 240 },
  "clouds": { "all": 75 },
  "dt": 1792704600,
  "sys": {
    "country": "GB",
    "sunrise": 1792650900,
    "sunset": 1792688100
  },
  "timezone": 3600,
  "id": 2636638,
  "name": "Stevenage",
  "cod": 200
}
```

**Fields used by AstroBot:** `name`, `sys.country`, `main.temp`, `weather[0].description`, `main.humidity`, `wind.speed`, plus `clouds.all` (cloud cover %) and `visibility` (metres) to judge whether the sky is clear enough for stargazing. `dt`, `sunrise` and `sunset` are epoch timestamps; `timezone` is the offset from UTC in seconds.

---

##  Epoch to Human Time Conversion (Python time module) (2 marks)

| Criteria | Details |
|---------|---------|
| Library used | `_______________________________` |
| Function used to convert epoch | `_______________________________` |
| Sample code to convert timestamp |  
```  
```
|
| Output (human-readable time) | `_______________________________` |

---

##  Extended Feature API ( 3 marks)

| Criteria | Details |
|---------|---------|
| API Provider | '_________' |
| API Base URL | `_______________________________` |
| Endpoint | `_______________________________` |
| Authentication method | `_______________________________` |
| Required query parameters | `_______________________________` |
| Sample JSON response (formatted example) |  
```

```
|

--- 

##  Evaluation – Web Architecture, MVC Design & Security 

In this section, evaluate how web technologies, architecture, and design patterns have been applied in your **AstroBot**. Your responses must relate directly to your implementation and include reflection on your design decisions.

---

###  Web Architecture – Client–Server Model (3 marks)

Explain how the client–server model applies to your AstroBot:

- Identify the **client** 
- Identify the **server(s)** 
- Describe how data flows between:
  - User, AstroBot and APIs

Include a **simple block diagram** to illustrate this interaction.

####  Security Considerations: (3 marks )
- Consider but not limiting to secure handling of API keys and tokens, API rate limiting, and Input validation (e.g., handling user commands safely), include examples from code where necessary to illustrate.

---

###  RESTful API Usage in Your Application (3 marks )

Explain how REST APIs are used in your AstroBot: 

- Describe how HTTP methods (GET, POST) are used  
- Explain how your bot interacts with APIs (Webex, Weather, ISS, Geocoding)  
- Describe how JSON responses are received and processed  

Note: Relate your explanation directly to your code for higher grade. 

#### Security Considerations: (2 marks)
- Check response status codes, Handling invalid or unexpected API responses, Avoiding excessive API calls

---

###  MVC Design Pattern in AstroBot (3 Marks)

Explain how the **Model–View–Controller (MVC)** pattern applies to your solution:
Provide a short example based on your implementation

| Component   | Description and Example (Relate to your Bot) |
|------------|----------------------------------|
| **Model**  |  |
| **View**   |  |
| **Controller** |  |

---

### 📝 Reflection and Evaluation ( 8 marks )

Reflect on your AstroBot (400 words):

- How effective is your bot in meeting the Astronomy Club’s needs?  
- What design decisions worked well?  
- What challenges did you face when integrating APIs?  
- What security risks did you identify and how were they handled?  
- How could your solution be improved in the future?  

---

 **Tip:** Link your answers directly to your code and examples for higher marks.
### Notes

- Use official documentation for accuracy (e.g. developer.webex.com, locationiq.com or Mapbox, open-notify.org or other ISS API).
- Be prepared to explain your findings to your instructor or demo how you retrieved them using tools like Postman, Curl, or Python scripts.

---

###  Total: /40
