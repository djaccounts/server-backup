#!/usr/bin/env python3
"""
weekly_digest_fetch.py — Fetch the past 7 days of data for the weekly digest.
Writes summary records to Airtable for the weekly digest to read.

Usage:
    python3 weekly_digest_fetch.py        # dry run (print what would be written)
    python3 weekly_digest_fetch.py --write  # write to Airtable
"""

import subprocess, sys, json, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

ENV_PATH = "/root/.hermes/.env"
BASE = "appzvmonQXs4x2AlL"

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
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def fetch_records(table, formula="", max_records=100):
    """Fetch records from Airtable with optional filter."""
    import urllib.parse
    encoded_table = urllib.parse.quote(table)
    params = f"?max_records={max_records}"
    if formula:
        params += f"&filterByFormula={urllib.parse.quote(formula)}"
    data, status = api("GET", f"{BASE}/{encoded_table}{params}")
    if status == 200:
        return data.get("records", [])
    return []

def get_date_range():
    """Return (week_start, week_end, today_iso, week_start_iso)."""
    today = datetime.now(timezone.utc)
    # Week starts Monday
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday + 7)  # Last week's Monday
    week_end = week_start + timedelta(days=6)  # Last week's Sunday
    # Current week (for intentions)
    current_week_start = today - timedelta(days=days_since_monday)
    return (
        today.strftime("%Y-%m-%d"),
        week_start.strftime("%Y-%m-%d"),
        week_end.strftime("%Y-%m-%d"),
        current_week_start.strftime("%Y-%m-%d"),
    )

def gather_todos(week_start_iso, week_end_iso, write):
    """Summarise todos created/completed in the last 7 days."""
    all_todos = fetch_records("Todos", max_records=100)
    week_todos = []
    completed_todos = []
    pending_todos = []

    for rec in all_todos:
        f = rec["fields"]
        date_val = f.get("Date", f.get("Created", ""))
        status = f.get("Status", "")
        if date_val >= week_start_iso and date_val <= week_end_iso:
            week_todos.append(f)
            if status in ("Done", "Cancelled"):
                completed_todos.append(f)
            else:
                pending_todos.append(f)

    print(f"  📋 Todos: {len(week_todos)} created, {len(completed_todos)} completed, {len(pending_todos)} pending")
    return {
        "created": week_todos,
        "completed": completed_todos,
        "pending": pending_todos,
    }

def gather_fitness(week_start_iso, write):
    """Summarise workouts in the last 7 days."""
    all_workouts = fetch_records("Workouts", max_records=100)
    week_workouts = []
    total_distance = 0
    types = {}

    for rec in all_workouts:
        f = rec["fields"]
        date_val = f.get("Date", "")
        if date_val >= week_start_iso:
            week_workouts.append(f)
            dist = f.get("Distance (km)", 0) or 0
            total_distance += dist
            wtype = f.get("Type", "Unknown")
            types[wtype] = types.get(wtype, 0) + 1

    print(f"  💪 Fitness: {len(week_workouts)} workouts, {total_distance:.1f}km total, types: {types}")
    return {
        "workouts": week_workouts,
        "count": len(week_workouts),
        "total_distance": total_distance,
        "types": types,
    }

def gather_sleep(week_start_iso):
    """Summarise sleep in the last 7 days."""
    all_sleep = fetch_records("Sleep Log", max_records=100)
    week_sleep = []
    total_hours = 0

    for rec in all_sleep:
        f = rec["fields"]
        date_val = f.get("Date", "")
        if date_val >= week_start_iso:
            week_sleep.append(f)
            hours = f.get("Hours slept", 0) or 0
            total_hours += hours

    avg = total_hours / len(week_sleep) if week_sleep else 0
    print(f"  😴 Sleep: {len(week_sleep)} nights, avg {avg:.1f}h")
    return {
        "nights": week_sleep,
        "count": len(week_sleep),
        "avg_hours": avg,
    }

def gather_habits(week_start_iso, write):
    """Summarise habit completion in the last 7 days."""
    all_habit_log = fetch_records("Habit Log", max_records=100)
    all_habits = fetch_records("Habits", max_records=50)

    habit_names = {}
    for rec in all_habits:
        habit_names[rec["id"]] = rec["fields"].get("Habit", "Unknown")

    completed = 0
    total = 0
    habit_counts = {}

    for rec in all_habit_log:
        f = rec["fields"]
        date_val = f.get("Date", "")
        if date_val >= week_start_iso:
            total += 1
            if f.get("Completed", False):
                completed += 1
                # Count per habit
                links = f.get("Habit", [])
                for link in links:
                    name = habit_names.get(link, "Unknown")
                    habit_counts[name] = habit_counts.get(name, 0) + 1

    print(f"  🔄 Habits: {completed}/{total} completed")
    return {
        "completed": completed,
        "total": total,
        "habit_counts": habit_counts,
    }

def gather_intentions(last_week_start_iso, current_week_start_iso, write):
    """
    Fetch last week's intentions (for review) and write suggested new ones.
    Returns (last_week_intentions, suggested_intentions).
    """
    all_intentions = fetch_records("Intentions", max_records=100)
    last_week = []
    current_week = []

    for rec in all_intentions:
        f = rec["fields"]
        ws = f.get("Week starting", "")
        if ws == last_week_start_iso:
            last_week.append({"id": rec["id"], "fields": f})
        elif ws == current_week_start_iso:
            current_week.append({"id": rec["id"], "fields": f})

    print(f"  🎯 Intentions: {len(last_week)} last week, {len(current_week)} already set for this week")

    return last_week, current_week

def write_digest_log(date_str, sections, write):
    """Write a Digest Log entry (Type = Weekly)."""
    content = ", ".join(sections)
    data = {
        "records": [{
            "fields": {
                "Date": date_str,
                "Type": "Weekly",
                "Content": content,
                "Delivered via": "Email",
                "Delivery status": "Pending",
                "Sections included": ", ".join(sections),
            }
        }]
    }
    if write:
        result, status = api("POST", f"{BASE}/Digest Log", data)
        if status == 200:
            print(f"  ✅ Wrote Digest Log entry")
        else:
            print(f"  ❌ Failed to write Digest Log: {json.dumps(result)[:200]}")

def main():
    write = "--write" in sys.argv
    today_iso, week_start_iso, week_end_iso, current_week_iso = get_date_range()
    last_week_start = (datetime.strptime(week_start_iso, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")

    mode = "WRITE" if write else "DRY RUN"
    print(f"\n📅 Weekly Digest Fetch [{mode}]")
    print(f"   Period: {week_start_iso} → {week_end_iso}")
    print(f"   Today:  {today_iso}")
    print()

    # Gather all data
    todos = gather_todos(week_start_iso, week_end_iso, write)
    fitness = gather_fitness(week_start_iso, write)
    sleep = gather_sleep(week_start_iso)
    habits = gather_habits(week_start_iso, write)
    last_intentions, current_intentions = gather_intentions(last_week_start, current_week_iso, write)

    sections = []
    if todos["created"] or todos["completed"]:
        sections.append("Todos")
    if fitness["count"] > 0:
        sections.append("Fitness")
    if sleep["count"] > 0:
        sections.append("Sleep")
    if habits["total"] > 0:
        sections.append("Habits")
    if last_intentions:
        sections.append("Intentions")

    print(f"\n   Sections: {', '.join(sections) if sections else '(none — no data yet)'}")
    print()

    if sections:
        write_digest_log(today_iso, sections, write)
    else:
        print("  ℹ️  No data to write — skipping Digest Log")

    # Return data for the HTML builder
    if not write:
        print("  💡 Run with --write to persist to Airtable")

    return {
        "todos": todos,
        "fitness": fitness,
        "sleep": sleep,
        "habits": habits,
        "last_intentions": last_intentions,
        "current_intentions": current_intentions,
        "sections": sections,
        "dates": {
            "today": today_iso,
            "week_start": week_start_iso,
            "week_end": week_end_iso,
            "current_week_start": current_week_iso,
            "last_week_start": last_week_start,
        },
    }

if __name__ == "__main__":
    main()
