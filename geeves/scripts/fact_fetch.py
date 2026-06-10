#!/usr/bin/env python3
"""
fact_fetch.py — Fetch a rich daily fact and log to Baserow.

Sources (rotated by day-of-year for variety):
  1. Wikipedia "On This Day" — historical events for today's date
  2. NASA APOD — Astronomy Picture of the Day
  3. Quote Garden — famous quotes
  4. Zen Quotes — Zen/mindfulness quotes
  5. Nager.Date — public holidays around the world today
  6. Useless Facts — fun random facts (fallback)

All free, no API keys required.

Usage:
    python3 fact_fetch.py              # fetch and print
    python3 fact_fetch.py --write      # fetch and write to Baserow
    python3 fact_fetch.py --source wikipedia   # force a specific source
"""

import subprocess, sys, json, urllib.request, urllib.error
from datetime import datetime, timezone

sys.path.insert(0, "/root/Geeves/scripts")
import baserow_api

TABLE = "Fact_of_the_Day"
SOURCES = ["wikipedia", "nasa", "quote", "zen", "holidays", "useless"]


def fetch_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "GeevesBot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def fetch_wikipedia_on_this_day():
    today = datetime.now(timezone.utc)
    url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/selected/{today.month}/{today.day}"
    data = fetch_json(url)
    events = data.get("selected", [])
    if not events:
        raise Exception("No events returned")
    selected = []
    for event in events[:10]:
        year = event.get("year", "")
        text = event.get("text", "").strip()
        if text:
            selected.append(f"[{year}] {text}" if year else text)
    if not selected:
        raise Exception("No usable events")
    events_text = "\n".join(f"• {e}" for e in selected[:5])
    return {
        "Category": "Wikipedia",
        "Fact": f"On this day ({today.strftime('%B %d')}):\n\n{events_text}",
        "Source URL": f"https://en.wikipedia.org/wiki/Portal:Current_events/{today.year}",
    }


def fetch_nasa_apod():
    data = fetch_json("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY")
    title = data.get("title", "Unknown")
    explanation = data.get("explanation", "No description available.")
    media_type = data.get("media_type", "image")
    media_url = data.get("url", data.get("hdurl", "https://apod.nasa.gov/"))
    if len(explanation) > 500:
        explanation = explanation[:497] + "..."
    fact = f"🌌 {title}\n\n{explanation}"
    if media_type == "image":
        fact += f"\n\nImage: {media_url}"
    return {
        "Category": "Wikipedia",
        "Fact": fact,
        "Source URL": "https://apod.nasa.gov/apod/astropix.html",
    }


def fetch_quote_garden():
    try:
        data = fetch_json("https://quote-garden.onrender.com/api/v3/quotes/random")
        quote = data.get("data", [{}])[0]
        text = quote.get("quoteText", "").strip()
        author = quote.get("quoteAuthor", "Unknown")
        if not text:
            raise Exception("Empty quote")
        genre = quote.get("quoteGenre", "")
        fact = f'"{text}"\n\n— {author}'
        if genre:
            fact += f" ({genre})"
        return {
            "Category": "Useless Fact",
            "Fact": fact,
            "Source URL": "https://quote-garden.onrender.com/",
        }
    except Exception:
        try:
            req = urllib.request.Request(
                "https://icanhazdadjoke.com/",
                headers={"Accept": "application/json", "User-Agent": "GeevesBot/1.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            joke = data.get("joke", "").strip()
            if joke:
                return {
                    "Category": "Useless Fact",
                    "Fact": f"😄 {joke}",
                    "Source URL": "https://icanhazdadjoke.com/",
                }
        except Exception:
            pass
        raise Exception("Quote Garden and dad joke fallback both failed")


def fetch_zen_quotes():
    data = fetch_json("https://zenquotes.io/api/random")
    if isinstance(data, list) and len(data) > 0:
        q = data[0]
        text = q.get("q", "Quote unavailable.")
        author = q.get("a", "Unknown")
        fact = f'"{text}"\n\n— {author}'
    else:
        raise Exception("Unexpected Zen Quotes response format")
    return {
        "Category": "Useless Fact",
        "Fact": fact,
        "Source URL": "https://zenquotes.io/",
    }


def fetch_holidays():
    today = datetime.now(timezone.utc)
    year = today.year
    countries = ["GB", "US", "FR", "DE", "JP", "AU", "CA", "IN", "BR", "ZA"]
    holidays = []
    for country in countries:
        try:
            data = fetch_json(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country}")
            for h in data:
                if h.get("date") == today.strftime("%Y-%m-%d"):
                    name = h.get("name", h.get("localName", "Holiday"))
                    holidays.append(f"{country}: {name}")
        except Exception:
            continue
    if holidays:
        holiday_text = "\n".join(f"• {h}" for h in holidays[:8])
        fact = f"Public holidays today ({today.strftime('%B %d, %Y')}):\n\n{holiday_text}"
    else:
        fact = f"No major public holidays today ({today.strftime('%B %d, %Y')}) in the countries checked."
    return {
        "Category": "Wikipedia",
        "Fact": fact,
        "Source URL": f"https://date.nager.at/Country/{countries[0]}",
    }


def fetch_useless():
    data = fetch_json("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en")
    return {
        "Category": "Useless Fact",
        "Fact": data.get("text", "Fact unavailable."),
        "Source URL": data.get("source_url", "https://uselessfacts.jsph.pl"),
    }


FETCHERS = {
    "wikipedia": fetch_wikipedia_on_this_day,
    "nasa": fetch_nasa_apod,
    "quote": fetch_quote_garden,
    "zen": fetch_zen_quotes,
    "holidays": fetch_holidays,
    "useless": fetch_useless,
}


def fetch_fact(source=None):
    today = datetime.now(timezone.utc)
    if source and source not in FETCHERS:
        print(f"  ⚠️  Unknown source '{source}', using rotation")
        source = None
    if not source:
        day_of_year = today.timetuple().tm_yday
        source = SOURCES[day_of_year % len(SOURCES)]
    print(f"  Source: {source}")
    try:
        return FETCHERS[source]()
    except Exception as e:
        print(f"  {source} failed: {e}, trying fallbacks...")
        for fallback_src in SOURCES:
            if fallback_src == source:
                continue
            try:
                print(f"  Trying fallback: {fallback_src}")
                return FETCHERS[fallback_src]()
            except Exception:
                continue
        raise Exception("All fact sources failed")


def write_to_baserow(record, today):
    record["Date"] = today
    ok, row_id = baserow_api.baserow_post(baserow_api.load_mapping(), TABLE, record)
    if ok:
        print(f"  ✅ Written to Baserow (record {row_id})")
    else:
        print(f"  ❌ Baserow error: {row_id}")


def main():
    write_mode = "--write" in sys.argv
    source = None
    if "--source" in sys.argv:
        idx = sys.argv.index("--source")
        if idx + 1 < len(sys.argv):
            source = sys.argv[idx + 1]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print("🎲 Fetching fact of the day...")
    try:
        record = fetch_fact(source)
    except Exception as e:
        print(f"  ❌ Fetch failed: {e}")
        sys.exit(1)

    print(f"  Category:  {record['Category']}")
    fact_lines = record['Fact'].split('\n')[:5]
    for line in fact_lines:
        print(f"  {line}")
    if len(record['Fact'].split('\n')) > 5:
        print(f"  ...")
    print(f"  Source:    {record['Source URL']}")

    if write_mode:
        write_to_baserow(record, today)
    else:
        print("\n  (dry run — add --write to save to Baserow)")


if __name__ == "__main__":
    main()
