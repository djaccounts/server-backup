#!/usr/bin/env python3
"""
baserow_api.py — Geeves Baserow API wrapper

Reads BASEROW_API_TOKEN from ~/.hermes/.env.
Uses Baserow database token auth.
All operations target the Geeves database (id=132).

Field names are automatically converted to field_XXXX IDs using the mapping file.
Select option names are automatically converted to option IDs.

Usage:
    python3 baserow_api.py list-tables
    python3 baserow_api.py list-fields <table>
    python3 baserow_api.py list-rows <table> [--limit N]
    python3 baserow_api.py create-row <table> '<json_fields>'
    python3 baserow_api.py update-row <table> <row_id> '<json_fields>'
    python3 baserow_api.py delete-row <table> <row_id>
    python3 baserow_api.py find <table> <search_term>
    python3 baserow_api.py get-mapping
"""
import subprocess, sys, json, os
import urllib.request, urllib.error, urllib.parse

ENV_PATH = os.path.expanduser("~/.hermes/.env")
GEVES_DB_ID = 132
MAPPING_PATH = "/root/Geeves/baserow_mapping.json"
BASE_URL = "http://77.68.33.121"


def get_token():
    r = subprocess.run(["grep", "BASEROW_API_TOKEN", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def api(method, path, data=None, token=None):
    tok = token or get_token()
    url = BASE_URL + path
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Token {tok}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read()
            if resp.status == 204 or not resp_body:
                return {}
            return json.loads(resp_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        try:
            err = json.loads(err_body)
        except Exception:
            err = {"raw": err_body[:500]}
        return {"error": e.code, "detail": err}


def load_mapping():
    if not os.path.exists(MAPPING_PATH):
        return None
    with open(MAPPING_PATH) as f:
        return json.load(f)


def resolve_table_id(mapping, table):
    if mapping and table in mapping.get("tables", {}):
        return mapping["tables"][table]["id"]
    if str(table).isdigit():
        return int(table)
    print(f"ERROR: Table '{table}' not found in mapping", file=sys.stderr)
    sys.exit(1)


def resolve_fields(mapping, table_name, fields_dict):
    """
    Convert a {field_name: value} dict to {field_XXXX: value} for Baserow API.
    Also handles select option name→ID conversion and linked row arrays.
    """
    if not mapping or table_name not in mapping.get("tables", {}):
        return fields_dict

    table_fields = mapping["tables"][table_name]["fields"]
    resolved = {}

    for field_name, value in fields_dict.items():
        # Find field info
        finfo = table_fields.get(field_name)
        if not finfo:
            # Try case-insensitive match
            for k, v in table_fields.items():
                if k.lower() == field_name.lower():
                    finfo = v
                    break

        if not finfo:
            print(f"WARNING: Field '{field_name}' not found in table '{table_name}'", file=sys.stderr)
            resolved[field_name] = value
            continue

        field_id = f"field_{finfo['id']}"

        # Handle select options: convert name to ID
        if finfo.get("select_options") and isinstance(value, str):
            option_id = None
            for opt in finfo["select_options"]:
                if opt["value"].lower() == value.lower():
                    option_id = opt["id"]
                    break
            if option_id:
                resolved[field_id] = option_id
            else:
                print(f"WARNING: Select option '{value}' not found for field '{field_name}'", file=sys.stderr)
                resolved[field_id] = value
        # Handle linked rows: value should be a list of row IDs
        elif finfo.get("link_row_table_id"):
            if isinstance(value, list):
                resolved[field_id] = value
            else:
                resolved[field_id] = [value]
        else:
            resolved[field_id] = value

    return resolved


def baserow_post(mapping, table_name, fields, token=None):
    """Create a row with field name resolution."""
    tid = resolve_table_id(mapping, table_name)
    resolved = resolve_fields(mapping, table_name, fields)
    resp = api("POST", f"/api/database/rows/table/{tid}/", resolved, token=token)
    if "id" in resp:
        return True, resp["id"]
    return False, resp


def baserow_patch(mapping, table_name, row_id, fields, token=None):
    """Update a row with field name resolution."""
    tid = resolve_table_id(mapping, table_name)
    resolved = resolve_fields(mapping, table_name, fields)
    resp = api("PATCH", f"/api/database/rows/table/{tid}/{row_id}/", resolved, token=token)
    return "id" in resp


def baserow_delete(mapping, table_name, row_id, token=None):
    tid = resolve_table_id(mapping, table_name)
    resp = api("DELETE", f"/api/database/rows/table/{tid}/{row_id}/", token=token)
    # 204 No Content = success, 404 = already deleted (also OK)
    if isinstance(resp, dict):
        if resp.get("error") == "ERROR_ROW_DOES_NOT_EXIST":
            return True  # Already deleted
        if "error" in resp:
            return False
    return True


def baserow_search(mapping, table_name, search_term, token=None):
    """Search rows by text."""
    tid = resolve_table_id(mapping, table_name)
    resp = api("GET", f"/api/database/rows/table/{tid}/?search={urllib.parse.quote(search_term)}", token=token)
    if "results" in resp:
        return resp["results"]
    return []


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]
    mapping = load_mapping()

    if cmd == "list-tables":
        if mapping:
            for name, info in mapping["tables"].items():
                print(f"  {info['id']:6d}  {name} ({len(info['fields'])} fields)")

    elif cmd == "list-fields":
        table = args[1] if len(args) > 1 else ""
        tid = resolve_table_id(mapping, table)
        resp = api("GET", f"/api/database/fields/table/{tid}/")
        if isinstance(resp, list):
            for f in resp:
                opts = ""
                if f.get("select_options"):
                    choices = [o["value"] for o in f["select_options"]]
                    opts = f"  choices={choices}"
                link = ""
                if f.get("link_row_table_id"):
                    link = f" → table {f['link_row_table_id']}"
                print(f"  {f['id']:6d}  {f['name']:25s}  type={f['type']}{opts}{link}")

    elif cmd == "list-rows":
        table = args[1] if len(args) > 1 else ""
        tid = resolve_table_id(mapping, table)
        limit = 100
        if "--limit" in args:
            idx = args.index("--limit")
            if idx + 1 < len(args):
                limit = int(args[idx + 1])
        json_mode = "--json" in args
        resp = api("GET", f"/api/database/rows/table/{tid}/?size={limit}")
        if "results" in resp:
            records = resp["results"]
            if json_mode:
                print(json.dumps({"results": records, "count": resp.get("count", len(records))}))
            else:
                print(f"{len(records)} records (total: {resp.get('count', '?')}):")
                for rec in records:
                    name = rec.get("Name", rec.get("name", "(no name)"))
                    print(f"  {rec['id']:6d}  {name}")

    elif cmd == "create-row":
        table = args[1] if len(args) > 1 else ""
        fields = json.loads(args[2]) if len(args) > 2 else {}
        ok, result = baserow_post(mapping, table, fields)
        if ok:
            print(f"Created: row {result}")
        else:
            print(f"Error: {result}")

    elif cmd == "update-row":
        table = args[1] if len(args) > 1 else ""
        row_id = int(args[2])
        fields = json.loads(args[3]) if len(args) > 3 else {}
        ok = baserow_patch(mapping, table, row_id, fields)
        if ok:
            print(f"Updated: row {row_id}")
        else:
            print(f"Error updating row {row_id}")

    elif cmd == "delete-row":
        table = args[1] if len(args) > 1 else ""
        row_id = int(args[2])
        ok = baserow_delete(mapping, table, row_id)
        if ok:
            print(f"Deleted: row {row_id}")
        else:
            print(f"Error deleting row {row_id}")

    elif cmd == "find":
        table = args[1] if len(args) > 1 else ""
        value = args[2] if len(args) > 2 else ""
        results = baserow_search(mapping, table, value)
        if results:
            for rec in results:
                print(f"  {rec['id']}  {rec}")
        else:
            print("  No records found")

    elif cmd == "get-mapping":
        if mapping:
            print(json.dumps(mapping, indent=2))

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
