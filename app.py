from flask import Flask, render_template, request
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

app = Flask(__name__)
API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

def get_apod(date=None):
    url = "https://api.nasa.gov/planetary/apod"
    params = {"api_key": API_KEY}
    if date:
        params["date"] = date
    r = requests.get(url, params=params)
    return r.json() if r.status_code == 200 else None

def get_mars_photos(rover=None, date=None):
    rover = "curiosity"
    base_url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}"
    params = {"api_key": API_KEY}

    try:
        # 1. Try photos for selected date (if provided)
        if date:
            params["earth_date"] = date
            r = requests.get(f"{base_url}/photos", params=params)
            print(f"[DEBUG] Date photos status: {r.status_code}")
            if r.status_code == 200:
                photos = r.json().get("photos", [])
                if photos:
                    return photos
            else:
                print("[ERROR] Date request failed:", r.text)

        # 2. Fallback: Get latest photos
        latest_url = f"{base_url}/latest_photos"
        r_latest = requests.get(latest_url, params={"api_key": API_KEY})
        print(f"[DEBUG] Latest photos status: {r_latest.status_code}")

        if r_latest.status_code == 200:
            try:
                data = r_latest.json()
                return data.get("latest_photos", [])
            except ValueError:
                print("[ERROR] Could not parse latest photos JSON:", r_latest.text)
                return []
        else:
            print("[ERROR] Latest request failed:", r_latest.text)
            return []

    except requests.RequestException as e:
        print("[ERROR] Request failed:", e)
        return []



def get_neo_today():
    # Get today's NEO data (date format: YYYY-MM-DD)
    from datetime import datetime
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url = "https://api.nasa.gov/neo/rest/v1/feed"
    params = {"api_key": API_KEY, "start_date": today, "end_date": today}
    r = requests.get(url, params=params)
    return r.json() if r.status_code == 200 else {}

@app.route("/", methods=["GET", "POST"])
def index():
    # APOD date from form or None
    date = request.form.get("date") if request.method == "POST" else None

    apod = get_apod(date)
    mars_photos = get_mars_photos(date=date)
    neo = get_neo_today()

    error = None
    if not apod:
        error = "Could not fetch Astronomy Picture of the Day."
    # elif not mars_photos:
    #     error = "Could not fetch Mars Rover photos."
    elif not neo:
        error = "Could not fetch Near-Earth Objects data."

    return render_template("index.html", apod=apod, mars_photos=mars_photos, neo=neo, error=error)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))  # Use Render's port or default 3000
    app.run(host="0.0.0.0", port=port)

