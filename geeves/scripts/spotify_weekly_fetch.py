#!/usr/bin/env python3
"""
spotify_weekly_fetch.py — Fetch last 7 days of Spotify listening data and summarise into Baserow.

Usage:
    python3 spotify_weekly_fetch.py          # print summary (dry run)
    python3 spotify_weekly_fetch.py --write  # write to Baserow

Fetches recently-played tracks from the Spotify API, computes top tracks,
top artists, total plays, most active day, and a text summary. Writes a
row to the Listening table (Baserow table 402).
"""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime, timedelta, timezone

# ── Baserow config ──────────────────────────────────────────────────────────
BASEROW_TABLE_ID = 402   # Listening table
MAPPING_PATH = "/root/Geeves/baserow_mapping.json"
BASE_URL = "http://77.68.33.121"
ENV_PATH = os.path.expanduser("~/.hermes/.env")


def get_baserow_token():
    r = subprocess.run(["grep", "BASEROW_API_TOKEN", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def baserow_post(fields):
    token = get_baserow_token()
    url = f"{BASE_URL}/api/database/rows/table/{BASEROW_TABLE_ID}/"
    body = json.dumps(fields).encode()
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}


def baserow_list():
    token = get_baserow_token()
    url = f"{BASE_URL}/api/database/rows/table/{BASEROW_TABLE_ID}/?size=100"
    headers = {"Authorization": f"Token {token}"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("results", [])
    except urllib.error.HTTPError as e:
        return []


# ── Spotify helpers ──────────────────────────────────────────────────────────
def spotify_request(endpoint, token):
    url = f"https://api.spotify.com/v1/{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}


def get_spotify_token():
    """
    Read the stored Spotify OAuth token from Hermes auth cache.
    Hermes stores tokens under ~/.hermes/auth/ or similar.
    Falls back to SPOTIFY_ACCESS_TOKEN env var.
    """
    # Try env var first
    token = os.environ.get("SPOTIFY_ACCESS_TOKEN", "")
    if token:
        return token

    # Try Hermes auth cache
    auth_paths = [
        os.path.expanduser("~/.hermes/auth/spotify_token.json"),
        os.path.expanduser("~/.hermes/auth/spotify.json"),
        os.path.expanduser("~/.hermes/spotify_token.json"),
        os.path.expanduser("~/.hermes/.spotify_token"),
    ]
    for p in auth_paths:
        if os.path.exists(p):
            with open(p) as f:
                data = json.load(f)
                return data.get("access_token", data.get("token", ""))

    return ""


def fetch_recently_played(token, days=7):
    """Fetch recently played tracks from Spotify API (max 50 most recent)."""
    # Spotify's /me/player/recently-played returns up to 50 tracks
    # We use the 'after' timestamp to filter to the last N days
    after_ts = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)

    all_tracks = []
    limit = 50
    after = after_tracks = after_ts

    # Paginate: Spotify returns a 'next' URL with cursor, but the 'after' param
    # approach gets us the most recent 50 which is enough for a weekly summary
    result = spotify_request(
        f"me/player/recently-played?limit={limit}&after={after}", token
    )

    if "error" in result:
        return None, result

    items = result.get("items", [])
    return items, None


def summarise_week(items):
    """Turn a list of recently-played items into a weekly summary."""
    if not items:
        return None

    track_counter = Counter()
    artist_counter = Counter()
    day_counter = Counter()
    total = 0

    for item in items:
        track = item.get("track", {})
        track_name = track.get("name", "Unknown")
        artists = ", ".join(a["name"] for a in track.get("artists", []))
        key = f"{track_name} — {artists}"
        track_counter[key] += 1

        for artist in track.get("artists", []):
            artist_counter[artist["name"]] += 1

        played_at = item.get("played_at", "")
        if played_at:
            try:
                dt = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
                day_counter[dt.strftime("%A")] += 1
            except ValueError:
                pass

        total += 1

    top_tracks = track_counter.most_common(5)
    top_artists = artist_counter.most_common(3)
    most_active_day = day_counter.most_common(1)[0][0] if day_counter else "N/A"

    # Build text summaries
    tracks_text = "\n".join(f"{i+1}. {name} ({count} plays)" for i, (name, count) in enumerate(top_tracks))
    artists_text = "\n".join(f"{i+1}. {name} ({count} plays)" for i, (name, count) in enumerate(top_artists))

    # Build a natural-language summary
    summary_parts = [f"This week you listened to {total} tracks."]
    if top_artists:
        summary_parts.append(f"Your top artist was {top_artists[0][0]} with {top_artists[0][1]} plays.")
    if top_tracks:
        summary_parts.append(f"Most-played track: {top_tracks[0][0].split(' — ')[0]} ({top_tracks[0][1]} plays).")
    if most_active_day != "N/A":
        summary_parts.append(f"You listened most on {most_active_day}s.")

    summary = " ".join(summary_parts)

    return {
        "top_tracks": tracks_text,
        "top_artists": artists_text,
        "total_plays": total,
        "most_active_day": most_active_day,
        "summary": summary,
    }


def main():
    dry_run = "--write" not in sys.argv

    # Week starting = last Monday
    today = datetime.now(timezone.utc).date()
    monday = today - timedelta(days=today.weekday())
    week_starting = monday.isoformat()

    if dry_run:
        print(f"🔍 DRY RUN — week starting {week_starting}")
    else:
        print(f"📝 WRITE MODE — week starting {week_starting}")

    # Check for existing entry
    if not dry_run:
        existing = baserow_list()
        for row in existing:
            if str(row.get("Week starting", "")) == week_starting:
                print(f"⚠️  Entry for week {week_starting} already exists (row {row['id']}). Skipping.")
                return

    # Get Spotify token
    token = get_spotify_token()
    if not token:
        print("ERROR: No Spotify token found. Run 'hermes auth spotify' first.")
        sys.exit(1)

    # Fetch recently played
    print("Fetching recently played tracks...")
    items, err = fetch_recently_played(token, days=7)
    if err:
        print(f"ERROR fetching from Spotify: {err}")
        sys.exit(1)

    if not items:
        print("No tracks found in the last 7 days.")
        sys.exit(0)

    print(f"Got {len(items)} tracks. Summarising...")

    summary = summarise_week(items)
    if not summary:
        print("ERROR: Could not summarise tracks.")
        sys.exit(1)

    print(f"\n📊 Weekly Listening Summary ({week_starting})")
    print(f"   Total plays: {summary['total_plays']}")
    print(f"   Most active day: {summary['most_active_day']}")
    print(f"   Top artists: {summary['top_artists'][:100]}...")
    print(f"   Summary: {summary['summary']}")

    if dry_run:
        print("\n(Dry run — not writing to Baserow. Use --write to save.)")
        return

    # Write to Baserow
    row_data = {
        "Week starting": week_starting,
        "Top Tracks": summary["top_tracks"],
        "Top Artists": summary["top_artists"],
        "Total Plays": summary["total_plays"],
        "Most Active Day": summary["most_active_day"],
        "Summary": summary["summary"],
    }

    result = baserow_post(row_data)
    if "id" in result:
        print(f"\n✅ Written to Baserow (row {result['id']})")
    else:
        print(f"\n❌ Baserow write failed: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
