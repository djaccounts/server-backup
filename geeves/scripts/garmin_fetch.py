#!/usr/bin/env python3
"""
garmin_fetch.py — Fetch cycling activities from Garmin Connect and write to Airtable.

Usage:
    python3 garmin_fetch.py              # Fetch recent rides (last 7 days), dry run
    python3 garmin_fetch.py --write      # Write to Airtable
    python3 garmin_fetch.py --days 30    # Fetch last 30 days
    python3 garmin_fetch.py --all        # Fetch all activities (use carefully)

Requirements:
    GARMIN_EMAIL, GARMIN_PASSWORD in /root/.hermes/.env

Uses the garminconnect Python package (unofficial Garmin Connect API client).
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────────────────────────

AIRTABLE_BASE = "appzvmonQXs4x2AlL"
CYCLING_TABLE = "tblZ7hkoE68IRnQwV"
WORKOUTS_TABLE = "tblMDYF8Lkl5A15CW"


def get_env_key(var_name):
    """Read a key from /root/.hermes/.env"""
    r = subprocess.run(["grep", var_name, "/root/.hermes/.env"], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def garmin_login():
    """Log in to Garmin Connect and return the client."""
    from garminconnect import Garmin

    email = get_env_key("GARMIN_EMAIL")
    password = get_env_key("GARMIN_PASSWORD")

    if not all([email, password]):
        print("ERROR: Missing Garmin credentials in /root/.hermes/.env")
        print("Need: GARMIN_EMAIL, GARMIN_PASSWORD")
        sys.exit(1)

    print("Logging in to Garmin Connect...")
    client = Garmin(email, password)
    client.login()
    print("✅ Logged in")
    return client


def fetch_cycling_activities(client, days=7):
    """Fetch cycling activities from Garmin Connect."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    print(f"Fetching activities from {start_date.date()} to {end_date.date()}...")

    # Get activities list
    activities = client.get_activities_by_date(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )

    # Filter to cycling only
    cycling = []
    for activity in activities:
        activity_type = activity.get("activityType", {}).get("typeKey", "")
        if activity_type in ("cycling", "road_biking", "mountain_biking", "gravel_cycling", "virtual_ride", "indoor_cycling"):
            cycling.append(activity)

    print(f"✅ Found {len(cycling)} cycling activities")
    return cycling


def fetch_activity_detail(client, activity_id):
    """Fetch detailed activity data from Garmin."""
    try:
        detail = client.get_activity_details(activity_id)
        return detail
    except Exception as e:
        print(f"    Warning: Could not fetch details for {activity_id}: {e}")
        return None


def airtable_request(method, table, data=None, record_id=None):
    """Make a request to the Airtable API."""
    key = get_env_key("AIRTABLE_API_KEY")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    if record_id:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{table}/{record_id}"
    else:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{table}"

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  Airtable ERROR {e.code}: {err}")
        return None


def map_ride_type(garmin_type):
    """Map Garmin activity types to our Ride type select options."""
    mapping = {
        "cycling": "Road",
        "road_biking": "Road",
        "mountain_biking": "MTB",
        "gravel_cycling": "Gravel",
        "virtual_ride": "Turbo",
        "indoor_cycling": "Turbo",
    }
    return mapping.get(garmin_type, "Road")


def create_workout_record(activity, detail):
    """Create a Workout record for a cycling activity."""
    start_time = activity.get("startTimeLocal", "")
    date = start_time[:10] if start_time else ""

    duration_secs = activity.get("duration", 0) or 0
    distance_m = activity.get("distance", 0) or 0

    data = {
        "fields": {
            "Date": date,
            "Type": "Cycle",
            "Duration (mins)": round(duration_secs / 60),
            "Distance (km)": round(distance_m / 1000, 1),
            "Energy level": 3,
            "Perceived difficulty": 3,
            "Source": "Garmin",
            "Notes": f"Auto-imported from Garmin: {activity.get('activityName', 'Ride')}"
        }
    }
    result = airtable_request("POST", WORKOUTS_TABLE, data)
    if result and "id" in result:
        return result["id"]
    return None


def create_cycling_record(activity, detail, workout_id=None):
    """Create a Cycling record from a Garmin activity."""
    start_time = activity.get("startTimeLocal", "")
    date = start_time[:10] if start_time else ""

    duration_secs = activity.get("duration", 0) or 0
    distance_m = activity.get("distance", 0) or 0
    elevation_m = activity.get("elevationGain", 0) or 0

    # Speed in mph
    avg_speed_mps = activity.get("averageSpeed", 0) or 0
    max_speed_mps = activity.get("maxSpeed", 0) or 0

    garmin_type = activity.get("activityType", {}).get("typeKey", "cycling")

    fields = {
        "Date": date,
        "Route": activity.get("activityName", ""),
        "Distance (miles)": round(distance_m * 0.000621371, 1),
        "Duration (mins)": round(duration_secs / 60),
        "Elevation gain (m)": round(elevation_m),
        "Avg speed (mph)": round(avg_speed_mps * 2.23694, 1) if avg_speed_mps else 0,
        "Max speed (mph)": round(max_speed_mps * 2.23694, 1) if max_speed_mps else 0,
        "Ride type": map_ride_type(garmin_type),
        "Source": "Garmin",
        "Notes": activity.get("description", "") or ""
    }

    # Add workout link
    if workout_id:
        fields["Workout"] = [workout_id]

    # Add detailed data if available
    if detail:
        # Heart rate
        if detail.get("averageHR"):
            fields["Avg heart rate"] = round(detail["averageHR"])
        if detail.get("maxHR"):
            fields["Max heart rate"] = round(detail["maxHR"])

        # Power
        if detail.get("avgPower"):
            fields["Avg power (W)"] = round(detail["avgPower"])

        # Calories
        if detail.get("calories"):
            fields["Calories burned"] = round(detail["calories"])

        # Bike/device
        if detail.get("deviceName"):
            fields["Bike used"] = detail["deviceName"]

        # GPS / map
        if detail.get("activityId"):
            fields["Strava URL"] = f"https://connect.garmin.com/modern/activity/{detail['activityId']}"

    data = {"fields": fields}
    result = airtable_request("POST", CYCLING_TABLE, data)
    return result


def main():
    days = 7
    write = False

    for arg in sys.argv[1:]:
        if arg == "--write":
            write = True
        elif arg.startswith("--days="):
            days = int(arg.split("=")[1])
        elif arg == "--all":
            days = 365

    print(f"🚴 Garmin Cycling Fetcher")
    print(f"   Mode: {'WRITE' if write else 'DRY RUN'}")
    print(f"   Days: {days}")
    print()

    # Log in to Garmin
    client = garmin_login()

    # Fetch activities
    activities = fetch_cycling_activities(client, days)

    if not activities:
        print("No cycling activities found.")
        return

    # Process each activity
    created = 0
    skipped = 0

    for activity in activities:
        name = activity.get("activityName", "Unknown")
        date = activity.get("startTimeLocal", "")[:10]
        distance_mi = round((activity.get("distance", 0) or 0) * 0.000621371, 1)
        duration_min = round((activity.get("duration", 0) or 0) / 60)

        print(f"\n  {date} — {name} ({distance_mi} mi, {duration_min} min)")

        if not write:
            print(f"    [DRY RUN] Would create Cycling + Workout records")
            continue

        # Fetch detailed data
        activity_id = activity.get("activityId")
        detail = None
        if activity_id:
            detail = fetch_activity_detail(client, activity_id)

        # Create Workout record
        workout_id = create_workout_record(activity, detail)
        if workout_id:
            print(f"    ✅ Workout: {workout_id}")

        # Create Cycling record
        result = create_cycling_record(activity, detail, workout_id)
        if result and "id" in result:
            print(f"    ✅ Cycling: {result['id']}")
            created += 1
        else:
            print(f"    ❌ Failed")
            skipped += 1

        time.sleep(1)  # Be nice to Garmin's API

    print(f"\n{'=' * 50}")
    print(f"Summary: {created} created, {skipped} skipped")


if __name__ == "__main__":
    main()
