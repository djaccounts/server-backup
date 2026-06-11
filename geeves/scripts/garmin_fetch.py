#!/usr/bin/env python3
"""
garmin_fetch.py — Fetch cycling activities from Garmin Connect and write to Baserow.

Usage:
    python3 garmin_fetch.py                    # Fetch last 7 days, dry run
    python3 garmin_fetch.py --write            # Write to Baserow
    python3 garmin_fetch.py --days 14          # Fetch last 14 days
    python3 garmin_fetch.py --weeks 4          # Fetch last 4 weeks (28 days)

For backfill (run weekly via cron):
    python3 garmin_fetch.py --write --days 7   # Each run fetches the next week

Requirements:
    GARMIN_EMAIL, GARMIN_PASSWORD in /root/.hermes/.env
    BASEROW_API_TOKEN in /root/.hermes/.env

Baserow tables:
    Cycling (id: 396), Workouts (id: 392), database ID: 132
"""

import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────────────────────────

BASEROW_BASE = "http://77.68.33.121/api"
BASEROW_DB = 132
CYCLING_TABLE_ID = 396
WORKOUTS_TABLE_ID = 392

# State file tracks the oldest date we've already imported
STATE_FILE = "/root/Geeves/scripts/.garmin_import_state.json"


def get_env_key(var_name):
    r = subprocess.run(["grep", var_name, "/root/.hermes/.env"], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def baserow_get(url):
    token = get_env_key("BASEROW_API_TOKEN")
    req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def baserow_post(table_id, data):
    token = get_env_key("BASEROW_API_TOKEN")
    url = f"{BASEROW_BASE}/database/rows/table/{table_id}/?user_field_names=true"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  Baserow ERROR {e.code}: {err}")
        return None


def load_state():
    """Load the import state (oldest date imported so far)."""
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"oldest_imported": None, "last_run": None}


def save_state(state):
    """Save the import state."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def garmin_login():
    from garminconnect import Garmin
    email = get_env_key("GARMIN_EMAIL")
    password = get_env_key("GARMIN_PASSWORD")
    if not all([email, password]):
        print("ERROR: Missing Garmin credentials")
        sys.exit(1)
    print("Logging in to Garmin Connect...")
    client = Garmin(email, password)
    try:
        client.login()
        print("✅ Logged in")
        return client
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "rate" in error_str.lower():
            print("⚠️  Garmin rate limit hit. Waiting 60 seconds and retrying...")
            time.sleep(60)
            try:
                client.login()
                print("✅ Logged in (after retry)")
                return client
            except Exception as e2:
                print(f"❌ Login failed after retry: {e2}")
                sys.exit(1)
        else:
            print(f"❌ Login failed: {e}")
            sys.exit(1)


def fetch_cycling_activities(client, start_date, end_date):
    """Fetch cycling activities from Garmin Connect within a date range."""
    print(f"Fetching activities from {start_date.date()} to {end_date.date()}...")
    activities = client.get_activities_by_date(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )
    cycling_types = ("cycling", "road_biking", "mountain_biking", "gravel_cycling", "virtual_ride", "indoor_cycling")
    cycling = [a for a in activities if a.get("activityType", {}).get("typeKey", "") in cycling_types]
    print(f"✅ Found {len(cycling)} cycling activities")
    return cycling


def activity_exists(date, route, distance_mi):
    """Check if a ride already exists in Baserow (dedup by date + route + distance)."""
    # Baserow filter formula
    formula = f"AND(DATE_ADD({{Date}},'days','0')='{date}','{{Route}}'='{route}',{{Distance (miles)}}={distance_mi})"
    url = f"{BASEROW_BASE}/database/rows/table/{CYCLING_TABLE_ID}/?user_field_names=true&filter_by_formula={urllib.parse.quote(formula)}"
    try:
        result = baserow_get(url)
        return len(result.get("results", [])) > 0
    except Exception:
        return False


def create_workout(activity):
    """Create a Workout record in Baserow."""
    start_time = activity.get("startTimeLocal", "")
    date = start_time[:10] if start_time else ""
    duration_secs = activity.get("duration", 0) or 0
    distance_m = activity.get("distance", 0) or 0

    data = {
        "Date": date,
        "Type": "Cycle",
        "Duration (mins)": round(duration_secs / 60),
        "Distance (km)": round(distance_m / 1000, 1),
        "Energy level": 3,
        "Perceived difficulty": 4,
        "Source": "Garmin",
        "Notes": f"Auto-imported from Garmin: {activity.get('activityName', 'Ride')}",
        "People": []  # Empty link
    }
    result = baserow_post(WORKOUTS_TABLE_ID, data)
    if result and "id" in result:
        return result["id"]
    if result and "id" in result.get("id", {}):
        return result["id"]
    # Try to extract ID from various response formats
    if isinstance(result, dict):
        rid = result.get("id")
        if rid:
            return rid if isinstance(rid, int) else rid.get("id")
    return None


def create_cycling(activity, detail, workout_id):
    """Create a Cycling record in Baserow."""
    start_time = activity.get("startTimeLocal", "")
    date = start_time[:10] if start_time else ""
    duration_secs = activity.get("duration", 0) or 0
    distance_m = activity.get("distance", 0) or 0
    elevation_m = activity.get("elevationGain", 0) or 0
    avg_speed_mps = activity.get("averageSpeed", 0) or 0
    max_speed_mps = activity.get("maxSpeed", 0) or 0
    garmin_type = activity.get("activityType", {}).get("typeKey", "cycling")

    ride_type_map = {
        "cycling": "Road", "road_biking": "Road", "mountain_biking": "MTB",
        "gravel_cycling": "Gravel", "virtual_ride": "Turbo", "indoor_cycling": "Turbo",
    }

    data = {
        "Date": date,
        "Route": activity.get("activityName", ""),
        "Distance (miles)": round(distance_m * 0.000621371, 1),
        "Duration (mins)": round(duration_secs / 60),
        "Elevation gain (m)": round(elevation_m),
        "Avg speed (mph)": round(avg_speed_mps * 2.23694, 1) if avg_speed_mps else 0,
        "Max speed (mph)": round(max_speed_mps * 2.23694, 1) if max_speed_mps else 0,
        "Ride type": ride_type_map.get(garmin_type, "Road"),
        "Bike used": "",
        "Source": "Garmin",
        "People": [],
        "Avg heart rate": None,
        "Max heart rate": None,
        "Avg power (W)": None,
        "Calories burned": None,
        "Strava URL": f"https://connect.garmin.com/modern/activity/{activity.get('activityId', '')}",
        "Notes": (activity.get("description", "") or "").strip(),
    }

    if detail:
        if detail.get("averageHR"):
            data["Avg heart rate"] = round(detail["averageHR"])
        if detail.get("maxHR"):
            data["Max heart rate"] = round(detail["maxHR"])
        if detail.get("avgPower"):
            data["Avg power (W)"] = round(detail["avgPower"])
        if detail.get("calories"):
            data["Calories burned"] = round(detail["calories"])
        if detail.get("deviceName"):
            data["Bike used"] = detail["deviceName"]

    if workout_id:
        data["Workout"] = [workout_id]

    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}

    result = baserow_post(CYCLING_TABLE_ID, data)
    if isinstance(result, dict):
        rid = result.get("id")
        if rid:
            return rid if isinstance(rid, int) else None
    return None


def main():
    days = 7
    write = False
    backfill = False

    for arg in sys.argv[1:]:
        if arg == "--write":
            write = True
        elif arg.startswith("--days="):
            days = int(arg.split("=")[1])
        elif arg.startswith("--weeks="):
            days = int(arg.split("=")[1]) * 7
        elif arg == "--backfill":
            backfill = True
            days = 7

    print(f"🚴 Garmin Cycling Fetcher → Baserow")
    print(f"   Mode: {'WRITE' if write else 'DRY RUN'}")
    print(f"   Backfill: {'yes' if backfill else 'no'}")
    print(f"   Days: {days}")
    print()

    state = load_state()
    print(f"   Last run: {state.get('last_run', 'never')}")
    print(f"   Oldest imported: {state.get('oldest_imported', 'N/A')}")
    print()

    client = garmin_login()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # In backfill mode, work backwards from the oldest imported date
    if backfill and state.get("oldest_imported"):
        oldest = datetime.strptime(state["oldest_imported"], "%Y-%m-%d")
        end_date = oldest - timedelta(days=1)  # Start from day before oldest
        start_date = end_date - timedelta(days=days)
        print(f"   Backfill range: {start_date.date()} → {end_date.date()}")
        print()

    activities = fetch_cycling_activities(client, start_date, end_date)

    if not activities:
        print("No cycling activities found.")
        return

    created = 0
    skipped_dup = 0
    skipped_err = 0

    for activity in activities:
        name = activity.get("activityName", "Unknown")
        date = activity.get("startTimeLocal", "")[:10]
        dist_mi = round((activity.get("distance", 0) or 0) * 0.000621371, 1)
        dur_min = round((activity.get("duration", 0) or 0) / 60)

        print(f"\n  {date} — {name} ({dist_mi} mi, {dur_min} min)")

        # Dedup check
        if activity_exists(date, name, dist_mi):
            print(f"    ⏭️  Already exists (duplicate)")
            skipped_dup += 1
            continue

        if not write:
            print(f"    [DRY RUN] Would create Cycling + Workout")
            continue

        # Fetch detail
        activity_id = activity.get("activityId")
        detail = None
        if activity_id:
            try:
                detail = client.get_activity_details(activity_id)
            except Exception:
                pass

        # Create Workout
        workout_id = create_workout(activity)
        if workout_id:
            print(f"    ✅ Workout: {workout_id}")

        # Create Cycling
        cycling_id = create_cycling(activity, detail, workout_id)
        if cycling_id:
            print(f"    ✅ Cycling: {cycling_id}")
            created += 1
        else:
            print(f"    ❌ Failed")
            skipped_err += 1

        time.sleep(1)

    # Update state
    oldest = min(a.get("startTimeLocal", "")[:10] for a in activities)
    state["oldest_imported"] = oldest
    state["last_run"] = datetime.now().isoformat()
    save_state(state)

    print(f"\n{'=' * 50}")
    print(f"Summary: {created} created, {skipped_dup} duplicates skipped, {skipped_err} errors")


if __name__ == "__main__":
    main()
