#!/usr/bin/env python3
"""
stocks_fetch.py — Fetch daily stock prices via yfinance and log to Airtable.

Tickers: BTC-GBP, AMZN, GOOGL, META
Uses yfinance (Yahoo Finance), no API key required.

Usage:
    python3 stocks_fetch.py              # fetch and print
    python3 stocks_fetch.py --write      # fetch and write to Airtable
"""

import subprocess, sys, json, urllib.request, urllib.error
from datetime import datetime, timezone

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip install yfinance")
    sys.exit(1)

ENV_PATH = "/root/.hermes/.env"
BASE = "appzvmonQXs4x2AlL"
TABLE = "Stock_Prices"

TICKERS = ["BTC-GBP", "AMZN", "GOOGL", "META"]

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
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def fetch_prices():
    """Fetch current prices for all configured tickers."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    records = []

    for ticker_str in TICKERS:
        try:
            ticker = yf.Ticker(ticker_str)
            info = ticker.fast_info
            price = info.last_price
            prev_close = info.previous_close

            # Determine currency
            if ticker_str.endswith("-GBP"):
                currency = "GBP"
            elif ticker_str.endswith("-USD"):
                currency = "USD"
            else:
                currency = "USD"  # default for equities

            # Calculate change %
            if prev_close and prev_close != 0:
                change_pct = round(((price - prev_close) / prev_close) * 100, 2)
            else:
                change_pct = 0.0

            records.append({
                "Date": today,
                "Ticker": ticker_str,
                "Price": round(price, 2),
                "Currency": currency,
                "Change Pct": change_pct,
                "Source": "yfinance",
            })
        except Exception as e:
            print(f"  ⚠️  Failed to fetch {ticker_str}: {e}")

    return records

def write_to_airtable(records):
    """Write stock price records to Airtable (one per ticker)."""
    for rec in records:
        r, status = api("POST", f"{BASE}/{TABLE}", {"fields": rec})
        if status == 200:
            print(f"  ✅ {rec['Ticker']}: {rec['Price']} {rec['Currency']} ({rec['Change Pct']:+.2f}%) — {r['id']}")
        else:
            print(f"  ❌ {rec['Ticker']} Airtable error: {r}")

def main():
    write_mode = "--write" in sys.argv

    print("📈 Fetching stock prices...")
    records = fetch_prices()

    if not records:
        print("  ❌ No data fetched")
        sys.exit(1)

    for rec in records:
        print(f"  {rec['Ticker']:10s}  {rec['Price']:>12,.2f} {rec['Currency']}  ({rec['Change Pct']:+.2f}%)")

    if write_mode:
        print("\n  Writing to Airtable...")
        write_to_airtable(records)
    else:
        print("\n  (dry run — add --write to save to Airtable)")

if __name__ == "__main__":
    main()
