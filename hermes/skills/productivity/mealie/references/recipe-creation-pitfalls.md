# Mealie — Recipe Creation Pitfalls

## POST /api/recipes — Structured Ingredients Not Parsed

Sending `recipeIngredient` arrays via `POST /api/recipes` creates a **stub recipe** with a single placeholder ingredient. The structured data is silently discarded.

**Workaround:** Use URL scraping (`POST /api/recipes/create/url`) for sites with good schema.org markup (BBC Good Food, Serious Eats, Minimalist Baker, WordPress food blogs).

**Sites that block scrapers** (return 400 BAD_RECIPE_DATA or HTTP errors):
- Reddit (all subreddits)
- AllRecipes
- Jamie Oliver
- NYT Cooking

For these, manually enter the recipe in Mealie's UI, then use the sync script.

## PATCH /api/recipes/{slug} — Ingredient Format

The PATCH endpoint is strict about ingredient format. Scraped recipes store ingredients as:
```json
{
  "quantity": 1.0,
  "unit": null,
  "food": null,
  "note": "1 tbsp olive oil",
  "isFood": false,
  "disableAmount": true,
  "display": "1 tbsp olive oil",
  "referenceId": "uuid..."
}
```

All meaningful data is in the `note` and `display` fields. `food` and `unit` are null for scraped recipes.

**When writing a sync script:** Parse the `display` field using regex to extract quantity + ingredient name. Don't try to reconstruct structured food/unit objects — the PATCH endpoint returns 500 TypeError.

## filterByFormula and Link Fields

Airtable's `filterByFormula` doesn't work reliably for `multipleRecordLinks` fields. When finding all ingredients linked to a recipe:
1. GET all records (no filter)
2. Filter locally by checking if the recipe ID is in the `Recipe` array

## Duplicate Prevention on Re-sync

When re-syncing a recipe:
1. Fetch all Ingredient records
2. Find those linked to the recipe ID
3. DELETE them all
4. Re-create from Mealie's current data

This prevents duplicates from accumulating on each sync.
