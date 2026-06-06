#!/usr/bin/env python3
"""
Geeves Airtable Table Builder

Creates tables and fields in the Geeves Airtable base via the REST API.

IMPORTANT: The Airtable API can CREATE tables and fields but CANNOT delete them.
If a table has the wrong schema, you must delete it manually in the Airtable
web UI first, then run this script to recreate it correctly.

Usage:
    python3 table_builder.py                    # show current schema
    python3 table_builder.py --fix              # create/fix core tables
    python3 table_builder.py --module DinnerParty  # scaffold a new module
    python3 table_builder.py --check            # verify schema matches spec
"""
import subprocess, json, sys, urllib.request, urllib.error

BASE = "appzvmonQXs4x2AlL"

FIELD_TYPE_MAP = {
    "text": "singleLineText",
    "longText": "multilineText",
    "date": "date",
    "select": "singleSelect",
    "multiSelect": "multipleSelects",
    "number": "number",
    "checkbox": "checkbox",
    "email": "email",
    "phone": "phoneNumber",
    "url": "url",
    "link": "multipleRecordLinks",
    "createdTime": "createdTime",
    "lastModifiedTime": "lastModifiedTime",
    "attachment": "multipleAttachments",
    "user": "singleCollaborator",
}

# Fields that can't be set via API (auto-managed by Airtable)
AUTO_FIELDS = {"createdTime", "lastModifiedTime"}


def get_key():
    r = subprocess.run(["grep", "AIRTABLE_API_KEY", "/root/.hermes/.env"], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def api(method, path, data=None):
    key = get_key()
    if not key:
        print("ERROR: AIRTABLE_API_KEY not found")
        sys.exit(1)
    url = f"https://api.airtable.com/v0/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code


def list_tables():
    r, status = api("GET", f"meta/bases/{BASE}/tables")
    if status == 200:
        return r.get("tables", [])
    print(f"Error listing tables: {r}")
    return []


def build_field_payload(field_def, ft):
    """Build the payload for creating a field via Airtable API."""
    if ft in AUTO_FIELDS:
        return None  # skip auto fields

    payload = {"name": field_def["name"], "type": ft}

    if ft == "singleSelect" and "options" in field_def:
        choices = [{"name": o} for o in field_def["options"]]
        payload["options"] = {"choices": choices}

    if ft == "multipleSelects" and "options" in field_def:
        choices = [{"name": o} for o in field_def["options"]]
        payload["options"] = {"choices": choices}

    if ft == "multipleRecordLinks" and "linked_table" in field_def:
        payload["options"] = {"linkedTableId": field_def["linked_table"]}

    # Date fields require format options when creating
    if ft == "date":
        payload["options"] = {"dateFormat": {"name": "local"}}

    # Number fields require precision options when creating
    if ft == "number":
        precision = field_def.get("precision", 0)
        payload["options"] = {"precision": precision}

    # Checkbox fields require options during table creation
    if ft == "checkbox":
        payload["options"] = {"icon": "check", "color": "greenBright"}

    return payload


def create_table(name, fields):
    """Create a table with the given fields."""
    create_fields = []
    for f in fields:
        ft = FIELD_TYPE_MAP.get(f["type"], f["type"])
        payload = build_field_payload(f, ft)
        if payload is None:
            continue
        create_fields.append(payload)

    r, status = api("POST", f"meta/bases/{BASE}/tables", {"name": name, "fields": create_fields})
    if status == 200:
        print(f"  ✅ Created table '{name}' (id: {r['id']})")
        return r
    else:
        print(f"  ❌ Failed to create '{name}': {json.dumps(r)}")
        return None


def add_field(table_id, field_def):
    """Add a field to an existing table."""
    ft = FIELD_TYPE_MAP.get(field_def["type"], field_def["type"])
    payload = build_field_payload(field_def, ft)
    if payload is None:
        return True  # skip auto fields

    r, status = api("POST", f"meta/bases/{BASE}/tables/{table_id}/fields", payload)
    if status == 200:
        print(f"    ✅ Added field '{field_def['name']}' ({ft})")
        return True
    else:
        print(f"    ❌ Failed to add '{field_def['name']}': {json.dumps(r)}")
        return False


def find_table(tables, name):
    for t in tables:
        if t["name"].lower() == name.lower():
            return t
    return None


# ── Table definitions ─────────────────────────────────────────────────────────
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
            {"name": "Linked Person", "type": "multipleRecordLinks", "link_type": "recordLink"},
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
            # Core film info
            {"name": "Film Title", "type": "text"},
            {"name": "Year", "type": "number", "precision": 0},
            {"name": "Director", "type": "text"},
            {"name": "Genre", "type": "text"},
            {"name": "IMDb Rating", "type": "number", "precision": 1},
            {"name": "IMDb Votes", "type": "number", "precision": 0},
            {"name": "Metascore", "type": "number", "precision": 0},
            {"name": "IMDb URL", "type": "url"},
            # Your personal rating
            {"name": "My Rating", "type": "select", "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]},
            {"name": "Date Watched", "type": "date"},
            {"name": "Personal Notes", "type": "longText"},
            # Film Club info
            {"name": "Film Club", "type": "select", "options": ["Yes", "No"]},
            {"name": "Month Picked", "type": "text"},
            {"name": "Watched At", "type": "select", "options": ["Hosted (at someone's home)", "Remote (streamed remotely)", "Cinema", "N/A"]},
            {"name": "Club Discussion Notes", "type": "longText"},
            # Other people's ratings
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
            # Times cooked = rollup from Meals (added when Meals table exists)
            # Ingredients = multipleRecordLinks → added after Ingredients table exists
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
            # Recipe = multipleRecordLinks → added after Recipes table exists
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
            # Guests = multipleRecordLinks → People (added after creation)
            # Chosen recipes = multipleRecordLinks → Recipes (added after creation)
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
            # Recipe = multipleRecordLinks → Recipes (added after creation)
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
            # Recipe = multipleRecordLinks → Recipes (added after creation)
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
            # Recipe(s) = multipleRecordLinks → Recipes (added after creation)
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


def create_films_table():
    """Create the Films table (master film diary + film club)."""
    print("🎬 Creating Films table via API...")
    print()

    tables = list_tables()
    people_table = find_table(tables, "People")
    people_table_id = people_table["id"] if people_table else None

    spec = FILM_TABLES["Films"]
    existing = find_table(tables, "Films")
    if existing:
        print(f"  ℹ️  Table 'Films' already exists (id: {existing['id']})")
        return

    # Separate link fields from normal fields
    normal_fields = [f for f in spec["fields"] if f.get("link_type") != "recordLink"]
    result = create_table("Films", normal_fields)
    if not result:
        return

    # Add link fields to People
    link_fields = [
        {"name": "Recommended By", "type": "multipleRecordLinks", "link_type": "recordLink"},
        {"name": "Member 2 Name", "type": "multipleRecordLinks", "link_type": "recordLink"},
        {"name": "Member 3 Name", "type": "multipleRecordLinks", "link_type": "recordLink"},
        {"name": "Member 4 Name", "type": "multipleRecordLinks", "link_type": "recordLink"},
    ]
    for f in link_fields:
        if people_table_id:
            add_field(result["id"], {**f, "linked_table": people_table_id})
            print(f"    ✅ Added field '{f['name']}' → People")
        else:
            print(f"    ⚠️  Skipping '{f['name']}' — People table not found")

    print()


def create_recipe_tables():
    """Create all Recipe module tables (Recipes, Ingredients, Dinner Parties, etc.)."""
    print("\n🍳 Creating Recipe module tables via API...")
    print()

    tables = list_tables()
    people_table = find_table(tables, "People")
    people_table_id = people_table["id"] if people_table else None

    # Phase 1: Create all base tables (without link fields)
    table_ids = {}
    recipe_table_order = [
        "Recipe Context",
        "Recipe Output Log",
        "Ingredients",
        "Dinner Parties",
        "Dinner Planner",
        "Shopping List",
        "Dining Preferences",
        "Recipes",  # Recipes last so we can link Ingredients → Recipes
    ]

    for table_name in recipe_table_order:
        spec = RECIPE_TABLES[table_name]
        existing = find_table(tables, table_name)
        if existing:
            print(f"  ℹ️  Table '{table_name}' already exists (id: {existing['id']})")
            table_ids[table_name] = existing["id"]
            continue

        normal_fields = [f for f in spec["fields"] if f.get("link_type") != "recordLink"]
        result = create_table(table_name, normal_fields)
        if result:
            table_ids[table_name] = result["id"]
            print(f"    ✅ Created '{table_name}' (id: {result['id']})")
        print()

    # Phase 2: Add link fields (now that all tables exist)
    if not table_ids:
        print("  ⚠️  No recipe tables created — skipping link fields")
        return

    recipes_id = table_ids.get("Recipes")
    ingredients_id = table_ids.get("Ingredients")
    dinner_parties_id = table_ids.get("Dinner Parties")
    dinner_planner_id = table_ids.get("Dinner Planner")
    shopping_list_id = table_ids.get("Shopping List")
    output_log_id = table_ids.get("Recipe Output Log")

    link_ops = [
        # Ingredients → Recipes
        (ingredients_id, "Recipe", "multipleRecordLinks", recipes_id),
        # Recipes → Ingredients
        (recipes_id, "Ingredients", "multipleRecordLinks", ingredients_id),
        # Dinner Parties → People
        (dinner_parties_id, "Guests", "multipleRecordLinks", people_table_id),
        # Dinner Parties → Recipes
        (dinner_parties_id, "Chosen recipes", "multipleRecordLinks", recipes_id),
        # Dinner Planner → Recipes
        (dinner_planner_id, "Recipe", "multipleRecordLinks", recipes_id),
        # Shopping List → Recipes
        (shopping_list_id, "Recipe", "multipleRecordLinks", recipes_id),
        # Recipe Output Log → Recipes
        (output_log_id, "Recipe(s)", "multipleRecordLinks", recipes_id),
    ]

    for table_id, field_name, field_type, linked_id in link_ops:
        if table_id and linked_id:
            add_field(table_id, {
                "name": field_name,
                "type": field_type,
                "link_type": "recordLink",
                "linked_table": linked_id,
            })
            print(f"    ✅ Added field '{field_name}' → linked table")
        elif table_id:
            print(f"    ⚠️  Skipping '{field_name}' — linked table not found")

    print()
    print("📊 Recipe module table IDs:")
    for name, tid in table_ids.items():
        print(f"   {name:25s} {tid}")
    print()


def fix_core_tables():
    """Create the 3 core tables. Assumes they've been deleted from web UI."""
    print("🔧 Creating core tables via API...")
    print()

    tables = list_tables()
    people_table = find_table(tables, "People")
    people_table_id = people_table["id"] if people_table else None

    for table_name, spec in CORE_TABLES.items():
        existing = find_table(tables, table_name)
        if existing:
            print(f"  ℹ️  Table '{table_name}' already exists (id: {existing['id']})")
            continue

        # Separate link fields (need table ID) from normal fields
        normal_fields = [f for f in spec["fields"] if f.get("link_type") != "recordLink"]
        link_fields = [f for f in spec["fields"] if f.get("link_type") == "recordLink"]

        result = create_table(table_name, normal_fields)
        if not result:
            continue

        # Add link fields with the People table ID
        for f in link_fields:
            if people_table_id:
                add_field(result["id"], {**f, "linked_table": people_table_id})
            else:
                print(f"    ⚠️  Skipping '{f['name']}' — People table not found")

        print()


def create_bulletin_tables():
    """Create the 3 daily bulletin tables (Weather, Stocks, Facts)."""
    print("📰 Creating bulletin tables via API...")
    print()

    tables = list_tables()

    for table_name, spec in BULLETIN_TABLES.items():
        existing = find_table(tables, table_name)
        if existing:
            print(f"  ℹ️  Table '{table_name}' already exists (id: {existing['id']})")
            continue

        normal_fields = [f for f in spec["fields"] if f.get("link_type") != "recordLink"]
        link_fields = [f for f in spec["fields"] if f.get("link_type") == "recordLink"]

        result = create_table(table_name, normal_fields)
        if not result:
            continue

        for f in link_fields:
            print(f"    ⚠️  Skipping link field '{f['name']}' — no linked table")

        print()


def scaffold_module(module_name):
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
        create_table(table_name, fields)
        print()


def show_schema():
    tables = list_tables()
    print(f"\n{'='*60}")
    print(f"Geeves Base Schema ({len(tables)} tables)")
    print(f"{'='*60}")
    for t in tables:
        print(f"\n  📋 {t['name']}  (id: {t['id']})")
        for f in t.get("fields", []):
            opts = ""
            if "options" in f and "choices" in f.get("options", {}):
                choices = [c["name"] for c in f["options"]["choices"]]
                opts = f"  → {choices}"
            print(f"     {f['id']:22s}  {f['name']:28s}  {f['type']}{opts}")


def main():
    args = sys.argv[1:]

    if not args or args[0] == "--schema":
        show_schema()
        return

    if args[0] == "--fix":
        fix_core_tables()
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--bulletin":
        create_bulletin_tables()
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--films":
        create_films_table()
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--recipe":
        create_recipe_tables()
        print("\n📊 Final schema:")
        show_schema()
    elif args[0] == "--module":
        if len(args) < 2:
            print("Usage: --module <ModuleName>")
            sys.exit(1)
        scaffold_module(args[1])
        print("\n📊 Final schema:")
        show_schema()
    else:
        print(__doc__)
        sys.exit(0)


if __name__ == "__main__":
    main()
