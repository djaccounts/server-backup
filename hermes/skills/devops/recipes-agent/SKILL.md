---
name: recipes-agent
description: "Geeves Recipes Agent — Mealie recipe management, Airtable sync, meal logging, dinner party planning, and shopping list generation. Use when adding recipes, planning meals, logging what you ate, planning dinner parties, or managing the recipe module."
version: 1.0.0
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
| Ingredient | text | Mealie `display` |
| Recipe | link → Recipes | Set during sync |
| Quantity | text | Mealie `quantity` + `unit` |
| Category | select | LLM categorises |
| Seasonal | multi-select | LLM infers |

### Other Tables

- **Dinner Parties** — links guests to recipes, auto-compiles dietary constraints, generates shopping lists
- **Dinner Planner** — forward-looking (what I intend to cook)
- **Recipe Context** — permanent preferences fed into prompts
- **Recipe Output Log** — prevents repetition
- **Dining Preferences** — bridge table for Restaurant Finder (auto-populated)

**⚠ Dinner Planner ≠ Meals.** Planner = forward-looking. Meals = backward-looking. Both link to Recipes but serve different purposes.

## Workflows

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

1. **SPA intercepts non-API routes** — `/api/openapi.json` returns HTML, not OpenAPI spec
2. **Shell variable persistence** — tokens lost across `terminal()` calls; always chain
3. **Default password may not work** — reset via SQLite if 401
4. **Duplicate ingredients** — deduplicate by `display` field
5. **BASE_URL must match access URL** — update when changing from port to path-based access
6. **POST returns plain string** — parse with `strip().strip('"')`, not `json.load()`

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Get David's explicit approval before creating any Airtable table
- Thread decisions supersede reference docs

## Reference

- `public-apis` skill — PDFBolt details
- `geeves-airtable/references/recipe-module.md` — full schema, sync flows, cross-module links
- `mealie` skill — Docker setup, auth troubleshooting, API quick reference
