# Photo Meal Logging — Pipeline Reference

## Overview

The photo-to-meal pipeline lets users upload a food photo in Slack and have it automatically logged to the Baserow Meals table with estimated macros.

## Architecture

```
Slack image upload
  → Agent receives image URL (files[0].url_private_download)
  → Download with Slack bot token auth
  → vision_analyze to identify food + estimate macros
  → Log to Baserow via baserow_api.py
  → Confirm to user
```

## Script

`/root/Geeves/scripts/meal_photo_pipeline.py`

```bash
# Download + prepare for analysis
python3 meal_photo_pipeline.py <image_url> --output /tmp/meal_photo.jpg --meal-type Lunch

# Download + log directly (if macros already known)
python3 meal_photo_pipeline.py <image_url> \
  --meal-type Dinner --log \
  --description "Grilled salmon with rice and broccoli" \
  --calories 650 --protein 42 --carbs 55 --fat 18
```

## Baserow Fields (Meals table, id=387)

| Field | ID | Type | Notes |
|-------|----|------|-------|
| Description | 3594 | text | Primary field, max 200 chars |
| Date | 3595 | date | YYYY-MM-DD |
| Meal type | 3596 | single_select | Breakfast/Lunch/Dinner/Snack |
| Calories (est) | 3597 | number | **Integer only** — round before sending |
| Protein (g) | 3598 | number | **Integer only** |
| Carbs (g) | 3599 | number | **Integer only** |
| Fat (g) | 3600 | number | **Integer only** |
| Accuracy | 3601 | single_select | Estimated/Barcode/From recipe |
| Source | 3602 | single_select | Manual/Slack/Voice (Photo TBD) |
| Logged | 3603 | date | Auto-set to today |
| From recipe | 3604 | link_row | Link to Recipes table (379) |

## Important Constraints

1. **Number fields are integers** — Baserow Meals number fields have 0 decimal places. Use `int(round(value))` before sending. Sending floats causes HTTP 400 `max_decimal_places` error.

2. **Source field** — Currently no "Photo" option exists. Use "Slack" as fallback. Adding "Photo" requires JWT auth to PATCH `/api/database/fields/3602/` with `{"select_options": [...]}`.

3. **Vision tool** — `vision_analyze` must be available. Requires `vision` in the `toolsets:` list in `config.yaml`. If missing: `hermes config set toolsets '["hermes-cli", "vision"]'` + gateway restart.

4. **Slack image download** — Use `curl -sL -H "Authorization: Bearer $SLACK...EN" "$URL" -o /tmp/meal_photo.jpg"`

## Meal Type Detection

If not specified by user:
- Before 11am → Breakfast
- 11am-2pm → Lunch
- 5pm+ → Dinner
- Other → Snack

## Macro Estimation Guidelines

When estimating from photos:
- Be transparent: "From your photo, I can see..." / "Estimated from visual analysis"
- If uncertain, log with just description and set Accuracy to "Estimated"
- Don't fabricate numbers — if you can't estimate, ask the user

## Session Learnings (June 2026)

- Vision tool was available in earlier sessions (June 2-9) but dropped out on June 11. Root cause: `vision` missing from `toolsets:` list. Fix: `hermes config set toolsets '["hermes-cli", "vision"]'` + gateway restart.
- The `baserow_mapping.json` file can get corrupted if error output is redirected to it. Always restore from `/root/server-backup/geeves/baserow_mapping.json` and verify with `python3 -c "import json; json.load(open('/root/Geeves/baserow_mapping.json')); print('OK')"`.
