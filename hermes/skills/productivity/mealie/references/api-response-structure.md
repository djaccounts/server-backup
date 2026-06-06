# Mealie API — Response Structure Reference

## Recipe Object (GET /api/recipes/{slug})

Top-level fields on a real recipe (confirmed 2026-06-05):

```json
{
  "id": "uuid",
  "userId": "uuid",
  "householdId": "uuid",
  "groupId": "uuid",
  "name": "Recipe Name",
  "slug": "recipe-name-slug",
  "image": null,
  "recipeServings": 0.0,
  "recipeYieldQuantity": 0.0,
  "recipeYield": null,
  "totalTime": null,
  "prepTime": null,
  "cookTime": null,
  "performTime": null,
  "description": "",
  "recipeCategory": [],
  "tags": [],
  "tools": [],
  "rating": null,
  "orgURL": null,
  "dateAdded": "2026-06-05",
  "dateUpdated": "2026-06-05T07:27:19.723293Z",
  "createdAt": "2026-06-05T07:27:19.724549Z",
  "updatedAt": "2026-06-05T07:27:19.724550Z",
  "lastMade": null,
  "nutrition": {
    "calories": null,
    "carbohydrateContent": null,
    "cholesterolContent": null,
    "fatContent": null,
    "fiberContent": null,
    "proteinContent": null,
    "saturatedFatContent": null,
    "sodiumContent": null,
    "sugarContent": null,
    "transFatContent": null,
    "unsaturatedFatContent": null
  },
  "settings": {
    "public": false,
    "showNutrition": false,
    "showAssets": false,
    "landscapeView": false,
    "disableComments": false,
    "disableAmount": true,
    "locked": false
  },
  "assets": [],
  "notes": [],
  "extras": {},
  "comments": []
}
```

## Ingredient Object

```json
{
  "quantity": 1.0,
  "unit": null,
  "food": null,
  "note": "1 Cup Flour",
  "isFood": false,
  "disableAmount": true,
  "display": "1 Cup Flour",
  "title": null,
  "originalText": null,
  "referenceId": "uuid"
}
```

**Key fields for sync:**
- `display` — the human-readable string (use this for deduplication)
- `quantity` — numeric amount (may be null)
- `unit` — may be null even when quantity exists
- `note` — often contains the full text when structured parsing failed
- `isFood` — whether Mealie matched it to a food entity

**Deduplication:** Recipes with variations return ingredients repeated per variation. Always deduplicate by `display` field using `seen = set()`.

## Instruction Object

```json
{
  "id": "uuid",
  "title": "",
  "summary": "",
  "text": "Step instructions... markdown supported",
  "ingredientReferences": []
}
```

**Variation headers:** Instructions whose `text` starts with `"Variation:"` (case-insensitive) are section dividers, not steps. Split into sections at these boundaries.

## Nutrition Object

All values are strings or null. Common keys: `calories`, `proteinContent`, `carbohydrateContent`, `fatContent`, `fiberContent`, `sodiumContent`, `sugarContent`.

**Note:** Nutrition is often all-null for scraped recipes unless the source site included structured nutrition data.

## lastMade Field

- `lastMade`: null (default) or ISO date string
- This is the sync-back target: when a Meal is logged in Airtable linked to this recipe, PATCH this field with the meal date
- Enables "when did I last make this?" queries against Mealie

## List Response (GET /api/recipes)

```json
{
  "page": 1,
  "perPage": 50,
  "total": 10,
  "total_pages": 10,
  "items": [...],
  "next": "/recipes?orderDirection=desc&page=2&perPage=50",
  "previous": null
}
```

**Note:** List endpoint returns a subset of fields (no `recipeIngredient`, `recipeInstructions`, or `nutrition`). Always fetch full recipe by slug for complete data.
