---
name: recipe-parser
description: Parse recipes from raw text or photos, push to Mealie, sync to Airtable. Use when user sends a recipe (text, URL, or photo) in Slack or asks to add a recipe.
version: 1.1.0
triggers:
  - recipe
  - add recipe
  - scan recipe
  - photo of recipe
  - parse recipe
---

# Recipe Parser Skill

Parse recipes from **raw text**, **URLs**, or **photos** → push to **Mealie** → sync to **Airtable**.

## Architecture

```
Input (text/URL/photo)
  ↓
[Vision API — if photo] → raw text
  ↓
[JSON-LD builder] → structured recipe
  ↓
[Mealie API] → recipe stored with ingredients
  ↓
[Airtable sync] → Recipes table + Ingredients table (auto-categorised)
```

**Mealie** = recipe engine (stores full recipe, ingredients, instructions, images)
**Airtable** = metadata layer (Recipes table for lookup, Ingredients table for shopping/dietary cross-checks)

## API Keys

All keys in `~/.hermes/.env`:
- `AIRTABLE_API_KEY` — Airtable PAT
- `NVIDIA_API_KEY` — NVIDIA NIM (vision)
- Mealie: username/password auth (no key needed, get token via `/api/auth/token`)

## Key IDs

| Resource | ID |
|---|---|
| Airtable Base | `appzvmonQXs4x2AlL` |
| Recipes table | `tblehBgzRMa2Xucjd` |
| Ingredients table | `tblNsgbYHNK8xWnB7` |
| Mealie URL | `http://localhost:9925` |
| Mealie user | `changeme@example.com` / `MyPassword123` |

## Airtable Field Names (exact!)

**Recipes table:** `Name`, `Mealie Slug`, `Notes`, `Ingredients` (linked), `Created` (auto)
**Ingredients table:** `Ingredient`, `Category` (single-select), `Recipe` (linked), `Quantity`

Existing Category options: `Meat`, `Fish`, `Veg`, `Fruit`, `Dairy`, `Grain`, `Spice`, `Pantry`, `Eggs`, `Other`

## Workflow

### 1. Photo Input

If user sends a photo (JPEG/PNG):

```bash
# Download from Slack (if url_private available)
curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" "<url_private>" -o /tmp/recipe_photo.jpg
```

Then run vision extraction (see `scripts/vision_extract.py`):

```bash
python3 scripts/vision_extract.py /tmp/recipe_photo.jpg
```

This uses **NVIDIA NIM** (`meta/llama-3.2-11b-vision-instruct`) to extract recipe text from the image.

### 2. Text/URL Input

If user pastes raw text or a URL:
- **URL**: Try `GET /api/recipes/create/url` on Mealie first (scrapes automatically)
- **Raw text**: Build JSON-LD manually (see below)

### 3. Push to Mealie

```python
import json, urllib.request

# Get token
token = json.loads(post("http://localhost:9925/api/auth/token",
    data="username=changeme@example.com&password=MyPassword123",
    headers={"Content-Type": "application/x-www-form-urlencoded"}
).read())["access_token"]

# Push JSON-LD
payload = json.dumps({"data": json.dumps(json_ld)}).encode()
req = urllib.request.Request(
    "http://localhost:9925/api/recipes/create/html-or-json",
    data=payload,
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
)
slug = resp.read().decode().strip().strip('"')
```

Mealie returns the slug as a **plain quoted string** (not JSON).

### 4. Sync to Airtable

Use `scripts/recipe_sync.py` or inline code:

```python
# Create recipe record
airtable_post("tblehBgzRMa2Xucjd", {"fields": {
    "Name": name,
    "Mealie Slug": slug,
    "Notes": f"Source: {source} | Yield: {yield} | ..."
}})

# Sync ingredients with auto-categorisation
airtable_post("tblNsgbYHNK8xWnB7", {"fields": {
    "Ingredient": ing_name,
    "Category": categorise(ing_name),  # map to existing single-select options
    "Recipe": [recipe_id]
}})
```

### 5. Categorisation Map

```python
CATEGORIES = {
    "chicken": "Meat", "beef": "Meat", "pork": "Meat", "lamb": "Meat",
    "salmon": "Fish", "tuna": "Fish", "shrimp": "Fish",
    "onion": "Veg", "garlic": "Veg", "tomato": "Veg", "parsley": "Veg",
    "lemon": "Fruit", "blueberr": "Fruit", "apple": "Fruit",
    "butter": "Dairy", "cheese": "Dairy", "milk": "Dairy", "cream": "Dairy",
    "flour": "Grain", "rice": "Grain", "pasta": "Grain", "bread": "Grain",
    "salt": "Spice", "pepper": "Spice", "paprika": "Spice", "cumin": "Spice",
    "cinnamon": "Spice", "turmeric": "Spice",
    "oil": "Pantry", "sugar": "Pantry", "vinegar": "Pantry",
}
```

Always map to existing single-select options: `Meat`, `Fish`, `Veg`, `Fruit`, `Dairy`, `Grain`, `Spice`, `Pantry`, `Eggs`, `Other`.

## Ingredient Name Cleaning

When syncing to Airtable, ingredient names are **cleaned** before storage:
- Raw: `"2-3 garlic cloves, finely grated"` → Clean: `"Garlic"`
- Raw: `"1/2 tsp ground cumin"` → Clean: `"Cumin"`
- Raw: `"500g full-fat Greek yoghurt (thick/strained)"` → Clean: `"Greek yoghurt"`
- Raw: `"2 tbsp extra-virgin olive oil"` → Clean: `"Olive oil"`

The `clean_ingredient_name()` function in `scripts/push_recipe.py` and `scripts/recipe_sync.py` handles this:
1. Removes parenthetical notes
2. Strips leading quantities and units (cups, tbsp, g, cloves, etc.)
3. Removes preparation instructions (chopped, minced, grated, etc.)
4. Deduplicates within a recipe (case-insensitive)

## Full Pipeline Script

Use `scripts/push_recipe.py` for the complete pipeline:

```bash
python3 scripts/push_recipe.py --photo /tmp/recipe_photo.jpg
python3 scripts/push_recipe.py --text "Recipe: ..."
python3 scripts/push_recipe.py --url "https://..."
```

## Pitfalls

1. **Mealie slug suffix**: If slug exists, Mealie appends `-1`, `-2`, etc. Always use the returned slug.
2. **Airtable field names**: Exact match required — `Mealie Slug` (not `Slug`), `Ingredient` (not `Name`).
3. **Category single-select**: Must use existing options only: `Meat`, `Fish`, `Veg`, `Fruit`, `Dairy`, `Grain`, `Spice`, `Pantry`, `Eggs`, `Other`. Use `typecast=true` to auto-create new options if needed (e.g. "Eggs" was added this way).
4. **Vision API**: NVIDIA NIM works. Google AI Studio key may be invalid. OpenRouter needs credits. Groq vision may be unavailable.
5. **JSON-LD format**: Mealie's `/api/recipes/create/html-or-json` expects `{"data": "<JSON-LD string>"}` — double-encoded JSON.
6. **URL scraping**: Reddit URLs are blocked. BBC Good Food, AllRecipes work. When in doubt, paste raw text.
7. **Duplicate detection**: Always check Airtable for existing `Mealie Slug` before creating.

## Verification

After pushing, verify:
```bash
# Mealie
curl -s "http://localhost:9925/api/recipes/{slug}?loadFood=true" -H "Authorization: Bearer {token}"

# Airtable
# Check Recipes table for the new record
# Check Ingredients table for linked ingredient records
```
