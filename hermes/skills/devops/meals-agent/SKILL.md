---
name: meals-agent
description: "Geeves Meals Agent — log meals and track nutrition in the Baserow Meals table. Use when logging food, meals, calories, macros, or when the user mentions eating, food, calories, protein, carbs, fat, breakfast, lunch, dinner, or snacks. Also use when the user uploads a food photo for meal logging."
version: 1.1.0
author: Geeves
---

# Meals Agent

Manages the `Meals` table — meal and nutrition logging. Handles Airtable CRUD, Slack capture, and nutrition estimation.

## Tables

| Table | Baserow ID | Purpose |
|-------|------------|---------|
| `Meals` | `387` | Every meal/snack logged |
| `Daily Nutrition Summary` | `tbl16Z64tClYJaPLZ` | Daily roll-up (auto-generated) |
| `Fitness Goals` | `tblAM0Grin01IQmdd` | Calorie/macro targets |

## Key Fields (Meals)

| Field | Type | Purpose |
|-------|------|---------|
| `Description` | single line text | What was eaten (primary field) |
| `Date` | date | Date of the meal (with time) |
| `Meal type` | single select | Breakfast / Lunch / Dinner / Snack |
| `Calories (est)` | number | Estimated calories |
| `Protein (g)` | number | Protein in grams |
| `Carbs (g)` | number | Carbs in grams |
| `Fat (g)` | number | Fat in grams |
| `From recipe` | multipleRecordLinks | Link to Recipes table (if cooked from a saved recipe) |
| `Accuracy` | single select | Estimated / Barcode / From recipe |
| `Source` | single_select | Manual / Slack / Voice |
| `Logged` | date | When this was logged |

## Baserow CRUD

Use `/root/Geeves/scripts/baserow_api.py`:

```bash
# Create a meal record
python3 /root/Geeves/scripts/baserow_api.py create-row Meals \
  '{"Description": "Porridge with banana and honey", "Date": "2026-06-07", "Meal type": "Breakfast", "Calories (est)": 420, "Protein (g)": 12, "Carbs (g)": 68, "Fat (g)": 8, "Accuracy": "Estimated", "Source": "Slack"}'

# List today's meals
python3 /root/Geeves/scripts/baserow_api.py list-rows Meals

# List all meals (recent first)
python3 /root/Geeves/scripts/baserow_api.py list-rows Meals
```

**Auth:** Reads `BASEROW_API_TOKEN` from `/root/.hermes/.env`. Field names are auto-resolved to Baserow field IDs via `baserow_mapping.json`.

## Workflows

### Logging a Meal

1. Extract what was eaten from the user's message
2. **Estimate calories and macros** using your nutritional knowledge:
   - Common foods: porridge ~150 cal/40g, banana ~105 cal, chicken breast ~165 cal/100g, etc.
   - Restaurant/takeaway meals: estimate based on dish type (e.g. fish & chips ~800 cal, pad thai ~600 cal)
   - Be transparent: prefix with "est." if uncertain
3. **Determine meal type** from context:
   - Morning (before 11am) → Breakfast
   - Midday (11am-2pm) → Lunch
   - Evening (5pm+) → Dinner
   - Other → Snack
4. **Check if from a recipe** — if the user mentions a recipe name, search the Recipes table and link it
5. Set `Accuracy` to `"Estimated"` (default), `"Barcode"` (if scanned), or `"From recipe"` (if linked)
6. Set `Source` to `"Slack"` when logged via Slack text, `"Photo"` when logged from a photo
7. Confirm back to the user with the description and macros

**Macro estimation heuristics:**
- Protein: meat/fish ~25g per 100g serving, eggs ~6g each, dairy ~8g per 100ml
- Carbs: rice/pasta ~30g per 100g cooked, bread ~15g per slice, fruit ~15g per serving
- Fat: oil/butter ~14g per tbsp, nuts ~15g per 30g, avocado ~15g per half

### Listing Meals

1. Fetch records from Airtable (filter by date if specified)
2. Group by meal type
3. Show running totals for calories, protein, carbs, fat
4. Compare to Fitness Goals targets if active

### Updating a Meal

1. Find the matching record (search by description + date)
2. Update only the fields that changed
3. Confirm the update

## Photo Meal Logging

When the user uploads a food photo in Slack (or sends an image attachment):

1. **Download the image** from the Slack attachment URL:
   - The image URL is in the message's `files[0].url_private_download` field
   - Use `curl` with the Slack bot token to download:
     ```bash
     SLACK_BOT_TOKEN=*** SLACK_BOT_TOKEN ~/.hermes/.env | head -1 | cut -d= -f2)
     curl -sL -H "Authorization: Bearer $SLACK...EN" "$IMAGE_URL" -o /tmp/meal_photo.jpg
     ```

2. **Analyze the image** using `vision_analyze`:
   - Pass the downloaded image to the vision tool
   - Ask it to identify all food items, estimate portion sizes, and estimate calories + macros
   - Prompt: "Identify all food and drink items in this photo. For each item, estimate the portion size and provide approximate calories, protein (g), carbs (g), and fat (g). Return as a structured list."

3. **Determine meal type** from context:
   - If the user says "breakfast/lunch/dinner/snack" → use that
   - Otherwise infer from time of day:
     - Before 11am → Breakfast
     - 11am-2pm → Lunch
     - 5pm+ → Dinner
     - Other → Snack

4. **Log to Baserow**:
   ```bash
   python3 /root/Geeves/scripts/baserow_api.py create-row Meals \
     '{"Description": "Grilled salmon with rice and broccoli", "Date": "2026-06-10", "Meal type": "Dinner", "Calories (est)": 650, "Protein (g)": 42, "Carbs (g)": 55, "Fat (g)": 18, "Accuracy": "Estimated", "Source": "Photo"}'
   ```

5. **Confirm to user** with:
   - What was identified in the photo
   - Estimated macros
   - Meal type
   - "Does that look right? Let me know if you want to adjust anything."

**Notes:**
- Always be transparent that macros are estimates from visual analysis
- If the photo is unclear, ask the user to describe the meal
- Set `Source` to `"Photo"` once the option is added to Baserow (currently use `"Slack"` as fallback)

## Slack Capture

Script: `/root/Geeves/scripts/slack_capture.py`

**Trigger keywords:** "ate", "had", "lunch", "dinner", "breakfast", "snack", "calories", "macros", "protein", "carbs", "fat", "food", "meal", "logged", "eating"

**Classification priority:** Meal appears AFTER Film Club, Recipe, Todo in `CATEGORY_RULES`.

### Extraction Patterns

**Food description:**
- "Had X for Y" → X is the food, Y is meal type
- "Ate X" → X is the food
- "X for breakfast/lunch/dinner" → X is the food

**Meal type:**
- "breakfast", "morning" → Breakfast
- "lunch", "midday" → Lunch
- "dinner", "evening", "supper" → Dinner
- "snack", "afternoon tea" → Snack

**Macros (if provided):**
- "X calories" → Calories
- "Xg protein" → Protein
- "Xg carbs" → Carbs
- "Xg fat" → Fat

## Cron Jobs

None yet. Future: daily nutrition summary generation (reads from Meals → writes to Daily Nutrition Summary).

## Dependencies

- **Recipes** — Meals can link to Recipes via `From recipe` field
- **Fitness Goals** — Daily nutrition totals compared to targets
- **Daily Nutrition Summary** — Roll-up table for digest inclusion

## Integration Points

- **Morning Digest** (planned) — could include yesterday's nutrition summary
- **Evening Digest** (planned) — could include today's running nutrition totals
- **Recipes module** — link meals to recipes for accurate macro data
- **Fitness module** — nutrition data feeds fitness tracking

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Get David's explicit approval before creating any Baserow table
- Thread decisions supersede reference docs
- Update this skill when conversation changes a decision

## Pitfalls

1. **Date field format:** Always use `YYYY-MM-DD` for Baserow date fields.
2. **Select field 422 errors:** Writing an undefined select option fails with 422. Always use exact values: `"Breakfast"`, `"Lunch"`, `"Dinner"`, `"Snack"` for Meal type; `"Estimated"`, `"Barcode"`, `"From recipe"` for Accuracy.
3. **From recipe linking:** Only link to Recipes if the user specifically mentions a recipe name or you can confidently match it. Don't guess.
4. **Macro estimation honesty:** If you can't estimate macros confidently, log the meal with just the description and set Accuracy to "Estimated". Don't fabricate numbers.
5. **filterByFormula on date fields:** Use `TODAY()` or `DATESTR()` functions. Direct date string comparison may not work as expected.
6. **Number fields are integers in Baserow** — Calories, Protein, Carbs, Fat all use 0 decimal places. Always `int(round(value))` before sending. Sending floats like `420.5` causes HTTP 400 `max_decimal_places` error.
7. **Photo logging:** When logging from a photo, always note the uncertainty. Use phrases like "From your photo, I can see..." and "Estimated from visual analysis."

## Reference

- `geeves-airtable/SKILL.md` — Airtable CRUD patterns
- `Geeves_Schema_Reference_v2.md` — full field definitions (Module 7 — Meal Tracker)
- `geeves-airtable/references/slack-capture.md` — classification rules, extraction patterns
- `recipes-agent/SKILL.md` — Recipes module for linking meals to recipes
