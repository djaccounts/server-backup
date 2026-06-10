#!/usr/bin/env python3
"""
build_weekly_digest_html.py — Build a rich HTML weekly digest from Airtable data.
Outputs HTML that can be emailed inline or converted to PDF via PDFBolt.

Usage:
    python3 build_weekly_digest_html.py              # print HTML to stdout
    python3 build_weekly_digest_html.py --save       # save to /root/Geeves/digests/
"""

import subprocess, sys, json, urllib.request, urllib.error, os
from datetime import datetime, timezone, timedelta

ENV_PATH = "/root/.hermes/.env"
BASE = "appzvmonQXs4x2AlL"
DIGEST_DIR = "/root/Geeves/digests"

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
    today = datetime.now(timezone.utc)
    days_since_monday = today.weekday()
    current_week_start = today - timedelta(days=days_since_monday)
    last_week_start = current_week_start - timedelta(days=7)
    last_week_end = current_week_start - timedelta(days=1)
    return (
        today.strftime("%Y-%m-%d"),
        last_week_start.strftime("%Y-%m-%d"),
        last_week_end.strftime("%Y-%m-%d"),
        current_week_start.strftime("%Y-%m-%d"),
    )

def esc(text):
    """Escape HTML special characters."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def build_html():
    today_iso, last_week_start, last_week_end, current_week_start = get_date_range()
    today = datetime.now(timezone.utc)
    date_str = today.strftime("%A, %B %d, %Y")
    week_range = f"{datetime.strptime(last_week_start, '%Y-%m-%d').strftime('%b %d')} – {datetime.strptime(last_week_end, '%Y-%m-%d').strftime('%b %d, %Y')}"

    # Fetch last week's data
    all_todos = fetch_records("Todos", max_records=100)
    all_workouts = fetch_records("Workouts", max_records=100)
    all_sleep = fetch_records("Sleep Log", max_records=100)
    all_habit_log = fetch_records("Habit Log", max_records=100)
    all_habits = fetch_records("Habits", max_records=50)
    all_intentions = fetch_records("Intentions", max_records=100)
    digest_log = fetch_records("Digest Log", max_records=5)

    # Filter to last week
    def in_week_date(date_val):
        if not date_val:
            return False
        return date_val >= last_week_start and date_val <= last_week_end

    week_todos = [r["fields"] for r in all_todos if in_week_date(r["fields"].get("Date", r["fields"].get("Created", "")))]
    week_completed = [f for f in week_todos if f.get("Status") in ("Done", "Cancelled")]
    week_pending = [f for f in week_todos if f.get("Status") not in ("Done", "Cancelled")]

    week_workouts = [r["fields"] for r in all_workouts if in_week_date(r["fields"].get("Date", ""))]
    week_sleep = [r["fields"] for r in all_sleep if in_week_date(r["fields"].get("Date", ""))]

    week_habit_log = [r["fields"] for r in all_habit_log if in_week_date(r["fields"].get("Date", ""))]
    habit_names = {rec["id"]: rec["fields"].get("Habit", "Unknown") for rec in all_habits}

    last_week_intentions = [r["fields"] for r in all_intentions if r["fields"].get("Week starting") == last_week_start]
    current_intentions = [r["fields"] for r in all_intentions if r["fields"].get("Week starting") == current_week_start]

    # Build HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 680px; margin: 0 auto; padding: 24px; color: #1a1a1a; line-height: 1.6; }}
  h1 {{ font-size: 22px; border-bottom: 2px solid #333; padding-bottom: 8px; }}
  h2 {{ font-size: 16px; color: #444; margin-top: 24px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
  .subtitle {{ color: #666; font-size: 14px; margin-bottom: 24px; }}
  .stat {{ display: inline-block; background: #f0f0f0; border-radius: 6px; padding: 8px 14px; margin: 4px 4px 4px 0; font-size: 13px; }}
  .stat strong {{ font-size: 18px; display: block; }}
  .item {{ padding: 6px 0; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
  .done {{ text-decoration: line-through; color: #999; }}
  .tag {{ display: inline-block; background: #e8f5e9; color: #2e7d32; border-radius: 3px; padding: 1px 6px; font-size: 11px; margin-left: 4px; }}
  .tag-missed {{ background: #ffebee; color: #c62828; }}
  .tag-achieved {{ background: #e8f5e9; color: #2e7d32; }}
  .tag-carried {{ background: #fff3e0; color: #e65100; }}
  .intention {{ padding: 8px 0; border-bottom: 1px solid #f0f0f0; }}
  .intention-type {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
  .reflection {{ font-style: italic; color: #666; font-size: 13px; margin-top: 2px; }}
  .empty {{ color: #999; font-style: italic; font-size: 13px; }}
  .footer {{ margin-top: 32px; padding-top: 12px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }}
</style>
</head>
<body>
<h1>📅 Weekly Digest</h1>
<p class="subtitle">{week_range} · Generated {date_str}</p>
"""

    # ── Intentions Review ──
    if last_week_intentions:
        html += "<h2>🎯 Last Week's Intentions</h2>\n"
        for intent in last_week_intentions:
            status = intent.get("Status", "Set")
            status_class = {"Achieved": "tag-achieved", "Missed": "tag-missed", "Carried over": "tag-carried"}.get(status, "")
            html += f'<div class="intention">'
            html += f'<div class="intention-type">{esc(intent.get("Type", ""))}</div>'
            html += f'<strong>{esc(intent.get("Intention", ""))}</strong>'
            html += f' <span class="tag {status_class}">{esc(status)}</span>'
            if intent.get("Reflection"):
                html += f'<div class="reflection">{esc(intent["Reflection"])}</div>'
            html += '</div>\n'
        html += "\n"

    # ── This Week's Intentions ──
    if current_intentions:
        html += "<h2>🎯 This Week's Intentions</h2>\n"
        for intent in current_intentions:
            html += f'<div class="intention">'
            html += f'<div class="intention-type">{esc(intent.get("Type", ""))}</div>'
            html += f'<strong>{esc(intent.get("Intention", ""))}</strong>'
            html += f' <span class="tag">{esc(intent.get("Source", ""))}</span>'
            html += '</div>\n'
        html += "\n"

    # ── Todos ──
    if week_todos:
        html += f"<h2>📋 Tasks <span style='font-weight:normal;color:#886'>({len(week_completed)}/{len(week_todos)} completed)</span></h2>\n"
        if week_completed:
            html += "<p><strong>✅ Completed</strong></p>\n"
            for t in week_completed:
                html += f'<div class="item done">{esc(t.get("Task", ""))}</div>\n'
        if week_pending:
            html += "<p><strong>⏳ Still pending</strong></p>\n"
            for t in week_pending:
                status = t.get("Status", "")
                html += f'<div class="item">{esc(t.get("Task", ""))} <span class="tag">{esc(status)}</span></div>\n'
        html += "\n"

    # ── Fitness ──
    if week_workouts:
        total_dist = sum(f.get("Distance (km)", 0) or 0 for f in week_workouts)
        types = {}
        for f in week_workouts:
            t = f.get("Type", "Unknown")
            types[t] = types.get(t, 0) + 1
        type_str = ", ".join(f"{k} ×{v}" for k, v in types.items())
        html += f"<h2>💪 Fitness</h2>\n"
        html += f'<div class="stat"><strong>{len(week_workouts)}</strong> workouts</div>\n'
        html += f'<div class="stat"><strong>{total_dist:.1f}km</strong> total distance</div>\n'
        html += f'<div class="stat">{esc(type_str)}</div>\n'
        html += "\n"

    # ── Sleep ──
    if week_sleep:
        total_hours = sum(f.get("Hours slept", 0) or 0 for f in week_sleep)
        avg = total_hours / len(week_sleep) if week_sleep else 0
        html += f"<h2>😴 Sleep</h2>\n"
        html += f'<div class="stat"><strong>{avg:.1f}h</strong> avg per night</div>\n'
        html += f'<div class="stat"><strong>{len(week_sleep)}</strong> nights logged</div>\n'
        html += "\n"

    # ── Habits ──
    if week_habit_log:
        completed = sum(1 for f in week_habit_log if f.get("Completed", False))
        total = len(week_habit_log)
        pct = (completed / total * 100) if total else 0
        html += f"<h2>🔄 Habits</h2>\n"
        html += f'<div class="stat"><strong>{completed}/{total}</strong> completed ({pct:.0f}%)</div>\n'
        html += "\n"

    # ── Footer ──
    html += '<div class="footer">'
    html += f"Geeves Weekly Digest · {week_range}"
    html += '</div>\n'
    html += "</body></html>"

    return html

def main():
    save = "--save" in sys.argv
    html = build_html()

    if save:
        os.makedirs(DIGEST_DIR, exist_ok=True)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = f"{DIGEST_DIR}/weekly_{today}.html"
        with open(path, "w") as f:
            f.write(html)
        print(f"✅ Saved to {path}")
    else:
        print(html)

if __name__ == "__main__":
    main()
