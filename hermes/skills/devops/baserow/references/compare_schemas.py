#!/usr/bin/env python3
"""Compare Airtable and Baserow schemas + row counts."""
import subprocess, json, sys, urllib.request

r = subprocess.run(["grep", "AIRTABLE_API_KEY", "/root/.hermes/.env"], capture_output=True, text=True)
AT_KEY = r.stdout.strip().split("\n")[0].split("=", 1)[1]
AT_BASE = "appzvmonQXs4x2AlL"
r2 = subprocess.run(["grep", "BASEROW_API_TOKEN", "/root/.hermes/.env"], capture_output=True, text=True)
BW_TOKEN=r2.std...=", 1)[1]
BW_BASE = "http://77.68.33.121"

TYPE_MAP = {
    "singleLineText": "text", "multilineText": "long_text", "date": "date",
    "singleSelect": "single_select", "multipleSelects": "multiple_select",
    "number": "number", "currency": "number", "checkbox": "boolean",
    "email": "email", "phoneNumber": "phone_number", "url": "url",
    "multipleRecordLinks": "link_row", "createdTime": "created_on",
    "lastModifiedTime": "last_modified", "multipleAttachments": "file",
    "rating": "rating",
}
SKIP = {"Created", "Last Modified", "created_on", "last_modified"}

def at_get(p):
    req = urllib.request.Request(f"https://api.airtable.com/v0{p}", headers={"Authorization": f"Bearer {AT_KEY}"})
    with urllib.request.urlopen(req, timeout=15) as resp: return json.loads(resp.read())

def bw_get(p):
    req = urllib.request.Request(f"{BW_BASE}{p}", headers={"Authorization": f"Token {BW_TOKEN}"})
    with urllib.request.urlopen(req, timeout=15) as resp: return json.loads(resp.read())

def at_count(tid):
    total, offset = 0, None
    while True:
        url = f"https://api.airtable.com/v0/{AT_BASE}/{tid}?pageSize=100"
        if offset: url += f"&offset={offset}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AT_KEY}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            total += len(result.get("records", []))
            offset = result.get("offset")
            if not offset: break
    return total

def bw_count(tid):
    total, page = 0, 1
    while True:
        result = bw_get(f"/api/database/rows/table/{tid}/?page={page}&size=100")
        total += len(result.get("results", []))
        if not result.get("next") or len(result.get("results", [])) < 100: break
        page += 1
    return total

# Fetch schemas
at_tables = at_get(f"/meta/bases/{AT_BASE}/tables").get("tables", [])
at_data = {t["name"]: {"_id": t["id"], "fields": {f["name"]: {"type": f["type"], "options": [c["name"] for c in f.get("options", {}).get("choices", [])]} for f in t.get("fields", [])}} for t in at_tables}

bw_list = bw_get("/api/database/tables/database/132/")
bw_data, bw_ids = {}, {}
for t in bw_list:
    fs = bw_get(f"/api/database/fields/table/{t['id']}/")
    bw_data[t["name"]] = {"fields": {f["name"]: {"type": f["type"], "options": [o["value"] for o in f.get("select_options", [])]} for f in fs}}
    bw_ids[t["name"]] = t["id"]

# Schema comparison
common = set(at_data) & (set(bw_data) - {"Airtable import report"})
for table in sorted(common):
    at_f, bw_f = at_data[table]["fields"], bw_data[table]["fields"]
    for fn in (set(at_f) - set(bw_f)) - SKIP:
        print(f"MISSING BW: {table}.{fn} (AT: {at_f[fn]['type']})")
    for fn in (set(bw_f) - set(at_f)) - SKIP:
        print(f"EXTRA BW:   {table}.{fn} (BW: {bw_f[fn]['type']})")
    for fn in (set(at_f) & set(bw_f)) - SKIP:
        exp = TYPE_MAP.get(at_f[fn]["type"], at_f[fn]["type"])
        if bw_f[fn]["type"] != exp:
            print(f"TYPE MISMATCH: {table}.{fn} AT={at_f[fn]['type']} BW={bw_f[fn]['type']} (expected {exp})")
        if sorted(at_f[fn]["options"]) != sorted(bw_f[fn]["options"]) and at_f[fn]["options"]:
            o_at = sorted(set(at_f[fn]["options"]) - set(bw_f[fn]["options"]))
            o_bw = sorted(set(bw_f[fn]["options"]) - set(at_f[fn]["options"]))
            print(f"OPTIONS {table}.{fn}: AT-only={o_at} BW-only={o_bw}")

# Row count comparison
print("\nROW COUNTS:")
for t in sorted(at_tables, key=lambda x: x["name"]):
    bw_tid = bw_ids.get(t["name"])
    if not bw_tid:
        print(f"  {t['name']}: NOT IN BASEROW")
        continue
    at_c, bw_c = at_count(t["id"]), bw_count(bw_tid)
    status = "OK" if at_c == bw_c else "DIFF"
    print(f"  {t['name']:<28s} AT={at_c:>6d} BW={bw_c:>6d} {status}")
