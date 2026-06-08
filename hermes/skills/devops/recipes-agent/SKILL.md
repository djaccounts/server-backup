---
name: recipes-agent
description: "Geeves Recipes Agent — Mealie recipe management, Airtable sync, meal logging, dinner party planning, shopping list generation, and recipe discovery via web search. Use when adding recipes, planning meals, logging what you ate, planning dinner parties, searching for recipe ideas, or managing the recipe module."
version: 1.2.0
author: Geeves
---

# Recipes Agent

Manages the recipe module: Mealie as the recipe engine, Airtable as the metadata/sync layer.

## Architecture

- **Mealie** (port 9925): URL scraping, ingredient parsing, nutrition, scaling, images, full-text search
- **Airtable**: Cross-module links (people, meals, dinner parties), ratings, preferences, shopping lists
- **Sync direction:** Mealie → Airtable (one-way). Edits in Mealie sync to Airtable. Edits in Airtable (ratings, notes) stay in Airtable.

## Mealie API

**Base URL:** `http://localhost:9925`

### Auth (JWT)

```bash
TOKEN=$(curl -s -X POST http://localhost:9925/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=changeme@example.com&password=MyPassword123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

**⚠ Chain token capture and API usage in ONE command.** Shell variables don't persist across `terminal()` calls.

### Key Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Import from URL | POST | `/api/recipes/create/url` |
| Bulk import | POST | `/api/recipes/create/url/bulk` |
| Test scrape | POST | `/api/recipes/test-scrape-url` |
| Get recipe | GET | `/api/recipes/{slug}` |
| Update recipe | PATCH | `/api/recipes/{slug}` |
| Delete recipe | DELETE | `/api/recipes/{slug}` |
| Duplicate | POST | `/api/recipes/{slug}/duplicate` |
| List/search | GET | `/api/recipes?search=keyword` |

**⚠ POST `/api/recipes/create/url` returns a plain string** (the slug), NOT JSON. Parse with `result.strip().strip('"')`.

### Fetch Full Recipe

```bash
TOKEN=$(curl -s -X POST http://localhost:9925/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=changeme@example.com&password=MyPassword123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])") \
  && curl -s http://localhost:9925/api/recipes/{slug} \
     -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Ingredient Deduplication

Recipes with variations return ingredients repeated. Deduplicate by `display` field:

```python
seen = set()
unique = []
for ing in recipe["recipeIngredient"]:
    key = ing.get("display", "")
    if key not in seen:
        seen.add(key)
        unique.append(ig)
```

## Airtable Tables

### Recipes (slim metadata)

| Field | Type | Source |
|-------|------|--------|
| Name | text | Mealie `name` |
| Mealie Slug | text | Mealie `slug` |
| Source URL | text | Mealie `orgURL` |
| Cuisine | select | LLM infers |
| Meal type | multi-select | LLM infers |
| Quality rating | rating 1-5 | User in Slack |
| Will do again | select | User feedback |
| Favourite | checkbox | User |
| Times cooked | rollup | Count from Meals |
| Last cooked | date | From Meals |
| Ingredients | link → Ingredients | Synced from Mealie |
| Photo | attachment | Mealie image URL |
| Notes | long text | Freeform |

### Ingredients (synced from Mealie)

| Field | Type | Source |
|-------|------|--------|
| Ingredient | text | Cleaned name (no qty/unit/prep) |
| Recipe | link → Recipes | Set during sync |
| Category | select | Heuristic categorises |
| Seasonal | multi-select | LLM infers |

**Ingredient name cleaning:** The `Ingredient` field stores ONLY the clean ingredient name (e.g., "Garlic"), NOT the full raw recipe line (e.g., "2-3 garlic cloves, finely grated"). The `clean_ingredient_name()` function in `recipe_sync.py` and `push_recipe.py` handles this:
1. Removes parenthetical notes
2. Strips leading quantities and units (cups, tbsp, g, cloves, etc.)
3. Removes preparation instructions (chopped, minced, grated, etc.)
4. Deduplicates within a recipe (case-insensitive)

**Category options:** `Meat`, `Fish`, `Veg`, `Fruit`, `Dairy`, `Grain`, `Spice`, `Pantry`, `Eggs`, `Other`
- "Eggs" was added via `typecast=true` (Metadata API rejects new options directly)
- Eggs are NOT in Dairy — they have their own category

### Other Tables

- **Dinner Parties** — links guests to recipes, auto-compiles dietary constraints, generates shopping lists
- **Dinner Planner** — forward-looking (what I intend to cook)
- **Recipe Context** — permanent preferences fed into prompts
- **Recipe Output Log** — prevents repetition
- **Dining Preferences** — bridge table for Restaurant Finder (auto-populated)

**⚠ Dinner Planner ≠ Meals.** Planner = forward-looking. Meals = backward-looking. Both link to Recipes but serve different purposes.

## Workflows

### Recipe Ideas & Web Search (Discovery)

**When to use:** User asks for recipe ideas, inspiration, or "what can I make with X" and the local Mealie collection is too small to draw from.

**Approach:** Use SerpApi (Google engine) via the `public-apis` skill to search the web for real, citable recipes.

**Script pattern** (write to `/tmp/` and run — do NOT use `execute_code`, and do NOT interpolate the key directly in shell):

```python
# Write this to /tmp/search_recipes.py, then run with: python3 /tmp/search_recipes.py
import subprocess, json, urllib.parse, urllib.request

# Get key safely — handles special chars (=, +, /) that break shell interpolation
r = subprocess.run(["grep", "SERPAPI_KEY", "/root/.hermes/.env"], capture_output=True, text=True)
key = r.stdout.strip().split("\n")[0].split("=", 1)[1]

params = urllib.parse.urlencode({
    "q": "your search query here leftover chicken quick dinner",
    "engine": "google",
    "api_key": key,
    "num": 10,
    "hl": "en"
})
url = f"https://serpapi.com/search?{params}"
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read().decode())

for r in data.get("organic_results", []):
    print(r.get("title",""))
    print(r.get("link",""))
    s = r.get("snippet","")
    if s: print(">", s[:150])
    print()
```

**Rules:**
- Always cite the source URL with each recipe suggestion
- Prefer reputable sources (BBC GoodFood, AllRecipes, established food blogs)
- After presenting ideas, offer to add any chosen recipe to Mealie via the "Add Recipe from URL" workflow
- Do NOT fabricate recipe details from training knowledge when the user asked you to search — only present what the search actually returned
- If SerpApi returns no useful results, try a second query with different keywords before falling back to general knowledge

### Add Recipe from URL
1. Mealie `POST /api/recipes/create/url` → scrape
2. Read back via `GET /api/recipes/{slug}`
3. Create Airtable Recipes record
4. Create Airtable Ingredient records (LLM categorises)
5. Update Recipe Output Log

### Log Meal (with recipe)
1. Find recipe in Airtable by name/slug
2. Fetch nutrition from Mealie
3. Create Meals record with macros
4. PATCH Mealie `lastMade` with meal date

### Dinner Party Planning
1. Pull guests from People graph → dietary constraints
2. Suggest recipes (filter by Favourites, high rating, cuisine preferences)
3. Check ingredients against allergies → flag conflicts
4. Generate shopping list (merge duplicates, sort by category)
5. Create Dinner Party record + Output Log entry

### Email/PDF Recipe
- **Email:** Fetch from Mealie → format (ingredients → method → nutrition → source) → AgentMail
- **PDF:** Format → PDFBolt → send as attachment
- **Trigger:** "email me the [recipe name]" or "PDF the [recipe name]"

## Mealie Pitfalls

0. **`execute_code` is blocked in some sessions** — when you need to run Python that calls subprocess or API keys, write the script to `/tmp/` with `write_file` and run it via `terminal(command="python3 /tmp/script.py")`. This also avoids shell interpolation issues with special characters in API keys.
1. **SPA intercepts non-API routes** — `/api/openapi.json` returns HTML, not OpenAPI spec
2. **Shell variable persistence** — tokens lost across `terminal()` calls; always chain
3. **Default password may not work** — reset via SQLite if 401
4. **Duplicate ingredients** — deduplicate by cleaned name (case-insensitive), NOT by raw display string
5. **BASE_URL must match access URL** — update when changing from port to path-based access
6. **POST returns plain string** — parse with `strip().strip('"')`, not `json.load()`
7. **Slug suffix on re-push** — Mealie appends `-1`, `-2`, etc. when slug exists. Delete old versions first if you want clean slugs. Mealie PATCH can rename: `PATCH /api/recipes/{slug}` with `{"name": "...", "slug": "..."}`.
8. **`food` field can be null** — Use `ing.get("food") or {}` before `.get("name")` to avoid `AttributeError`
9. **Ingredient `display` field is raw** — Contains full recipe line (qty + unit + name + prep). Must be cleaned before storing in Airtable.

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Get David's explicit approval before creating any Airtable table
- Thread decisions supersede reference docs

## Reference

- `public-apis` skill — PDFBolt details
- `geeves-airtable/references/recipe-module.md` — full schema, sync flows, cross-module links
- `mealie` skill — Docker setup, auth troubleshooting, API quick reference
