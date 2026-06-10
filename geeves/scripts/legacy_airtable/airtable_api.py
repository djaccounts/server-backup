#!/usr/bin/env python3
"""
airtable_api.py — Geeves Airtable API wrapper

Reads AIRTABLE_API_KEY from ~/.hermes/.env via shell (Hermes credential store).
Supports all CRUD operations needed for Geeves.

Usage:
    python3 airtable_api.py list-bases
    python3 airtable_api.py list-tables <base_id>
    python3 airtable_api.py list-records <base_id> <table>
    python3 airtable_api.py create-record <base_id> <table> '<json_fields>'
    python3 airtable_api.py update-record <base_id> <table> <record_id> '<json_fields>'
    python3 airtable_api.py delete-record <base_id> <table> <record_id>'
"""
import subprocess, sys, json, os
import urllib.request, urllib.error, urllib.parse

ENV_PATH = os.path.expanduser("~/.hermes/.env")
GEVES_BASE = "appzvmonQXs4x2AlL"

def get_key():
    """Read AIRTABLE_API_KEY from Hermes .env (not directly readable by Python)."""
    r = subprocess.run(
        ["grep", "AIRTABLE_API_KEY", ENV_PATH],
        capture_output=True, text=True
    )
    line = r.stdout.strip().split("\n")[0]
    # Handle KEY=VALUE where VALUE may contain =
    return line.split("=", 1)[1] if "=" in line else ""

def api(method, path, data=None):
    key = get_key()
    if not key:
        print("ERROR: AIRTABLE_API_KEY not found", file=sys.stderr)
        sys.exit(1)
    url = f"https://api.airtable.com/v0/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"HTTP {e.code}: {err}", file=sys.stderr)
        return err

def urlencode(s):
    return urllib.parse.quote(s, safe="")

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]

    if cmd == "list-bases":
        r = api("GET", "meta/bases")
        for b in r.get("bases", []):
            print(f"  {b['id']:25s}  {b['name']}")

    elif cmd == "list-tables":
        base = args[1] if len(args) > 1 else GEVES_BASE
        r = api("GET", f"meta/bases/{base}/tables")
        if "error" in r:
            print(f"Error: {r}")
            return
        for t in r.get("tables", []):
            print(f"\nTable: {t['name']}  (id: {t['id']})")
            for f in t.get("fields", []):
                opts = ""
                if "options" in f and "choices" in f["options"]:
                    choices = [c["name"] for c in f["options"]["choices"]]
                    opts = f"  choices={choices}"
                print(f"  {f['id']:20s}  {f['name']:25s}  type={f['type']}{opts}")

    elif cmd == "list-records":
        base = args[1] if len(args) > 1 else GEVES_BASE
        table = urlencode(args[2]) if len(args) > 2 else "Table%201"
        formula = urlencode(args[3]) if len(args) > 3 else None
        url = f"{base}/{table}?maxRecords=100"
        if formula:
            url += f"&filterByFormula={formula}"
        r = api("GET", url)
        records = r.get("records", [])
        print(f"{len(records)} records:")
        for rec in records:
            name = rec["fields"].get("Name", "(no name)")
            print(f"  {rec['id']:20s}  {name}")

    elif cmd == "create-record":
        base = args[1] if len(args) > 1 else GEVES_BASE
        table = urlencode(args[2]) if len(args) > 2 else "Table%201"
        fields = json.loads(args[3]) if len(args) > 3 else {}
        r = api("POST", f"{base}/{table}", {"fields": fields})
        if "id" in r:
            print(f"Created: {r['id']}")
        else:
            print(f"Error: {r}")

    elif cmd == "update-record":
        base = args[1] if len(args) > 1 else GEVES_BASE
        table = urlencode(args[2]) if len(args) > 2 else "Table%201"
        rec_id = args[3]
        fields = json.loads(args[4]) if len(args) > 4 else {}
        r = api("PATCH", f"{base}/{table}/{rec_id}", {"fields": fields})
        if "id" in r:
            print(f"Updated: {r['id']}")
        else:
            print(f"Error: {r}")

    elif cmd == "delete-record":
        base = args[1] if len(args) > 1 else GEVES_BASE
        table = urlencode(args[2]) if len(args) > 2 else "Table%201"
        rec_id = args[3]
        r = api("DELETE", f"{base}/{table}/{rec_id}")
        if "deleted" in r:
            print(f"Deleted: {r['id']}")
        else:
            print(f"Error: {r}")

    elif cmd == "find":
        # Quick find by name: find <table> <name>
        base = args[1] if len(args) > 1 else GEVES_BASE
        table = urlencode(args[2]) if len(args) > 2 else "Table%201"
        name = args[3] if len(args) > 3 else ""
        enc_name = urlencode(f"{{{name}}}")
        formula = urlencode(f"{{Name}}='{name}'")
        r = api("GET", f"{base}/{table}?filterByFormula={formula}&maxRecords=5")
        records = r.get("records", [])
        if records:
            for rec in records:
                print(f"  {rec['id']}  {rec['fields']}")
        else:
            print("  No records found")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
