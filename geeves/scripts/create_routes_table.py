#!/usr/bin/env python3
"""Create the Routes table in Baserow for the Travel & Commute module."""
import json, sys, urllib.request, urllib.error

DB_ID = 132
BASE_URL = "http://77.68.33.121"
ENV_PATH = "/root/.hermes/.env"

def get_jwt_token():
    email = "daverj1987@gmail.com"
    password = "TempPass123!"
    data = json.dumps({"email": email, "password": password}).encode()
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(f"{BASE_URL}/api/user/token-auth/", data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            return result.get("token", "")
    except Exception as e:
        print(f"ERROR: Failed to get JWT token: {e}")
        return ""

def api(method, path, data=None, jwt=None):
    token = jwt or get_jwt_token()
    if not token:
        print("ERROR: No JWT token available")
        sys.exit(1)
    url = BASE_URL + path
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"JWT {token}", "Content-Type": "application/json"}
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

def get_api_token():
    import subprocess
    r = subprocess.run(["grep", "BASEROW_API_TOKEN", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def api_db(method, path, data=None):
    token = get_api_token()
    url = BASE_URL + path
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
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

SELECT_COLORS = [
    "red-light", "orange-light", "yellow-light", "green-light",
    "blue-light", "purple-light", "pink-light", "gray-light",
]

# Routes table schema
ROUTES_FIELDS = [
    {"name": "From", "type": "text", "primary": True},
    {"name": "To", "type": "text"},
    {"name": "Default mode", "type": "select", "options": ["Tube", "Bus", "Walk", "Cycle", "Train", "Drive"]},
    {"name": "Typical duration (mins)", "type": "number", "precision": 0},
    {"name": "Notes", "type": "longText"},
    {"name": "Active", "type": "checkbox"},
]

# Enhanced schema with lat/lon for reliable routing (not in original spec but needed)
ROUTES_FIELDS_ENHANCED = [
    {"name": "From", "type": "text", "primary": True},
    {"name": "From lat", "type": "number", "precision": 6},
    {"name": "From lon", "type": "number", "precision": 6},
    {"name": "To", "type": "text"},
    {"name": "To lat", "type": "number", "precision": 6},
    {"name": "To lon", "type": "number", "precision": 6},
    {"name": "Default mode", "type": "select", "options": ["Tube", "Bus", "Walk", "Cycle", "Train", "Drive"]},
    {"name": "Typical duration (mins)", "type": "number", "precision": 0},
    {"name": "Notes", "type": "longText"},
    {"name": "Active", "type": "checkbox"},
]

def create_table(jwt):
    # Check if Routes table already exists
    tables = api("GET", f"/api/database/tables/database/{DB_ID}/", jwt=jwt)
    if isinstance(tables, list):
        for t in tables:
            if t.get("name") == "Routes":
                print(f"Routes table already exists (id={t['id']})")
                return t["id"]

    # Create the table
    result = api("POST", f"/api/database/tables/database/{DB_ID}/", data={"name": "Routes"}, jwt=jwt)
    if "error" in result:
        print(f"ERROR creating table: {result}")
        sys.exit(1)
    table_id = result["id"]
    print(f"Created Routes table (id={table_id})")
    return table_id

def create_fields(table_id, jwt):
    # Get existing fields
    existing = api("GET", f"/api/database/fields/table/{table_id}/", jwt=jwt)
    existing_names = {f["name"] for f in existing} if isinstance(existing, list) else set()
    print(f"Existing fields: {existing_names}")

    for field_def in ROUTES_FIELDS_ENHANCED:
        if field_def["name"] in existing_names:
            print(f"  Field '{field_def['name']}' already exists, skipping")
            continue

        payload = {"name": field_def["name"], "type": field_def["type"]}

        if field_def["type"] == "select" and "options" in field_def:
            choices = []
            for i, o in enumerate(field_def["options"]):
                color = SELECT_COLORS[i % len(SELECT_COLORS)]
                choices.append({"value": o, "color": color})
            payload["select_options"] = choices

        if field_def["type"] == "number":
            payload["number_decimal_places"] = field_def.get("precision", 0)
            payload["number_negative"] = True

        if field_def.get("primary"):
            payload["primary"] = True

        result = api("POST", f"/api/database/fields/table/{table_id}/", data=payload, jwt=jwt)
        if "error" in result:
            print(f"  ERROR creating field '{field_def['name']}': {result}")
        else:
            print(f"  Created field '{field_def['name']}' (id={result.get('id', '?')})")

def seed_home_route(table_id):
    """Seed the home location as a route from Home."""
    # Check if home route exists
    rows = api_db("GET", f"/api/database/rows/table/{table_id}/?user_field_names=true")
    if isinstance(rows, dict) and "error" in rows:
        print(f"Error listing rows: {rows}")
        return

    results = rows.get("results", [])
    for r in results:
        if r.get("From") == "Home":
            print("Home route already exists")
            return

    # Home coordinates (Englands Lane, Camden NW3 4YD area)
    home_data = {
        "From": "Home",
        "From lat": "51.5567",
        "From lon": "-0.1879",
        "To": "",
        "To lat": "",
        "To lon": "",
        "Default mode": "Cycle",
        "Typical duration (mins)": 0,
        "Notes": "43 Englands Lane, Camden, NW3 4YD",
        "Active": True,
    }
    result = api_db("POST", f"/api/database/rows/table/{table_id}/?user_field_names=true", data=home_data)
    if isinstance(result, dict) and "error" in result:
        print(f"Error seeding home route: {result}")
    else:
        print(f"Seeded home route (id={result.get('id', '?')})")

if __name__ == "__main__":
    jwt = get_jwt_token()
    print(f"Got JWT token: {jwt[:20]}...")

    table_id = create_table(jwt)
    create_fields(table_id, jwt)
    seed_home_route(table_id)

    print("\nDone!")
