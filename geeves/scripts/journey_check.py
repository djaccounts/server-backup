#!/usr/bin/env python3
"""
journey_check.py — Ad-hoc journey planner for Geeves.

Usage:
    python3 journey_check.py "King's Cross" --mode cycling
    python3 journey_check.py "King's Cross" --mode tube
    python3 journey_check.py "10 Downing Street" --mode walking
    python3 journey_check.py --tfl-status
    python3 journey_check.py --tfl-status --lines northern,piccadilly
"""

import argparse
import json
import subprocess
import sys
import urllib.request
import urllib.error
import os

HOME_LAT = 51.5567
HOME_LON = -0.1879
MAPS_CLIENT = os.path.expanduser("~/.hermes/skills/productivity/maps/scripts/maps_client.py")
GEVES_SCRIPTS = "/root/Geeves/scripts"


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
                "display": r.get("display_name", destination)
            }
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def osrm_route(from_lat, from_lon, to_lat, to_lon, mode="cycling"):
    """Get route from OSRM."""
    url = f"https://router.project-osrm.org/route/v1/{mode}/{from_lon},{from_lat};{to_lon},{to_lat}?overview=false"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("code") == "Ok":
                route = data["routes"][0]
                return {
                    "duration_mins": round(route["duration"] / 60, 1),
                    "distance_km": round(route["distance"] / 1000, 1),
                    "straight_km": round(
                        ((to_lat - from_lat)**2 + (to_lon - from_lon)**2)**0.5 * 111, 1
                    )
                }
    except Exception as e:
        pass
    return None


def tfl_request(url):
    """Make a TfL API request with proper headers."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Geeves-Agent/1.0",
        "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def tfl_line_status(lines=None):
    """Get TfL line status. Optionally filter to specific lines."""
    try:
        data = tfl_request("https://api.tfl.gov.uk/Line/Mode/tube/Status")
    except Exception as e:
        return {"error": f"TfL API error: {e}", "lines": []}

    results = []
    for line in data:
        name = line.get("name", "Unknown")
        if lines and name.lower() not in [l.lower() for l in lines]:
            continue
        statuses = line.get("lineStatuses", [])
        if statuses:
            status = statuses[0]
            results.append({
                "line": name,
                "status": status.get("statusSeverityDescription", "Unknown"),
                "severity": status.get("statusSeverity", 0),
                "disruption": status.get("disruption", {}).get("description", "") if status.get("disruption") else ""
            })

    return {"lines": results, "error": None}


def tfl_journey(from_lat, from_lon, to_lat, to_lon):
    """Get TfL journey plan."""
    url = f"https://api.tfl.gov.uk/Journey/JourneyResults/{from_lat},{from_lon}/to/{to_lat},{to_lon}"
    try:
        data = tfl_request(url)
        journeys = data.get("journeys", [])
        if journeys:
                j = journeys[0]
                return {
                    "duration_mins": j.get("duration", 0),
                    "legs": [
                        {
                            "mode": leg.get("mode", {}).get("name", "?"),
                            "instruction": leg.get("instruction", {}).get("summary", "?"),
                            "duration": leg.get("duration", 0)
                        }
                        for leg in j.get("legs", [])
                    ]
                }
    except Exception as e:
        pass
    return None


def format_journey_result(dest_name, osrm_data, tfl_data, mode):
    """Format journey result for display."""
    lines = [f"🚲 **{dest_name}**" if mode == "cycling" else f"🚇 **{dest_name}**"]

    if osrm_data:
        lines.append(f"  • {osrm_data['duration_mins']} mins ({osrm_data['distance_km']} km) by {mode}")

    if tfl_data and tfl_data.get("legs"):
        total = tfl_data["duration_mins"]
        lines.append(f"  • {total} mins by transit:")
        for leg in tfl_data["legs"]:
            lines.append(f"    - {leg['instruction']} ({leg['duration']} mins)")

    return "\n".join(lines)


def format_tfl_status(tfl_data):
    """Format TfL status for display."""
    if tfl_data.get("error"):
        return f"⚠️ {tfl_data['error']}"

    lines = ["🚇 **TfL Line Status**"]
    for line in tfl_data.get("lines", []):
        emoji = "✅" if line["severity"] == 10 else "⚠️" if line["severity"] >= 5 else "🔴"
        lines.append(f"  {emoji} {line['line']}: {line['status']}")
        if line.get("disruption"):
            lines.append(f"     {line['disruption'][:100]}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Geeves Journey Checker")
    parser.add_argument("destination", nargs="?", help="Where you're going")
    parser.add_argument("--mode", default="cycling", choices=["cycling", "walking", "driving", "tube", "bus"],
                       help="Transport mode (default: cycling)")
    parser.add_argument("--tfl-status", action="store_true", help="Show TfL line status")
    parser.add_argument("--lines", help="Comma-separated list of TfL lines to check")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--from-lat", type=float, help="Override origin latitude")
    parser.add_argument("--from-lon", type=float, help="Override origin longitude")

    args = parser.parse_args()

    origin_lat = args.from_lat or HOME_LAT
    origin_lon = args.from_lon or HOME_LON

    # TfL status only
    if args.tfl_status and not args.destination:
        lines_filter = args.lines.split(",") if args.lines else None
        tfl = tfl_line_status(lines_filter)
        if args.json:
            print(json.dumps(tfl, indent=2))
        else:
            print(format_tfl_status(tfl))
        return

    # Journey planning
    if not args.destination:
        parser.print_help()
        sys.exit(1)

    # Geocode destination
    geo = geocode(args.destination)
    if not geo:
        print(f"❌ Could not geocode: {args.destination}")
        print("Try a more specific address or landmark name.")
        sys.exit(1)

    dest_lat = geo["lat"]
    dest_lon = geo["lon"]
    dest_name = geo["name"]

    result = {
        "destination": dest_name,
        "destination_display": geo["display"],
        "mode": args.mode,
        "osrm": None,
        "tfl": None
    }

    # OSRM for cycling/walking/driving
    if args.mode in ("cycling", "walking", "driving"):
        result["osrm"] = osrm_route(origin_lat, origin_lon, dest_lat, dest_lon, args.mode)

    # TfL for tube/bus
    if args.mode in ("tube", "bus"):
        result["tfl"] = tfl_journey(origin_lat, origin_lon, dest_lat, dest_lon)
        # Also get line status
        tfl_status = tfl_line_status()
        result["tfl_line_status"] = tfl_status

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_journey_result(dest_name, result["osrm"], result["tfl"], args.mode))
        if result.get("tfl_line_status"):
            print()
            print(format_tfl_status(result["tfl_line_status"]))


if __name__ == "__main__":
    main()
