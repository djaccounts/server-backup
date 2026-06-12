#!/usr/bin/env python3
"""
garmin_bulk_import.py — One-time bulk import of all cycling activities from Garmin Connect to Baserow.

Usage:
    python3 garmin_bulk_import.py              # Dry run
    python3 garmin_bulk_import.py --write      # Write to Baserow

Requirements:
    GARMIN_EMAIL, GARMIN_PASSWORD in /root/.hermes/.env
    BASEROW_API_TOKEN in /root/.hermes/.env
"""

import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────────────────────────

BASEROW_BASE = "http://77.68.33.121/api"
BASEROW_DB = 132
CYCLING_TABLE_ID = 396
WORKOUTS_TABLE_ID = 392

STATE_FILE = "/root/Geeves/scripts/.garmin_bulk_state.json"


def get_env_key(var_name):
    r = subprocess.run(["grep", var_name, "/root/.hermes/.env"], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def baserow_get(url):
    token = get_env_key("BASEROW_API_TOKEN")
    req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def baserow_get_all(table_id):
    """Fetch all records from a Baserow table, handling pagination."""
    all_results = []
    url = f"{BASEROW_BASE}/database/rows/table/{table_id}/?user_field_names=true&size=200"
    while url:
        result = baserow_get(url)
        all_results.extend(result.get("results", []))
        url = result.get("next")
    return all_results


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


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_offset": 0, "total_imported": 0, "total_skipped": 0}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def activity_exists(date, route, distance_mi, existing_records):
    """Check if a ride already exists in our local cache of Baserow records."""
    for r in existing_records:
        r_date = r.get("Date", "")
        r_route = r.get("Route", "") or ""
        r_dist = float(r.get("Distance (miles)", 0) or 0)
        if r_date == date and r_route == route and abs(r_dist - distance_mi) < 0.2:
            return True
    return False


def create_workout(activity, write):
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
        "People": []
    }
    if write:
        result = baserow_post(WORKOUTS_TABLE_ID, data)
        if result and "id" in result:
            return result["id"]
    return None


def create_cycling(activity, detail, workout_id, write):
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

    # HR and calories from summary (available without detail fetch)
    if activity.get("averageHR"):
        data["Avg heart rate"] = round(activity["averageHR"])
    if activity.get("maxHR"):
        data["Max heart rate"] = round(activity["maxHR"])
    if activity.get("calories"):
        data["Calories burned"] = round(activity["calories"])

    if detail:
        if detail.get("deviceName"):
            data["Bike used"] = detail["deviceName"]

    if workout_id:
        data["Workout"] = [workout_id]

    data = {k: v for k, v in data.items() if v is not None}

    if write:
        result = baserow_post(CYCLING_TABLE_ID, data)
        if isinstance(result, dict):
            rid = result.get("id")
            if rid:
                return rid if isinstance(rid, int) else None
    return None


def main():
    write = "--write" in sys.argv
    batch_size = 100  # Fetch 100 activities at a time from Garmin

    print(f"🚴 Garmin Bulk Cycling Import → Baserow")
    print(f"   Mode: {'WRITE' if write else 'DRY RUN'}")
    print()

    state = load_state()
    print(f"   Previous runs: {state.get('total_imported', 0)} imported, {state.get('total_skipped', 0)} skipped")
    print()

    client = garmin_login()

    # Load existing Baserow records for dedup
    print("Loading existing Baserow records for dedup...")
    existing = baserow_get_all(CYCLING_TABLE_ID)
    print(f"   {len(existing)} existing records")
    print()

    # Fetch ALL cycling activities from Garmin using pagination
    # Garmin API: get_activities(offset, limit) — offset starts at 0
    all_cycling = []
    offset = state.get("last_offset", 0)
    cycling_types = ("cycling", "road_biking", "mountain_biking", "gravel_cycling", "virtual_ride", "indoor_cycling")

    print(f"Fetching activities from Garmin (starting at offset {offset})...")
    while True:
        try:
            activities = client.get_activities(offset, batch_size)
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                print(f"  Rate limited, waiting 60s...")
                time.sleep(60)
                continue
            print(f"  Error fetching: {e}")
            break

        if not activities:
            print("  No more activities.")
            break

        batch_cycling = [a for a in activities if a.get("activityType", {}).get("typeKey", "") in cycling_types]
        all_cycling.extend(batch_cycling)
        print(f"  Offset {offset}: {len(activities)} total, {len(batch_cycling)} cycling (total so far: {len(all_cycling)})")

        offset += batch_size
        save_state({"last_offset": offset, "total_imported": state.get("total_imported", 0), "total_skipped": state.get("total_skipped", 0)})
        time.sleep(1)

    print(f"\n✅ Total cycling activities to process: {len(all_cycling)}")
    print()

    # Sort by date (oldest first)
    all_cycling.sort(key=lambda a: a.get("startTimeLocal", ""))

    created = 0
    skipped_dup = 0
    skipped_err = 0

    for activity in all_cycling:
        name = activity.get("activityName", "Unknown")
        date = activity.get("startTimeLocal", "")[:10]
        dist_mi = round((activity.get("distance", 0) or 0) * 0.000621371, 1)
        dur_min = round((activity.get("duration", 0) or 0) / 60)

        print(f"  {date} — {name} ({dist_mi} mi, {dur_min} min)")

        # Dedup check
        if activity_exists(date, name, dist_mi, existing):
            print(f"    ⏭️  Already exists (duplicate)")
            skipped_dup += 1
            continue

        if not write:
            print(f"    [DRY RUN] Would create")
            continue

        # Fetch detail for device name only
        activity_id = activity.get("activityId")
        detail = None
        if activity_id:
            try:
                detail = client.get_activity_details(activity_id)
            except Exception:
                pass

        # Create Workout
        workout_id = create_workout(activity, write)

        # Create Cycling
        cycling_id = create_cycling(activity, detail, workout_id, write)
        if cycling_id:
            print(f"    ✅ Created (id: {cycling_id})")
            created += 1
            # Add to existing cache to avoid dupes within this run
            existing.append({"Date": date, "Route": name, "Distance (miles)": str(dist_mi)})
        else:
            print(f"    ❌ Failed")
            skipped_err += 1

        time.sleep(0.5)

    # Update state
    total_imported = state.get("total_imported", 0) + created
    total_skipped = state.get("total_skipped", 0) + skipped_dup
    save_state({"last_offset": offset, "total_imported": total_imported, "total_skipped": total_skipped})

    print(f"\n{'=' * 50}")
    print(f"This run: {created} created, {skipped_dup} duplicates, {skipped_err} errors")
    print(f"All time: {total_imported} imported, {total_skipped} skipped")


if __name__ == "__main__":
    main()
