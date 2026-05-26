# GENER8R — Voice AI Assistant

A voice-controlled AI assistant with a web dashboard, built with Python and Flask. Speak a command, get a response — either spoken back or executed on your system.

---

## What it does

- Answers questions using **LLaMA 3.3-70B** via the Groq API
- Speaks responses out loud using text-to-speech
- Fetches live **weather** (WeatherAPI) and **news headlines** (NewsData.io)
- Opens websites, apps, and system tools by voice
- Takes screenshots on command
- Reads battery status
- Maintains conversation context across a session

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| AI Model | LLaMA 3.3-70B via Groq API |
| Speech Input | SpeechRecognition + Google Speech API |
| Text-to-Speech | pyttsx3 |
| Weather | WeatherAPI.com |
| News | NewsData.io |
| Frontend | HTML, CSS, Vanilla JS |

---

## Project Structure

```
GENER8R/
├── app.py              # Flask backend, voice logic, all routes
├── config.py           # API keys (gitignored)
├── requirements.txt    # Python dependencies
└── templates/
    └── index.html      # Web dashboard frontend
```

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/Shubhamawasthiii/GENER8R.git
cd GENER8R
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your API keys**

Create a `config.py` file in the root folder:
```python
GROQ_API_KEY    = "your_groq_api_key"
WEATHER_API_KEY = "your_weatherapi_key"
NEWS_API_KEY    = "your_newsdata_key"
```

| Key | Where to get it | Free tier |
|---|---|---|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Yes |
| `WEATHER_API_KEY` | [weatherapi.com](https://www.weatherapi.com) | Yes — 1M calls/month |
| `NEWS_API_KEY` | [newsdata.io](https://newsdata.io) | Yes — 200 calls/day |

**4. Run it**
```bash
python app.py
```

Open `http://localhost:5000` in your browser.

---

## Voice Commands

| Command | What happens |
|---|---|
| "What's the time" | Tells current time |
| "Today's date" | Tells current date |
| "Weather in [city]" | Live weather for that city |
| "News headlines" | Top 3 Indian news headlines |
| "Battery status" | Battery % and charging state |
| "Take a screenshot" | Saves screenshot to project folder |
| "Open YouTube / GitHub / Google" | Opens in browser |
| "Open VS Code / Notepad / Calculator" | Opens the app |
| "Reset chat" | Clears conversation history |
| "GENER8R quit" | Shuts down the assistant |
| Anything else | Answered by LLaMA 3.3-70B |

---

## Known Limitations

- Speech recognition requires an internet connection (uses Google Speech API)
- Response speed depends on Groq API latency (~1-2 seconds)
- TTS voice quality depends on voices installed on your system
- Screenshot and app commands are Windows-only

---

## Built by

**Shubham Awasthi** — B.Tech CSE, VIT Bhopal  
[GitHub](https://github.com/Shubhamawasthiii)
