---
name: recipe-parser
description: Parse raw recipe text or photos into structured Mealie-compatible JSON-LD format, push to Mealie, and sync to Airtable. Use when the user pastes a recipe, sends a photo of a recipe, or says "add this recipe" with unstructured text.
---

# Recipe Parser — Raw Text/Photo → Mealie → Airtable

Parse unstructured recipe input (text or photo) into structured data, push to Mealie via the `html-or-json` endpoint, then sync to Airtable.

## Trigger

Use this skill when:
- User pastes raw recipe text (ingredients + instructions)
- User sends a photo of a recipe (cookbook page, handwritten recipe, screenshot)
- User says "add this recipe" with unstructured content
- User says "parse this recipe" or "save this recipe"

## Workflow

### Step 1: Parse the Recipe

#### From Text
If the user provides raw recipe text, parse it into structured JSON-LD (schema.org Recipe format):

```json
{
  "@context": "https://schema.org",
  "@type": "Recipe",
  "name": "Recipe Name",
  "description": "Brief description",
  "recipeIngredient": [
    "2 cups flour",
    "1 tsp salt",
    ...
  ],
  "recipeInstructions": [
    {"@type": "HowToStep", "text": "Step 1 instructions..."},
    {"@type": "HowToStep", "text": "Step 2 instructions..."}
  ],
  "prepTime": "PT20M",
  "cookTime": "PT1H",
  "recipeYield": "8 servings"
}
```

**Parsing rules:**
- Extract recipe name from the first line or a prominent heading
- Split ingredients list: each line = one ingredient with quantity, unit, and name
- Split instructions: numbered steps or paragraphs
- Estimate prep/cook times if mentioned, omit if not
- Extract yield/servings if mentioned

#### From Photo
If the user sends a photo:

1. **Use the `vision_analyze` tool** to read the recipe from the image
2. Extract: name, ingredients (with quantities), instructions, times, yield
3. Format as JSON-LD above

**Photo tips:**
- If the photo is hard to read, ask the user to clarify specific ingredients/quantities
- Handwritten recipes: do your best, flag uncertain items with "(?)"
- Cookbook pages: capture the full recipe including any headnotes

### Step 2: Push to Mealie

Use the `html-or-json` endpoint with schema.org JSON-LD:

```bash
TOKEN=$(curl -s -X POST http://localhost:9925/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=changeme@example.com&password=MyPassword123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Build JSON-LD and push
python3 -c "
import json, urllib.request

token = '$TOKEN'
recipe = {
    '@context': 'https://schema.org',
    '@type': 'Recipe',
    'name': 'RECIPE_NAME',
    'description': 'DESCRIPTION',
    'recipeIngredient': [ ... ],
    'recipeInstructions': [ ... ],
    'prepTime': 'PT20M',
    'cookTime': 'PT1H',
    'recipeYield': 'YIELD',
}

payload = json.dumps({'data': json.dumps(recipe)}).encode()
req = urllib.request.Request(
    'http://localhost:9925/api/recipes/create/html-or-json',
    data=payload,
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(req) as resp:
    slug = resp.read().decode().strip().strip('\"')
    print(f'Slug: {slug}')
"
```

The endpoint returns the slug as a plain quoted string.

### Step 3: Sync to Airtable

Run the existing sync script:

```bash
python3 /root/Geeves/scripts/recipe_sync.py <slug>
```

This creates the Airtable Recipes record and linked Ingredient records with auto-categorisation.

### Step 4: Report Back

Tell the user:
- ✅ Recipe name and slug
- ✅ Number of ingredients parsed and synced
- ✅ Airtable link
- ✅ Mealie link (http://77.68.33.121/mealie/recipes/<slug>)

## Edge Cases

- **No structured ingredients in text:** If the user just pastes a paragraph describing a dish, ask for the ingredient list separately
- **Photo too blurry:** Ask the user to retype the ingredients or send a clearer photo
- **Duplicate recipe:** Check if a recipe with the same name already exists in Airtable before creating
- **Mealie slug collision:** If the slug already exists, Mealie appends a number (e.g., `recipe-name-1`). The sync script handles this — it finds by slug.

## Key Learnings (from testing)

### Mealie API Behaviour
- `POST /api/recipes` with JSON body creates a **stub** — ingredients/instructions are NOT properly parsed
- `POST /api/recipes/create/html-or-json` with `{"data": "<JSON-LD string>"}` is the correct endpoint for programmatic creation
- The `data` field must be a **JSON string** (double-encoded), not a JSON object
- Returns the slug as a plain quoted string: `"recipe-slug"`
- Slug collisions are auto-handled (appends `-1`, `-2`, etc.)

### JSON-LD Format That Works
```json
{
  "@context": "https://schema.org",
  "@type": "Recipe",
  "name": "Recipe Name",
  "description": "...",
  "recipeIngredient": ["quantity unit ingredient, note", ...],
  "recipeInstructions": [
    {"@type": "HowToStep", "text": "Step text..."}
  ],
  "prepTime": "PT20M",
  "cookTime": "PT1H",
  "recipeYield": "8 servings"
}
```

### Sync Script
- `/root/Geeves/scripts/recipe_sync.py <slug>` handles Mealie → Airtable
- Parses the `display` field from Mealie's ingredient format
- Auto-categorises ingredients (heuristic-based)
- Auto-tags seasonal months
- Handles deduplication on re-sync

### Photo Input
- Mealie has `POST /api/recipes/create/image` but it expects `images` (plural) multipart field
- For now, use `vision_analyze` to read the photo, then format as JSON-LD and use `html-or-json` endpoint
- Future: test direct image upload with proper multipart form data
