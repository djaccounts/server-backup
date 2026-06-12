#!/usr/bin/env python3
"""
upcoming_occasions.py — Fetch upcoming birthdays/anniversaries from Baserow.

Usage:
    python3 upcoming_occasions.py [--days 14]
    python3 upcoming_occasions.py --json
"""
import json, os, sys, subprocess, datetime
import urllib.request, urllib.error

ENV_PATH = os.path.expanduser("~/.hermes/.env")
BASE_URL = "http://77.68.33.121"
OCCASIONS_TABLE_ID = 403

def get_token():
    r = subprocess.run(["grep", "BASEROW_API_TOKEN", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def baserow_get(path):
    token = get_token()
    url = BASE_URL + path
    req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def get_all_rows(table_id):
    all_rows = []
    page = 1
    while True:
        result = baserow_get(f"/api/database/rows/table/{table_id}/?size=100&page={page}&user_field_names=true")
        batch = result.get("results", [])
        if not batch:
            break
        all_rows.extend(batch)
        if not result.get("next"):
            break
        page += 1
    return all_rows

def extract_link_id(field_val):
    """Extract row ID from a link_row field value."""
    if isinstance(field_val, list) and field_val:
        item = field_val[0]
        if isinstance(item, dict):
            return item.get("id")
        return item
    if isinstance(field_val, dict):
        return field_val.get("id")
    return field_val

def extract_select_value(field_val):
    """Extract value from a single_select field value."""
    if isinstance(field_val, dict):
        return field_val.get("value", "")
    return field_val or ""

def get_upcoming_occasions(days_ahead=14):
    today = datetime.date.today()

    occasions = get_all_rows(OCCASIONS_TABLE_ID)
    people_rows = get_all_rows(359)

    people_map = {}
    for p in people_rows:
        pid = p.get("id")
        if pid:
            people_map[str(pid)] = p.get("Name", "Unknown")

    upcoming = []
    for occ in occasions:
        date_str = occ.get("Date", "")
        if not date_str:
            continue

        try:
            parts = date_str.split("-")
            if len(parts) >= 2:
                month, day = int(parts[-2]), int(parts[-1])
            else:
                continue
        except (ValueError, IndexError):
            continue

        try:
            datetime.date(2000, month, day)
        except ValueError:
            continue

        occ_this_year = datetime.date(today.year, month, day)
        delta = (occ_this_year - today).days
        if delta < 0:
            try:
                occ_next = datetime.date(today.year + 1, month, day)
                delta = (occ_next - today).days
            except ValueError:
                continue

        if 0 <= delta <= days_ahead:
            pids_raw = occ.get("Person", [])
            person_id = extract_link_id(pids_raw)
            person_name = people_map.get(str(person_id), "Unknown") if person_id else "Unknown"

            occ_type = extract_select_value(occ.get("Occasion Type"))

            upcoming.append({
                "date": f"{today.year if occ_this_year.year == today.year else today.year + 1}-{month:02d}-{day:02d}",
                "days_until": delta,
                "type": occ_type,
                "person_name": person_name,
                "notes": occ.get("Extra Notes", ""),
            })

    upcoming.sort(key=lambda x: x["days_until"])
    return upcoming

def format_upcoming(days_ahead=14):
    upcoming = get_upcoming_occasions(days_ahead)
    if not upcoming:
        return ""

    lines = []
    for occ in upcoming:
        days = occ["days_until"]

        if days == 0:
            emoji = "🎉"
            when = "TODAY"
        elif days == 1:
            emoji = "🎈"
            when = "tomorrow"
        elif days <= 7:
            emoji = "📅"
            when = f"in {days} days"
        else:
            emoji = "🗓️"
            when = f"in {days} days"

        line = f"- {emoji} **{occ['person_name']}**'s {occ['type']} — {when}"
        lines.append(line)

    return "### Upcoming Occasions\n\n" + "\n".join(lines)

if __name__ == "__main__":
    days = 14
    json_output = "--json" in sys.argv

    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])

    if json_output:
        upcoming = get_upcoming_occasions(days)
        print(json.dumps(upcoming, indent=2))
    else:
        print(format_upcoming(days))
