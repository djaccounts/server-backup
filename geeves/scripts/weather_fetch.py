#!/usr/bin/env python3
"""
weather_fetch.py — Fetch London weather from Open-Meteo and log to Airtable.

Open-Meteo is free, no API key required.
https://open-meteo.com/en/docs

Usage:
    python3 weather_fetch.py              # fetch and print
    python3 weather_fetch.py --write      # fetch and write to Airtable
"""

import subprocess, sys, json, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

ENV_PATH = "/root/.hermes/.env"
BASE = "appzvmonQXs4x2AlL"
TABLE = "Weather_Data"

# London coordinates
LAT = 51.5074
LON = -0.1278

def get_key():
    r = subprocess.run(["grep", "AIRTABLE_API_KEY", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def api(method, path, data=None):
    key = get_key()
    url = f"https://api.airtable.com/v0/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

# WMO Weather interpretation codes
CONDITIONS = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}

# Codes that involve rain
RAIN_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}

def fetch_weather():
    """Fetch current weather + daily forecast + hourly rain data from Open-Meteo."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LAT}&longitude={LON}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
        f"&daily=temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum"
        f"&hourly=weather_code,precipitation_probability,precipitation,temperature_2m"
        f"&timezone=Europe%2FLondon"
        f"&forecast_days=1"
    )
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    current = data["current"]
    daily = data["daily"]
    hourly = data["hourly"]

    temp = current["temperature_2m"]
    feels = current["apparent_temperature"]
    humidity = current["relative_humidity_2m"]
    wind = current["wind_speed_10m"]
    code = current["weather_code"]

    # Daily highs and lows
    temp_max = daily["temperature_2m_max"][0]
    temp_min = daily["temperature_2m_min"][0]
    daily_code = daily["weather_code"][0]
    precip_sum = daily["precipitation_sum"][0]

    condition = CONDITIONS.get(code, f"Unknown ({code})")
    daily_condition = CONDITIONS.get(daily_code, f"Unknown ({daily_code})")

    # Determine rain times from hourly data
    rain_periods = []
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")

    for i, ts in enumerate(hourly["time"]):
        # Parse the hourly timestamp (ISO format, may or may not have tz info)
        try:
            hour_dt = datetime.fromisoformat(ts)
        except Exception:
            continue
        if hour_dt.tzinfo is None:
            hour_dt = hour_dt.replace(tzinfo=timezone.utc)
        
        # Only look at future hours today
        if hour_dt < now:
            continue
        # Stop if we've moved past today (London time)
        london_offset = timedelta(hours=1)  # BST in summer
        london_date = (hour_dt + london_offset).strftime("%Y-%m-%d")
        if london_date != (now + london_offset).strftime("%Y-%m-%d"):
            break

        h_code = hourly["weather_code"][i]
        h_precip = hourly["precipitation"][i]
        h_prob = hourly["precipitation_probability"][i]

        if h_code in RAIN_CODES or h_precip > 0 or h_prob >= 50:
            rain_periods.append({
                "time": ts,
                "hour": hour_dt.hour,
                "code": h_code,
                "precip_mm": h_precip,
                "prob": h_prob,
            })

    # Build rain description
    rain_desc = ""
    if rain_periods:
        # Group consecutive hours into periods
        groups = []
        current_group = [rain_periods[0]]
        for rp in rain_periods[1:]:
            if rp["hour"] == current_group[-1]["hour"] + 1:
                current_group.append(rp)
            else:
                groups.append(current_group)
                current_group = [rp]
        groups.append(current_group)

        period_strs = []
        for g in groups:
            start = g[0]["hour"]
            end = g[-1]["hour"] + 1
            max_prob = max(rp["prob"] for rp in g)
            if start == end - 1:
                period_strs.append(f"{start:02d}:00 ({max_prob}% chance)")
            else:
                period_strs.append(f"{start:02d}:00–{end:02d}:00 ({max_prob}% chance)")

        rain_desc = "Rain expected: " + ", ".join(period_strs)
    else:
        rain_desc = "No rain expected today."

    today = now.strftime("%Y-%m-%d")

    # === MORNING / AFTERNOON / EVENING SPLITS ===
    morning_temps = []
    afternoon_temps = []
    evening_temps = []

    london_offset = timedelta(hours=1)  # BST; Open-Meteo returns Europe/London times

    for i, ts in enumerate(hourly["time"]):
        hour_dt = datetime.fromisoformat(ts)
        if hour_dt.tzinfo is None:
            hour_dt = hour_dt.replace(tzinfo=timezone.utc)

        london_hour = (hour_dt + london_offset).hour
        temp = hourly["temperature_2m"][i]
        code = hourly["weather_code"][i]
        prob = hourly["precipitation_probability"][i]

        if 6 <= london_hour < 12:
            morning_temps.append((temp, code, prob))
        elif 12 <= london_hour < 18:
            afternoon_temps.append((temp, code, prob))
        elif 18 <= london_hour < 22:
            evening_temps.append((temp, code, prob))

    def period_summary(temps):
        if not temps:
            return {"avg_temp": None, "max_rain_prob": 0, "code": None}
        return {
            "avg_temp": round(sum(t[0] for t in temps) / len(temps), 1),
            "max_rain_prob": max(t[2] for t in temps),
            "code": max(set(t[1] for t in temps), key=lambda c: sum(1 for t in temps if t[1] == c)),
        }

    morning = period_summary(morning_temps)
    afternoon = period_summary(afternoon_temps)
    evening = period_summary(evening_temps)

    morning_condition = CONDITIONS.get(morning["code"], "") if morning["code"] is not None else ""
    afternoon_condition = CONDITIONS.get(afternoon["code"], "") if afternoon["code"] is not None else ""
    evening_condition = CONDITIONS.get(evening["code"], "") if evening["code"] is not None else ""

    description = (
        f"{condition}. Now {temp}°C (feels {feels}°C). "
        f"High {temp_max}°C / Low {temp_min}°C. "
        f"Humidity {humidity}%, wind {wind} km/h. "
        f"{rain_desc}"
    )

    return {
        "Date": today,
        "Location": "London",
        "Temperature C": temp,
        "Feels Like C": feels,
        "High C": temp_max,
        "Low C": temp_min,
        "Humidity Pct": humidity,
        "Wind Speed KPH": wind,
        "Condition": condition,
        "Daily Condition": daily_condition,
        "Rain Expected": "Yes" if rain_periods else "No",
        "Rain Times": rain_desc,
        "Precipitation MM": precip_sum,
        "Morning Temp C": morning["avg_temp"],
        "Morning Condition": morning_condition,
        "Morning Rain Prob": morning["max_rain_prob"],
        "Afternoon Temp C": afternoon["avg_temp"],
        "Afternoon Condition": afternoon_condition,
        "Afternoon Rain Prob": afternoon["max_rain_prob"],
        "Evening Temp C": evening["avg_temp"],
        "Evening Condition": evening_condition,
        "Evening Rain Prob": evening["max_rain_prob"],
        "Description": description,
    }

def write_to_airtable(record):
    """Write a weather record to Airtable."""
    r, status = api("POST", f"{BASE}/{TABLE}", {"fields": record})
    if status == 200:
        print(f"  ✅ Written to Airtable (record {r['id']})")
    else:
        print(f"  ❌ Airtable error: {r}")

def main():
    write_mode = "--write" in sys.argv

    print("🌤️  Fetching London weather...")
    try:
        record = fetch_weather()
    except Exception as e:
        print(f"  ❌ Fetch failed: {e}")
        sys.exit(1)

    print(f"  Date:           {record['Date']}")
    print(f"  Location:       {record['Location']}")
    print(f"  Now:            {record['Temperature C']}°C (feels {record['Feels Like C']}°C)")
    print(f"  High / Low:     {record['High C']}°C / {record['Low C']}°C")
    print(f"  Humidity:       {record['Humidity Pct']}%")
    print(f"  Wind:           {record['Wind Speed KPH']} km/h")
    print(f"  Condition:      {record['Condition']}")
    print(f"  Daily Outlook:  {record['Daily Condition']}")
    print(f"  Rain Expected:  {record['Rain Expected']}")
    if record['Rain Expected'] == "Yes":
        print(f"  Rain Times:     {record['Rain Times']}")
    print(f"  Precipitation:  {record['Precipitation MM']} mm")
    print(f"  Morning (6-12):  {record['Morning Temp C']}°C — {record['Morning Condition']} (rain {record['Morning Rain Prob']}%)")
    print(f"  Afternoon (12-18): {record['Afternoon Temp C']}°C — {record['Afternoon Condition']} (rain {record['Afternoon Rain Prob']}%)")
    print(f"  Evening (18-22): {record['Evening Temp C']}°C — {record['Evening Condition']} (rain {record['Evening Rain Prob']}%)")

    if write_mode:
        write_to_airtable(record)
    else:
        print("\n  (dry run — add --write to save to Airtable)")

if __name__ == "__main__":
    main()
