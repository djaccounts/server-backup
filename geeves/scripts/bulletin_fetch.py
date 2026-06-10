#!/usr/bin/env python3
"""
bulletin_fetch.py — Master script to fetch all daily bulletin data.

Fetches weather, stock prices, and fact of the day,
then writes to their respective Baserow tables.

Usage:
    python3 bulletin_fetch.py         # fetch all and print
    python3 bulletin_fetch.py --write # fetch all and write to Baserow
"""

import subprocess, sys

SCRIPTS = [
    ("🌤️  Weather", "weather_fetch.py"),
    ("📈 Stocks", "stocks_fetch.py"),
    ("💡 Fact", "fact_fetch.py"),
    ("📊 Token Usage", "token_usage.py"),
]


def main():
    write_mode = "--write" in sys.argv
    scripts_dir = "/root/Geeves/scripts"
    success = True

    for label, script in SCRIPTS:
        print(f"\n{label}")
        print("-" * 40)
        cmd = ["python3", f"{scripts_dir}/{script}"]
        if write_mode:
            cmd.append("--write")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"  ❌ Error: {result.stderr}")
            success = False

    if write_mode:
        print("\n✅ Bulletin data written to Baserow.")
    else:
        print("\n⚠️  Dry run — add --write to save to Baserow.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
