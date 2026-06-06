#!/usr/bin/env python3
"""
serpapi_search.py — Google search via SerpApi.

Usage:
    python3 serpapi_search.py "UK news today"
    python3 serpapi_search.py "London weather" --num 3
    python3 serpapi_search.py "BTC price" --engine google
    python3 serpapi_search.py "UK headlines" --engine google_news
"""

import subprocess, sys, json, urllib.request, urllib.parse

ENV_PATH = "/root/.hermes/.env"

def get_key():
    r = subprocess.run(["grep", "SERPAPI_KEY", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def search(query, engine="google", num=5, gl="gb", hl="en"):
    """Search Google via SerpApi."""
    key = get_key()
    params = {
        "engine": engine,
        "q": query,
        "api_key": key,
        "num": num,
        "gl": gl,
        "hl": hl,
    }
    url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "GeevesBot/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 serpapi_search.py <query> [--num N] [--engine google|google_news]")
        return

    query = sys.argv[1]
    num = 5
    engine = "google"

    if "--num" in sys.argv:
        idx = sys.argv.index("--num")
        if idx + 1 < len(sys.argv):
            num = int(sys.argv[idx + 1])

    if "--engine" in sys.argv:
        idx = sys.argv.index("--engine")
        if idx + 1 < len(sys.argv):
            engine = sys.argv[idx + 1]

    print(f"🔍 Searching: {query} (engine={engine}, num={num})")
    data = search(query, engine=engine, num=num)

    # Extract results based on engine type
    if engine == "google_news":
        results = data.get("news_results", [])
        for i, r in enumerate(results[:num], 1):
            title = r.get("title", "No title")
            snippet = r.get("snippet", "")[:150]
            link = r.get("link", "")
            source = r.get("source", "")
            if isinstance(source, dict):
                source = source.get("name", "")
            date = r.get("date", "")
            print(f"\n{i}. {title}")
            if source or date:
                print(f"   {source} • {date}")
            if snippet:
                print(f"   {snippet}")
            print(f"   {link}")
    else:
        results = data.get("organic_results", [])
        for i, r in enumerate(results[:num], 1):
            title = r.get("title", "No title")
            snippet = r.get("snippet", "")[:150]
            link = r.get("link", "")
            print(f"\n{i}. {title}")
            if snippet:
                print(f"   {snippet}")
            print(f"   {link}")

    # Show search info
    info = data.get("search_information", {})
    total = info.get("total_results", "?")
    print(f"\n📊 {total} total results")

if __name__ == "__main__":
    main()
