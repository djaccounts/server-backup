---
name: recipe-parser
description: Parse raw recipe text or photos into structured Mealie-compatible JSON-LD format, push to Mealie, and sync to Baserow. Use when the user pastes a recipe, sends a photo of a recipe, or says "add this recipe" with unstructured text.
---

# Recipe Parser — Raw Text/Photo → Mealie → Baserow

Parse unstructured recipe input (text or photo) into structured data, push to Mealie via the `html-or-json` endpoint, then sync to Baserow.

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

1. **Download the file** using the Slack `files:read` scope (if from Slack) or read directly from a local path
2. **Use the vision API fallback chain** to read the recipe from the image. Try providers in order — use the first one that works:

**Provider priority (tested June 2026):**
1. **NVIDIA NIM** ✅ — `meta/llama-3.2-11b-vision-instruct` at `https://integrate.api.nvidia.com/v1/chat/completions`
2. **OpenRouter** — `google/gemini-2.5-flash` at `https://openrouter.ai/api/v1/chat/completions` (may need credits)
3. **Google AI Studio** — `gemini-2.0-flash` at `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=KEY`
4. **Groq** — `llama-3.2-11b-vision-instruct` at `https://api.groq.com/openai/v1/chat/completions`

**Critical: API key extraction from `.env`**

API keys in `~/.hermes/.env` may contain special characters (`=`, `+`, `/`) that break inline string literals in both Python and shell. **Never embed keys directly in source code.** Use one of these patterns:

```python
# Python: line-by-line parsing (safe for all special chars)
api_key = None
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        if line.strip().startswith("NVIDIA_API_KEY="):
            api_key = line.strip().split("=", 1)[1]
            break
```

```python
# Python: via subprocess (avoids regex/string issues entirely)
import subprocess
result = subprocess.run(
    ["bash", "-c", "grep NVIDIA_API_KEY /root/.hermes/.env | head -1 | sed 's/.*=//'"],
    capture_output=True, text=True
)
api_key = result.stdout.strip()
```

**Working vision call pattern (NVIDIA NIM):**

```python
import base64, json, urllib.request, urllib.error, subprocess

# Get key safely
result = subprocess.run(
    ["bash", "-c", "grep NVIDIA_API_KEY /root/.hermes/.env | head -1 | sed 's/.*=//'"],
    capture_output=True, text=True
)
api_key = result.stdout.strip()

# Encode image
with open("/tmp/recipe_photo.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("utf-8")

payload = json.dumps({
    "model": "meta/llama-3.2-11b-vision-instruct",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
            {"type": "text", "text": "Read this recipe photo carefully. Extract: 1) Recipe name, 2) All ingredients with quantities and units (one per line), 3) All instructions/steps (numbered), 4) Prep time, cook time, serving size if mentioned. Format clearly with INGREDIENTS and INSTRUCTIONS sections."}
        ]
    }],
    "max_tokens": 2048
}).encode("utf-8")

req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=payload,
    headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
)
with urllib.request.urlopen(req, timeout=120) as resp:
    result = json.loads(resp.read().decode("utf-8"))
    recipe_text = result["choices"][0]["message"]["content"]
```

3. Parse the extracted text into JSON-LD format
4. Continue with Step 2 (Push to Mealie) below

**Photo tips:**
- If the photo is hard to read, ask the user to clarify specific ingredients/quantities
- Handwritten recipes: do your best, flag uncertain items with "(?)"
- Cookbook pages: capture the full recipe including any headnotes
- If all vision providers fail, ask the user to type out the recipe or paste a URL

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

### Step 3: Sync to Baserow

Run the existing sync script:

```bash
python3 /root/Geeves/scripts/recipe_sync.py <slug>
```

This creates the Baserow Recipes record (table 379) and linked Ingredient records (table 375) with auto-categorisation.

### Step 4: Report Back

Tell the user:
- ✅ Recipe name and slug
- ✅ Number of ingredients parsed and synced
- ✅ Baserow link (http://77.68.33.121/database/132/table/379)
- ✅ Mealie link (http://77.68.33.121:9925/recipes/<slug>)

## Edge Cases

- **No structured ingredients in text:** If the user just pastes a paragraph describing a dish, ask for the ingredient list separately
- **Photo too blurry:** Ask the user to retype the ingredients or send a clearer photo
- **Duplicate recipe:** Check if a recipe with the same slug already exists in Baserow before creating
- **Mealie slug collision (expected behaviour):** Mealie auto-appends `-1`, `-2`, `-3` etc. when a similar slug already exists. This is **normal and fine** — don't try to avoid it.
- **Mealie ingredient `food` field can be null:** When parsing ingredients from `GET /api/recipes/{slug}?loadFood=true`, the `food` key may be `null`. Always use `ing.get("food") or {}` before accessing `.get("name")` — otherwise `AttributeError: 'NoneType' object has no attribute 'get'`.
- **Mealie ingredients are dicts, not strings:** The `?loadFood=true` endpoint returns ingredients as `{"display": "...", "note": "...", "food": {...}}` dicts. Extract text with `ing.get("display", "") or ing.get("note", "") or ing.get("food", {}).get("name", "")`.

## Baserow Field Names (Exact — Do Not Guess)

**Recipes table** (ID: 379):
- `Name` — text
- `Mealie Slug` — text
- `Source URL` — text
- `Notes` — long_text

**Ingredients table** (ID: 375):
- `Ingredient` — text
- `Category` — singleSelect (must use existing options only)
- `Recipe` — link_row → Recipes table
- `Quantity` — text
- `Seasonal` — multiple_select

**Category single-select options** (exact strings): `Meat`, `Fish`, `Veg`, `Fruit`, `Dairy`, `Grain`, `Spice`, `Pantry`, `Eggs`, `Other`

## Full Pipeline Script

For the complete photo/text/URL → Mealie → Baserow pipeline, use:
```
python3 /root/Geeves/skills/recipe-parser/scripts/push_recipe.py --photo /path/to/image.jpg
python3 /root/Geeves/skills/recipe-parser/scripts/push_recipe.py --text "recipe text..."
python3 /root/Geeves/skills/recipe-parser/scripts/push_recipe.py --json-ld '{"@type":"Recipe",...}'
```

For Mealie → Baserow sync only (e.g., after manual Mealie edits):
```
python3 /root/Geeves/scripts/recipe_sync.py <slug>
```

## Ingredient Name Cleaning

When syncing to Baserow, ingredient names are **cleaned** — the `Ingredient` field stores ONLY the ingredient name, not the full recipe line. See `references/ingredient-cleaning.md` for the full algorithm, category mapping, and examples.

## Listing & Deduplicating Mealie Recipes

To list all recipes in Mealie:
```bash
python3 /root/.hermes/skills/productivity/recipe-parser/scripts/list_mealie_recipes.py
```

To find potential duplicates (groups by normalised name):
```bash
python3 /root/.hermes/skills/productivity/recipe-parser/scripts/list_mealie_recipes.py --dupes
```

To delete a specific recipe by slug:
```bash
python3 /root/.hermes/skills/productivity/recipe-parser/scripts/list_mealie_recipes.py --delete-slug <slug>
```

**Deduplication workflow:**
1. Run with `--dupes` to see grouped duplicates
2. Decide which slug to keep (usually the highest `-N` number = most recent)
3. Delete unwanted slugs with `--delete-slug`
4. Also clean up corresponding Baserow records and linked ingredients

## Reference Files

- `references/baserow-schema.md` — Exact field names, category options, API gotchas
- `references/vision-providers.md` — Vision API provider status and priority order
- `references/ingredient-cleaning.md` — Ingredient name cleaning algorithm

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
- `/root/Geeves/scripts/recipe_sync.py <slug>` handles Mealie → Baserow
- Parses the `display` field from Mealie's ingredient format (dicts, not strings)
- Auto-categorises ingredients (heuristic-based)
- Auto-tags seasonal months
- Handles deduplication on re-sync

### Baserow API Gotchas
- Use `baserow_api.py create-row` for writes (handles field name→ID + select option resolution)
- Use `baserow_api.py list-rows --json --limit N` for reads (machine-readable)
- `create-row` outputs `Created: row N` — parse with `stdout.split("Created: row")[1].strip()`
- `single_select` fields return `{"id": N, "value": "..."}` dicts — use `get_select_value()` helper
- Date fields are naive — add `.replace(tzinfo=timezone.utc)` before comparing
- `order_by` param returns 400 — sort client-side
- Number fields may return strings — cast to `int()` before `f"{val:,}"` formatting

### Photo Input
- Mealie has `POST /api/recipes/create/image` but it expects `images` (plural) multipart field
- For now, use `vision_analyze` to read the photo, then format as JSON-LD and use `html-or-json` endpoint
- Future: test direct image upload with proper multipart form data
