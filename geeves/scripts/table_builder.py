#!/usr/bin/env python3
"""
Geeves Baserow Table Builder

Creates tables and fields in the Geeves Baserow database via the Platform API.

IMPORTANT: The Baserow Platform API can CREATE and DELETE tables and fields.
If a table has the wrong schema, you can delete it via API and recreate it.

Usage:
    python3 table_builder.py                    # show current schema
    python3 table_builder.py --fix              # create/fix core tables
    python3 table_builder.py --module <Name>    # scaffold a new module
    python3 table_builder.py --check            # verify schema matches spec
    python3 table_builder.py --delete-table <name>  # delete a table
"""
import subprocess, json, sys, urllib.request, urllib.error, urllib.parse

DB_ID = 132
BASE_URL = "http://77.68.33.121"
ENV_PATH = "/root/.hermes/.env"

# Baserow field type names (Platform API)
FIELD_TYPE_MAP = {
    "text": "text",
    "longText": "long_text",
    "date": "date",
    "select": "single_select",
    "multiSelect": "multiple_select",
    "number": "number",
    "checkbox": "boolean",
    "email": "email",
    "phone": "phone_number",
    "url": "url",
    "link": "link_row",
    "createdTime": "created_on",
    "lastModifiedTime": "last_modified",
    "attachment": "file",
    "user": "created_by",
    "rating": "rating",
}

# Fields that are auto-managed by Baserow (skip during creation)
AUTO_FIELDS = {"created_on", "last_modified", "created_by", "last_modified_by", "id"}

# Color palette for select options (cycles through)
SELECT_COLORS = [
    "red-light", "orange-light", "yellow-light", "green-light",
    "blue-light", "purple-light", "pink-light", "gray-light",
]


def get_api_token():
    """Get the database API token from .env (for row operations)."""
    r = subprocess.run(["grep", "BASEROW_API_TOKEN", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def get_jwt_token():
    """Get a JWT token for Platform API operations (table/field CRUD)."""
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
    """Make a Platform API request using JWT auth."""
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


def api_db(method, path, data=None):
    """Make a Database API request using token auth (for row operations)."""
    token = get_api_token()
    if not token:
        print("ERROR: No API token available")
        sys.exit(1)
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


def list_tables():
    """List all tables in the database."""
    r = api("GET", f"/api/database/tables/database/{DB_ID}/")
    if isinstance(r, list):
        return r
    print(f"Error listing tables: {r}")
    return []


def list_fields(table_id):
    """List all fields in a table."""
    r = api("GET", f"/api/database/fields/table/{table_id}/")
    if isinstance(r, list):
        return r
    print(f"Error listing fields for table {table_id}: {r}")
    return []


def build_field_payload(field_def, ft):
    """Build the payload for creating a field via Baserow Platform API."""
    if ft in AUTO_FIELDS:
        return None  # skip auto fields

    payload = {"name": field_def["name"], "type": ft}

    if ft == "single_select" and "options" in field_def:
        choices = []
        for i, o in enumerate(field_def["options"]):
            color = SELECT_COLORS[i % len(SELECT_COLORS)]
            choices.append({"value": o, "color": color})
        payload["select_options"] = choices

    if ft == "multiple_select" and "options" in field_def:
        choices = []
        for i, o in enumerate(field_def["options"]):
            color = SELECT_COLORS[i % len(SELECT_COLORS)]
            choices.append({"value": o, "color": color})
        payload["select_options"] = choices

    if ft == "link_row" and "linked_table" in field_def:
        payload["link_row_table_id"] = field_def["linked_table"]

    if ft == "date":
        payload["date_format"] = "ISO"
        payload["date_include_time"] = False
        payload["date_show_tzinfo"] = False

    if ft == "number":
        payload["number_decimal_places"] = field_def.get("precision", 0)
        payload["number_negative"] = field_def.get("negative", True)

    if ft == "rating":
        payload["max_value"] = field_def.get("max_value", 5)

    return payload


def create_table(name, jwt=None):
    """Create a new table (empty, no fields)."""
    r = api("POST", f"/api/database/tables/database/{DB_ID}/", {"name": name}, jwt=jwt)
    if "id" in r:
        print(f"  ✅ Created table '{name}' (id: {r['id']})")
        return r
    else:
        print(f"  ❌ Failed to create '{name}': {json.dumps(r)}")
        return None


def delete_table(table_id, jwt=None):
    """Delete a table by ID."""
    r = api("DELETE", f"/api/database/tables/{table_id}/", jwt=jwt)
    if isinstance(r, dict) and "error" in r:
        print(f"  ❌ Failed to delete table {table_id}: {json.dumps(r)}")
        return False
    print(f"  🗑️  Deleted table {table_id}")
    return True


def add_field(table_id, field_def, jwt=None):
    """Add a field to an existing table."""
    ft = FIELD_TYPE_MAP.get(field_def["type"], field_def["type"])
    payload = build_field_payload(field_def, ft)
    if payload is None:
        return True  # skip auto fields

    r = api("POST", f"/api/database/fields/table/{table_id}/", payload, jwt=jwt)
    if "id" in r:
        print(f"    ✅ Added field '{field_def['name']}' ({ft})")
        return True
    else:
        print(f"    ❌ Failed to add '{field_def['name']}': {json.dumps(r)}")
        return False


def delete_field(field_id, jwt=None):
    """Delete a field by ID."""
    r = api("DELETE", f"/api/database/fields/{field_id}/", jwt=jwt)
    if isinstance(r, dict) and "error" in r:
        print(f"    ❌ Failed to delete field {field_id}: {json.dumps(r)}")
        return False
    print(f"    🗑️  Deleted field {field_id}")
    return True


def find_table(tables, name):
    for t in tables:
        if t["name"].lower() == name.lower():
            return t
    return None


def find_field(fields, name):
    for f in fields:
        if f["name"].lower() == name.lower():
            return f
    return None


# ── Table definitions ─────────────────────────────────────────────────────────
# These mirror the original Airtable definitions but use Baserow types.
# Link fields use "linked_table" with the Baserow table ID.
# Since all 41 tables already exist, these are for reference and new modules.

BULLETIN_TABLES = {
    "Weather_Data": {
        "fields": [
            {"name": "Date", "type": "date"},
            {"name": "Location", "type": "text"},
            {"name": "Temperature C", "type": "number", "precision": 1},
            {"name": "Feels Like C", "type": "number", "precision": 1},
            {"name": "Humidity Pct", "type": "number", "precision": 0},
            {"name": "Wind Speed KPH", "type": "number", "precision": 1},
            {"name": "Condition", "type": "text"},
            {"name": "Description", "type": "longText"},
        ],
    },
    "Stock_Prices": {
        "fields": [
            {"name": "Date", "type": "date"},
            {"name": "Ticker", "type": "text"},
            {"name": "Price", "type": "number", "precision": 2},
            {"name": "Currency", "type": "text"},
            {"name": "Change Pct", "type": "number", "precision": 2},
            {"name": "Source", "type": "text"},
        ],
    },
    "Fact_of_the_Day": {
        "fields": [
            {"name": "Date", "type": "date"},
            {"name": "Category", "type": "select", "options": ["Wikipedia", "Numbers", "Useless Fact"]},
            {"name": "Fact", "type": "longText"},
            {"name": "Source URL", "type": "url"},
        ],
    },
}

CORE_TABLES = {
    "Todos": {
        "fields": [
            {"name": "Task", "type": "text"},
            {"name": "Status", "type": "select", "options": ["Todo", "In Progress", "Done", "Cancelled"]},
            {"name": "Priority", "type": "select", "options": ["Low", "Medium", "High"]},
            {"name": "Due Date", "type": "date"},
            {"name": "Module", "type": "text"},
            {"name": "Linked Person", "type": "link"},
            {"name": "Notes", "type": "longText"},
            {"name": "Created", "type": "createdTime"},
            {"name": "Completed Date", "type": "date"},
        ],
    },
    "Memory_Summaries": {
        "fields": [
            {"name": "Period", "type": "text"},
            {"name": "Summary", "type": "longText"},
            {"name": "Source Entries", "type": "longText"},
            {"name": "Created", "type": "date"},
        ],
    },
    "Output_Log": {
        "fields": [
            {"name": "Item", "type": "text"},
            {"name": "Module", "type": "text"},
            {"name": "Generated At", "type": "date"},
            {"name": "Content", "type": "longText"},
            {"name": "Rating", "type": "select", "options": ["★★★ Great", "★★ OK", "★ Poor"]},
            {"name": "Feedback", "type": "longText"},
            {"name": "Prompt Used", "type": "longText"},
        ],
    },
}


FILM_TABLES = {
    "Films": {
        "fields": [
            {"name": "Film Title", "type": "text"},
            {"name": "Year", "type": "number", "precision": 0},
            {"name": "Director", "type": "text"},
            {"name": "Genre", "type": "text"},
            {"name": "IMDb Rating", "type": "number", "precision": 1},
            {"name": "IMDb Votes", "type": "number", "precision": 0},
            {"name": "Metascore", "type": "number", "precision": 0},
            {"name": "IMDb URL", "type": "url"},
            {"name": "My Rating", "type": "select", "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]},
            {"name": "Date Watched", "type": "date"},
            {"name": "Personal Notes", "type": "longText"},
            {"name": "Film Club", "type": "select", "options": ["Yes", "No"]},
            {"name": "Month Picked", "type": "text"},
            {"name": "Watched At", "type": "select", "options": ["Hosted (at someone's home)", "Remote (streamed remotely)", "Cinema", "N/A"]},
            {"name": "Club Discussion Notes", "type": "longText"},
            {"name": "Member 2 Rating", "type": "select", "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Not rated"]},
            {"name": "Member 2 Notes", "type": "longText"},
            {"name": "Member 3 Rating", "type": "select", "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Not rated"]},
            {"name": "Member 3 Notes", "type": "longText"},
            {"name": "Member 4 Rating", "type": "select", "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Not rated"]},
            {"name": "Member 4 Notes", "type": "longText"},
        ],
    },
}


RECIPE_TABLES = {
    "Recipes": {
        "fields": [
            {"name": "Name", "type": "text"},
            {"name": "Mealie Slug", "type": "text"},
            {"name": "Source URL", "type": "text"},
            {"name": "Cuisine", "type": "select", "options": [
                "Italian", "Indian", "Thai", "British", "Mexican",
                "Chinese", "French", "Japanese", "Korean", "Other",
            ]},
            {"name": "Meal type", "type": "multiSelect", "options": [
                "Breakfast", "Lunch", "Dinner", "Side", "Dessert", "Snack",
            ]},
            {"name": "Quality rating", "type": "number", "precision": 1},
            {"name": "Will do again", "type": "select", "options": [
                "Never", "Rarely", "Sometimes", "Often", "Staple",
            ]},
            {"name": "Favourite", "type": "checkbox"},
            {"name": "Photo", "type": "attachment"},
            {"name": "Notes", "type": "longText"},
            {"name": "Last cooked", "type": "date"},
        ],
    },
    "Ingredients": {
        "fields": [
            {"name": "Ingredient", "type": "text"},
            {"name": "Quantity", "type": "text"},
            {"name": "Category", "type": "select", "options": [
                "Meat", "Fish", "Veg", "Fruit", "Dairy",
                "Grain", "Spice", "Pantry", "Other",
            ]},
            {"name": "Seasonal", "type": "multiSelect", "options": [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
            ]},
        ],
    },
    "Dinner Parties": {
        "fields": [
            {"name": "Event name", "type": "text"},
            {"name": "Date", "type": "date"},
            {"name": "Dietary constraints (auto)", "type": "longText"},
            {"name": "Menu notes", "type": "longText"},
            {"name": "Shopping list generated", "type": "checkbox"},
            {"name": "Status", "type": "select", "options": [
                "Planning", "Confirmed", "Done",
            ]},
        ],
    },
    "Dinner Planner": {
        "fields": [
            {"name": "Date", "type": "date"},
            {"name": "Meal", "type": "text"},
            {"name": "Prep notes", "type": "longText"},
            {"name": "Status", "type": "select", "options": [
                "Planned", "Shopping", "Cooking", "Done",
            ]},
        ],
    },
    "Shopping List": {
        "fields": [
            {"name": "Item", "type": "text"},
            {"name": "Category", "type": "select", "options": [
                "Meat", "Fish", "Veg", "Fruit", "Dairy",
                "Grain", "Spice", "Pantry", "Household", "Other",
            ]},
            {"name": "Quantity", "type": "text"},
            {"name": "Source", "type": "select", "options": [
                "Recipe", "Dinner Party", "Manual",
            ]},
            {"name": "Purchased", "type": "checkbox"},
        ],
    },
    "Recipe Context": {
        "fields": [
            {"name": "Preference", "type": "text"},
            {"name": "Detail", "type": "longText"},
            {"name": "Source", "type": "select", "options": ["Inferred", "Manual"]},
        ],
    },
    "Recipe Output Log": {
        "fields": [
            {"name": "Output", "type": "longText"},
            {"name": "Type", "type": "select", "options": [
                "Suggestion", "Shopping List", "Meal Plan",
                "Dinner Party Plan", "Email", "PDF",
            ]},
            {"name": "Rating", "type": "number", "precision": 1},
            {"name": "Feedback", "type": "longText"},
        ],
    },
    "Dining Preferences": {
        "fields": [
            {"name": "Preference", "type": "text"},
            {"name": "Category", "type": "select", "options": [
                "Cuisine", "Dish", "Style", "Avoid", "Dietary",
            ]},
            {"name": "Confidence", "type": "select", "options": [
                "Strong", "Moderate", "Emerging",
            ]},
            {"name": "Evidence", "type": "longText"},
            {"name": "Source modules", "type": "multiSelect", "options": [
                "Recipes", "Meals", "People Graph",
            ]},
            {"name": "Last updated", "type": "date"},
        ],
    },
}


WEEKLY_DIGEST_TABLES = {
    "Intentions": {
        "fields": [
            {"name": "Intention", "type": "text"},
            {"name": "Week starting", "type": "date"},
            {"name": "Type", "type": "select", "options": [
                "Accomplish", "Let go of", "Focus",
            ]},
            {"name": "Status", "type": "select", "options": [
                "Set", "Achieved", "Missed", "Carried over",
            ]},
            {"name": "Source", "type": "select", "options": [
                "Suggested", "Manual",
            ]},
            {"name": "Reflection", "type": "longText"},
        ],
    },
}


RESTAURANT_TABLES = {
    "Restaurants": {
        "fields": [
            {"name": "Name", "type": "text"},
            {"name": "Cuisine", "type": "multiSelect", "options": [
                "Italian", "Indian", "Thai", "Chinese", "Japanese", "French",
                "British", "Mexican", "Mediterranean", "Korean", "Vietnamese",
                "Spanish", "Turkish", "Other",
            ]},
            {"name": "Address", "type": "longText"},
            {"name": "Postcode", "type": "text"},
            {"name": "Phone", "type": "text"},
            {"name": "Website", "type": "url"},
            {"name": "Maps URL", "type": "url"},
            {"name": "Price Range", "type": "select", "options": [
                "£", "££", "£££", "££££",
            ]},
            {"name": "Food Type", "type": "multiSelect", "options": [
                "Fine dining", "Casual", "Pub", "Cafe", "Street food",
                "Takeaway", "Brunch", "Roast", "Bistro", "Gastropub",
            ]},
            {"name": "Dietary Friendly", "type": "multiSelect", "options": [
                "Vegetarian-friendly", "Vegan-friendly", "Gluten-free options",
                "Halal", "Kosher",
            ]},
            {"name": "Ambience", "type": "multiSelect", "options": [
                "Romantic", "Family-friendly", "Quiet", "Lively",
                "Outdoor seating", "BYOB", "Dog-friendly", "Date night",
            ]},
            {"name": "Google Rating", "type": "number", "precision": 1},
            {"name": "Google Review Count", "type": "number", "precision": 0},
            {"name": "Google Price Level", "type": "number", "precision": 0},
            {"name": "Google Types", "type": "longText"},
            {"name": "Review Summary", "type": "longText"},
            {"name": "Alignment Score", "type": "select", "options": [
                "Strong match", "Moderate", "Weak", "Unknown",
            ]},
            {"name": "Alignment Notes", "type": "longText"},
            {"name": "Source", "type": "select", "options": [
                "We went", "Recommended", "Found online", "Want to try",
            ]},
            {"name": "Status", "type": "select", "options": [
                "Want to go", "Been — loved it", "Been — liked it",
                "Been — meh", "Been — avoid",
            ]},
            {"name": "Overall Rating", "type": "select", "options": [
                "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            ]},
            {"name": "Times Visited", "type": "number", "precision": 0},
            {"name": "Last Visited", "type": "date"},
            {"name": "Photo", "type": "attachment"},
            {"name": "Notes", "type": "longText"},
        ],
    },
    "Restaurant Visits": {
        "fields": [
            {"name": "Date", "type": "date"},
            {"name": "Dishes Ordered", "type": "longText"},
            {"name": "Dish Ratings", "type": "longText"},
            {"name": "Service Rating", "type": "select", "options": [
                "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            ]},
            {"name": "Ambience Rating", "type": "select", "options": [
                "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            ]},
            {"name": "Value Rating", "type": "select", "options": [
                "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            ]},
            {"name": "Overall Rating", "type": "select", "options": [
                "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            ]},
            {"name": "Wife's Rating", "type": "select", "options": [
                "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            ]},
            {"name": "Wife's Notes", "type": "longText"},
            {"name": "Would Return", "type": "select", "options": [
                "Definitely", "Maybe", "No",
            ]},
            {"name": "Best Dish", "type": "text"},
            {"name": "Worst Dish", "type": "text"},
            {"name": "Cost Total", "type": "number", "precision": 2},
            {"name": "Cost Per Head", "type": "number", "precision": 2},
            {"name": "Occasion", "type": "select", "options": [
                "Date night", "Family meal", "Friends", "Birthday",
                "Casual", "Business", "Anniversary",
            ]},
            {"name": "Photo", "type": "attachment"},
            {"name": "Notes", "type": "longText"},
            {"name": "Source", "type": "select", "options": ["Slack", "Manual"]},
        ],
    },
}


BOOKS_TABLES = {
    "Books": {
        "fields": [
            {"name": "Title", "type": "text"},
            {"name": "Author", "type": "text"},
            {"name": "Status", "type": "select", "options": [
                "Want to read", "Reading", "Read", "Abandoned",
            ]},
            {"name": "Genre", "type": "multiSelect", "options": [
                "Fiction", "Non-fiction", "Biography", "History",
                "Science", "Philosophy", "Self-help", "Business",
                "Fantasy", "Sci-fi", "Thriller", "Romance", "Other",
            ]},
            {"name": "Date started", "type": "date"},
            {"name": "Date finished", "type": "date"},
            {"name": "Goodreads ID", "type": "text"},
            {"name": "ISBN", "type": "text"},
            {"name": "Page count", "type": "number", "precision": 0},
            {"name": "Format", "type": "select", "options": [
                "Hardcover", "Paperback", "eBook", "Audiobook",
            ]},
            {"name": "Cover image", "type": "attachment"},
            {"name": "Notes", "type": "longText"},
            {"name": "Source", "type": "select", "options": [
                "Manual", "Slack", "Goodreads import",
            ]},
        ],
    },
}


# ── Module creation functions ─────────────────────────────────────────────────
# These create tables with all fields including link fields.
# Link fields reference existing tables by Baserow table ID.

def resolve_link_table_id(table_name):
    """Resolve a table name to its Baserow ID from the existing database."""
    tables = list_tables()
    t = find_table(tables, table_name)
    return t["id"] if t else None


def create_module_table(table_name, spec, link_resolutions=None, jwt=None):
    """
    Create a single table with all its fields.
    link_resolutions: dict of {field_name: target_table_name} for link fields.
    """
    tables = list_tables()
    existing = find_table(tables, table_name)
    if existing:
        print(f"  ℹ️  Table '{table_name}' already exists (id: {existing['id']})")
        return existing["id"]

    # Create the table
    result = create_table(table_name, jwt=jwt)
    if not result:
        return None
    table_id = result["id"]

    # Add non-link fields first
    link_fields = []
    for f in spec["fields"]:
        ft = FIELD_TYPE_MAP.get(f["type"], f["type"])
        if ft == "link_row":
            link_fields.append(f)
        else:
            add_field(table_id, f, jwt=jwt)

    # Add link fields (now that the table exists)
    for f in link_fields:
        target_name = (link_resolutions or {}).get(f["name"])
        if target_name:
            target_id = resolve_link_table_id(target_name)
            if target_id:
                add_field(table_id, {**f, "linked_table": target_id}, jwt=jwt)
            else:
                print(f"    ⚠️  Skipping '{f['name']}' — target table '{target_name}' not found")
        else:
            print(f"    Skipping '{f['name']}' - no link target specified")

    return table_id


def create_books_tables(jwt=None):
    """Create the Books table."""
    print("\n📚 Creating Books table...")
    print()

    tables = list_tables()
    people_table = find_table(tables, "People")
    people_table_id = people_table["id"] if people_table else None

    spec = BOOKS_TABLES["Books"]
    existing = find_table(tables, "Books")
    if existing:
        print(f"  ℹ️  Table 'Books' already exists (id: {existing['id']})")
        books_id = existing["id"]
    else:
        # Create table without link fields
        non_link = [f for f in spec["fields"] if f["type"] != "link"]
        result = create_table("Books", jwt=jwt)
        if not result:
            return None
        books_id = result["id"]
        for f in non_link:
            add_field(books_id, f, jwt=jwt)

    # Add rating field separately
    add_field(books_id, {"name": "My rating", "type": "rating", "max_value": 10}, jwt=jwt)

    # Add link field to People
    if people_table_id:
        add_field(books_id, {
            "name": "Recommended by",
            "type": "link",
            "linked_table": people_table_id,
        }, jwt=jwt)
    else:
        print("    ⚠️  Skipping 'Recommended by' — People table not found")

    print()
    print("📊 Books module table IDs:")
    print(f"   Books                    {books_id}")
    print()
    return books_id


def create_weekly_digest_tables(jwt=None):
    """Create all Weekly Digest module tables (Intentions)."""
    print("\n📅 Creating Weekly Digest module tables...")
    print()

    tables = list_tables()

    for table_name, spec in WEEKLY_DIGEST_TABLES.items():
        existing = find_table(tables, table_name)
        if existing:
            print(f"  ℹ️  Table '{table_name}' already exists (id: {existing['id']})")
            continue

        non_link = [f for f in spec["fields"] if f["type"] != "link"]
        result = create_table(table_name, jwt=jwt)
        if result:
            for f in non_link:
                add_field(result["id"], f, jwt=jwt)
            print(f"    ✅ Created '{table_name}' (id: {result['id']})")
        print()

    print("📊 Weekly Digest module table IDs:")
    for table_name in WEEKLY_DIGEST_TABLES:
        t = find_table(list_tables(), table_name)
        if t:
            print(f"   {table_name:25s} {t['id']}")
    print()


def create_restaurant_tables(jwt=None):
    """Create all Restaurant module tables."""
    print("\n🍽️  Creating Restaurant module tables...")
    print()

    tables = list_tables()
    people_table = find_table(tables, "People")
    people_table_id = people_table["id"] if people_table else None

    table_ids = {}
    table_order = ["Restaurant Visits", "Restaurants"]

    for table_name in table_order:
        spec = RESTAURANT_TABLES[table_name]
        existing = find_table(tables, table_name)
        if existing:
            print(f"  ℹ️  Table '{table_name}' already exists (id: {existing['id']})")
            table_ids[table_name] = existing["id"]
            continue

        non_link = [f for f in spec["fields"] if f["type"] != "link"]
        result = create_table(table_name, jwt=jwt)
        if result:
            table_ids[table_name] = result["id"]
            for f in non_link:
                add_field(result["id"], f, jwt=jwt)
            print(f"    ✅ Created '{table_name}' (id: {result['id']})")
        print()

    # Add link fields
    restaurants_id = table_ids.get("Restaurants")
    visits_id = table_ids.get("Restaurant Visits")

    link_ops = [
        (visits_id, "Restaurant", "link", restaurants_id),
        (visits_id, "People", "link", people_table_id),
        (restaurants_id, "Recommended By", "link", people_table_id),
    ]

    for table_id, field_name, field_type, linked_id in link_ops:
        if table_id and linked_id:
            add_field(table_id, {
                "name": field_name,
                "type": field_type,
                "linked_table": linked_id,
            }, jwt=jwt)
        elif table_id:
            print(f"    ⚠️  Skipping '{field_name}' — linked table not found")

    print()
    print("📊 Restaurant module table IDs:")
    for name, tid in table_ids.items():
        print(f"   {name:25s} {tid}")
    print()


def create_films_table(jwt=None):
    """Create the Films table."""
    print("🎬 Creating Films table...")
    print()

    tables = list_tables()
    people_table = find_table(tables, "People")
    people_table_id = people_table["id"] if people_table else None

    spec = FILM_TABLES["Films"]
    existing = find_table(tables, "Films")
    if existing:
        print(f"  ℹ️  Table 'Films' already exists (id: {existing['id']})")
        return

    non_link = [f for f in spec["fields"] if f["type"] != "link"]
    result = create_table("Films", jwt=jwt)
    if not result:
        return

    for f in non_link:
        add_field(result["id"], f, jwt=jwt)

    # Add link fields to People
    link_fields = [
        {"name": "Recommended By", "type": "link"},
        {"name": "Member 2 Name", "type": "link"},
        {"name": "Member 3 Name", "type": "link"},
        {"name": "Member 4 Name", "type": "link"},
    ]
    for f in link_fields:
        if people_table_id:
            add_field(result["id"], {**f, "linked_table": people_table_id}, jwt=jwt)
        else:
            print(f"    ⚠️  Skipping '{f['name']}' — People table not found")

    print()


def create_recipe_tables(jwt=None):
    """Create all Recipe module tables."""
    print("\n🍳 Creating Recipe module tables...")
    print()

    tables = list_tables()
    people_table = find_table(tables, "People")
    people_table_id = people_table["id"] if people_table else None

    table_ids = {}
    table_order = [
        "Recipe Context", "Recipe Output Log", "Ingredients",
        "Dinner Parties", "Dinner Planner", "Shopping List",
        "Dining Preferences", "Recipes",
    ]

    for table_name in table_order:
        spec = RECIPE_TABLES[table_name]
        existing = find_table(tables, table_name)
        if existing:
            print(f"  ℹ️  Table '{table_name}' already exists (id: {existing['id']})")
            table_ids[table_name] = existing["id"]
            continue

        non_link = [f for f in spec["fields"] if f["type"] != "link"]
        result = create_table(table_name, jwt=jwt)
        if result:
            table_ids[table_name] = result["id"]
            for f in non_link:
                add_field(result["id"], f, jwt=jwt)
            print(f"    ✅ Created '{table_name}' (id: {result['id']})")
        print()

    # Add link fields
    recipes_id = table_ids.get("Recipes")
    ingredients_id = table_ids.get("Ingredients")
    dinner_parties_id = table_ids.get("Dinner Parties")
    dinner_planner_id = table_ids.get("Dinner Planner")
    shopping_list_id = table_ids.get("Shopping List")
    output_log_id = table_ids.get("Recipe Output Log")

    link_ops = [
        (ingredients_id, "Recipe", "link", recipes_id),
        (recipes_id, "Ingredients", "link", ingredients_id),
        (dinner_parties_id, "Guests", "link", people_table_id),
        (dinner_parties_id, "Chosen recipes", "link", recipes_id),
        (dinner_planner_id, "Recipe", "link", recipes_id),
        (shopping_list_id, "Recipe", "link", recipes_id),
        (output_log_id, "Recipe(s)", "link", recipes_id),
    ]

    for table_id, field_name, field_type, linked_id in link_ops:
        if table_id and linked_id:
            add_field(table_id, {
                "name": field_name,
                "type": field_type,
                "linked_table": linked_id,
            }, jwt=jwt)
        elif table_id:
            print(f"    ⚠️  Skipping '{field_name}' — linked table not found")

    print()
    print("📊 Recipe module table IDs:")
    for name, tid in table_ids.items():
        print(f"   {name:25s} {tid}")
    print()


def fix_core_tables(jwt=None):
    """Create the 3 core tables."""
    print("🔧 Creating core tables...")
    print()

    tables = list_tables()
    people_table = find_table(tables, "People")
    people_table_id = people_table["id"] if people_table else None

    for table_name, spec in CORE_TABLES.items():
        existing = find_table(tables, table_name)
        if existing:
            print(f"  ℹ️  Table '{table_name}' already exists (id: {existing['id']})")
            continue

        non_link = [f for f in spec["fields"] if f["type"] != "link"]
        link_fields = [f for f in spec["fields"] if f["type"] == "link"]

        result = create_table(table_name, jwt=jwt)
        if not result:
            continue

        for f in non_link:
            add_field(result["id"], f, jwt=jwt)

        for f in link_fields:
            if people_table_id:
                add_field(result["id"], {**f, "linked_table": people_table_id}, jwt=jwt)
            else:
                print(f"    ⚠️  Skipping '{f['name']}' — People table not found")

        print()


def create_bulletin_tables(jwt=None):
    """Create the 3 daily bulletin tables."""
    print("📰 Creating bulletin tables...")
    print()

    tables = list_tables()

    for table_name, spec in BULLETIN_TABLES.items():
        existing = find_table(tables, table_name)
        if existing:
            print(f"  ℹ️  Table '{table_name}' already exists (id: {existing['id']})")
            continue

        non_link = [f for f in spec["fields"] if f["type"] != "link"]
        result = create_table(table_name, jwt=jwt)
        if result:
            for f in non_link:
                add_field(result["id"], f, jwt=jwt)
            print(f"    ✅ Created '{table_name}' (id: {result['id']})")
        print()


def scaffold_module(module_name, jwt=None):
    """Scaffold a new module with Data, Context, and Log tables."""
    prefix = module_name.replace(" ", "")

    tables = list_tables()
    people_table = find_table(tables, "People")
    people_table_id = people_table["id"] if people_table else None

    module_tables = {
        f"{prefix}_Data": [
            {"name": "Name", "type": "text"},
            {"name": "Created", "type": "createdTime"},
            {"name": "Last Modified", "type": "lastModifiedTime"},
        ],
        f"{prefix}_Context": [
            {"name": "Key", "type": "text"},
            {"name": "Value", "type": "longText"},
            {"name": "Updated", "type": "lastModifiedTime"},
        ],
        f"{prefix}_Log": [
            {"name": "Item", "type": "text"},
            {"name": "Generated At", "type": "date"},
            {"name": "Content", "type": "longText"},
            {"name": "Rating", "type": "select", "options": ["★★★ Great", "★★ OK", "★ Poor"]},
            {"name": "Feedback", "type": "longText"},
        ],
    }

    print(f"\n🔨 Scaffolding module: {module_name}")
    print()

    for table_name, fields in module_tables.items():
        existing = find_table(tables, table_name)
        if existing:
            print(f"  ℹ️  Table '{table_name}' already exists, skipping")
            continue
        result = create_table(table_name, jwt=jwt)
        if result:
            for f in fields:
                add_field(result["id"], f, jwt=jwt)
        print()


def show_schema():
    """Display the full database schema."""
    tables = list_tables()
    print(f"\n{'='*60}")
    print(f"Geeves Database Schema ({len(tables)} tables)")
    print(f"{'='*60}")
    for t in tables:
        print(f"\n  📋 {t['name']}  (id: {t['id']})")
        fields = list_fields(t["id"])
        for f in fields:
            opts = ""
            if f.get("select_options"):
                choices = [o["value"] for o in f["select_options"]]
                opts = f"  → {choices}"
            link = ""
            if f.get("link_row_table_id"):
                link = f" → table {f['link_row_table_id']}"
            print(f"     {f['id']:6d}  {f['name']:28s}  {f['type']}{opts}{link}")


def check_schema():
    """Verify existing schema matches expected definitions."""
    print("\n🔍 Checking schema...")
    tables = list_tables()
    issues = []

    all_defs = {}
    all_defs.update(BULLETIN_TABLES)
    all_defs.update(CORE_TABLES)
    all_defs.update(FILM_TABLES)
    all_defs.update(RECIPE_TABLES)
    all_defs.update(WEEKLY_DIGEST_TABLES)
    all_defs.update(RESTAURANT_TABLES)
    all_defs.update(BOOKS_TABLES)

    for table_name, spec in all_defs.items():
        t = find_table(tables, table_name)
        if not t:
            issues.append(f"  ❌ Missing table: {table_name}")
            continue

        fields = list_fields(t["id"])
        for fdef in spec["fields"]:
            ft = FIELD_TYPE_MAP.get(fdef["type"], fdef["type"])
            if ft in AUTO_FIELDS:
                continue
            f = find_field(fields, fdef["name"])
            if not f:
                issues.append(f"  ❌ {table_name}: missing field '{fdef['name']}'")
            elif f["type"] != ft:
                issues.append(f"  ⚠️  {table_name}.{fdef['name']}: expected {ft}, got {f['type']}")

    if issues:
        print(f"\n{len(issues)} issues found:")
        for i in issues:
            print(i)
    else:
        print("  ✅ All tables and fields match expected schema")


def main():
    args = sys.argv[1:]
    jwt = get_jwt_token()

    if not args or args[0] == "--schema":
        show_schema()
        return

    if args[0] == "--check":
        check_schema()
        return

    if args[0] == "--fix":
        fix_core_tables(jwt=jwt)
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--bulletin":
        create_bulletin_tables(jwt=jwt)
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--films":
        create_films_table(jwt=jwt)
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--recipe":
        create_recipe_tables(jwt=jwt)
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--restaurant":
        create_restaurant_tables(jwt=jwt)
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--books":
        create_books_tables(jwt=jwt)
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--weekly":
        create_weekly_digest_tables(jwt=jwt)
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--fitness":
        print("ℹ️  Fitness tables already exist: Workouts, Exercise Log, Cycling, Fitness Goals")
        print("   No creation needed. Use --schema to verify.")
        show_schema()
    elif args[0] == "--module":
        if len(args) < 2:
            print("Usage: --module <ModuleName>")
            sys.exit(1)
        scaffold_module(args[1], jwt=jwt)
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--delete-table":
        if len(args) < 2:
            print("Usage: --delete-table <name|id>")
            sys.exit(1)
        target = args[1]
        if target.isdigit():
            delete_table(int(target), jwt=jwt)
        else:
            tables = list_tables()
            t = find_table(tables, target)
            if t:
                delete_table(t["id"], jwt=jwt)
            else:
                print(f"Table '{target}' not found")
    else:
        print(__doc__)
        sys.exit(0)


if __name__ == "__main__":
    main()
