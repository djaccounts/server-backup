# Airtable Schema Reference — Recipe Module

Last verified: June 2026

## Base

- **Base ID:** `appzvmonQXs4x2AlL` (Geeves)
- **API key:** `AIRTABLE_API_KEY` in `~/.hermes/.env`

## Tables

### Recipes (`tblehBgzRMa2Xucjd`)

| Field | Type | Notes |
|-------|------|-------|
| `Name` | singleLineText | Recipe title |
| `Mealie Slug` | singleLineText | **NOT `Slug`** — exact name with space |
| `Notes` | multilineText | Source, yield, times, etc. |
| `Ingredients` | multipleRecordLinks | → Ingredients table |

### Ingredients (`tblNsgbYHNK8xWnB7`)

| Field | Type | Notes |
|-------|------|-------|
| `Ingredient` | singleLineText | **NOT `Name`** — exact name |
| `Category` | singleSelect | Must use existing options only (see below) |
| `Recipe` | multipleRecordLinks | → Recipes table |
| `Quantity` | singleLineText | Optional |

## Category Single-Select Options

**Exact strings** (case-sensitive): `Meat`, `Fish`, `Veg`, `Fruit`, `Dairy`, `Grain`, `Spice`, `Pantry`, `Other`

⚠️ Creating new options via API returns HTTP 422 "Insufficient permissions". Always map to existing options.

## Category Mapping Heuristics

| Keyword in ingredient | Category |
|----------------------|----------|
| chicken, beef, pork, lamb, thighs, bacon, mince, sausage | Meat |
| salmon, tuna, shrimp, fish, cod | Fish |
| onion, garlic, tomato, parsley, celery, carrot, chilli, cucumber, eggplant, basil, rosemary, bay leaf, pepper | Veg |
| lemon, blueberr, apple, banana | Fruit |
| butter, cheese, milk, cream, yogurt, parmesan, feta, egg | Dairy |
| flour, rice, pasta, spaghetti, bread, oat, cake flour, all-purpose | Grain |
| salt, paprika, cumin, cinnamon, turmeric, oregano, thyme, ginger | Spice |
| oil, sugar, vinegar, honey, tomato puree, stock, wine, powdered sugar, confectioners | Pantry |
| (anything else) | Other |

## API Gotchas

1. **URL-encode filter formulas** — Field names with spaces (e.g., `Mealie Slug`) must be URL-encoded:
   ```python
   import urllib.parse
   formula = f"{{Mealie Slug}}='{slug}'"
   url = f"?filterByFormula={urllib.parse.quote(formula)}"
   ```

2. **filterByFormula doesn't work on multipleRecordLinks** — Fetch all records and filter locally.

3. **Unknown field names return HTTP 422** — Always use exact field names. The API tells you which field is wrong in the error message.

4. **New single-select options return HTTP 422** — Map to existing options only.
