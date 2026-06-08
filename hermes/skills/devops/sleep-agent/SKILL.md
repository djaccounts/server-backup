---
name: sleep-agent
description: "Geeves Sleep & Habits Agent — track sleep and habits in Airtable. Use when logging sleep, tracking habits, reporting bedtime/wake time, sleep quality, habit completion, or when the user mentions sleep, rest, tired, habit, routine, or streaks."
version: 1.0.0
author: Geeves
---

# Sleep & Habits Agent

Manages the `Sleep Log`, `Habits`, and `Habit Log` tables. Handles sleep tracking and habit streak management.

## Tables

| Table | ID | Purpose |
|-------|----|---------|
| `Sleep Log` | `tblTZchsmcXXernI0` | Daily sleep records |
| `Habits` | `tblS6SryrC3RnRl1L` | Habit definitions to track |
| `Habit Log` | `tbl3YRZ1yoQ7kRPIT` | Daily habit completion records |

## Key Fields

### Sleep Log

| Field | Type | Purpose |
|-------|------|---------|
| `Date` | date | Date of the sleep (primary field) |
| `Bedtime` | single line text | e.g. "23:15" |
| `Wake time` | single line text | e.g. "06:45" |
| `Hours slept` | number | Total hours slept |
| `Quality` | rating | 1-5 sleep quality rating |
| `Notes` | multilineText | Sleep notes (woke in night, etc.) |
| `Logged` | date | When this was logged |

### Habits

| Field | Type | Purpose |
|-------|------|---------|
| `Habit` | single line text | Name of the habit (primary field) |
| `Frequency target` | single select | Daily / Weekdays / 3x week / Weekly |
| `Category` | single select | Health / Learning / Mindfulness / Household / Other |
| `Active` | checkbox | Whether this habit is active |
| `Habit Log` | multipleRecordLinks | Link to Habit Log entries |

### Habit Log

| Field | Type | Purpose |
|-------|------|---------|
| `Date` | date | Date of completion (primary field) |
| `Habit` | multipleRecordLinks | Link to Habits table |
| `Completed` | checkbox | Whether the habit was completed |
| `Logged` | date | When this was logged |

## Airtable CRUD

Use `/root/Geeves/scripts/airtable_api.py`:

```bash
# Log sleep
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "Sleep Log" \
  '{"Date": "2026-06-07", "Bedtime": "23:15", "Wake time": "06:45", "Hours slept": 7.5, "Quality": 4, "Notes": "Woke once in the night"}'

# Log habit completion
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "Habit Log" \
  '{"Date": "2026-06-07", "Completed": true}'

# List active habits
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "Habits" "filterByFormula={Active}=1"

# List this week's habit log
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "Habit Log"
```

**Auth:** Read `AIRTABLE_API_KEY` from `/root/.hermes/.env` via grep (never from `os.environ`).

## Workflows

### Logging Sleep

1. Extract bedtime and wake time from the user's message
2. Calculate hours slept (wake time - bedtime, handling midnight crossing)
3. Ask for or infer quality (1-5 rating)
4. Optionally capture notes (woke in night, etc.)
5. Confirm back with a summary (e.g. "7.5 hours, quality 4/5")
6. Create record with today's date

**Time parsing hints:**
- "23:15" / "11:15pm" / "half eleven" → 23:15
- "06:45" / "6:45am" / "quarter to seven" → 06:45
- If user says "slept from 11 to 6" → Bedtime: 23:00, Wake: 06:00, Hours: 7
- Crossing midnight: 23:00 → 06:00 = 7 hours

### Logging a Habit Completion

1. Identify which habit the user is logging
2. Find or create the matching Habit record
3. Create a Habit Log entry with `Completed: true`
4. Confirm with current streak count

### Defining a New Habit

1. Extract the habit name from the user's message
2. Ask for or infer frequency target and category
3. Create the Habit record with `Active: true`
4. Confirm the new habit

### Listing Sleep/Habits

1. Fetch recent records (last 7 days by default)
2. For sleep: show average hours and quality
3. For habits: show completion rate and current streaks
4. Format as a readable summary

## Slack Capture

Script: `/root/Geeves/scripts/slack_capture.py`

**Trigger keywords:** "sleep", "slept", "bed", "wake", "woke", "tired", "rest", "habit", "routine", "streak", "completed", "did my", "logged"

**Classification priority:** Sleep/Habit appears AFTER Meal, Restaurant, Module Request in `CATEGORY_RULES`.

### Extraction Patterns

**Sleep logging:**
- "slept from X to Y" → Bedtime: X, Wake: Y
- "went to bed at X" → Bedtime: X
- "woke up at X" → Wake: time: X
- "slept X hours" → Hours slept: X
- "quality X/5" or "rated X" → Quality: X
- If only bedtime + wake time given, calculate hours

**Habit logging:**
- "did my X" / "completed X" → Habit name: X, Completed: true
- "logged X" → Habit name: X, Completed: true
- "started X habit" → Add new habit: X

## Cron Jobs

None yet. Future: morning digest could include last night's sleep summary.

## Dependencies

- **People** (Phase 1) — No direct links, but habits may relate to people
- **Fitness Goals** (Phase 2) — Sleep quality affects fitness recommendations

## Integration Points

- **Morning Digest** (planned) — include last night's sleep summary
- **Cross-module Intelligence** (Phase 5) — sleep quality correlates with fitness, mood, nutrition

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Get David's explicit approval before creating any Airtable table
- Thread decisions supersede reference docs
- Update this skill when conversation changes a decision

## Pitfalls

1. **Date field format:** Always use `YYYY-MM-DD` for Airtable date fields.
2. **Rating field:** Quality is a `rating` type (1-5), not a select. Write as integer.
3. **Hours slept calculation:** Handle midnight crossing correctly. 23:00 → 06:00 = 7 hours, not -17.
4. **Habit linking:** When logging a habit completion, always link to the Habits table via the `Habit` field.
5. **Select field 422 errors:** Use exact values: `"Daily"`, `"Weekdays"`, `"3x week"`, `"Weekly"` for Frequency target; `"Health"`, `"Learning"`, `"Mindfulness"`, `"Household"`, `"Other"` for Category.
6. **filterByFormula on linked fields:** Cannot filter Habit Log by Habit name directly — filter by linked record ID.

## Reference

- `geeves-airtable/SKILL.md` — Airtable CRUD patterns
- `Geeves_Schema_Reference_v2.md` — full field definitions (Module 5 — Sleep + Habit Tracker)
- `geeves-airtable/references/slack-capture.md` — classification rules, extraction patterns
