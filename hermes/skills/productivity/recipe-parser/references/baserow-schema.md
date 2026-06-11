# Baserow Schema — Recipe Tables

## Recipes Table (ID: 379)

| Field | Baserow Type | Notes |
|-------|-------------|-------|
| `Name` | text | Recipe name |
| `Mealie Slug` | text | Unique slug from Mealie |
| `Source URL` | text | Original recipe URL |
| `Notes` | long_text | Description/notes |
| `Cuisine` | single_select | e.g. Italian, Greek, Indian |
| `Meal type` | multiple_select | e.g. Lunch, Dinner, Snack |
| `Ingredients` | link_row | → Ingredients table (auto-created reverse link) |

## Ingredients Table (ID: 375)

| Field | Baserow Type | Notes |
|-------|-------------|-------|
| `Ingredient` | text | Clean ingredient name (no quantities) |
| `Category` | single_select | See options below |
| `Recipe` | link_row | → Recipes table |
| `Quantity` | text | Raw quantity string |
| `Seasonal` | multiple_select | Months: Jan–Dec |

### Category Single-Select Options

`Meat`, `Fish`, `Veg`, `Fruit`, `Dairy`, `Grain`, `Spice`, `Pantry`, `Eggs`, `Other`

⚠️ When writing via `baserow_api.py create-row`, pass the option **name** (e.g. `"Meat"`). The helper resolves it to the internal ID automatically.

## Dinner Parties Table (ID: 376)

| Field | Type | Notes |
|-------|------|-------|
| `Date` | date | Party date |
| `Guests` | long_text | Guest list |
| `Menu` | long_text | Planned menu |
| `Recipe(s)` | link_row | → Recipes table |
| `Notes` | long_text | General notes |

## Dinner Planner Table (ID: 377)

| Field | Type | Notes |
|-------|------|-------|
| `Date` | date | Planned date |
| `Recipe` | link_row | → Recipes table |
| `Notes` | long_text | |

## Shopping List Table (ID: 378)

| Field | Type | Notes |
|-------|------|-------|
| `Ingredient` | text | Item name |
| `Quantity` | text | Amount needed |
| `Category` | single_select | Same as Ingredients.Category |
| `Done` | boolean | Checked off? |

## Recipe Context Table (ID: 372)

| Field | Type | Notes |
|-------|------|-------|
| `Preference` | text | e.g. "David likes spicy" |
| `Detail` | long_text | Full context |
| `Source` | single_select | How was this learned? |

## Recipe Output Log Table (ID: 373)

| Field | Type | Notes |
|-------|------|-------|
| `Output` | long_text | What was generated |
| `Type` | single_select | e.g. Suggestion, Meal Plan |
| `Rating` | number | User rating 1-5 |
| `Feedback` | long_text | User feedback |
| `Recipe(s)` | link_row | → Recipes table |

## Dining Preferences Table (ID: 382)

| Field | Type | Notes |
|-------|------|-------|
| `Preference` | text | e.g. "Loves Thai food" |
| `Source` | single_select | How was this learned? |
| `Confidence` | number | 1-5 scale |
