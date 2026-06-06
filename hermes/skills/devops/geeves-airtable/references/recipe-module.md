# Recipe Module — Reference

## Architecture
- **Mealie** (port 9925) = recipe engine (URL scrape, ingredients, method, nutrition, images)
- **Airtable** = metadata + cross-module links
- Sync: Mealie → Airtable (one-way, on-demand)
- Script: `python3 /root/Geeves/scripts/recipe_sync.py <slug>`

## Table IDs

| Table | ID |
|-------|----|
| `Recipes` | `tblehBgzRMa2Xucjd` |
| `Ingredients` | `tblNsgbYHNK8xWnB7` |
| `Dinner Parties` | `tblwbQrIu3nUWDz3G` |
| `Dinner Planner` | `tblnts17CCckLJoUQ` |
| `Shopping List` | `tbldvpIO91xi72a0K` |
| `Recipe Context` | `tblJRsw77kbCFyoz9` |
| `Recipe Output Log` | `tblYaJTAZDZzBkcwH` |
| `Dining Preferences` | `tblzzGIF7yPf37NG5` |

## Key Pitfalls

1. **Mealie POST /api/recipes doesn't parse structured ingredients** — only URL scraping populates full ingredient data. Sites that block scrapers (Reddit, AllRecipes, Jamie Oliver) return BAD_RECIPE_DATA or 400. Use Mealie's UI for manual entry.
2. **Mealie PATCH for ingredients is format-sensitive** — Scraped ingredients store everything in the `note` field as free text (`food` and `unit` are null). Parse the `display` field in the sync script.
3. **filterByFormula doesn't work for link fields** — Must fetch all records and filter locally when finding linked ingredients.
4. **Delete-then-recreate for deduplication** — sync script deletes all existing linked ingredients before re-creating on re-sync.
5. **Ingredient categorisation** — Heuristic-based (~90% accuracy). Edge cases: "beef stock" → Meat, "plum tomatoes" → Fruit. Corrections go in Recipe Context table.

## Cross-Module Links
- Recipes ↔ Ingredients (many-to-many)
- Dinner Parties → People (guests) + Recipes (chosen)
- Dinner Planner → Recipes
- Shopping List → Recipes
- Dining Preferences → future Restaurant Finder
- Dining Preferences also ← Meals (restaurant logging, Module 8)

## Ingredient Sync Script Details

The sync script (`recipe_sync.py`) flow:
1. GET recipe from Mealie `/api/recipes/{slug}`
2. Check for existing Airtable record by `Mealie Slug`
3. If re-syncing: delete all existing linked ingredients (fetch all, filter locally, batch DELETE)
4. Create/update Recipes record with metadata
5. For each ingredient in `recipeIngredient`:
   - Deduplicate by `display` field
   - Parse quantity from `display` using regex
   - Categorise using `categorize_ingredient()` heuristic
   - Tag seasonal months using `get_seasonal_months()` lookup
   - POST to Ingredients table with link to Recipes record

## Airtable `build_field_payload` Requirements

When adding new field types to table_builder.py, these types require `options` during table creation:
- `singleSelect` → `options.choices` array
- `multipleSelects` → `options.choices` array
- `checkbox` → `options.icon` + `options.color`
- `date` → `options.dateFormat`
- `number` → `options.precision`
- `multipleRecordLinks` → `options.linkedTableId`

Missing any of these causes `INVALID_FIELD_TYPE_OPTIONS_FOR_CREATE` (422).
