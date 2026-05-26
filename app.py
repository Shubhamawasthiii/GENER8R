# main backend - flask handles the web server, everything else handles the AI and voice

from flask import Flask, render_template, jsonify
from groq import Groq
from config import GROQ_API_KEY, WEATHER_API_KEY, NEWS_API_KEY
import speech_recognition as sr
import pyttsx3
import datetime
import requests
import psutil
import pyautogui
import webbrowser
import os
import threading
import queue

app = Flask(__name__)

# storing chat history and app state in memory
chatMessages = []
status = {"state": "idle"}

# TTS runs in its own thread so it doesnt freeze the rest of the app
tts_queue = queue.Queue()

def tts_worker():
    # initializing the voice engine inside the thread that will use it
    # doing it outside caused crashes on some systems
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
    engine.setProperty('rate', 170)
    engine.setProperty('volume', 1.0)

    while True:
        text = tts_queue.get()
        if text is None:
            break
        status["state"] = "speaking"
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"tts error: {e}")
        status["state"] = "idle"
        tts_queue.task_done()

# start speech worker immediately when app launches
threading.Thread(target=tts_worker, daemon=True).start()

def say(text):
    # non-blocking - just drops text into the queue
    print(f"GENER8R: {text}")
    tts_queue.put(text)

# groq client using key from config.py
client = Groq(api_key=GROQ_API_KEY)

def set_status(state):
    status["state"] = state


# routes

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def get_status():
    # frontend polls this to keep the status indicator updated
    return jsonify(status)

@app.route("/history")
def get_history():
    return jsonify(chatMessages)

@app.route("/clear", methods=["POST"])
def clear_history():
    chatMessages.clear()
    return jsonify({"ok": True})


@app.route("/listen", methods=["POST"])
def listen():
    # runs in background so browser doesnt hang waiting
    def do_listen():
        set_status("listening")
        r = sr.Recognizer()

        # tuned these values to reduce lag and false triggers
        r.energy_threshold = 400
        r.dynamic_energy_threshold = True
        r.pause_threshold = 0.8
        r.phrase_threshold = 0.3

        try:
            with sr.Microphone() as source:
                print("mic open, listening...")
                r.adjust_for_ambient_noise(source, duration=0.3)
                audio = r.listen(source, timeout=6, phrase_time_limit=8)

            print("sending to google speech...")
            set_status("thinking")
            query = r.recognize_google(audio, language="en-in")
            print(f"heard: {query}")
            process_query(query)

        except sr.WaitTimeoutError:
            print("timeout - nothing heard")
            set_status("idle")
            chatMessages.append({"role": "system", "content": "No speech detected. Try again."})

        except sr.UnknownValueError:
            print("couldnt understand audio")
            set_status("idle")
            chatMessages.append({"role": "system", "content": "Could not understand. Please speak clearly."})

        except sr.RequestError as e:
            print(f"speech api error: {e}")
            set_status("idle")
            chatMessages.append({"role": "system", "content": "Speech service unavailable. Check internet."})

        except Exception as e:
            print(f"unexpected error: {e}")
            set_status("idle")
            chatMessages.append({"role": "system", "content": f"Error: {str(e)}"})

    threading.Thread(target=do_listen, daemon=True).start()
    return jsonify({"ok": True})


def process_query(query):
    query_lower = query.lower().strip()
    chatMessages.append({"role": "user", "content": query})

    # sites i want to open by voice
    SITES = [
        ["youtube",   "https://www.youtube.com"],
        ["github",    "https://www.github.com"],
        ["google",    "https://www.google.com"],
        ["wikipedia", "https://www.wikipedia.org"],
        ["linkedin",  "https://www.linkedin.com"],
        ["instagram", "https://www.instagram.com"],
    ]

    for site in SITES:
        if f"open {site[0]}" in query_lower:
            reply = f"Opening {site[0]}."
            chatMessages.append({"role": "assistant", "content": reply})
            webbrowser.open(site[1])
            say(reply)
            set_status("idle")
            return

    # routing commands to the right function
    if "weather in" in query_lower:
        city = query_lower.split("weather in")[-1].strip()
        reply = get_weather(city)

    elif "weather" in query_lower and "in" in query_lower:
        city = query_lower.split("in")[-1].strip()
        reply = get_weather(city)

    elif "news" in query_lower:
        reply = get_news()

    elif "battery" in query_lower:
        reply = get_battery()

    elif "screenshot" in query_lower:
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        try:
            pyautogui.screenshot().save(filename)
            reply = f"Screenshot saved as {filename}."
        except Exception as e:
            reply = f"Screenshot failed: {str(e)}"

    elif "time" in query_lower:
        now = datetime.datetime.now().strftime("%I:%M %p")
        reply = f"The time is {now}."

    elif "date" in query_lower:
        today = datetime.datetime.now().strftime("%B %d, %Y")
        reply = f"Today is {today}."

    elif "calculator" in query_lower:
        os.system("calc.exe")
        reply = "Opening Calculator."

    elif "notepad" in query_lower:
        os.system("notepad.exe")
        reply = "Opening Notepad."

    elif "open vs code" in query_lower or "open code" in query_lower:
        os.system("code")
        reply = "Opening VS Code."

    elif "open camera" in query_lower:
        os.system("start microsoft.windows.camera:")
        reply = "Opening Camera."

    elif "reset chat" in query_lower or "clear chat" in query_lower:
        chatMessages.clear()
        reply = "Chat history cleared."

    elif "gener8r quit" in query_lower or "quit" in query_lower or "goodbye" in query_lower:
        reply = "Goodbye Shubham. Shutting down."
        chatMessages.append({"role": "assistant", "content": reply})
        say(reply)
        import time
        time.sleep(2)
        os._exit(0)

    else:
        reply = ai_chat(query)

    if reply:
        chatMessages.append({"role": "assistant", "content": reply})
        say(reply)
    set_status("idle")


def ai_chat(query):
    try:
        set_status("thinking")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are GENER8R, a voice assistant built by Shubham Awasthi, a CS student at VIT Bhopal. "
                    "Keep all replies under 3 sentences since they will be spoken out loud. "
                    "Be direct, helpful, and conversational. No markdown, no bullet points."
                )
            }
        ]

        # include last 10 messages for context
        recent = [m for m in chatMessages[:-1] if m["role"] in ("user", "assistant")]
        messages += recent[-10:]
        messages.append({"role": "user", "content": query})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"groq error: {e}")
        return "Sorry, I couldn't reach the AI right now."


def get_weather(city):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no"
        res = requests.get(url, timeout=5).json()
        if "error" not in res:
            temp     = res["current"]["temp_c"]
            feels    = res["current"]["feelslike_c"]
            desc     = res["current"]["condition"]["text"]
            humidity = res["current"]["humidity"]
            return f"It's {temp}°C in {city}, feels like {feels}°C with {desc}. Humidity is {humidity}%."
        return "Couldn't find that city."
    except requests.Timeout:
        return "Weather request timed out."
    except Exception as e:
        return f"Weather check failed: {str(e)}"


def get_news():
    # using newsdata.io for indian headlines
    try:
        url = f"https://newsdata.io/api/1/latest?apikey={NEWS_API_KEY}&country=in&language=en"
        res = requests.get(url, timeout=5).json()
        articles = res.get("results", [])[:3]
        if not articles:
            return "No headlines available right now."
        headlines = [f"{i+1}. {a['title']}" for i, a in enumerate(articles)]
        return "Here are the top headlines. " + " | ".join(headlines)
    except requests.Timeout:
        return "News request timed out."
    except Exception as e:
        return f"News fetch failed: {str(e)}"


def get_battery():
    battery = psutil.sensors_battery()
    if battery:
        pct     = int(battery.percent)
        plugged = "plugged in" if battery.power_plugged else "not plugged in"
        warning = " Consider charging soon." if pct < 20 and not battery.power_plugged else ""
        return f"Battery is at {pct}%, {plugged}.{warning}"
    return "Couldn't read battery info on this device."


if __name__ == "__main__":
    print("=" * 40)
    print("  GENER8R — running at localhost:5000")
    print("=" * 40)
    app.run(debug=False, port=5000, threaded=True)