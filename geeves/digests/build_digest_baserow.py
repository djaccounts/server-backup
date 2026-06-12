#!/usr/bin/env python3
"""
build_digest_baserow.py — Build a rich HTML digest from today's Baserow data.
Reads from Baserow tables and outputs HTML digest.

Usage:
    python3 build_digest_baserow.py              # print HTML to stdout
    python3 build_digest_baserow.py --save       # save to /root/Geeves/digests/
"""

import json, urllib.request, urllib.error, os, subprocess, sys
from datetime import datetime, timezone, timedelta

ENV_PATH = "/root/.hermes/.env"
DIGEST_DIR = "/root/Geeves/digests"

def get_token():
    result = subprocess.run(["grep", "BASEROW_API_TOKEN", ENV_PATH], capture_output=True, text=True)
    line = result.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def baserow_get(table_id, size=100):
    token = get_token()
    url = f"http://77.68.33.121/api/database/rows/table/{table_id}/?size={size}"
    req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def baserow_get_all(table_id):
    """Get all rows with pagination."""
    token = get_token()
    all_rows = []
    page = 1
    while True:
        url = f"http://77.68.33.121/api/database/rows/table/{table_id}/?page={page}&size=100"
        req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        results = data.get("results", [])
        all_rows.extend(results)
        if not data.get("next"):
            break
        page += 1
    return all_rows

def get_select_value(field_val):
    """Extract display value from a Baserow single_select field."""
    if field_val is None:
        return ""
    if isinstance(field_val, dict):
        return field_val.get("value", "")
    return str(field_val)

def build_html():
    today_dt = datetime.now(timezone.utc)
    date_str = today_dt.strftime("%A, %B %d, %Y")
    today_iso = today_dt.strftime("%Y-%m-%d")
    yesterday_iso = (today_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    # Calculate "short term" window: today + next 7 days
    week_ahead = (today_dt + timedelta(days=7)).strftime("%Y-%m-%d")

    sections = []

    # === WEATHER (latest available) ===
    try:
        w_data = baserow_get(364)
        w_recs = sorted(w_data.get("results", []), key=lambda r: r.get("id", 0), reverse=True)
        if w_recs:
            w = w_recs[0]
            weather_date = w.get("field_3364", "")
            # Use yesterday's weather if today unavailable
            if weather_date != today_iso:
                for r in w_recs:
                    if r.get("field_3364") == yesterday_iso:
                        w = r
                        weather_date = yesterday_iso
                        break

            cond = w.get("field_3370", "")
            temp = w.get("field_3366", "?")
            feels = w.get("field_3367", "?")
            high = w.get("field_3372", "?")
            low = w.get("field_3373", "?")
            humidity = w.get("field_3368", "?")
            wind = w.get("field_3369", "?")
            rain_expected = get_select_value(w.get("field_3375"))
            rain_times = w.get("field_3376", "")

            rain_info = ""
            if rain_expected == "Yes":
                rain_info = f'<p style="color: #dc2626;">☔ {rain_times}</p>'
            elif rain_expected == "No":
                rain_info = '<p style="color: #16a34a;">☀️ No rain expected today</p>'

            periods = []
            for label, temp_key, cond_key, prob_key in [
                ("Morning", "field_3378", "field_3379", "field_3380"),
                ("Afternoon", "field_3381", "field_3382", "field_3383"),
                ("Evening", "field_3384", "field_3385", "field_3386"),
            ]:
                t = w.get(temp_key)
                c = w.get(cond_key, "")
                p = w.get(prob_key, 0)
                if t is not None:
                    rain_badge = f" 🌧️ {p}%" if p and int(p) >= 50 else ""
                    periods.append(f"<strong>{label}:</strong> {t}°C — {c}{rain_badge}")

            period_html = "<br>".join(periods) if periods else ""

            date_note = ""
            if weather_date != today_iso:
                date_note = f'<p class="source">⚠️ Weather data from {weather_date} (today\'s fetch may have failed)</p>'

            sections.append(f"""
            <div class="section">
                <h2>🌤️ London Weather</h2>
                {date_note}
                <p><strong>{cond}</strong> — {temp}°C (feels {feels}°C)</p>
                <p>High: <strong>{high}°C</strong> / Low: <strong>{low}°C</strong></p>
                <p>Humidity: {humidity}% | Wind: {wind} km/h</p>
                {rain_info}
                <p style="font-size: 13px; margin-top: 8px;">{period_html}</p>
            </div>""")
    except Exception as e:
        sections.append(f"""
            <div class="section">
                <h2>🌤️ London Weather</h2>
                <p class="source">⚠️ Weather data unavailable ({e})</p>
            </div>""")

    # === CALENDAR (today's events) ===
    try:
        _gapi = "/root/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
        # Fetch today's timed events
        _r1 = subprocess.run(
            ["python3", _gapi, "calendar", "list",
             "--start", today_iso + "T00:00:00Z",
             "--end", today_iso + "T23:59:59Z",
             "--max", "20"],
            capture_output=True, text=True, timeout=15
        )
        cal_events = json.loads(_r1.stdout) if _r1.returncode == 0 else []
        # Fetch wider window to catch all-day events
        _prev = (today_dt - timedelta(days=1)).strftime("%Y-%m-%d")
        _r2 = subprocess.run(
            ["python3", _gapi, "calendar", "list",
             "--start", _prev + "T00:00:00Z",
             "--end", today_iso + "T23:59:59Z",
             "--max", "20"],
            capture_output=True, text=True, timeout=15
        )
        cal_events_all = json.loads(_r2.stdout) if _r2.returncode == 0 else []

        # Merge: prefer timed events from today, add all-day events whose date matches today
        all_day_events = []
        timed_events = []
        seen_ids = set()
        for ev in cal_events_all + cal_events:
            eid = ev.get("id", "")
            if eid in seen_ids:
                continue
            seen_ids.add(eid)
            start_val = ev.get("start", "")
            if len(start_val) == 10:  # all-day event (YYYY-MM-DD)
                if start_val == today_iso:
                    all_day_events.append(ev)
            else:
                if start_val.startswith(today_iso):
                    timed_events.append(ev)

        if all_day_events or timed_events:
            cal_rows = ""
            # All-day events first
            for ev in all_day_events:
                summary = ev.get("summary", "(No title)")
                cal_rows += f"""
                <tr>
                    <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb;">📌 {summary}</td>
                    <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 13px;">All day</td>
                </tr>"""
            # Then timed events, sorted by start time
            timed_events.sort(key=lambda e: e.get("start", ""))
            for ev in timed_events:
                summary = ev.get("summary", "(No title)")
                start_val = ev.get("start", "")
                end_val = ev.get("end", "")
                # Extract HH:MM from ISO timestamp (already in local tz from Google)
                def _fmt_time(ts):
                    try:
                        if "T" in ts:
                            return ts.split("T")[1][:5]
                        return ts
                    except:
                        return ts
                start_str = _fmt_time(start_val)
                end_str = _fmt_time(end_val)
                loc = ev.get("location", "")
                loc_html = f' <span style="color:#6b7280;font-size:12px;">📍 {loc}</span>' if loc else ""
                cal_rows += f"""
                <tr>
                    <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb;">{summary}{loc_html}</td>
                    <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 13px;">{start_str} – {end_str}</td>
                </tr>"""

            sections.append(f"""
            <div class="section">
                <h2>📅 Today's Calendar</h2>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <tr>
                        <th style="text-align: left; padding: 4px 8px; border-bottom: 2px solid #e5e7eb; color: #6b7280;">Event</th>
                        <th style="text-align: left; padding: 4px 8px; border-bottom: 2px solid #e5e7eb; color: #6b7280;">Time</th>
                    </tr>
                    {cal_rows}
                </table>
            </div>""")
    except Exception:
        pass

    # === SHORT-TERM TODOS ===
    try:
        t_data = baserow_get_all(362)
        # Filter: not done, due date is today or within next 7 days (or overdue)
        short_term_todos = []
        for r in t_data:
            status = get_select_value(r.get("field_3350"))
            if status == "Done":
                continue
            due = r.get("field_3352", "")
            if not due:
                continue
            # Include if due today, overdue, or within next 7 days
            if due <= week_ahead:
                short_term_todos.append(r)

        # Sort by due date
        short_term_todos.sort(key=lambda r: r.get("field_3352", ""))

        if short_term_todos:
            todo_rows = ""
            for t in short_term_todos[:10]:  # max 10
                task = t.get("field_3349", "")
                due = t.get("field_3352", "")
                priority = get_select_value(t.get("field_3351"))
                timeframe = get_select_value(t.get("field_3357"))
                category = get_select_value(t.get("field_3358"))

                # Highlight overdue
                overdue_marker = ""
                if due < today_iso:
                    overdue_marker = " 🔴 OVERDUE"
                elif due == today_iso:
                    overdue_marker = " 📌 TODAY"

                meta_parts = []
                if priority:
                    meta_parts.append(priority)
                if timeframe:
                    meta_parts.append(timeframe)
                if category:
                    meta_parts.append(category)
                meta = " · ".join(meta_parts)

                todo_rows += f"""
                <tr>
                    <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb;">{task}{overdue_marker}</td>
                    <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 13px;">{due}</td>
                    <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 12px;">{meta}</td>
                </tr>"""

            sections.append(f"""
            <div class="section">
                <h2>📋 Short-Term Todos</h2>
                <p class="source">Due today or within the next 7 days</p>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <tr>
                        <th style="text-align: left; padding: 4px 8px; border-bottom: 2px solid #e5e7eb; color: #6b7280;">Task</th>
                        <th style="text-align: left; padding: 4px 8px; border-bottom: 2px solid #e5e7eb; color: #6b7280;">Due</th>
                        <th style="text-align: left; padding: 4px 8px; border-bottom: 2px solid #e5e7eb; color: #6b7280;">Info</th>
                    </tr>
                    {todo_rows}
                </table>
            </div>""")
    except Exception as e:
        pass

    # === FACT ===
    try:
        f_data = baserow_get(363)
        f_recs = [r for r in f_data.get("results", []) if r.get("field_3360") == today_iso]
        if f_recs:
            f = f_recs[0]
            cat = f.get("field_3361", {})
            cat_name = cat.get("value", "") if isinstance(cat, dict) else str(cat)
            fact_text = f.get("field_3362", "").replace("\n", "<br>\n")
            source_url = f.get("field_3363", "")
            source_link = f'<br><a href="{source_url}" class="source">Source</a>' if source_url else ""

            sections.append(f"""
            <div class="section">
                <h2>💡 Fact of the Day</h2>
                <p class="source">Category: {cat_name}</p>
                <p>{fact_text}</p>
                {source_link}
            </div>""")
    except Exception:
        pass

    # === WORD OF THE DAY ===
    try:
        w_data = baserow_get(407)
        w_recs = [r for r in w_data.get("results", []) if r.get("field_3785") == today_iso]
        if w_recs:
            w = w_recs[0]
            word = w.get("field_3786", "")
            pronunciation = w.get("field_3787", "")
            pos = get_select_value(w.get("field_3788"))
            definition_en = w.get("field_3789", "").replace("\n", "<br>\n")
            example_en = w.get("field_3790", "").replace("\n", "<br>\n")
            russian = w.get("field_3791", "")
            russian_def = w.get("field_3792", "").replace("\n", "<br>\n")
            russian_ex = w.get("field_3793", "").replace("\n", "<br>\n")
            hebrew = w.get("field_3794", "")
            hebrew_def = w.get("field_3795", "").replace("\n", "<br>\n")
            hebrew_ex = w.get("field_3796", "").replace("\n", "<br>\n")
            source_url = w.get("field_3797", "")
            source_link = f'<br><a href="{source_url}" class="source">Source</a>' if source_url else ""

            # Build trilingual display
            ru_html = ""
            if russian:
                ru_html = f'<p><strong>🇷🇺 Russian:</strong> {russian}</p>'
                if russian_def:
                    ru_html += f'<p style="font-size:13px;color:#4b5563;">{russian_def}</p>'
                if russian_ex:
                    ru_html += f'<p style="font-size:13px;font-style:italic;color:#6b7280;">"{russian_ex}"</p>'

            he_html = ""
            if hebrew:
                he_html = f'<p><strong>🇮🇱 Hebrew:</strong> <span dir="rtl">{hebrew}</span></p>'
                if hebrew_def:
                    he_html += f'<p style="font-size:13px;color:#4b5563;"><span dir="rtl">{hebrew_def}</span></p>'
                if hebrew_ex:
                    he_html += f'<p style="font-size:13px;font-style:italic;color:#6b7280;"><span dir="rtl">"{hebrew_ex}"</span></p>'

            pron_html = f' <span style="color:#6b7280;font-size:13px;">{pronunciation}</span>' if pronunciation else ""
            pos_html = f'<p class="source">{pos}</p>' if pos else ""
            example_html = f'<p style="font-style:italic;color:#4b5563;">"{example_en}"</p>' if example_en else ""

            sections.append(f"""
            <div class="section">
                <h2>📖 Word of the Day</h2>
                <p style="font-size:18px;margin:4px 0;"><strong>{word}</strong>{pron_html}</p>
                {pos_html}
                <p>{definition_en}</p>
                {example_html}
                <hr style="border:0;border-top:1px solid #e5e7eb;margin:12px 0;">
                {ru_html}
                {he_html}
                {source_link}
            </div>""")
    except Exception:
        pass

    # === STAR WARS ===
    try:
        sw_data = baserow_get(371)
        sw_recs = [r for r in sw_data.get("results", []) if r.get("field_3441") == today_iso]
        if sw_recs:
            sw = sw_recs[0]
            sw_fact = sw.get("field_3451", "").replace("\n", "<br>\n")
            sw_name = sw.get("field_3442", "")
            sw_source = sw.get("field_3452", "https://www.swapi.tech")
            source_link = f'<br><a href="{sw_source}" class="source">Source</a>' if sw_source else ""

            sections.append(f"""
            <div class="section">
                <h2>⚔️ Star Wars Fact of the Day</h2>
                <p class="source">Character: {sw_name}</p>
                <p>{sw_fact}</p>
                {source_link}
            </div>""")
    except Exception:
        pass

    # === MARKETS ===
    try:
        s_data = baserow_get(365)
        s_recs = [r for r in s_data.get("results", []) if r.get("field_3387") == today_iso]
        # Deduplicate by ticker
        seen_tickers = set()
        unique_stocks = []
        for r in s_recs:
            t = r.get("field_3388", "")
            if t not in seen_tickers:
                seen_tickers.add(t)
                unique_stocks.append(r)

        if unique_stocks:
            stock_rows = ""
            for s in unique_stocks:
                ticker = s.get("field_3388", "?")
                price = float(s.get("field_3389", 0))
                currency = s.get("field_3390", "?")
                change = s.get("field_3391", 0)
                if change is None:
                    change = 0
                change = float(change)
                sign = "+" if change >= 0 else ""
                color = "#16a34a" if change >= 0 else "#dc2626"
                sym = {"GBP": "£", "USD": "$"}.get(currency, "")
                stock_rows += f'<tr><td><strong>{ticker}</strong></td><td>{sym}{price:,.2f} {currency}</td><td style="color:{color}">{sign}{change}%</td></tr>'

            sections.append(f"""
            <div class="section">
                <h2>📈 Markets</h2>
                <table class="stock-table">
                    <tr><th>Ticker</th><th>Price</th><th>Change</th></tr>
                    {stock_rows}
                </table>
            </div>""")
    except Exception:
        pass

    # === TOKEN USAGE ===
    try:
        t_data = baserow_get(367)
        t_recs = [r for r in t_data.get("results", []) if r.get("field_3418") == yesterday_iso]
        if t_recs:
            t = t_recs[0]
            total = int(t.get("field_3423", 0))
            sessions = t.get("field_3419", 0)
            top = t.get("field_3425", "?")
            input_t = int(t.get("field_3420", 0))
            output_t = int(t.get("field_3421", 0))
            cache_t = int(t.get("field_3422", 0))

            sections.append(f"""
            <div class="section">
                <h2>📊 Token Usage ({yesterday_iso})</h2>
                <p><strong>{total:,}</strong> active tokens across {sessions} sessions</p>
                <p style="font-size: 13px;">Input: {input_t:,} | Output: {output_t:,} | Cache: {cache_t:,}</p>
                <p class="source">Top model: {top}</p>
            </div>""")
    except Exception:
        pass

    # === PROPERTIES ===
    try:
        p_data = baserow_get_all(380)
        # Filter to new properties from the last 7 days
        recent_props = []
        for r in p_data:
            status = get_select_value(r.get("field_3522"))
            first_seen = r.get("field_3524", "")
            if status == "New" and first_seen:
                try:
                    seen_date = datetime.strptime(first_seen[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if (today_dt - seen_date).days <= 7:
                        recent_props.append(r)
                except:
                    pass

        if recent_props:
            # Sort by match score descending
            recent_props.sort(key=lambda p: float(p.get("field_3521", 0) or 0), reverse=True)
            prop_rows = ""
            for p in recent_props[:5]:  # max 5
                address = p.get("field_3508", "")
                price = p.get("field_3510", 0)
                beds = p.get("field_3511", "?")
                prop_type = get_select_value(p.get("field_3513"))
                score = p.get("field_3521", 0)
                url = p.get("field_3509", "#")
                features = p.get("field_3518", "")
                # Extract first 3 key features
                feat_list = [l.strip() for l in features.split("\n") if l.strip()][:3]
                feat_html = " · ".join(feat_list) if feat_list else ""
                price_val = int(price) if price else 0
                price_str = f"£{price_val:,}" if price_val else "Price TBC"

                prop_rows += f"""
                <div class="property-card">
                    <p><strong><a href="{url}">{address}</a></strong></p>
                    <p>{price_str} · {beds} bed {prop_type}</p>
                    <p class="source">{feat_html}</p>
                    <p class="source">⭐ Match score: {score}/10 · <a href="{url}">View on Rightmove →</a></p>
                </div>"""

            sections.append(f"""
            <div class="section">
                <h2>🏠 New Property Listings</h2>
                <p class="source">New listings from the past 7 days matching your criteria</p>
                {prop_rows}
            </div>""")
    except Exception:
        pass

    sections_html = "\n".join(sections)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
         color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 24px; line-height: 1.6; }}
  h1 {{ color: #2563eb; font-size: 22px; margin-bottom: 4px; }}
  .date {{ color: #6b7280; font-size: 14px; margin-bottom: 24px; }}
  h2 {{ color: #374151; font-size: 16px; margin: 0 0 8px 0; }}
  .section {{ margin-bottom: 16px; padding: 12px 16px; background: #f9fafb; border-radius: 8px; border-left: 4px solid #2563eb; }}
  .source {{ color: #6b7280; font-size: 12px; }}
  a {{ color: #2563eb; }}
  .stock-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
  .stock-table th {{ text-align: left; padding: 4px 8px; border-bottom: 1px solid #e5e7eb; color: #6b7280; }}
  .stock-table td {{ padding: 4px 8px; }}
  .property-card {{ margin-bottom: 12px; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }}
  .property-card:last-child {{ border-bottom: none; }}
  .footer {{ margin-top: 32px; padding-top: 12px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 11px; }}
</style>
</head>
<body>
<h1>☀️ Geeves Morning Digest</h1>
<p class="date">{date_str}</p>

{sections_html}

<div class="footer">
<p>Generated by Geeves 🤖 | Weather: Open-Meteo | Markets: yfinance | Facts: Rotating sources | Star Wars: SWAPI.tech | Data: Baserow</p>
</div>
</body>
</html>"""

    return html

if __name__ == "__main__":
    html = build_html()
    if "--save" in sys.argv:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        os.makedirs(DIGEST_DIR, exist_ok=True)
        path = f"{DIGEST_DIR}/digest_{today}.html"
        with open(path, "w") as f:
            f.write(html)
        print(f"Saved to {path}")
    else:
        print(html)
