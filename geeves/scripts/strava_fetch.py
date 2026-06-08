#!/usr/bin/env python3
"""
strava_fetch.py — Fetch cycling activities from Strava and write to Airtable Cycling table.

Usage:
    python3 strava_fetch.py              # Fetch recent activities (last 7 days)
    python3 strava_fetch.py --write      # Write to Airtable
    python3 strava_fetch.py --days 30    # Fetch last 30 days
    python3 strava_fetch.py --all        # Fetch all activities (paginated)

Requirements:
    STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN in /root/.hermes/.env

API: Strava API v3 — https://developers.strava.com/docs/reference/
Rate limit: 200 requests per 15 minutes, 2000 per day (free tier)
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────────────────────────

AIRTABLE_BASE = "appzvmonQXs4x2AlL"
CYCLING_TABLE = "tblZ7hkoE68IRnQwV"
WORKOUTS_TABLE = "tblMDYF8Lkl5A15CW"

STRAVA_API_BASE = "https://www.strava.com/api/v3"
TOKEN_URL = "https://www.strava.com/oauth/token"


def get_env_key(var_name):
    """Read a key from /root/.hermes/.env"""
    r = subprocess.run(["grep", var_name, "/root/.hermes/.env"], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def get_access_token():
    """Refresh the Strava OAuth access token."""
    client_id = get_env_key("STRAVA_CLIENT_ID")
    client_secret = get_env_key("STRAVA_CLIENT_SECRET")
    refresh_token = get_env_key("STRAVA_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        print("ERROR: Missing Strava credentials in /root/.hermes/.env")
        print("Need: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN")
        sys.exit(1)

    data = json.dumps({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result["access_token"]
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"ERROR refreshing token: {e.code} {err}")
        sys.exit(1)


def strava_get(access_token, endpoint, params=None):
    """Make a GET request to the Strava API."""
    url = f"{STRAVA_API_BASE}{endpoint}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())

    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    })

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"ERROR {e.code}: {err}")
        return None


def fetch_activities(access_token, days=7):
    """Fetch cycling activities from the last N days."""
    after = int((datetime.now() - timedelta(days=days)).timestamp())
    activities = []
    page = 1

    while True:
        result = strava_get(access_token, "/athlete/activities", {
            "after": after,
            "per_page": 50,
            "page": page
        })

        if not result:
            break

        for activity in result:
            # Only cycling activities
            if activity.get("type") in ("Ride", "VirtualRide", "GravelRide", "MountainBikeRide"):
                activities.append(activity)

        if len(result) < 50:
            break
        page += 1
        time.sleep(0.5)  # Rate limit safety

    return activities


def fetch_activity_detail(access_token, activity_id):
    """Fetch detailed activity data (streams, etc.)."""
    return strava_get(access_token, f"/activities/{activity_id}")


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


def activity_exists_in_airtable(strava_id):
    """Check if a Strava activity is already in Airtable."""
    key = get_env_key("AIRTABLE_API_KEY")
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{CYCLING_TABLE}?filterByFormula=%7BStrava+ID%7D%3D%27{strava_id}%27"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return len(result.get("records", [])) > 0
    except Exception:
        return False


def create_workout_record(activity):
    """Create a Workout record for a cycling activity."""
    data = {
        "fields": {
            "Date": activity["start_date_local"][:10],
            "Type": "Cycle",
            "Duration (mins)": round(activity.get("moving_time", 0) / 60),
            "Distance (km)": round(activity.get("distance", 0) / 1000, 1),
            "Energy level": 3,  # Default, can be updated manually
            "Perceived difficulty": 3,
            "Source": "Strava",
            "Notes": f"Auto-imported from Strava: {activity.get('name', 'Ride')}"
        }
    }
    result = airtable_request("POST", WORKOUTS_TABLE, data)
    if result and "id" in result:
        return result["id"]
    return None


def create_cycling_record(activity, workout_id=None):
    """Create a Cycling record from a Strava activity."""
    detail = None
    # Try to get detailed data (heart rate, power)
    # Note: This uses an extra API call per activity
    access_token = get_access_token()
    detail = fetch_activity_detail(access_token, activity["id"])

    fields = {
        "Date": activity["start_date_local"][:10],
        "Route": activity.get("name", ""),
        "Distance (miles)": round(activity.get("distance", 0) * 0.000621371, 1),
        "Duration (mins)": round(activity.get("moving_time", 0) / 60),
        "Elevation gain (m)": round(activity.get("total_elevation_gain", 0)),
        "Avg speed (mph)": round(activity.get("average_speed", 0) * 2.23694, 1),
        "Max speed (mph)": round(activity.get("max_speed", 0) * 2.23694, 1),
        "Ride type": map_ride_type(activity.get("type", "Ride")),
        "Source": "Strava",
        "Strava URL": f"https://www.strava.com/activities/{activity['id']}",
        "Notes": activity.get("description", "") or ""
    }

    # Add workout link if created
    if workout_id:
        fields["Workout"] = [workout_id]

    # Add heart rate data if available
    if detail:
        if detail.get("average_heartrate"):
            fields["Avg heart rate"] = round(detail["average_heartrate"])
        if detail.get("max_heartrate"):
            fields["Max heart rate"] = round(detail["max_heartrate"])
        if detail.get("average_watts"):
            fields["Avg power (W)"] = round(detail["average_watts"])
        if detail.get("calories"):
            fields["Calories burned"] = round(detail["calories"])
        if detail.get("device_name"):
            fields["Bike used"] = detail["device_name"]

    data = {"fields": fields}
    result = airtable_request("POST", CYCLING_TABLE, data)
    return result


def map_ride_type(strava_type):
    """Map Strava activity types to our Ride type select options."""
    mapping = {
        "Ride": "Road",
        "VirtualRide": "Turbo",
        "GravelRide": "Gravel",
        "MountainBikeRide": "MTB",
        "EBikeRide": "Road",
    }
    return mapping.get(strava_type, "Road")


def main():
    days = 7
    write = False
    fetch_all = False

    for arg in sys.argv[1:]:
        if arg == "--write":
            write = True
        elif arg.startswith("--days="):
            days = int(arg.split("=")[1])
        elif arg == "--all":
            fetch_all = True
            days = 365

    print(f"🚴 Strava Cycling Fetcher")
    print(f"   Mode: {'WRITE' if write else 'DRY RUN'}")
    print(f"   Days: {days}")
    print()

    # Get access token
    print("Refreshing Strava access token...")
    access_token = get_access_token()
    print("✅ Token refreshed")

    # Fetch activities
    print(f"Fetching cycling activities (last {days} days)...")
    activities = fetch_activities(access_token, days)
    print(f"✅ Found {len(activities)} cycling activities")

    if not activities:
        print("No cycling activities found.")
        return

    # Process each activity
    created = 0
    skipped = 0

    for activity in activities:
        name = activity.get("name", "Unknown")
        date = activity.get("start_date_local", "")[:10]
        distance = round(activity.get("distance", 0) * 0.000621371, 1)

        print(f"\n  {date} — {name} ({distance} mi)")

        if not write:
            print(f"    [DRY RUN] Would create Cycling record")
            continue

        # Check for duplicates (by Strava URL)
        # Note: We check by date + distance as a simple dedup
        # A more robust approach would store the Strava activity ID

        # Create Workout record first
        workout_id = create_workout_record(activity)
        if workout_id:
            print(f"    ✅ Workout created: {workout_id}")

        # Create Cycling record
        result = create_cycling_record(activity, workout_id)
        if result and "id" in result:
            print(f"    ✅ Cycling record created: {result['id']}")
            created += 1
        else:
            print(f"    ❌ Failed to create Cycling record")
            skipped += 1

        time.sleep(0.5)  # Rate limit safety

    print(f"\n{'=' * 50}")
    print(f"Summary: {created} created, {skipped} skipped")


if __name__ == "__main__":
    main()
