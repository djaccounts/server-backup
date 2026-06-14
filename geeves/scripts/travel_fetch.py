#!/usr/bin/env python3
"""
travel_fetch.py — Travel data fetcher for the Geeves morning digest.

Reads today's Google Calendar events with locations, cross-references Routes table,
gets live OSRM routing + TfL status, and outputs a JSON travel briefing.

Usage:
    python3 travel_fetch.py
    python3 travel_fetch.py --json    # raw JSON output
"""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

HOME_LAT = 51.5567
HOME_LON = -0.1879
HOME_NAME = "Home"
MAPS_CLIENT = os.path.expanduser("~/.hermes/skills/productivity/maps/scripts/maps_client.py")
GEVES_SCRIPTS = "/root/Geeves/scripts"
GOOGLE_API = os.path.expanduser("~/.hermes/skills/productivity/google-workspace/scripts/google_api.py")


# ── Google Calendar ──────────────────────────────────────────────────────────

def get_today_events():
    """Get today's Google Calendar events with locations using google_api CLI."""
    try:
        result = subprocess.run(
            [sys.executable, GOOGLE_API, "calendar", "list", "--today", "--json"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return []

        events_data = json.loads(result.stdout)
        events = []
        for item in events_data:
            location = item.get("location", "")
            if not location:
                continue
            events.append({
                "summary": item.get("summary", "Event"),
                "location": location,
                "start": item.get("start", {}).get("dateTime", item.get("start", {}).get("date", "")),
            })
        return events

    except Exception as e:
        print(f"Warning: Could not fetch calendar events: {e}", file=sys.stderr)
        return []


# ── Baserow Routes ───────────────────────────────────────────────────────────

def get_active_routes():
    """Get active routes from Baserow."""
    result = subprocess.run(
        [sys.executable, f"{GEVES_SCRIPTS}/baserow_api.py", "list-rows", "Routes", "--limit", "50"],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        return []
    try:
        rows = json.loads(result.stdout)
        return [r for r in rows if r.get("Active", False)]
    except (json.JSONDecodeError, KeyError):
        return []


# ── Geocoding ────────────────────────────────────────────────────────────────

def geocode(destination):
    """Geocode a destination using the maps skill."""
    result = subprocess.run(
        [sys.executable, MAPS_CLIENT, "search", destination],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        results = data.get("results", [])
        if results:
            r = results[0]
            return {
                "name": r.get("name", destination),
                "lat": float(r["lat"]),
                "lon": float(r["lon"]),
            }
    except (json.JSONDecodeError, KeyError):
        pass
    return None


# ── OSRM Routing ─────────────────────────────────────────────────────────────

def osrm_route(from_lat, from_lon, to_lat, to_lon, mode="cycling"):
    """Get route from OSRM."""
    url = (
        f"https://router.project-osrm.org/route/v1/{mode}"
        f"/{from_lon},{from_lat};{to_lon},{to_lat}?overview=false"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Geeves-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("code") == "Ok":
                route = data["routes"][0]
                return {
                    "duration_mins": round(route["duration"] / 60, 1),
                    "distance_km": round(route["distance"] / 1000, 1),
                }
    except Exception:
        pass
    return None


# ── TfL Status ───────────────────────────────────────────────────────────────

def tfl_line_status():
    """Get TfL tube line status."""
    try:
        req = urllib.request.Request(
            "https://api.tfl.gov.uk/Line/Mode/tube/Status",
            headers={"User-Agent": "Geeves-Agent/1.0", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        lines = []
        for line in data:
            statuses = line.get("lineStatuses", [])
            if statuses:
                s = statuses[0]
                lines.append({
                    "line": line.get("name", "?"),
                    "status": s.get("statusSeverityDescription", "?"),
                    "severity": s.get("statusSeverity", 10),
                })
        return lines
    except Exception:
        return []


# ── Main Logic ───────────────────────────────────────────────────────────────

def build_travel_briefing():
    """Build the travel briefing for today."""
    events = get_today_events()

    if not events:
        return {"has_travel": False, "journeys": [], "tfl_summary": ""}

    routes = get_active_routes()
    tfl_lines = tfl_line_status()
    journeys = []

    for event in events:
        location = event["location"]
        summary = event["summary"]
        start = event.get("start", "")

        # Try to match against known routes
        matched_route = None
        for route in routes:
            route_to = route.get("To", "")
            if route_to and route_to.lower() in location.lower():
                matched_route = route
                break

        # Geocode the destination
        geo = geocode(location)
        if not geo:
            journeys.append({
                "destination": location,
                "event_summary": summary,
                "event_time": start,
                "error": "Could not geocode destination",
            })
            continue

        # Determine mode
        mode = "cycling"  # David's default
        if matched_route:
            mode_raw = matched_route.get("Default Mode", "Cycle")
            mode_map = {
                "Tube": "driving",
                "Bus": "driving",
                "Walk": "walking",
                "Cycle": "cycling",
                "Train": "driving",
                "Drive": "driving",
            }
            mode = mode_map.get(mode_raw, "cycling")

        # Get OSRM route
        osrm = osrm_route(HOME_LAT, HOME_LON, geo["lat"], geo["lon"], mode)

        # Check TfL if relevant
        tfl_disruptions = []
        if mode == "driving":
            tfl_disruptions = [
                f"{l['line']}: {l['status']}"
                for l in tfl_lines
                if l["severity"] < 7
            ]

        journey = {
            "destination": geo["name"],
            "full_address": location,
            "event_summary": summary,
            "event_time": start,
            "mode": mode,
            "osrm": osrm,
            "tfl_disruptions": tfl_disruptions[:3],
            "route_notes": matched_route.get("Notes", "") if matched_route else "",
        }
        journeys.append(journey)

    # Build TfL summary
    problems = [l for l in tfl_lines if l["severity"] < 10]
    if problems:
        parts = ", ".join(f'{l["line"]} ({l["status"]})' for l in problems[:3])
        tfl_summary = f"TfL: {parts}"
    else:
        tfl_summary = "All Tube lines good service"

    return {
        "has_travel": True,
        "journeys": journeys,
        "tfl_summary": tfl_summary,
        "tfl_lines": tfl_lines,
    }


def format_digest_section(data):
    """Format travel data as a digest section."""
    if not data["has_travel"]:
        return ""

    lines = ["## 🚲 Travel"]
    for j in data["journeys"]:
        time_str = ""
        if j.get("event_time"):
            try:
                t = j["event_time"]
                if "T" in t:
                    time_str = t.split("T")[1][:5]
            except Exception:
                pass

        dest = j["destination"]
        event = j.get("event_summary", "")
        header = f"**{dest}**"
        if event:
            header += f" ({event})"
        if time_str:
            header += f" @ {time_str}"
        lines.append(header)

        if j.get("error"):
            lines.append(f"  ⚠️ {j['error']}")
            continue

        osrm = j.get("osrm")
        mode = j.get("mode", "cycling")
        mode_emoji = {"cycling": "🚲", "walking": "🚶", "driving": "🚗"}.get(mode, "🚲")

        if osrm:
            lines.append(f"  {mode_emoji} {osrm['duration_mins']} mins ({osrm['distance_km']} km) by {mode}")

        if j.get("route_notes"):
            lines.append(f"  📝 {j['route_notes']}")

        if j.get("tfl_disruptions"):
            for d in j["tfl_disruptions"]:
                lines.append(f"  ⚠️ {d}")

    lines.append(f"\n{data['tfl_summary']}")
    return "\n".join(lines)


def main():
    """Main entry point."""
    data = build_travel_briefing()

    if "--json" in sys.argv:
        print(json.dumps(data, indent=2))
    else:
        section = format_digest_section(data)
        if section:
            print(section)
        else:
            print("No travel today.")


if __name__ == "__main__":
    main()
