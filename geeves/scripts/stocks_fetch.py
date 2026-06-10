#!/usr/bin/env python3
"""
stocks_fetch.py — Fetch daily stock prices via yfinance and log to Baserow.

Tickers: BTC-GBP, AMZN, GOOGL, META
Uses yfinance (Yahoo Finance), no API key required.

Usage:
    python3 stocks_fetch.py              # fetch and print
    python3 stocks_fetch.py --write      # fetch and write to Baserow
"""

import subprocess, sys, json, urllib.request, urllib.error
from datetime import datetime, timezone

sys.path.insert(0, "/root/Geeves/scripts")
import baserow_api

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip install yfinance")
    sys.exit(1)

TABLE = "Stock_Prices"
TICKERS = ["BTC-GBP", "AMZN", "GOOGL", "META"]


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

            if ticker_str.endswith("-GBP"):
                currency = "GBP"
            elif ticker_str.endswith("-USD"):
                currency = "USD"
            else:
                currency = "USD"

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


def write_to_baserow(records):
    """Write stock price records to Baserow (one per ticker)."""
    mapping = baserow_api.load_mapping()
    for rec in records:
        ok, row_id = baserow_api.baserow_post(mapping, TABLE, rec)
        if ok:
            print(f"  ✅ {rec['Ticker']}: {rec['Price']} {rec['Currency']} ({rec['Change Pct']:+.2f}%) — {row_id}")
        else:
            print(f"  ❌ {rec['Ticker']} Baserow error: {row_id}")


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
        print("\n  Writing to Baserow...")
        write_to_baserow(records)
    else:
        print("\n  (dry run — add --write to save to Baserow)")


if __name__ == "__main__":
    main()
