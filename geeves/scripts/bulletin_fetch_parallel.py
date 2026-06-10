#!/usr/bin/env python3
"""
bulletin_fetch_parallel.py — Fetch all daily bulletin data in PARALLEL.

Replaces bulletin_fetch.py (which runs fetchers sequentially).
Uses Python threading to fetch weather, stocks, fact, and token usage
simultaneously, cutting total fetch time from sum(latencies) to
max(latencies).

Usage:
    python3 bulletin_fetch_parallel.py              # fetch all, print
    python3 bulletin_fetch_parallel.py --write      # fetch all + write to Baserow
"""

import subprocess, sys, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

SCRIPTS_DIR = "/root/Geeves/scripts"

# Each fetcher: (label, emoji, script_filename)
FETCHERS = [
    ("Weather",     "🌤️",  "weather_fetch.py"),
    ("Stocks",      "📈",  "stocks_fetch.py"),
    ("Fact",        "💡",  "fact_fetch.py"),
    ("Token Usage", "📊",  "token_usage.py"),
]


def run_fetcher(label, emoji, script, write_mode):
    """Run a single fetcher script and capture its output."""
    cmd = ["python3", f"{SCRIPTS_DIR}/{script}"]
    if write_mode:
        cmd.append("--write")

    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    elapsed = time.time() - start

    return {
        "label": label,
        "emoji": emoji,
        "script": script,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "elapsed": round(elapsed, 2),
    }


def main():
    write_mode = "--write" in sys.argv
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"⚡ Parallel bulletin fetch — {today}")
    print(f"   Mode: {'write to Baserow' if write_mode else 'dry run'}")
    print(f"   Fetchers: {len(FETCHERS)}")
    print()

    overall_start = time.time()
    results = []

    # Run all fetchers concurrently (threads, not processes — these are I/O bound)
    with ThreadPoolExecutor(max_workers=len(FETCHERS)) as pool:
        futures = {}
        for label, emoji, script in FETCHERS:
            future = pool.submit(run_fetcher, label, emoji, script, write_mode)
            futures[future] = (label, emoji, script)

        for future in as_completed(futures):
            label, emoji, script = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "label": label,
                    "emoji": emoji,
                    "script": script,
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": -1,
                    "elapsed": 0,
                })

    overall_elapsed = time.time() - overall_start

    # Print results in original order (not completion order)
    label_order = {f[0]: i for i, f in enumerate(FETCHERS)}
    results.sort(key=lambda r: label_order.get(r["label"], 99))

    all_ok = True
    for r in results:
        print(f"{r['emoji']}  {r['label']} ({r['elapsed']}s)")
        print("─" * 40)
        if r["stdout"]:
            print(r["stdout"])
        if r["returncode"] != 0:
            print(f"  ❌ Error: {r['stderr']}")
            all_ok = False
        print()

    # Summary
    print("═" * 40)
    print(f"⏱  Total time: {overall_elapsed:.2f}s (parallel)")
    sequential = sum(r["elapsed"] for r in results)
    print(f"   Sequential would be: {sequential:.2f}s")
    if sequential > 0:
        speedup = sequential / overall_elapsed
        print(f"   Speedup: {speedup:.1f}x faster")

    if all_ok:
        if write_mode:
            print("✅ All bulletin data written to Baserow.")
        else:
            print("⚠️  Dry run — add --write to save to Baserow.")
    else:
        print("⚠️  Some fetchers failed — see errors above.")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
