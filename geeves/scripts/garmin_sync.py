#!/usr/bin/env python3
"""
Garmin Connect → Geeves Cycling Sync
Fetches recent cycling activities from Garmin Connect and stores them in Airtable.
Uses the unofficial python-garminconnect library (no developer API key needed).

Run daily via cron to sync new rides.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────

AIRTABLE_BASE_ID = "appzvmonQXs4x2AlL"
WORKOUTS_TABLE = "tblMDYF8Lkl5A15CW"
CYCLING_TABLE = "tblZ7hkoE68IRnQwV"

# How many days back to look for new activities
LOOKBACK_DAYS = 7

# ── Airtable Helpers ───────────────────────────────────────────────────────────

def get_env_key(name):
    """Read an API key from .env file."""
    env_path = Path("/root/.hermes/.env")
    with open(env_path) as f:
        for line in f:
            if line.startswith(f"{name}="):
                return line.strip().split("=", 1)[1]
    raise RuntimeError(f"{name} not found in .env")


def airtable_request(method, table, data=None, params=None, record_id=None):
    """Make an Airtable API request."""
    import urllib.parse, urllib.request, urllib.error

    key = get_env_key("AIRTABLE_API_KEY")
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}"
    if record_id:
        url += f"/{record_id}"
    if params:
        encoded = urllib.parse.urlencode(params, doseq=True)
        url += "?" + encoded

    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")

    if data:
        req.data = json.dumps(data).encode()

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"  Airtable API error {e.code}: {body[:300]}", file=sys.stderr)
        return None


def get_existing_garmin_ids():
    """Get all existing Garmin activity IDs from the Cycling table to avoid duplicates."""
    ids = set()
    offset = None
    while True:
        # The Cycling table has a Garmin Activity ID field (to be added if not present)
        # For now we check by date + distance combination
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        result = airtable_request("GET", CYCLING_TABLE, params=params)
        if not result:
            break
        records = result.get("records", [])
        for r in records:
            f = r.get("fields", {})
            # Use a composite key: date + distance
            date = f.get("Date", "")
            dist = f.get("Distance (miles)", 0)
            if date:
                ids.add(f"{date}_{dist}")
        offset = result.get("offset")
        if not offset:
            break
    return ids


def create_workout_record(fields):
    """Create a Workout record in Airtable."""
    result = airtable_request("POST", WORKOUTS_TABLE, data={
        "fields": fields,
        "typecast": True,
    })
    if result:
        print(f"  ✓ Workout created: {fields.get('Date', '?')} {fields.get('Type', '?')} (ID: {result['id']})")
    return result


def create_cycling_record(fields):
    """Create a Cycling record in Airtable."""
    result = airtable_request("POST", CYCLING_TABLE, data={
        "fields": fields,
        "typecast": True,
    })
    if result:
        print(f"  ✓ Cycling record created: {fields.get('Date', '?')} {fields.get('Distance (miles)', '?')}mi (ID: {result['id']})")
    return result


def update_cycling_with_workout(cycling_id, workout_id):
    """Link a Cycling record to its parent Workout."""
    result = airtable_request("PATCH", CYCLING_TABLE, data={
        "fields": {"Workout": [workout_id]}
    }, record_id=cycling_id)
    if result:
        print(f"  ✓ Linked cycling {cycling_id} → workout {workout_id}")
    return result


# ── Garmin Connect ─────────────────────────────────────────────────────────────

def get_garmin_client():
    """
    Authenticate with Garmin Connect.
    Requires GARMIN_EMAIL and GARMIN_PASSWORD in .env.
    Tokens are cached in ~/.garminconnect/ for subsequent runs.
    """
    try:
        from garminconnect import Garmin
    except ImportError:
        print("ERROR: garminconnect not installed. Run: pip install garminconnect", file=sys.stderr)
        sys.exit(1)

    email = get_env_key("GARMIN_EMAIL")
    password = get_env_key("GARMIN_PASSWORD")

    tokenstore = Path.home() / ".garminconnect"
    tokenstore.mkdir(exist_ok=True)

    try:
        # Try to use cached tokens first
        client = Garmin(email, password)
        client.login()
        print("  Authenticated with Garmin Connect")
        return client
    except Exception as e:
        print(f"  Garmin login failed: {e}", file=sys.stderr)
        raise


def fetch_cycling_activities(client, days_back=LOOKBACK_DAYS):
    """
    Fetch cycling activities from Garmin Connect within the lookback window.
    Returns a list of activity dicts.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"  Fetching activities from {start_str} to {end_str}...")

    try:
        # Use get_activities_by_date for date-range queries
        activities = client.get_activities_by_date(startdate=start_str, enddate=end_str)
        if not activities:
            print("  No activities found in date range")
            return []

        # Garmin activity type IDs
        # Cycling types we want to keep
        cycling_type_ids = {
            2, 5, 10, 19, 21, 22, 25, 143, 152, 175, 176, 197, 198,
        }
        # Walking/hiking types that are likely duplicates of a cycling ride
        # (user wears two Garmins — one set to cycling, one to walking)
        walking_type_ids = {
            3,    # hiking
            9,    # walking
            15,   # casual_walking
            16,   # speed_walking
        }

        # Separate cycling and walking activities
        cycling_acts = []
        walking_acts = []
        for a in activities:
            type_id = a.get("activityType", {}).get("typeId", 0)
            if type_id in cycling_type_ids:
                cycling_acts.append(a)
            elif type_id in walking_type_ids:
                walking_acts.append(a)
            # Ignore all other types (running, swimming, etc.)

        print(f"  Total activities: {len(activities)}, cycling: {len(cycling_acts)}, walking: {len(walking_acts)}")

    except Exception as e:
        print(f"  Error fetching activities: {e}", file=sys.stderr)
        return []

    # Deduplicate: for each walking activity, check if there's a cycling activity
    # on the same day with a similar distance (±1 mile). If so, skip the walking one.
    # This handles the two-Garmin scenario (one set to cycling, one to walking).
    walking_duplicates = set()
    for w in walking_acts:
        w_date = w.get("startTimeLocal", "")[:10]
        w_dist = round(w.get("distance", 0) * 0.000621371, 1)
        for c in cycling_acts:
            c_date = c.get("startTimeLocal", "")[:10]
            c_dist = round(c.get("distance", 0) * 0.000621371, 1)
            if w_date == c_date and abs(w_dist - c_dist) <= 1.0:
                walking_duplicates.add(id(w))
                w_name = w.get("activityName", "")
                c_name = c.get("activityName", "")
                print(f"  ⏭ Walking duplicate of cycling: '{w_name}' ({w_dist}mi) ≈ '{c_name}' ({c_dist}mi)")
                break

    # Keep all cycling + non-duplicate walking
    # Only keep walking activities that are >= 3 miles — shorter walks are likely
    # genuine walks, not misrecorded cycling rides from the second Garmin
    cycling = cycling_acts + [
        w for w in walking_acts
        if id(w) not in walking_duplicates
        and round(w.get("distance", 0) * 0.000621371, 1) >= 3.0
    ]
    # Count how many short walks were filtered out
    short_walks = sum(
        1 for w in walking_acts
        if id(w) not in walking_duplicates
        and round(w.get("distance", 0) * 0.000621371, 1) < 3.0
    )
    if short_walks:
        print(f"  Filtered {short_walks} short walks (< 3mi, likely genuine walks)")

    if walking_duplicates:
        print(f"  Removed {len(walking_duplicates)} walking duplicates (two-Garmin scenario)")

    # Deduplicate within remaining activities by (date, rounded_distance)
    # Catches any remaining edge cases
    seen_in_run = {}
    deduped = []
    for a in cycling:
        date = a.get("startTimeLocal", "")[:10]
        dist_m = a.get("distance", 0)
        dist_mi = round(dist_m * 0.000621371, 1)
        dist_key = round(dist_mi * 2) / 2  # Round to nearest 0.5mi
        key = f"{date}_{dist_key}"
        if key in seen_in_run:
            existing_name = seen_in_run[key].get("activityName", "")
            new_name = a.get("activityName", "")
            print(f"  ⏭ Duplicate in run: '{new_name}' ({dist_mi}mi) — keeping '{existing_name}'")
            continue
        seen_in_run[key] = a
        deduped.append(a)
    if len(deduped) < len(cycling):
        print(f"  After in-run dedup: {len(deduped)} (removed {len(cycling) - len(deduped)} duplicates)")
    cycling = deduped

    # Enrich with detailed data
    enriched = []
    for a in cycling:
        activity_id = a.get("activityId")
        if activity_id:
            try:
                details = client.get_activity_details(activity_id)
                a["_details"] = details
            except Exception as e:
                print(f"    Warning: couldn't fetch details for {activity_id}: {e}")
                a["_details"] = None
        enriched.append(a)

    return enriched


def parse_cycling_activity(activity):
    """
    Parse a Garmin activity dict into structured fields for Airtable.
    Returns (workout_fields, cycling_fields) tuple.
    """
    # Basic activity data
    start_time = activity.get("startTimeLocal", "")
    if start_time:
        try:
            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        except:
            date_str = start_time[:10]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Distance in metres → miles
    distance_m = activity.get("distance", 0)
    distance_miles = round(distance_m * 0.000621371, 1)

    # Duration in seconds → minutes
    duration_s = activity.get("duration", 0)
    duration_mins = round(duration_s / 60, 1)

    # Speed
    avg_speed_mps = activity.get("averageSpeed", 0)
    max_speed_mps = activity.get("maxSpeed", 0)
    avg_speed_mph = round(avg_speed_mps * 2.23694, 1) if avg_speed_mps else None
    max_speed_mph = round(max_speed_mps * 2.23694, 1) if max_speed_mps else None

    # Elevation
    elev_gain = activity.get("elevationGain", 0)
    elev_gain_m = round(elev_gain, 1) if elev_gain else None

    # Determine ride type from Garmin activity type ID
    activity_type_id = activity.get("activityType", {}).get("typeId", 2)
    ride_type_map = {
        2: "Road",
        5: "MTB",
        10: "Road",
        19: "Road",
        21: "Road",
        22: "Road",
        25: "Turbo",
        143: "Gravel",
        152: "Turbo",
        175: "Road",
        176: "Road",
        197: "Road",
        198: "Turbo",
    }
    ride_type = ride_type_map.get(activity_type_id, "Road")

    # Activity name as route
    route_name = activity.get("activityName", "") or "Garmin Sync"

    # Calories
    calories = activity.get("calories", 0)

    # Heart rate
    avg_hr = activity.get("averageHR", 0)

    # Workout fields
    workout_fields = {
        "Date": date_str,
        "Type": "Cycle",
        "Duration (mins)": duration_mins,
        "Distance (km)": round(distance_m / 1000, 1),
        "Source": "Garmin",
        "Notes": f"Auto-synced from Garmin. {route_name}. Avg HR: {avg_hr}bpm. Calories: {calories}.",
    }

    # Cycling fields
    cycling_fields = {
        "Date": date_str,
        "Route": route_name,
        "Distance (miles)": distance_miles,
        "Duration (mins)": duration_mins,
        "Elevation gain (m)": elev_gain_m,
        "Avg speed (mph)": avg_speed_mph,
        "Max speed (mph)": max_speed_mph,
        "Ride type": ride_type,
    }

    return workout_fields, cycling_fields


# ── Main Sync ──────────────────────────────────────────────────────────────────

def sync_garmin():
    """Main sync: fetch Garmin cycling activities → Airtable."""
    print(f"🚴 Garmin Connect sync started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check for Garmin credentials
    try:
        get_env_key("GARMIN_EMAIL")
        get_env_key("GARMIN_PASSWORD")
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Add GARMIN_EMAIL and GARMIN_PASSWORD to /root/.hermes/.env", file=sys.stderr)
        sys.exit(1)

    # Get existing records to avoid duplicates
    print("Checking existing records...")
    existing = get_existing_garmin_ids()
    print(f"  Found {len(existing)} existing cycling records")
    print()

    # Authenticate with Garmin
    print("Connecting to Garmin Connect...")
    client = get_garmin_client()
    print()

    # Fetch cycling activities
    activities = fetch_cycling_activities(client)
    if not activities:
        print("\nNo cycling activities to sync. Done.")
        return []

    # Process each activity
    synced = []
    skipped = 0

    for activity in activities:
        workout_fields, cycling_fields = parse_cycling_activity(activity)

        # Deduplication check
        dedup_key = f"{cycling_fields['Date']}_{cycling_fields['Distance (miles)']}"
        if dedup_key in existing:
            print(f"  ⏭ Skipping duplicate: {cycling_fields['Date']} {cycling_fields['Distance (miles)']}mi")
            skipped += 1
            continue

        print(f"\n  Processing: {cycling_fields['Date']} — {cycling_fields['Distance (miles)']}mi — {cycling_fields['Route']}")

        # Create workout first
        workout_result = create_workout_record(workout_fields)
        if not workout_result:
            print(f"  ✗ Failed to create workout, skipping")
            continue

        workout_id = workout_result["id"]

        # Create cycling record linked to workout
        cycling_fields["Workout"] = [workout_id]
        cycling_result = create_cycling_record(cycling_fields)

        if cycling_result:
            synced.append({
                "date": cycling_fields["Date"],
                "distance_miles": cycling_fields["Distance (miles)"],
                "route": cycling_fields["Route"],
                "workout_id": workout_id,
                "cycling_id": cycling_result["id"],
            })
            # Add to existing set to prevent double-creation in same run
            existing.add(dedup_key)

        time.sleep(0.5)  # Rate limit

    print(f"\n{'='*60}")
    print(f"SYNC COMPLETE: {len(synced)} new rides synced, {skipped} skipped (duplicates)")

    if synced:
        print("\nSynced rides:")
        for s in synced:
            print(f"  • {s['date']} — {s['distance_miles']}mi — {s['route']}")

    return synced


if __name__ == "__main__":
    sync_garmin()
