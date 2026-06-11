#!/usr/bin/env python3
"""
recipe_sync.py — Mealie → Baserow Recipe Sync

Fetches a recipe from Mealie by slug, creates/updates the Baserow Recipes
record and linked Ingredient records.

Usage:
    python3 recipe_sync.py <mealie_slug>
    python3 recipe_sync.py horiatiki-greek-village-salad-1

Environment:
    BASEROW_API_TOKEN — read from ~/.hermes/.env
    MEALIE_URL        — defaults to http://localhost:9925

Baserow tables:
    Recipes (id: 379), Ingredients (id: 375), database ID: 132
"""
import subprocess, json, sys, os, re
import urllib.request, urllib.error, urllib.parse

ENV_PATH = os.path.expanduser("~/.hermes/.env")
MEALIE_URL = os.environ.get("MEALIE_URL", "http://localhost:9925")
BASEROW_URL = "http://77.68.33.121"

# Baserow table IDs
TABLE_RECIPES = 379
TABLE_INGREDIENTS = 375


def get_baserow_token():
    r = subprocess.run(["grep", "BASEROW_API_TOKEN", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def get_mealie_token():
    """Get a fresh JWT from Mealie."""
    data = "username=changeme@example.com&password=MyPassword123".encode()
    req = urllib.request.Request(
        f"{MEALIE_URL}/api/auth/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    return result["access_token"]


def mealie_get(path, token):
    """GET from Mealie API."""
    req = urllib.request.Request(
        f"{MEALIE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def baserow_get_all(table_id, token):
    """Get all rows from a Baserow table with pagination."""
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


def baserow_delete(table_id, row_id):
    """Delete a row from Baserow."""
    token = get_baserow_token()
    url = f"{BASEROW_URL}/api/database/rows/table/{table_id}/{row_id}/"
    req = urllib.request.Request(url, method="DELETE",
                                 headers={"Authorization": f"Token {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status == 204
    except Exception:
        return False


def categorize_ingredient(name):
    """LLM-free heuristic categorization of ingredients."""
    name_lower = name.lower()

    if any(w in name_lower for w in ["egg", "eggs"]):
        return "Eggs"
    if any(w in name_lower for w in ["chicken", "beef", "pork", "lamb", "turkey", "duck",
                                       "bacon", "sausage", "steak", "mince", "ham", "prosciutto",
                                       "salami", "chorizo", "pancetta", "veal", "venison"]):
        return "Meat"
    if any(w in name_lower for w in ["salmon", "tuna", "cod", "haddock", "prawn", "shrimp",
                                       "fish", "anchovy", "sardine", "mackerel", "trout",
                                       "sea bass", "scallop", "mussel", "clam", "lobster", "crab",
                                       "octopus", "squid", "calamari"]):
        return "Fish"
    if any(w in name_lower for w in ["milk", "cheese", "butter", "cream", "yogurt", "yoghurt",
                                       "feta", "parmesan", "mozzarella", "cheddar", "ricotta",
                                       "mascarpone", "halloumi", "brie", "gouda"]):
        return "Dairy"
    if any(w in name_lower for w in ["rice", "pasta", "noodle", "bread", "flour", "oat",
                                       "quinoa", "couscous", "barley", "wheat", "tortilla",
                                       "wrap", "pita", "lasagne", "spaghetti", "penne", "fusilli",
                                       "orzo", "bulgur", "semolina"]):
        return "Grain"
    if any(w in name_lower for w in ["apple", "banana", "orange", "lemon", "lime", "berry",
                                       "strawberry", "blueberry", "raspberry", "grape", "mango",
                                       "peach", "pear", "plum", "cherry", "pineapple", "melon",
                                       "watermelon", "kiwi", "pomegranate", "fig", "date",
                                       "apricot", "coconut", "avocado"]):
        return "Fruit"
    if any(w in name_lower for w in ["salt", "pepper", "cumin", "coriander", "turmeric",
                                       "paprika", "chili", "chilli", "cinnamon", "nutmeg",
                                       "oregano", "basil", "thyme", "rosemary", "parsley",
                                       "dill", "mint", "sage", "bay leaf", "clove", "cardamom",
                                       "saffron", "fennel seed", "mustard seed", "curry powder",
                                       "garam masala", "five spice", "za'atar", "sumac",
                                       "cayenne", "chipotle", "anise", "fenugreek"]):
        return "Spice"
    if any(w in name_lower for w in ["oil", "vinegar", "sauce", "sugar", "honey", "syrup",
                                       "paste", "canned", "tin", "can", "stock", "broth",
                                       "bouillon", "soy sauce", "fish sauce", "oyster sauce",
                                       "tomato", "passata", "harissa", "tahini", "pesto",
                                       "mayo", "mayonnaise", "ketchup", "mustard", "worcester",
                                       "balsamic", "olive oil", "sesame oil", "vegetable oil",
                                       "coconut milk", "coconut cream", "almond", "walnut",
                                       "peanut", "cashew", "pine nut", "seed", "raisin",
                                       "lentil", "chickpea", "bean", "kidney bean", "black bean",
                                       "cannellini", "borlotti"]):
        return "Pantry"
    if any(w in name_lower for w in ["onion", "garlic", "tomato", "potato", "carrot", "celery",
                                       "pepper", "courgette", "zucchini", "aubergine", "eggplant",
                                       "cucumber", "lettuce", "spinach", "kale", "cabbage",
                                       "broccoli", "cauliflower", "asparagus", "pea", "bean",
                                       "mushroom", "leek", "shallot", "spring onion", "scallion",
                                       "ginger", "chili", "chilli", "sweet potato", "butternut",
                                       "pumpkin", "squash", "beetroot", "radish", "turnip",
                                       "swede", "artichoke", "fennel", "corn", "sweetcorn",
                                       "olive", "capers", "sun-dried"]):
        return "Veg"

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


def get_seasonal_months(ingredient_name):
    """Return seasonal months for common UK ingredients."""
    name_lower = ingredient_name.lower()
    seasonal = {
        "asparagus": ["Apr", "May", "Jun"],
        "pea": ["May", "Jun", "Jul"],
        "radish": ["Mar", "Apr", "May"],
        "spring onion": ["Mar", "Apr", "May"],
        "new potato": ["May", "Jun"],
        "strawberry": ["Jun", "Jul"],
        "tomato": ["Jul", "Aug", "Sep"],
        "cucumber": ["Jun", "Jul", "Aug"],
        "courgette": ["Jun", "Jul", "Aug"],
        "aubergine": ["Jul", "Aug", "Sep"],
        "pepper": ["Jul", "Aug", "Sep"],
        "blueberry": ["Jul", "Aug"],
        "raspberry": ["Jul", "Aug"],
        "peach": ["Jul", "Aug"],
        "cherry": ["Jun", "Jul"],
        "basil": ["Jun", "Jul", "Aug"],
        "sweetcorn": ["Aug", "Sep"],
        "apple": ["Sep", "Oct", "Nov"],
        "pear": ["Sep", "Oct"],
        "plum": ["Aug", "Sep"],
        "blackberry": ["Aug", "Sep", "Oct"],
        "pumpkin": ["Oct", "Nov"],
        "butternut": ["Oct", "Nov", "Dec"],
        "mushroom": ["Sep", "Oct", "Nov"],
        "leek": ["Oct", "Nov", "Dec", "Jan", "Feb"],
        "kale": ["Nov", "Dec", "Jan", "Feb"],
        "brussels sprout": ["Nov", "Dec", "Jan"],
        "cabbage": ["Nov", "Dec", "Jan", "Feb"],
        "parsnip": ["Nov", "Dec", "Jan", "Feb"],
        "swede": ["Nov", "Dec", "Jan", "Feb"],
        "turnip": ["Nov", "Dec", "Jan"],
        "celeriac": ["Nov", "Dec", "Jan"],
        "onion": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "garlic": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "carrot": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "potato": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "celery": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "ginger": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "lemon": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "banana": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    }

    for key, months in seasonal.items():
        if key in name_lower:
            return months
    return []


def find_existing_recipe(slug):
    """Check if a recipe already exists in Baserow by Mealie Slug."""
    token = get_baserow_token()
    all_rows = baserow_get_all(TABLE_RECIPES, token)
    for row in all_rows:
        if row.get("Mealie Slug") == slug:
            return row
    return None


def delete_existing_ingredients(recipe_record_id):
    """Delete all existing ingredient records linked to a recipe."""
    token = get_baserow_token()
    all_rows = baserow_get_all(TABLE_INGREDIENTS, token)
    to_delete = []
    for row in all_rows:
        recipe_links = row.get("Recipe", [])
        if recipe_record_id in recipe_links:
            to_delete.append(row["id"])

    for rid in to_delete:
        baserow_delete(TABLE_INGREDIENTS, rid)
    return len(to_delete)


def sync_recipe(slug):
    """Main sync: fetch from Mealie, create/update Baserow."""
    print(f"🔄 Syncing recipe: {slug}")
    print()

    # 1. Get Mealie token and fetch recipe
    token = get_mealie_token()
    recipe = mealie_get(f"/api/recipes/{slug}", token)

    name = recipe.get("name", slug)
    org_url = recipe.get("orgURL", "")
    description = recipe.get("description", "")

    print(f"  📖 {name}")
    print(f"  🔗 {org_url or 'No source URL'}")
    print()

    # 2. Check for existing Baserow record
    existing = find_existing_recipe(slug)
    if existing:
        print(f"  ℹ️  Recipe already in Baserow (id: {existing['id']}) — updating")
        recipe_record_id = existing["id"]
        delete_existing_ingredients(recipe_record_id)
    else:
        # 3. Create Baserow Recipes record
        recipe_fields = {
            "Name": name,
            "Mealie Slug": slug,
            "Source URL": org_url,
            "Notes": description,
        }

        result = baserow_post(TABLE_RECIPES, recipe_fields)
        if not result:
            print("  ❌ Failed to create Baserow Recipes record", file=sys.stderr)
            return
        recipe_record_id = result["id"]
        print(f"  ✅ Created Baserow Recipes record (id: {recipe_record_id})")

    # 4. Sync ingredients
    ingredients = recipe.get("recipeIngredient", [])
    seen_names = set()
    ingredient_count = 0

    for ing in ingredients:
        raw_text = ing.get("display", "") or ing.get("note", "")
        if not raw_text:
            food = ing.get("food") or {}
            raw_text = food.get("name", "")
        if not raw_text:
            continue

        ing_name = clean_ingredient_name(raw_text)
        if not ing_name or ing_name.lower() in seen_names:
            continue
        seen_names.add(ing_name.lower())

        category = categorize_ingredient(ing_name)
        seasonal = get_seasonal_months(ing_name)

        ing_fields = {
            "Ingredient": ing_name,
            "Recipe": [recipe_record_id],
            "Category": category,
        }
        if seasonal:
            ing_fields["Seasonal"] = seasonal

        baserow_post(TABLE_INGREDIENTS, ing_fields)
        ingredient_count += 1

    print(f"  ✅ Synced {ingredient_count} ingredients")
    print()
    print(f"✅ Sync complete: {name}")
    print(f"   Baserow: {BASEROW_URL}/database/132/table/{TABLE_RECIPES}/{recipe_record_id}")
    if org_url:
        print(f"   Source:   {org_url}")
    print(f"   Mealie:   {MEALIE_URL}/recipes/{slug}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    slug = sys.argv[1]
    sync_recipe(slug)


if __name__ == "__main__":
    main()
