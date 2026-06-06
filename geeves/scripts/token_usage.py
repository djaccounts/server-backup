#!/usr/bin/env python3
"""
token_usage.py — Query Hermes token usage from the sessions database.

Usage:
    python3 token_usage.py              # yesterday's usage
    python3 token_usage.py --today       # today's usage so far
    python3 token_usage.py --days 7      # last 7 days summary
    python3 token_usage.py --json        # JSON output for Airtable
"""

import sys, json, sqlite3, subprocess, urllib.request, urllib.error
from datetime import datetime, timedelta

DB_PATH = "/root/.hermes/state.db"

def get_usage(start_ts, end_ts):
    """Get aggregated token usage for a time range."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute('''
        SELECT 
            COUNT(*) as sessions,
            COALESCE(SUM(input_tokens), 0) as input_tokens,
            COALESCE(SUM(output_tokens), 0) as output_tokens,
            COALESCE(SUM(cache_read_tokens), 0) as cache_read,
            COALESCE(SUM(cache_write_tokens), 0) as cache_write,
            COALESCE(SUM(reasoning_tokens), 0) as reasoning,
            COALESCE(SUM(estimated_cost_usd), 0) as estimated_cost
        FROM sessions
        WHERE started_at >= ? AND started_at < ?
    ''', (start_ts, end_ts))
    
    row = cur.fetchone()
    result = {
        "sessions": row[0],
        "input_tokens": row[1],
        "output_tokens": row[2],
        "cache_read_tokens": row[3],
        "cache_write_tokens": row[4],
        "reasoning_tokens": row[5],
        "estimated_cost_usd": row[6],
        "total_active_tokens": row[1] + row[2] + row[5],
    }
    
    # Per-model breakdown
    cur.execute('''
        SELECT 
            model,
            COUNT(*) as sessions,
            COALESCE(SUM(input_tokens), 0) as input_tokens,
            COALESCE(SUM(output_tokens), 0) as output_tokens,
            COALESCE(SUM(estimated_cost_usd), 0) as estimated_cost
        FROM sessions
        WHERE started_at >= ? AND started_at < ?
        GROUP BY model
        ORDER BY estimated_cost DESC
    ''', (start_ts, end_ts))
    
    result["by_model"] = []
    for r in cur.fetchall():
        result["by_model"].append({
            "model": r[0] or "unknown",
            "sessions": r[1],
            "input_tokens": r[2],
            "output_tokens": r[3],
            "estimated_cost_usd": r[4],
        })
    
    conn.close()
    return result

def format_usage(date_label, usage):
    """Format usage for display."""
    lines = []
    lines.append(f"📊 Token Usage — {date_label}")
    lines.append(f"   Sessions: {usage['sessions']}")
    lines.append(f"   Input:  {usage['input_tokens']:>12,.0f} tokens")
    lines.append(f"   Output: {usage['output_tokens']:>12,.0f} tokens")
    lines.append(f"   Cache:  {usage['cache_read_tokens']:>12,.0f} tokens read")
    lines.append(f"   Total:  {usage['total_active_tokens']:>12,.0f} active tokens")
    if usage['estimated_cost_usd'] > 0:
        lines.append(f"   Cost:   ${usage['estimated_cost_usd']:.4f}")
    
    if usage['by_model']:
        lines.append("   By model:")
        for m in usage['by_model']:
            name = m['model'].replace('openrouter/', '')
            lines.append(f"     {name}: {m['sessions']} sessions, {m['input_tokens']:,.0f} in + {m['output_tokens']:,.0f} out")
    
    return "\n".join(lines)

def write_to_airtable(usage, date_str):
    """Write token usage to Airtable."""
    r = subprocess.run(["grep", "AIRTABLE_API_KEY", "/root/.hermes/.env"], capture_output=True, text=True)
    key = r.stdout.strip().split("\n")[0].split("=", 1)[1]
    
    # Build summary text
    top_model = usage['by_model'][0]['model'].replace('openrouter/', '') if usage['by_model'] else 'unknown'
    summary_parts = [f"{usage['sessions']} sessions, {usage['total_active_tokens']:,.0f} active tokens"]
    for m in usage['by_model']:
        name = m['model'].replace('openrouter/', '')
        summary_parts.append(f"{name}: {m['sessions']} ses, {m['input_tokens']:,.0f} in + {m['output_tokens']:,.0f} out")
    summary = "\n".join(summary_parts)
    
    record = {
        "Date": date_str,
        "Sessions": usage['sessions'],
        "Input Tokens": usage['input_tokens'],
        "Output Tokens": usage['output_tokens'],
        "Cache Read Tokens": usage['cache_read_tokens'],
        "Total Active Tokens": usage['total_active_tokens'],
        "Estimated Cost USD": usage['estimated_cost_usd'],
        "Top Model": top_model,
        "Summary": summary,
    }
    
    url = f"https://api.airtable.com/v0/appzvmonQXs4x2AlL/Token_Usage"
    body = json.dumps({"fields": record}).encode()
    req = urllib.request.Request(url, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            print(f"  ✅ Written to Airtable (record {data['id']})")
    except urllib.error.HTTPError as e:
        print(f"  ❌ Airtable error: {json.loads(e.read())}")

def main():
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    write_mode = "--write" in sys.argv
    
    if "--today" in sys.argv:
        start = today_start
        end = now
        label = now.strftime("%Y-%m-%d") + " (so far)"
    elif "--days" in sys.argv:
        idx = sys.argv.index("--days")
        days = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 7
        start = today_start - timedelta(days=days)
        end = now
        label = f"Last {days} days"
    else:
        # Yesterday (default)
        start = today_start - timedelta(days=1)
        end = today_start
        label = (today_start - timedelta(days=1)).strftime("%Y-%m-%d")
    
    usage = get_usage(start.timestamp(), end.timestamp())
    
    if "--json" in sys.argv:
        usage["date"] = label
        usage["start"] = start.isoformat()
        usage["end"] = end.isoformat()
        print(json.dumps(usage, indent=2))
    else:
        print(format_usage(label, usage))
    
    if write_mode:
        write_to_airtable(usage, start.strftime("%Y-%m-%d"))

if __name__ == "__main__":
    main()
