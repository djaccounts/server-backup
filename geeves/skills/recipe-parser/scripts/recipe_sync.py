#!/usr/bin/env python3
"""
Sync recipes from Mealie to Baserow.
Run periodically or after adding a new recipe to Mealie.

Usage: python3 recipe_sync.py [--slug <slug>]

Baserow tables:
    Recipes (id: 379), Ingredients (id: 375), database ID: 132
"""
import json, subprocess, urllib.request, urllib.error, urllib.parse, sys

BASE_ID = "appzvmonQXs4x2AlL"  # Legacy — kept for reference
RECIPES_TABLE = "tblehBgzRMa2Xucjd"
INGREDIENTS_TABLE = "tblNsgbYHNK8xWnB7"
MEALIE_URL = "http://localhost:9925"

# Baserow table IDs
BASEROW_RECIPES_TABLE = 379
BASEROW_INGREDIENTS_TABLE = 375

CATEGORIES = {
    "chicken": "Meat", "beef": "Meat", "pork": "Meat", "lamb": "Meat", "thighs": "Meat", "mince": "Meat", "bacon": "Meat",
    "salmon": "Fish", "tuna": "Fish", "shrimp": "Fish", "fish": "Fish",
    "onion": "Veg", "garlic": "Veg", "tomato": "Veg", "parsley": "Veg", "celery": "Veg", "carrot": "Veg", "chilli": "Veg", "cucumber": "Veg", "eggplant": "Veg", "basil": "Veg", "rosemary": "Veg", "bay leaf": "Veg",
    "lemon": "Fruit", "blueberr": "Fruit", "apple": "Fruit", "banana": "Fruit", "cherry tomato": "Fruit",
    "butter": "Dairy", "cheese": "Dairy", "milk": "Dairy", "cream": "Dairy", "yogurt": "Dairy", "parmesan": "Dairy", "feta": "Dairy", "egg": "Dairy",
    "flour": "Grain", "rice": "Grain", "pasta": "Grain", "spaghetti": "Grain", "bread": "Grain", "oat": "Grain", "cake flour": "Grain", "all-purpose": "Grain",
    "salt": "Spice", "pepper": "Spice", "paprika": "Spice", "cumin": "Spice", "cinnamon": "Spice", "turmeric": "Spice", "oregano": "Spice",
    "oil": "Pantry", "sugar": "Pantry", "vinegar": "Pantry", "honey": "Pantry", "tomato puree": "Pantry", "tomato purée": "Pantry", "stock": "Pantry", "wine": "Pantry", "powdered sugar": "Pantry", "confectioners": "Pantry",
}

def categorise(ingredient):
    ing_lower = ingredient.lower()
    for keyword, cat in CATEGORIES.items():
        if keyword in ing_lower:
            return cat
    return "Other"

def get_env_key(key_name):
    result = subprocess.run(
        ["bash", "-c", f"grep {key_name} ~/.hermes/.env | head -1 | sed 's/.*=//'"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def get_mealie_token():
    r = subprocess.run(["bash", "-c",
        f'curl -s -X POST {MEALIE_URL}/api/auth/token '
        f'-H "Content-Type: application/x-www-form-urlencoded" '
        f'-d "username=changeme@example.com&password=MyPassword123"'],
        capture_output=True, text=True)
    return json.loads(r.stdout).get("access_token", "")

def baserow_post(table_id, fields):
    """POST to Baserow using the baserow_api helper."""
    fields_json = json.dumps(fields)
    result = subprocess.run(
        ["python3", "/root/Geeves/scripts/baserow_api.py", "create-row",
         str(table_id), fields_json],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0 and result.stdout.strip():
        stdout = result.stdout.strip()
        if "Created: row" in stdout:
            row_id = int(stdout.split("Created: row")[1].strip())
            return {"id": row_id}
    return None

def baserow_get_all(table_id):
    """Get all rows from Baserow."""
    token = get_env_key("BASEROW_API_TOKEN")
    all_rows = []
    page = 1
    while True:
        url = f"http://77.68.33.121/api/database/rows/table/{table_id}/?page={page}&size=100"
        req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        results = data.get("results", [])
        all_rows.extend(results)
        if not data.get("next"):
            break
        page += 1
    return all_rows

def sync_recipe(slug):
    token = get_mealie_token()
    # Get recipe from Mealie
    req = urllib.request.Request(
        f"{MEALIE_URL}/api/recipes/{slug}?loadFood=true",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        recipe = json.loads(resp.read().decode("utf-8"))

    name = recipe.get("name", "Unknown")
    ingredients = recipe.get("recipeIngredient", [])
    print(f"Syncing: {name} ({len(ingredients)} ingredients)")

    # Check if already in Baserow
    all_recipes = baserow_get_all(BASEROW_RECIPES_TABLE)
    existing = None
    for r in all_recipes:
        if r.get("Mealie Slug") == slug:
            existing = r
            break

    if existing:
        recipe_id = existing["id"]
        print(f"  Already in Baserow: {recipe_id}")
    else:
        r = baserow_post(BASEROW_RECIPES_TABLE, {
            "Name": name,
            "Mealie Slug": slug,
            "Notes": f"Source: Mealie sync"
        })
        if not r:
            print("  ❌ Failed to create recipe in Baserow", file=sys.stderr)
            return
        recipe_id = r["id"]
        print(f"  Created: {recipe_id}")

    if not recipe_id:
        return

    # Sync ingredients
    for ing in ingredients:
        # Ingredients can be dicts (from Mealie API) or strings
        if isinstance(ing, dict):
            raw_text = ing.get("display", "") or ing.get("note", "") or ing.get("food", {}).get("name", "")
        else:
            raw_text = str(ing)
        if not raw_text:
            continue
        cat = categorise(raw_text)
        r = baserow_post(BASEROW_INGREDIENTS_TABLE, {
            "Ingredient": raw_text[:200],
            "Category": cat,
            "Recipe": [recipe_id]
        })
        status = "OK" if r and "id" in r else "FAIL"
        print(f"  {status} {raw_text[:50]} -> {cat}")

    print(f"  Done! Baserow: http://77.68.33.121/database/132/table/{BASEROW_RECIPES_TABLE}")

if __name__ == "__main__":
    if "--slug" in sys.argv:
        idx = sys.argv.index("--slug")
        slug = sys.argv[idx + 1]
    else:
        # Sync all recipes from Mealie
        token = get_mealie_token()
        req = urllib.request.Request(
            f"{MEALIE_URL}/api/recipes?limit=100",
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        slugs = [r["slug"] for r in data.get("items", data.get("recipes", []))]
        print(f"Found {len(slugs)} recipes in Mealie")
        for slug in slugs:
            sync_recipe(slug)
            print()
