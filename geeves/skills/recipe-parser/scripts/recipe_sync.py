#!/usr/bin/env python3
"""
Sync recipes from Mealie to Airtable.
Run periodically or after adding a new recipe to Mealie.

Usage: python3 recipe_sync.py [--slug <slug>]
"""
import json, subprocess, urllib.request, urllib.error, urllib.parse, sys

BASE_ID = "appzvmonQXs4x2AlL"
RECIPES_TABLE = "tblehBgzRMa2Xucjd"
INGREDIENTS_TABLE = "tblNsgbYHNK8xWnB7"
MEALIE_URL = "http://localhost:9925"

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

def airtable_headers():
    return {
        "Authorization": "Bearer " + get_env_key("AIRTABLE_API_KEY"),
        "Content-Type": "application/json"
    }

def airtable_get(table, params=""):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table}{params}"
    req = urllib.request.Request(url, headers=airtable_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def airtable_post(table, data):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=airtable_headers(), method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

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

    # Check if already in Airtable
    f = urllib.parse.quote(f"{{Mealie Slug}}='{slug}'")
    existing = airtable_get(RECIPES_TABLE, f"?filterByFormula={f}")
    if existing.get("records"):
        recipe_id = existing["records"][0]["id"]
        print(f"  Already in Airtable: {recipe_id}")
    else:
        r = airtable_post(RECIPES_TABLE, {"fields": {
            "Name": name,
            "Mealie Slug": slug,
            "Notes": f"Source: Mealie sync"
        }})
        recipe_id = r.get("id")
        print(f"  Created: {recipe_id}")

    if not recipe_id:
        return

    # Sync ingredients
    for ing in ingredients:
        cat = categorise(ing)
        r = airtable_post(INGREDIENTS_TABLE, {"fields": {
            "Ingredient": ing,
            "Category": cat,
            "Recipe": [recipe_id]
        }})
        status = "OK" if "id" in r else f"FAIL"
        print(f"  {status} {ing} -> {cat}")

    print(f"  Done! Airtable: https://airtable.com/appzvmonQXs4x2AlL/{RECIPES_TABLE}")

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
