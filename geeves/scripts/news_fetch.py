#!/usr/bin/env python3
"""
news_fetch.py — Fetch UK news headlines via SerpApi Google News and log to Airtable.

Usage:
    python3 news_fetch.py              # fetch and print
    python3 news_fetch.py --write      # fetch and write to Airtable
"""

import subprocess, sys, json, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

ENV_PATH = "/root/.hermes/.env"
BASE = "appzvmonQXs4x2AlL"
TABLE = "News_Headlines"

def get_key(path, prefix):
    r = subprocess.run(["grep", prefix, ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def airtable_api(method, path, data=None):
    key = get_key(ENV_PATH, "AIRTABLE_API_KEY")
    url = f"https://api.airtable.com/v0/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def fetch_news():
    """Fetch top UK news headlines from SerpApi Google News."""
    serp_key = get_key(ENV_PATH, "SERPAPI_KEY")
    
    params = {
        "engine": "google_news",
        "q": "UK news today",
        "api_key": serp_key,
        "gl": "gb",
        "hl": "en",
        "num": 10,
    }
    url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "GeevesBot/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())

    results = data.get("news_results", [])
    if not results:
        raise Exception("No news results returned from SerpApi")

    headlines = []
    for r in results[:10]:
        title = r.get("title", "").strip()
        if not title:
            continue
        source = r.get("source", "")
        if isinstance(source, dict):
            source = source.get("name", "")
        date = r.get("date", "")
        link = r.get("link", "")
        snippet = r.get("snippet", "")[:200]
        
        headlines.append({
            "title": title,
            "source": source,
            "date": date,
            "link": link,
            "snippet": snippet,
        })

    if not headlines:
        raise Exception("No usable headlines found")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Build summary text
    summary_lines = []
    for i, h in enumerate(headlines[:5], 1):
        line = f"• {h['title']}"
        if h['source']:
            line += f" ({h['source']})"
        summary_lines.append(line)
    summary = "\n".join(summary_lines)

    return {
        "Date": today,
        "Headline Count": len(headlines),
        "Top Headline": headlines[0]["title"],
        "Top Source": headlines[0]["source"],
        "Summary": summary,
        "_headlines": headlines,  # Internal, not written to Airtable
    }

def write_to_airtable(record):
    """Write news record to Airtable."""
    headlines = record.pop("_headlines", [])  # Remove internal field
    r, status = airtable_api("POST", f"{BASE}/{TABLE}", {"fields": record})
    if status == 200:
        print(f"  ✅ Written to Airtable (record {r['id']})")
    else:
        print(f"  ❌ Airtable error: {r}")

def main():
    write_mode = "--write" in sys.argv

    print("📰 Fetching UK news headlines...")
    try:
        record = fetch_news()
    except Exception as e:
        print(f"  ❌ Fetch failed: {e}")
        sys.exit(1)

    headlines = record.get("_headlines", [])
    print(f"  Date: {record['Date']}")
    print(f"  Headlines: {record['Headline Count']}")
    print()
    for i, h in enumerate(headlines[:8], 1):
        source_str = f" ({h['source']})" if h['source'] else ""
        print(f"  {i}. {h['title']}{source_str}")

    if write_mode:
        write_to_airtable(record)
    else:
        print("\n  (dry run — add --write to save to Airtable)")

if __name__ == "__main__":
    main()
