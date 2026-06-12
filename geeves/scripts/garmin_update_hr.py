#!/usr/bin/env python3
"""
garmin_update_hr.py — Update existing Baserow cycling records with HR and calorie data from Garmin.

Fetches all cycling activities from Garmin (summary data only — fast),
then updates matching Baserow records with avgHR, maxHR, and calories.
"""

import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

BASEROW_BASE = "http://77.68.33.121/api"
CYCLING_TABLE_ID = 396


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
    all_results = []
    url = f"{BASEROW_BASE}/database/rows/table/{table_id}/?user_field_names=true&size=200"
    while url:
        result = baserow_get(url)
        all_results.extend(result.get("results", []))
        url = result.get("next")
    return all_results


def baserow_patch(row_id, data):
    token = get_env_key("BASEROW_API_TOKEN")
    url = f"{BASEROW_BASE}/database/rows/table/{CYCLING_TABLE_ID}/{row_id}/?user_field_names=true"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }, method="PATCH")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  PATCH ERROR {e.code}: {err}")
        return None


def garmin_login():
    from garminconnect import Garmin
    email = get_env_key("GARMIN_EMAIL")
    password = get_env_key("GARMIN_PASSWORD")
    client = Garmin(email, password)
    try:
        client.login()
    except Exception as e:
        if "429" in str(e) or "rate" in str(e).lower():
            time.sleep(60)
            client.login()
        else:
            raise
    return client


def main():
    print("🚴 Updating cycling records with HR + calorie data...")
    print()

    client = garmin_login()
    print("✅ Logged in")

    # Load existing Baserow records
    print("Loading Baserow records...")
    existing = baserow_get_all(CYCLING_TABLE_ID)
    print(f"  {len(existing)} records")

    # Build lookup: date+route -> (row_id, has_hr)
    baserow_lookup = {}
    for r in existing:
        date = r.get("Date", "")
        route = r.get("Route", "") or ""
        key = (date, route)
        baserow_lookup[key] = r

    # Fetch all cycling from Garmin
    print("\nFetching all cycling activities from Garmin...")
    all_cycling = []
    offset = 0
    batch_size = 100
    cycling_types = ("cycling", "road_biking", "mountain_biking", "gravel_cycling", "virtual_ride", "indoor_cycling")

    while True:
        try:
            activities = client.get_activities(offset, batch_size)
        except Exception as e:
            if "429" in str(e):
                time.sleep(60)
                continue
            break
        if not activities:
            break
        batch = [a for a in activities if a.get("activityType", {}).get("typeKey", "") in cycling_types]
        all_cycling.extend(batch)
        print(f"  Offset {offset}: {len(batch)} cycling (total: {len(all_cycling)})")
        offset += batch_size
        time.sleep(0.5)

    print(f"\n✅ {len(all_cycling)} cycling activities to process")

    updated = 0
    skipped_no_hr = 0
    skipped_no_match = 0
    errors = 0

    for activity in all_cycling:
        date = activity.get("startTimeLocal", "")[:10]
        route = activity.get("activityName", "")
        key = (date, route)

        if key not in baserow_lookup:
            skipped_no_match += 1
            continue

        row = baserow_lookup[key]
        row_id = row["id"]

        avg_hr = activity.get("averageHR")
        max_hr = activity.get("maxHR")
        calories = activity.get("calories")

        if not avg_hr and not calories:
            skipped_no_hr += 1
            continue

        update_data = {}
        if avg_hr:
            update_data["Avg heart rate"] = round(avg_hr)
        if max_hr:
            update_data["Max heart rate"] = round(max_hr)
        if calories:
            update_data["Calories burned"] = round(calories)

        if update_data:
            result = baserow_patch(row_id, update_data)
            if result:
                print(f"  ✅ {date} — {route}: HR {avg_hr}/{max_hr}, {calories} cal")
                updated += 1
            else:
                errors += 1

        time.sleep(0.3)

    print(f"\n{'='*50}")
    print(f"Updated: {updated}")
    print(f"Skipped (no HR data): {skipped_no_hr}")
    print(f"Skipped (no match): {skipped_no_match}")
    print(f"Errors: {errors}")


if __name__ == "__main__":
    main()
