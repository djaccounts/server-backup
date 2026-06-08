# Ingredient Name Cleaning

## Problem

Mealie's `recipeIngredient` display field contains the full raw recipe line:
```
"2-3 garlic cloves, finely grated"
"1/2 tsp ground cumin"  
"500g full-fat Greek yoghurt (thick/strained)"
"2 tbsp extra-virgin olive oil"
```

Airtable's `Ingredient` field should contain ONLY the clean name:
```
"Garlic"
"Cumin"
"Greek yoghurt"
"Olive oil"
```

## Solution: `clean_ingredient_name()`

Both `push_recipe.py` and `recipe_sync.py` implement this function. It:

1. **Removes parenthetical notes** — `(thick/strained)`, `(12-16 thighs)`, `(Maldon)`
2. **Strips leading quantities and units** — numbers, fractions, ranges, then unit words (cup, tbsp, g, cloves, etc.)
3. **Removes preparation instructions** — everything after a comma that's a prep verb (chopped, minced, grated, pressed, etc.) or trailing phrase (to taste, to serve, optional)
4. **Removes leading articles** — "a", "an", "the", "~"
5. **Title-cases** the result

## Deduplication

Within a single recipe, deduplicate by cleaned name (case-insensitive). The first occurrence wins.

## Category Mapping

After cleaning, ingredients are categorised using keyword matching against `CATEGORY_KEYWORDS`:

| Category | Example keywords |
|----------|-----------------|
| Meat | chicken, beef, pork, lamb, bacon, sausage, steak, mince |
| Fish | salmon, tuna, cod, haddock, prawn, shrimp, anchovy |
| Veg | onion, garlic, tomato, potato, cucumber, pepper, chilli, carrot, celery |
| Fruit | lemon, lime, orange, apple, banana, blueberr, olive, kalamata |
| Dairy | butter, milk, cream, cheese, yogurt, yoghurt, feta, parmesan |
| Grain | flour, spaghetti, pasta, rice, oat, bread, yeast |
| Spice | salt, pepper, paprika, cumin, cinnamon, turmeric, oregano, basil |
| Pantry | oil, vinegar, sugar, honey, baking powder, stock, wine, cocoa |
| Eggs | egg, eggs |
| Other | (fallback) |

**Important:** "Eggs" is its own category, NOT inside "Dairy".

## Airtable Category Single-Select

The `Category` field is a single-select. Existing options (as of June 2026):
`Meat`, `Fish`, `Veg`, `Fruit`, `Dairy`, `Grain`, `Spice`, `Pantry`, `Eggs`, `Other`

⚠️ The Metadata API rejects new options (HTTP 422). Use `typecast=true` on POST to auto-create new options (this is how "Eggs" was added).

## Examples

| Raw input | Cleaned output | Category |
|-----------|---------------|----------|
| `2-3 garlic cloves, finely grated` | `Garlic` | Veg |
| `1/2 tsp ground cumin` | `Cumin` | Spice |
| `500g full-fat Greek yoghurt (thick/strained)` | `Greek yoghurt` | Dairy |
| `2 tbsp extra-virgin olive oil` | `Olive oil` | Pantry |
| `2-2.5 lbs boneless skinless chicken thighs (12-16 thighs)` | `Chicken thighs` | Meat |
| `Squeeze of lemon juice to finish` | `Lemon juice` | Fruit |
| `Black pepper to taste` | `Black pepper` | Spice |
| `~20 Kalamata olives` | `Kalamata olives` | Fruit |
| `1 cup fresh blueberries` | `Blueberries` | Fruit |
| `2 x 400g tins plum tomatoes` | `Plum tomatoes` | Veg |
