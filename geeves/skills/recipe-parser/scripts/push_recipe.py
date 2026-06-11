#!/usr/bin/env python3
"""
Full recipe pipeline: text/URL/photo → Mealie → Baserow.

Usage:
  python3 push_recipe.py --photo /path/to/image.jpg
  python3 push_recipe.py --text "Recipe title\n\nIngredients:\n- ...\n\nInstructions:\n1. ..."
  python3 push_recipe.py --url "https://example.com/recipe"
  python3 push_recipe.py --json-ld '{"@type":"Recipe","name":"...",...}'

Requires in ~/.hermes/.env:
  BASEROW_API_TOKEN, NVIDIA_API_KEY (for photo), SLACK_BOT_TOKEN (for Slack download)

Baserow tables:
    Recipes (id: 379), Ingredients (id: 375), database ID: 132
"""
import argparse, base64, json, re, subprocess, sys, urllib.request, urllib.error, urllib.parse

# ── Config ──
BASEROW_URL = "http://77.68.33.121"
RECIPES_TABLE = 379
INGREDIENTS_TABLE = 375
MEALIE_URL = "http://localhost:9925"
MEALIE_USER = "changeme@example.com"
MEALIE_PASS = "MyPassword123"

CATEGORY_KEYWORDS = {
    "Meat": ["chicken", "beef", "pork", "lamb", "bacon", "sausage", "pancetta", "prosciutto", "steak", "mince", "turkey", "duck", "gammon", "ham"],
    "Fish": ["salmon", "tuna", "cod", "haddock", "prawn", "shrimp", "anchovy", "fish", "trout", "mackerel", "sardine", "mussel", "scallop", "crab", "lobster"],
    "Veg": ["onion", "garlic", "tomato", "potato", "cucumber", "pepper", "chilli", "chili", "carrot", "celery", "broccoli", "cauliflower", "spinach", "kale", "cabbage", "lettuce", "rocket", "mushroom", "pea", "bean", "leek", "courgette", "aubergine", "sweetcorn", "corn", "beetroot", "parsnip", "turnip", "swede", "butternut", "pumpkin", "squash", "asparagus", "artichoke", "fennel", "watercress", "mangetout", "spring onion", "shallot", "scallion", "avocado", "sweet potato"],
    "Fruit": ["lemon", "lime", "orange", "apple", "banana", "blueberr", "strawberr", "raspberr", "cranberr", "raisin", "sultana", "date", "apricot", "mango", "pineapple", "grape", "peach", "pear", "plum", "cherry", "fig", "pomegranate", "coconut", "olive", "kalamata"],
    "Dairy": ["butter", "milk", "cream", "cheese", "yogurt", "yoghurt", "feta", "parmesan", "mozzarella", "cheddar", "ricotta", "halloumi", "mascarpone", "crème fraiche", "sour cream", "cream cheese", "goat"],
    "Grain": ["flour", "spaghetti", "penne", "pasta", "rice", "oat", "bread", "couscous", "bulgur", "quinoa", "noodle", "lasagne", "macaroni", "fusilli", "rigatoni", "linguine", "fettuccine", "breadcrumb", "tortilla", "wrap", "ciabatta", "focaccia", "pitta", "pita", "yeast", "cake flour", "bread flour", "self-raising"],
    "Spice": ["salt", "pepper", "paprika", "cumin", "cinnamon", "turmeric", "ginger", "nutmeg", "clove", "coriander", "cardamom", "saffron", "vanilla", "oregano", "basil", "thyme", "rosemary", "dill", "parsley", "sage", "mint", "chive", "bay leaf", "bay leave", "chilli flake", "chilli powder", "cayenne", "five spice", "garam masala", "curry", "ras el hanout", "baharat", "allspice", "star anise", "mixed spice", "italian seasoning", "herbes de provence", "mustard seed", "mustard powder"],
    "Pantry": ["oil", "vinegar", "sugar", "honey", "syrup", "baking powder", "baking soda", "bicarbonate", "cornflour", "cornstarch", "gelatine", "agar", "stock", "wine", "soy sauce", "tamari", "fish sauce", "oyster sauce", "worcestershire", "tabasco", "ketchup", "mayonnaise", "mustard", "pesto", "tahini", "hummus", "miso", "capers", "gherkin", "pickle", "tomato purée", "tomato paste", "passata", "chickpea", "kidney bean", "lentil", "black bean", "coconut milk", "coconut cream", "desiccated coconut", "cream of tartar", "cocoa", "chocolate"],
    "Eggs": ["egg"],
    "Nuts": ["almond", "walnut", "cashew", "peanut", "pistachio", "hazelnut", "pecan", "pine nut", "sesame seed", "poppy seed", "sunflower seed", "pumpkin seed", "chia seed", "flax seed", "linseed"],
    "Other": [],
}

def categorise(ingredient):
    ing_lower = ingredient.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in ing_lower:
                return cat
    return "Other"

def clean_ingredient_name(raw):
    """Extract clean ingredient name from a raw recipe ingredient line."""
    text = raw.strip()
    text = re.sub(r'\s*\(.*?\)', '', text).strip()
    text = re.sub(
        r'^(?:[\d/→.\s-]+|x\s*\d+\s*)\s*'
        r'(?:cup|cups|tbsp|tsp|tablespoon|teaspoons|tablespoons|'
        r'lbs?|oz|g|kg|ml|l|litre|liter|'
        r'clove|cloves|slice|slices|piece|pieces|'
        r'sprig|sprigs|pack|packs|pinch|dash|bunch|'
        r'large|medium|small|'
        r'whole|half|quarter|'
        r'tin|tins|can|cans|jar|jars|bottle|bottles|'
        r'teaspoon|teaspoons)\s+',
        '', text, flags=re.IGNORECASE).strip()
    text = re.sub(
        r'\s*,\s*(?:'
        r'finely|roughly|thinly|thickly|'
        r'chopped|diced|minced|grated|sliced|shredded|crushed|'
        r'pressed|peeled|deseeded|quartered|trimmed|'
        r'softened|melted|room temperature|'
        r'plus\s+extra.*|to\s+taste|for\s+garnish|to\s+serve|optional|'
        r'cored|chunked|rings|strips|'
        r'sifted|picked|left whole|'
        r'thaw.*|measure.*'
        r').*$',
        '', text, flags=re.IGNORECASE).strip()
    text = re.sub(
        r'\s+(?:to taste|to serve|for serving|for garnish|optional|for \w+|to finish).*$',
        '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'^(?:a |an |the |~|small |large |medium )', '', text, flags=re.IGNORECASE).strip()
    if text:
        words = text.split()
        result = []
        for w in words:
            if len(w) <= 2 and w.lower() not in ('oz',):
                result.append(w.lower())
            else:
                result.append(w.capitalize())
        return ' '.join(result)
    return text

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

# ── Baserow ──
def baserow_post(table_id, fields):
    """POST to Baserow using the baserow_api helper for field resolution."""
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
        url = f"{BASEROW_URL}/api/database/rows/table/{table_id}/?page={page}&size=100"
        req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        results = data.get("results", [])
        all_rows.extend(results)
        if not data.get("next"):
            break
        page += 1
    return all_rows

def sync_to_baserow(recipe_name, slug, source, ingredients):
    # Check existing
    all_recipes = baserow_get_all(RECIPES_TABLE)
    existing = None
    for r in all_recipes:
        if r.get("Mealie Slug") == slug:
            existing = r
            break

    if existing:
        recipe_id = existing["id"]
        print(f"Recipe exists: {recipe_id}")
    else:
        r = baserow_post(RECIPES_TABLE, {
            "Name": recipe_name,
            "Mealie Slug": slug,
            "Notes": f"Source: {source}"
        })
        if not r:
            print(f"Failed to create recipe: {r}", file=sys.stderr)
            return None
        recipe_id = r["id"]
        print(f"Created recipe: {recipe_id}")

    # Sync ingredients
    seen = set()
    for ing in ingredients:
        clean_name = clean_ingredient_name(ing)
        if not clean_name or clean_name.lower() in seen:
            continue
        seen.add(clean_name.lower())
        cat = categorise(clean_name)
        r = baserow_post(INGREDIENTS_TABLE, {
            "Ingredient": clean_name,
            "Category": cat,
            "Recipe": [recipe_id]
        })
        status = "OK" if r and "id" in r else f"FAIL"
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
    parser = argparse.ArgumentParser(description="Push recipe to Mealie + Baserow")
    parser.add_argument("--photo", help="Path to recipe photo")
    parser.add_argument("--text", help="Raw recipe text")
    parser.add_argument("--url", help="Recipe URL")
    parser.add_argument("--json-ld", help="JSON-LD string")
    args = parser.parse_args()

    if args.photo:
        print("Extracting recipe from photo...")
        text = extract_from_photo(args.photo)
        print(f"Extracted:\n{text}\n")
        lines = text.strip().split("\n")
        name = lines[0].strip("# *")
        json_ld = {
            "@context": "https://schema.org", "@type": "Recipe",
            "name": name, "description": f"Extracted from photo: {args.photo}",
            "recipeIngredient": [], "recipeInstructions": []
        }
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
        if args.text.strip().startswith("{"):
            json_ld = json.loads(args.text)
        else:
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
    print(f"Syncing to Baserow ({len(ingredients)} ingredients)...")
    sync_to_baserow(recipe_name, slug, source, ingredients)

    print(f"\nDone!")
    print(f"Mealie: http://77.68.33.121:9925/recipes/{slug}")
    print(f"Baserow: {BASEROW_URL}/database/132/table/{RECIPES_TABLE}")
