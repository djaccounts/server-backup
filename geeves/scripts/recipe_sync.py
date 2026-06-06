#!/usr/bin/env python3
"""
recipe_sync.py — Mealie → Airtable Recipe Sync

Fetches a recipe from Mealie by slug, creates/updates the Airtable Recipes
record and linked Ingredient records.

Usage:
    python3 recipe_sync.py <mealie_slug>
    python3 recipe_sync.py horiatiki-greek-village-salad-1

Environment:
    AIRTABLE_API_KEY — read from ~/.hermes/.env
    MEALIE_URL        — defaults to http://localhost:9925
"""
import subprocess, json, sys, os, re
import urllib.request, urllib.error, urllib.parse

ENV_PATH = os.path.expanduser("~/.hermes/.env")
BASE = "appzvmonQXs4x2AlL"
MEALIE_URL = os.environ.get("MEALIE_URL", "http://localhost:9925")

# Airtable table IDs
TABLE_RECIPES = "tblehBgzRMa2Xucjd"
TABLE_INGREDIENTS = "tblNsgbYHNK8xWnB7"


def get_key():
    r = subprocess.run(["grep", "AIRTABLE_API_KEY", ENV_PATH], capture_output=True, text=True)
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


def airtable_get(table, formula=""):
    """GET from Airtable with optional filter."""
    key = get_key()
    url = f"https://api.airtable.com/v0/{BASE}/{table}"
    if formula:
        url += f"?filterByFormula={urllib.parse.quote(formula, safe='')}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def airtable_post(table, fields):
    """POST to Airtable."""
    key = get_key()
    data = json.dumps({"fields": fields}).encode()
    req = urllib.request.Request(
        f"https://api.airtable.com/v0/{BASE}/{table}",
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def airtable_patch(table, record_id, fields):
    """PATCH an Airtable record."""
    key = get_key()
    data = json.dumps({"fields": fields}).encode()
    req = urllib.request.Request(
        f"https://api.airtable.com/v0/{BASE}/{table}/{record_id}",
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="PATCH",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def categorize_ingredient(name):
    """LLM-free heuristic categorization of ingredients."""
    name_lower = name.lower()

    # Meat
    if any(w in name_lower for w in ["chicken", "beef", "pork", "lamb", "turkey", "duck",
                                       "bacon", "sausage", "steak", "mince", "ham", "prosciutto",
                                       "salami", "chorizo", "pancetta", "veal", "venison"]):
        return "Meat"

    # Fish
    if any(w in name_lower for w in ["salmon", "tuna", "cod", "haddock", "prawn", "shrimp",
                                       "fish", "anchovy", "sardine", "mackerel", "trout",
                                       "sea bass", "scallop", "mussel", "clam", "lobster", "crab",
                                       "octopus", "squid", "calamari"]):
        return "Fish"

    # Dairy
    if any(w in name_lower for w in ["milk", "cheese", "butter", "cream", "yogurt", "yoghurt",
                                       "feta", "parmesan", "mozzarella", "cheddar", "ricotta",
                                       "mascarpone", "halloumi", "brie", "gouda", "egg", "eggs"]):
        return "Dairy"

    # Grain
    if any(w in name_lower for w in ["rice", "pasta", "noodle", "bread", "flour", "oat",
                                       "quinoa", "couscous", "barley", "wheat", "tortilla",
                                       "wrap", "pita", "lasagne", "spaghetti", "penne", "fusilli",
                                       "orzo", "bulgur", "semolina"]):
        return "Grain"

    # Fruit
    if any(w in name_lower for w in ["apple", "banana", "orange", "lemon", "lime", "berry",
                                       "strawberry", "blueberry", "raspberry", "grape", "mango",
                                       "peach", "pear", "plum", "cherry", "pineapple", "melon",
                                       "watermelon", "kiwi", "pomegranate", "fig", "date",
                                       "apricot", "coconut", "avocado"]):
        return "Fruit"

    # Spice
    if any(w in name_lower for w in ["salt", "pepper", "cumin", "coriander", "turmeric",
                                       "paprika", "chili", "chilli", "cinnamon", "nutmeg",
                                       "oregano", "basil", "thyme", "rosemary", "parsley",
                                       "dill", "mint", "sage", "bay leaf", "clove", "cardamom",
                                       "saffron", "fennel seed", "mustard seed", "curry powder",
                                       "garam masala", "five spice", "za'atar", "sumac",
                                       "cayenne", "chipotle", "anise", "fenugreek"]):
        return "Spice"

    # Pantry
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

    # Veg (catch-all for vegetables)
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


def get_seasonal_months(ingredient_name):
    """Return seasonal months for common UK ingredients. Very approximate."""
    name_lower = ingredient_name.lower()
    seasonal = {
        # Spring
        "asparagus": ["Apr", "May", "Jun"],
        "pea": ["May", "Jun", "Jul"],
        "radish": ["Mar", "Apr", "May"],
        "spring onion": ["Mar", "Apr", "May"],
        "new potato": ["May", "Jun"],
        "strawberry": ["Jun", "Jul"],
        # Summer
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
        # Autumn
        "apple": ["Sep", "Oct", "Nov"],
        "pear": ["Sep", "Oct"],
        "plum": ["Aug", "Sep"],
        "blackberry": ["Aug", "Sep", "Oct"],
        "pumpkin": ["Oct", "Nov"],
        "butternut": ["Oct", "Nov", "Dec"],
        "mushroom": ["Sep", "Oct", "Nov"],
        "leek": ["Oct", "Nov", "Dec", "Jan", "Feb"],
        # Winter
        "kale": ["Nov", "Dec", "Jan", "Feb"],
        "brussels sprout": ["Nov", "Dec", "Jan"],
        "cabbage": ["Nov", "Dec", "Jan", "Feb"],
        "parsnip": ["Nov", "Dec", "Jan", "Feb"],
        "swede": ["Nov", "Dec", "Jan", "Feb"],
        "turnip": ["Nov", "Dec", "Jan"],
        "celeriac": ["Nov", "Dec", "Jan"],
        # Year-round
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
    return []  # Unknown seasonality


def find_existing_recipe(slug):
    """Check if a recipe already exists in Airtable by Mealie Slug."""
    result = airtable_get(TABLE_RECIPES, f"{{Mealie Slug}}='{slug}'")
    records = result.get("records", [])
    return records[0] if records else None


def delete_existing_ingredients(recipe_record_id):
    """Delete all existing ingredient records linked to a recipe."""
    # Get all records and filter locally (formula filter is unreliable for link fields)
    result = airtable_get(TABLE_INGREDIENTS)
    to_delete = []
    for r in result.get("records", []):
        recipe_links = r.get("fields", {}).get("Recipe", [])
        if recipe_record_id in recipe_links:
            to_delete.append(r["id"])

    for rid in to_delete:
        key = get_key()
        req = urllib.request.Request(
            f"https://api.airtable.com/v0/{BASE}/{TABLE_INGREDIENTS}/{rid}",
            headers={"Authorization": f"Bearer {key}"},
            method="DELETE",
        )
        try:
            urllib.request.urlopen(req)
        except Exception:
            pass
    return len(to_delete)


def sync_recipe(slug):
    """Main sync: fetch from Mealie, create/update Airtable."""
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

    # 2. Check for existing Airtable record
    existing = find_existing_recipe(slug)
    if existing:
        print(f"  ℹ️  Recipe already in Airtable (id: {existing['id']}) — updating")
        recipe_record_id = existing["id"]
        # Delete old ingredients (will re-create)
        delete_existing_ingredients(recipe_record_id)
    else:
        # 3. Create Airtable Recipes record
        recipe_fields = {
            "Name": name,
            "Mealie Slug": slug,
            "Source URL": org_url,
            "Notes": description,
        }

        # Try to extract photo
        if recipe.get("image"):
            recipe_fields["Photo"] = [{"url": f"{MEALIE_URL}/api/media/recipes/{slug}/image"}]

        result = airtable_post(TABLE_RECIPES, recipe_fields)
        recipe_record_id = result["id"]
        print(f"  ✅ Created Airtable Recipes record (id: {recipe_record_id})")

    # 4. Sync ingredients
    ingredients = recipe.get("recipeIngredient", [])
    seen_displays = set()
    ingredient_count = 0

    for ing in ingredients:
        display = ing.get("display", "")
        if not display or display in seen_displays:
            continue
        seen_displays.add(display)

        # Parse quantity and ingredient name from display
        # Display format is typically: "500g Chicken thighs" or "2 tbsp olive oil"
        quantity = ""
        ing_name = display

        # Try to extract quantity from the beginning
        qty_match = re.match(r'^([\d./]+\s*\w*)\s+(.+)$', display)
        if qty_match:
            quantity = qty_match.group(1).strip()
            ing_name = qty_match.group(2).strip()

        # Use 'note' field if available for cleaner name
        if ing.get("note") and not ing.get("food"):
            ing_name = ing["note"]
            quantity = str(ing.get("quantity", "")) + " " + str(ing.get("unit", "")).strip()
            quantity = quantity.strip()

        category = categorize_ingredient(ing_name)
        seasonal = get_seasonal_months(ing_name)

        ing_fields = {
            "Ingredient": ing_name,
            "Recipe": [recipe_record_id],
            "Quantity": quantity,
            "Category": category,
        }
        if seasonal:
            ing_fields["Seasonal"] = seasonal

        airtable_post(TABLE_INGREDIENTS, ing_fields)
        ingredient_count += 1

    print(f"  ✅ Synced {ingredient_count} ingredients")
    print()
    print(f"✅ Sync complete: {name}")
    print(f"   Airtable: https://airtable.com/{BASE}/{TABLE_RECIPES}/{recipe_record_id}")
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
