#!/usr/bin/env python3
"""
upcoming_occasions.py — Fetch upcoming birthdays/anniversaries from Baserow.

Queries the Occasions table for events happening in the next N days.
Outputs a formatted summary for the morning digest.

Usage:
    python3 upcoming_occcasions.py [--days 14]
    python3 upcoming_occasions.py --json
"""
import json, os, sys, subprocess, datetime
import urllib.request, urllib.error

ENV_PATH = os.path.expanduser("~/.hermes/.env")
BASE_URL = "http://77.68.33.121"
DB_ID = 132
OCCASIONS_TABLE_ID = 403

def get_token():
    r = subprocess.run(["grep", "BASEROW_API_TOKEN", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def baserow_get(path):
    token = get_token()
    url = BASE_URL + path
    req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

def get_upcoming_occasions(days_ahead=14):
    """Get occasions happening in the next N days."""
    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=days_ahead)
    
    # Fetch all occasions (paginated)
    all_occasions = []
    page = 1
    while True:
        result = baserow_get(f"/api/database/rows/table/{OCCASIONS_TABLE_ID}/?size=100&page={page}")
        batch = result.get("results", [])
        all_occasions.extend(batch)
        if not result.get("next") or len(batch) == 0:
            break
        page += 1
    
    # Resolve person names (paginated)
    people_map = {}
    page = 1
    while True:
        people_result = baserow_get(f"/api/database/rows/table/359/?size=100&page={page}")
        for p in people_result.get("results", []):
            people_map[str(p.get("id"))] = p.get("Name", "Unknown")
        if not people_result.get("next") or len(people_result.get("results", [])) == 0:
            break
        page += 1
    
    # Filter upcoming
    upcoming = []
    for occ in all_occasions:
        date_str = occ.get("Date", "")
        if not date_str:
            continue
        
        try:
            parts = date_str.split("-")
            if len(parts) == 3:
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                # Use 1900 as placeholder year if needed
                if year == 0 or year == 1900:
                    year = today.year
                occ_date = datetime.date(year, month, day)
            elif len(parts) == 2:
                month, day = int(parts[0]), int(parts[1])
                occ_date = datetime.date(today.year, month, day)
            else:
                continue
            
            # Check if within window (handle year wrapping)
            delta = (occ_date - today).days
            if delta < 0:
                # Try next year
                occ_date_next = occ_date.replace(year=occ_date.year + 1)
                delta = (occ_date_next - today).days
            
            if 0 <= delta <= days_ahead:
                person_id = occ.get("Person", [])
                person_name = "Unknown"
                if person_id and isinstance(person_id, list):
                    # We need to look up the person name
                    person_name = str(person_id[0])  # Will resolve below
                
                upcoming.append({
                    "date": occ_date.isoformat(),
                    "days_until": delta,
                    "type": occ.get("Occasion Type", "Other"),
                    "person_id": person_id,
                    "notes": occ.get("Extra Notes", ""),
                })
        except (ValueError, TypeError):
            continue
    
    # Sort by days until (soonest first)
    upcoming.sort(key=lambda x: x["days_until"])
    
    return upcoming

def format_upcoming(days_ahead=14):
    """Format upcoming occasions for the digest."""
    upcoming = get_upcoming_occasions(days_ahead)
    if not upcoming:
        return "No upcoming occasions in the next {} days.".format(days_ahead)
    
    lines = ["### 🎂 Upcoming Occasions"]
    for occ in upcoming:
        days = occ["days_until"]
        date_str = occ["date"]
        
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
            when = f"in {days} days ({date_str})"
        
        line = f"- {emoji} **{occ['person_name']}**'s {occ['type']} — {when}"
        if occ.get("notes"):
            line += f" ({occ['notes'][:60]})"
        lines.append(line)
    
    return "\n".join(lines)

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
