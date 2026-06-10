#!/usr/bin/env python3
"""Compare row counts between Airtable and Baserow for all tables."""
import json, sys, urllib.request, urllib.error

env = open("/root/.hermes/.env").read()
lines = env.split("\n")
AT_KEY = [l for l in lines if l.startswith("AIRTABLE_API_KEY=")][0].split("=", 1)[1]
BW_TOKEN = [l for l in lines if l.startswith("BASEROW_API_TOKEN=")][0].split("=", 1)[1]
AT_BASE = "appzvmonQXs4x2AlL"
BW_BASE = "http://77.68.33.121"

sys.path.insert(0, "/root/Geeves/scripts")
from table_builder import list_tables
bw_table_map = {t["name"]: t["id"] for t in list_tables()}

def at_count(tid):
    total, offset = 0, None
    while True:
        url = f"https://api.airtable.com/v0/{AT_BASE}/{tid}?pageSize=100"
        if offset:
            url += f"&offset={offset}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AT_KEY}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            total += len(result.get("records", []))
            offset = result.get("offset")
            if not offset or len(result.get("records", [])) < 100:
                break
    return total

def bw_count(tid):
    total, page = 0, 1
    while True:
        url = f"{BW_BASE}/api/database/rows/table/{tid}/?page={page}&size=100"
        req = urllib.request.Request(url, headers={"Authorization": f"Token {BW_TOKEN}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            total += len(result.get("results", []))
            if not result.get("next") or len(result.get("results", [])) < 100:
                break
            page += 1
    return total

# Get Airtable tables
req = urllib.request.Request(
    f"https://api.airtable.com/v0/meta/bases/{AT_BASE}/tables",
    headers={"Authorization": f"Bearer {AT_KEY}"}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    at_tables = json.loads(resp.read()).get("tables", [])

print(f"{'Table':<30s} {'Airtable':>8s} {'Baserow':>8s} {'Status':>8s}")
print("=" * 60)

mismatches = 0
for t in sorted(at_tables, key=lambda x: x["name"]):
    name = t["name"]
    at_c = at_count(t["id"])
    bw_tid = bw_table_map.get(name)
    bw_c = bw_count(bw_tid) if bw_tid else -1
    status = "OK" if at_c == bw_c else "DIFF"
    if at_c != bw_c:
        mismatches += 1
    print(f"{name:<30s} {at_c:>8d} {bw_c:>8d} {status:>8s}")

print(f"\n{'='*60}")
if mismatches == 0:
    print("ALL ROW COUNTS MATCH!")
else:
    print(f"{mismatches} tables still have mismatches")
