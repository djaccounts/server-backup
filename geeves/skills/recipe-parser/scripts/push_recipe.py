#!/usr/bin/env python3
"""
Full recipe pipeline: text/URL/photo → Mealie → Airtable.

Usage:
  python3 push_recipe.py --photo /path/to/image.jpg
  python3 push_recipe.py --text "Recipe title\n\nIngredients:\n- ...\n\nInstructions:\n1. ..."
  python3 push_recipe.py --url "https://example.com/recipe"
  python3 push_recipe.py --json-ld '{"@type":"Recipe","name":"...",...}'

Requires in ~/.hermes/.env:
  AIRTABLE_API_KEY, NVIDIA_API_KEY (for photo), SLACK_BOT_TOKEN (for Slack download)
"""
import argparse, base64, json, subprocess, sys, urllib.request, urllib.error, urllib.parse

# ── Config ──
BASE_ID = "appzvmonQXs4x2AlL"
RECIPES_TABLE = "tblehBgzRMa2Xucjd"
INGREDIENTS_TABLE = "tblNsgbYHNK8xWnB7"
MEALIE_URL = "http://localhost:9925"
MEALIE_USER = "changeme@example.com"
MEALIE_PASS = "MyPassword123"

CATEGORIES = {
    "chicken": "Meat", "beef": "Meat", "pork": "Meat", "lamb": "Meat", "thighs": "Meat",
    "salmon": "Fish", "tuna": "Fish", "shrimp": "Fish", "fish": "Fish",
    "onion": "Veg", "garlic": "Veg", "tomato": "Veg", "parsley": "Veg",
    "lemon": "Fruit", "blueberr": "Fruit", "apple": "Fruit", "banana": "Fruit",
    "butter": "Dairy", "cheese": "Dairy", "milk": "Dairy", "cream": "Dairy", "yogurt": "Dairy",
    "flour": "Grain", "rice": "Grain", "pasta": "Grain", "bread": "Grain", "oat": "Grain",
    "salt": "Spice", "pepper": "Spice", "paprika": "Spice", "cumin": "Spice",
    "cinnamon": "Spice", "turmeric": "Spice", "oregano": "Spice", "basil": "Spice",
    "oil": "Pantry", "sugar": "Pantry", "vinegar": "Pantry", "honey": "Pantry",
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

def run(cmd):
    r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)
    return r.stdout.strip()

# ── Mealie ──
def get_mealie_token():
    r = run(f'curl -s -X POST {MEALIE_URL}/api/auth/token '
            f'-H "Content-Type: application/x-www-form-urlencoded" '
            f'-d "username={MEALIE_USER}&password={MEALIE_PASS}"')
    return json.loads(r).get("access_token", "")

def push_to_mealie(json_ld):
    token = get_mealie_token()
    payload = json.dumps({"data": json.dumps(json_ld)}).encode("utf-8")
    req = urllib.request.Request(
        f"{MEALIE_URL}/api/recipes/create/html-or-json",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8").strip().strip('"')
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Mealie error: {e.code} {body[:300]}", file=sys.stderr)
        return None

# ── Airtable ──
def airtable_headers():
    return {
        "Authorization": "Bearer " + get_env_key("AIRTABLE_API_KEY"),
        "Content-Type": "application/json"
    }

def airtable_post(table, data):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=airtable_headers(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body[:300]}"}

def airtable_get(table, params=""):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table}{params}"
    req = urllib.request.Request(url, headers=airtable_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body[:300]}"}

def sync_to_airtable(recipe_name, slug, source, ingredients):
    # Check existing
    f = urllib.parse.quote(f"{{Mealie Slug}}='{slug}'")
    existing = airtable_get(RECIPES_TABLE, f"?filterByFormula={f}")
    if existing.get("records"):
        recipe_id = existing["records"][0]["id"]
        print(f"Recipe exists: {recipe_id}")
    else:
        r = airtable_post(RECIPES_TABLE, {"fields": {
            "Name": recipe_name,
            "Mealie Slug": slug,
            "Notes": f"Source: {source}"
        }})
        if "id" not in r:
            print(f"Failed to create recipe: {r}", file=sys.stderr)
            return None
        recipe_id = r["id"]
        print(f"Created recipe: {recipe_id}")

    # Sync ingredients
    for ing in ingredients:
        cat = categorise(ing)
        r = airtable_post(INGREDIENTS_TABLE, {"fields": {
            "Ingredient": ing,
            "Category": cat,
            "Recipe": [recipe_id]
        }})
        status = "OK" if "id" in r else f"FAIL: {r.get('error','?')}"
        print(f"  {status} {ing} -> {cat}")

    return recipe_id

# ── Vision ──
def extract_from_photo(image_path):
    api_key = get_env_key("NVIDIA_API_KEY")
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    payload = json.dumps({
        "model": "meta/llama-3.2-11b-vision-instruct",
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            {"type": "text", "text": "Extract the full recipe from this image. Include title, all ingredients with quantities, and all step-by-step instructions. Note prep time, cook time, temperature, and yield if visible."}
        ]}],
        "max_tokens": 2048
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]

# ── Main ──
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Push recipe to Mealie + Airtable")
    parser.add_argument("--photo", help="Path to recipe photo")
    parser.add_argument("--text", help="Raw recipe text")
    parser.add_argument("--url", help="Recipe URL")
    parser.add_argument("--json-ld", help="JSON-LD string")
    args = parser.parse_args()

    if args.photo:
        print("Extracting recipe from photo...")
        text = extract_from_photo(args.photo)
        print(f"Extracted:\n{text}\n")
        # Parse the extracted text into JSON-LD (simplified)
        lines = text.strip().split("\n")
        name = lines[0].strip("# *")
        json_ld = {
            "@context": "https://schema.org", "@type": "Recipe",
            "name": name, "description": f"Extracted from photo: {args.photo}",
            "recipeIngredient": [], "recipeInstructions": []
        }
        # Simple parsing: look for ingredient lines and step lines
        in_ingredients = False
        in_instructions = False
        for line in lines[1:]:
            line = line.strip()
            if "ingredient" in line.lower():
                in_ingredients = True
                in_instructions = False
                continue
            if "instruction" in line.lower() or "step" in line.lower() or "direction" in line.lower():
                in_instructions = True
                in_ingredients = False
                continue
            if in_ingredients and line.startswith(("-", "*", "•")):
                json_ld["recipeIngredient"].append(line.lstrip("-*• ").strip())
            elif in_instructions and (line[0:1].isdigit() or line.startswith("**")):
                clean = line.lstrip("0123456789. ").lstrip("**").strip()
                if clean:
                    json_ld["recipeInstructions"].append({"@type": "HowToStep", "text": clean})
        source = f"Photo: {args.photo}"
    elif args.text:
        # Treat as pre-built JSON-LD if it starts with {, else raw text
        if args.text.strip().startswith("{"):
            json_ld = json.loads(args.text)
        else:
            # Minimal JSON-LD from raw text
            json_ld = {
                "@context": "https://schema.org", "@type": "Recipe",
                "name": "Recipe from text",
                "recipeIngredient": [], "recipeInstructions": []
            }
        source = "Text input"
    elif args.url:
        json_ld = {"url": args.url}
        source = f"URL: {args.url}"
    elif args.json_ld:
        json_ld = json.loads(args.json_ld)
        source = "JSON-LD input"
    else:
        print("Need --photo, --text, --url, or --json-ld", file=sys.stderr)
        sys.exit(1)

    print(f"Pushing to Mealie...")
    slug = push_to_mealie(json_ld)
    if not slug:
        print("Failed to push to Mealie", file=sys.stderr)
        sys.exit(1)
    print(f"Slug: {slug}")

    recipe_name = json_ld.get("name", "Unknown")
    ingredients = json_ld.get("recipeIngredient", [])
    print(f"Syncing to Airtable ({len(ingredients)} ingredients)...")
    sync_to_airtable(recipe_name, slug, source, ingredients)

    print(f"\nDone!")
    print(f"Mealie: http://77.68.33.121:9925/recipes/{slug}")
    print(f"Airtable: https://airtable.com/appzvmonQXs4x2AlL/{RECIPES_TABLE}")
