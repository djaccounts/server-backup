#!/usr/bin/env python3
"""
build_digest_html.py — Build a rich HTML digest from today's Airtable data.
Outputs HTML that can be emailed inline or converted to PDF via PDFBolt.

Usage:
    python3 build_digest_html.py              # print HTML to stdout
    python3 build_digest_html.py --save       # save to /root/Geeves/digests/
"""

import subprocess, sys, json, urllib.request, urllib.error, os
from datetime import datetime, timezone

ENV_PATH = "/root/.hermes/.env"
BASE = "appzvmonQXs4x2AlL"

def get_key():
    r = subprocess.run(["grep", "AIRTABLE_API_KEY", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def airtable_get(path):
    key = get_key()
    url = f"https://api.airtable.com/v0/{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def fetch_latest(table, max_records=10):
    """Fetch most recent records from a table."""
    data = airtable_get(f"{BASE}/{table}?maxRecords={max_records * 3}")
    records = data.get("records", [])
    # Sort by Date field descending
    records.sort(key=lambda r: r["fields"].get("Date", ""), reverse=True)
    return records[:max_records]

def build_html():
    today = datetime.now(timezone.utc)
    date_str = today.strftime("%A, %B %d, %Y")
    today_iso = today.strftime("%Y-%m-%d")
    
    # Fetch all data
    weather_recs = fetch_latest("Weather_Data", 1)
    stock_recs = fetch_latest("Stock_Prices", 20)
    fact_recs = fetch_latest("Fact_of_the_Day", 1)
    sw_recs = fetch_latest("Star_Wars_Fact", 1)
    token_recs = fetch_latest("Token_Usage", 2)
    
    sections = []
    
    # === WEATHER ===
    if weather_recs:
        w = weather_recs[0]["fields"]
        rain_info = ""
        if w.get("Rain Expected") == "Yes":
            rain_info = f'<p style="color: #dc2626;">☔ {w.get("Rain Times", "Rain expected today")}</p>'
        elif w.get("Rain Expected") == "No":
            rain_info = '<p style="color: #16a34a;">☀️ No rain expected today</p>'
        
        # Morning / Afternoon / Evening breakdown
        periods = []
        for label, temp_key, cond_key, prob_key in [
            ("Morning", "Morning Temp C", "Morning Condition", "Morning Rain Prob"),
            ("Afternoon", "Afternoon Temp C", "Afternoon Condition", "Afternoon Rain Prob"),
            ("Evening", "Evening Temp C", "Evening Condition", "Evening Rain Prob"),
        ]:
            temp = w.get(temp_key)
            cond = w.get(cond_key, "")
            prob = w.get(prob_key, 0)
            if temp is not None:
                rain_badge = f" 🌧️ {prob}%" if prob and prob >= 50 else ""
                periods.append(f"<strong>{label}:</strong> {temp}°C — {cond}{rain_badge}")
        
        period_html = "<br>".join(periods) if periods else ""
        
        sections.append(f"""
        <div class="section">
            <h2>🌤️ London Weather</h2>
            <p><strong>{w.get("Condition", "")}</strong> — {w.get("Temperature C", "?")}°C (feels {w.get("Feels Like C", "?")}°C)</p>
            <p>High: <strong>{w.get("High C", "?")}°C</strong> / Low: <strong>{w.get("Low C", "?")}°C</strong></p>
            <p>Humidity: {w.get("Humidity Pct", "?")}% | Wind: {w.get("Wind Speed KPH", "?")} km/h</p>
            {rain_info}
            <p style="font-size: 13px; margin-top: 8px;">{period_html}</p>
        </div>""")
    
    # === STAR WARS ===
    if sw_recs:
        sw = sw_recs[0]["fields"]
        fact_text = sw.get("Fact", "").replace("\n", "<br>\n")
        name = sw.get("Name", "")
        source = sw.get("Source URL", "")
        source_link = f'<br><a href="{source}" class="source">SWAPI.tech</a>' if source else ""
        sections.append(f"""
        <div class="section">
            <h2>⚔️ Star Wars Fact of the Day</h2>
            <p><strong>{name}</strong></p>
            <p>{fact_text}</p>
            {source_link}
        </div>""")
    
    # === FACT ===
    if fact_recs:
        f_rec = fact_recs[0]["fields"]
        fact_text = f_rec.get("Fact", "").replace("\n", "<br>\n")
        source = f_rec.get("Source URL", "")
        source_link = f'<br><a href="{source}" class="source">Source</a>' if source else ""
        sections.append(f"""
        <div class="section">
            <h2>💡 Fact of the Day</h2>
            <p>{fact_text}</p>
            {source_link}
        </div>""")
    
    # === MARKETS ===
    today_stocks = [r["fields"] for r in stock_recs if r["fields"].get("Date") == today_iso]
    # Deduplicate by ticker
    seen_tickers = set()
    unique_stocks = []
    for s in today_stocks:
        t = s.get("Ticker", "")
        if t not in seen_tickers:
            seen_tickers.add(t)
            unique_stocks.append(s)
    
    if unique_stocks:
        stock_rows = ""
        for s in unique_stocks:
            ticker = s.get("Ticker", "?")
            price = s.get("Price", 0)
            currency = s.get("Currency", "?")
            change = s.get("Change Pct", 0)
            sign = "+" if change >= 0 else ""
            color = "#16a34a" if change >= 0 else "#dc2626"
            sym = {"GBP": "£", "USD": "$"}.get(currency, "")
            stock_rows += f'<tr><td><strong>{ticker}</strong></td><td>{sym}{price:,.2f}</td><td style="color:{color}">{sign}{change}%</td></tr>'
        
        sections.append(f"""
        <div class="section">
            <h2>📈 Markets</h2>
            <table class="stock-table">
                <tr><th>Ticker</th><th>Price</th><th>Change</th></tr>
                {stock_rows}
            </table>
        </div>""")
    
    # === TOKEN USAGE ===
    if len(token_recs) >= 1:
        t = token_recs[0]["fields"]
        # Get yesterday's record specifically
        for rec in token_recs:
            if rec["fields"].get("Date") != today_iso:
                t = rec["fields"]
                break
        total = t.get("Total Active Tokens", 0)
        sessions = t.get("Sessions", 0)
        top = t.get("Top Model", "?")
        summary = t.get("Summary", "")

        sections.append(f"""
        <div class="section">
            <h2>📊 Token Usage (Yesterday)</h2>
            <p><strong>{total:,.0f}</strong> active tokens across {sessions} sessions</p>
            <p class="source">Top model: {top}</p>
        </div>""")

    # === PROPERTY SEARCH ===
    property_recs = fetch_latest("Properties", 50)
    # Filter to new/interested properties seen in the last 3 days
    recent_props = []
    for r in property_recs:
        f = r["fields"]
        status = f.get("Status", "")
        if status in ("New", "Interested"):
            recent_props.append(f)

    if recent_props:
        # Sort by match score descending
        recent_props.sort(key=lambda p: p.get("Match Score", 0), reverse=True)
        prop_rows = ""
        for p in recent_props[:5]:
            address = p.get("Address", "")
            price = p.get("Price", 0)
            beds = p.get("Bedrooms", "?")
            prop_type = p.get("Property Type", "")
            score = p.get("Match Score", 0)
            url = p.get("Rightmove URL", "#")
            features = p.get("Key Features", "")
            # Extract first 3 key features
            feat_list = [l.strip() for l in features.split("\n") if l.strip()][:3]
            feat_html = " · ".join(feat_list) if feat_list else ""
            price_str = f"£{price:,}" if price else "Price TBC"

            prop_rows += f"""
            <div class="property-card">
                <p><strong><a href="{url}">{address}</a></strong></p>
                <p>{price_str} · {beds} bed {prop_type}</p>
                <p class="source">{feat_html}</p>
                <p class="source">⭐ Match score: {score}/10 · <a href="{url}">View on Rightmove →</a></p>
            </div>"""

        sections.append(f"""
        <div class="section">
            <h2>🏠 Property Picks</h2>
            <p class="source">New listings matching your criteria (3+ beds, garden, north of Thames, £750k-£1m)</p>
            {prop_rows}
        </div>""")

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
  .headlines {{ font-size: 14px; line-height: 1.8; }}
  .headlines strong {{ color: #1e40af; }}
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
<p>Generated by Geeves 🤖 | Weather: Open-Meteo | Markets: yfinance | Facts: Wikipedia, NASA, Quotes | Star Wars: SWAPI.tech</p>
</div>
</body>
</html>"""
    
    return html

def main():
    html = build_html()
    
    if "--save" in sys.argv:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        digest_dir = "/root/Geeves/digests"
        os.makedirs(digest_dir, exist_ok=True)
        path = f"{digest_dir}/digest_{today}.html"
        with open(path, "w") as f:
            f.write(html)
        print(f"✅ Saved to {path}")
    else:
        print(html)

if __name__ == "__main__":
    main()
