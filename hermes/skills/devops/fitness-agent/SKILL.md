---
name: fitness-agent
description: "Geeves Fitness Agent — log workouts, track exercises, and manage fitness goals in Airtable. Use when logging workouts, gym sessions, runs, cycles, swims, exercise sets/reps/weight, or when the user mentions gym, run, cycle, swim, workout, exercise, training, lifting, cardio, stretching, or fitness goals."
version: 1.0.0
author: Geeves
---

# Fitness Agent

Manages the `Workouts`, `Exercise Log`, `Cycling`, and `Fitness Goals` tables. Handles workout logging, exercise detail tracking, cycling ride logging, and fitness goal management.

## Tables

| Table | ID | Purpose |
|-------|----|---------|
| `Workouts` | `tblMDYF8Lkl5A15CW` | Every workout session |
| `Exercise Log` | `tbl8MXDYZ2hajsdIk` | Per-exercise detail for gym sessions |
| `Cycling` | `tblZ7hkoE68IRnQwV` | Cycling ride details |
| `Fitness Goals` | `tblAM0Grin01IQmdd` | Calorie/macro/weekly targets |

## Key Fields

### Workouts

| Field | Type | Purpose |
|-------|------|---------|
| `Date` | date | Date of workout (primary field) |
| `Type` | single select | Gym / Run / Cycle / Walk / Swim / Yoga / Class / Other |
| `Duration (mins)` | number | Duration in minutes |
| `Distance (km)` | number | Distance in km (for cardio) |
| `Energy level` | rating | 1-5 how it felt |
| `Perceived difficulty` | rating | 1-5 how hard it was |
| `Notes` | multilineText | Freeform notes |
| `Source` | single select | Manual / Slack / Voice / Strava / Google Fit |
| `Exercise Log` | multipleRecordLinks | Link to Exercise Log entries |
| `Cycling` | multipleRecordLinks | Link to Cycling records (if Cycle workout) |
| `People` | multipleRecordLinks | Link to People (if working out with someone) |
| `Logged` | date | When this was logged |

### Exercise Log

| Field | Type | Purpose |
|-------|------|---------|
| `Exercise` | single line text | e.g. Bench press (primary field) |
| `Workout` | multipleRecordLinks | Link to parent Workout |
| `Sets` | number | Number of sets |
| `Reps` | single line text | e.g. "8, 8, 6" |
| `Weight (kg)` | single line text | e.g. "60, 60, 65" |

### Cycling

| Field | Type | Purpose |
|-------|------|---------|
| `Date` | date | Ride date (primary field) |
| `Workout` | multipleRecordLinks | Link to parent Workout |
| `Route` | single line text | Route name/description |
| `Distance (miles)` | number | Distance in miles |
| `Duration (mins)` | number | Duration in minutes |
| `Elevation gain (m)` | number | Elevation gain in metres |
| `Avg speed (mph)` | number | Average speed |
| `Max speed (mph)` | number | Maximum speed |
| `Ride type` | single select | Road / Gravel / MTB / Turbo / Commute |
| `Bike used` | single line text | Which bike |

### Fitness Goals

| Field | Type | Purpose |
|-------|------|---------|
| `Goal type` | single line text | Text description |
| `Goal type select` | single select | Cut / Bulk / Maintain / Endurance / Strength |
| `Daily calorie target` | number | Target calories per day |
| `Daily protein target (g)` | number | Target protein in grams |
| `Weekly workout target` | number | Target workouts per week |
| `Start date` | date | When this goal started |
| `Active` | checkbox | Is this the current active goal? |
| `Notes` | multilineText | Freeform goal notes |

## Airtable CRUD

Use `/root/Geeves/scripts/airtable_api.py`:

```bash
# Create a workout
python3 /root/Geeves/scripts/airtable-api.py create-record appzvmonQXs4x2AlL "Workouts" \
  '{"Date": "2026-06-09", "Type": "Gym", "Duration (mins)": 45, "Energy level": 4, "Perceived difficulty": 3, "Source": "Slack"}'

# Create workout with exercise detail
# Step 1: Create the workout
WORKOUT_JSON='{"Date": "2026-06-09", "Type": "Gym", "Duration (mins)": 60, "Energy level": 4, "Source": "Slack"}'
# Step 2: Create exercise log entries linked to the workout ID

# List recent workouts
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "Workouts"

# List exercises for a workout
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "Exercise Log"

# Check active fitness goals
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "Fitness Goals" "filterByFormula={Active}=1"

# Log a cycling ride
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "Workouts" \
  '{"Date": "2026-06-09", "Type": "Cycle", "Duration (mins)": 90, "Distance (km)": 35, "Source": "Strava"}'
```

**Auth:** Read `AIRTABLE_API_KEY` from `/root/.hermes/.env` via grep (never from `os.environ`).

## Workflows

### Logging a Workout (General)

1. Extract workout type from the user's message (gym, run, cycle, swim, yoga, etc.)
2. Extract duration, distance, and any other metrics
3. If gym session → also extract exercises (see Gym Session below)
4. If cycle ride → also extract ride details (see Cycling below)
5. Ask for energy level and difficulty if not provided (1-5 scale)
6. Set `Source` to `"Slack"` when logged via Slack
7. Confirm back to the user with a summary

### Logging a Gym Session

1. Create the Workout record with Type "Gym"
2. For each exercise mentioned, create an Exercise Log entry linked to the Workout:
   - Extract exercise name, sets, reps, weight
   - Handle formats like "3x8 bench press at 60kg" or "bench press 3 sets of 8 at 60"
3. Confirm with a summary of exercises logged

**Exercise parsing patterns:**
- "X reps of Y" → Exercise: Y, Reps: X
- "Y X reps Z sets" → Exercise: Y, Sets: Z, Reps: X
- "Y Z kg X reps" → Exercise: Y, Weight: Z, Reps: X
- "bench press: 3x8 at 60kg" → Exercise: Bench press, Sets: 3, Reps: 8, Weight: 60

### Logging a Cycling Ride

1. Create the Workout record with Type "Cycle"
2. Create a Cycling record linked to the Workout:
   - Extract distance (miles or km — convert km to miles if needed: miles = km × 0.621)
   - Extract duration, elevation, speed, ride type, bike used
   - Default ride type to "Road" if not specified
3. Confirm with a ride summary

### Logging a Run/Walk/Swim

1. Create Workout record with appropriate Type
2. Extract distance and duration
3. Calculate pace if both distance and duration provided
4. Confirm with summary

### Setting/Updating Fitness Goals

1. Check if an active goal exists — if so, deactivate it (set Active: false)
2. Create new Fitness Goal record with Active: true
3. Extract goal type, calorie target, protein target, weekly workout target
4. Set Start Date to today
5. Confirm the new goals

### Viewing Workout History

1. Fetch recent workouts (last 7 days by default, or user-specified range)
2. Group by type
3. Show total duration, distance, average energy
4. If goal is active, show progress toward weekly workout target
5. For gym sessions, fetch linked Exercise Log entries

## Slack Capture

Script: `/root/Geeves/scripts/slack_capture.py`

**Fitness classification priority:** Fitness appears AFTER Sleep/Habit in `CATEGORY_RULES` (added at the end, scored highest for fitness-specific keywords).

**Trigger keywords:** "workout", "gym", "run", "ran", "cycling", "cycled", "bike", "swim", "swam", "yoga", "walk", "walked", "trained", "training", "lifting", "lifted", "exercise", "cardio", "stretch", "fitness", "strava", "peloton", "set", "reps", "bench", "squat", "deadlift", "press", "treadmill", "rowing", "row", "PBs", "personal best", "exercise", "gymnastics", "HIIT", "weights"

**Workout type detection:**
- "gym", "lift", "weights", "bench", "squat", "deadlift", "press", "HIIT" → Gym
- "run", "ran", "jog", "treadmill" → Run
- "cycle", "cycled", "bike", "ride", "strava" → Cycle
- "swim", "swam", "pool" → Swim
- "walk", "walked", "hike" → Walk
- "yoga", "stretch" → Yoga
- "class", "session", "peloton", "HIIT" → Class

**Exercise extraction (gym sessions):**
- "Exercise: sets x reps at weight kg"
- "Exercise sets of reps at weight"
- Multiple exercises separated by commas, semicolons, or "and"
- "Trained X and Y" → link both as exercise names

**Cycling extraction:**
- "X miles/km" → Distance
- "X mins/hours" → Duration
- "road/gravel/MTB/turbo/commute" → Ride type
- "elevated/elevation/climbed X" → Elevation gain
- "avg/average X mph" → Avg speed
- "max/top speed X mph" → Max speed

## Cron Jobs

None yet. Future: weekly fitness summary in Weekly Digest.

## Dependencies

- **Meals** — Fitness Goals daily calorie target used for meal tracking comparison
- **Sleep** — Sleep quality affects recovery recommendations
- **People** — Workouts can link to People (working out with someone)

## Integration Points

- **Morning Digest** — could include yesterday's workout summary
- **Weekly Digest** — weekly workout summary vs goal target
- **Cross-module Intelligence** (Phase 5) — workout patterns correlate with sleep, nutrition

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Get David's explicit approval before creating any Airtable table or field
- Thread decisions supersede reference docs
- Update this skill when conversation changes a decision

## Pitfalls

1. **Date field format:** Always use `YYYY-MM-DD` for Airtable date fields.
2. **Select field 422 errors:** Writing an undefined select option fails with 422. Exact values: `Type`: "Gym", "Run", "Cycle", "Walk", "Swim", "Yoga", "Class", "Other". `Source`: "Manual", "Slack", "Voice", "Strava", "Google Fit". `Ride type`: "Road", "Gravel", "MTB", "Turbo", "Commute".
3. **Rating fields:** Energy level and Perceived difficulty are `rating` type (1-5), write as integer.
4. **Cycling distance conversion:** Cycling table uses miles. If user gives km, convert: miles = km × 0.621. If user gives miles, use directly.
5. **Linking Exercise Log to Workout:** Must create Workout first, get its ID, then create Exercise Log entries with `Workout` field set to `[workout_id]`.
6. **Linked record errors:** Links must be arrays of record IDs: `["recXXXXXX"]`. Passing a plain string fails.
7. **Two workouts same day:** Airtable allows multiple records with the same date. Don't check for duplicates unless asked — David might do morning gym and evening run.
8. **Distance on Workouts table is km, on Cycling table is miles:** Don't mix them up.
9. **Dry-run print bug:** The `handle_fitness()` dry-run print statement has `dur={distance}` — should be `dur={duration}`. This is cosmetic (doesn't affect live writes) but confusing when debugging. Fix when touching the handler next.
10. **Exercise extraction fallback:** The regex patterns in `_extract_exercises()` are greedy and can capture trailing words. The fallback to known exercise names is more reliable for simple "trained X and Y" messages. When the regex produces garbage, fall back to known-exercise matching.

## Reference

- `geeves-airtable/SKILL.md` — Airtable CRUD patterns
- `Geeves_Schema_Reference_v2.md` — full field definitions (Module 6 — Fitness Tracker)
- `meals-agent/SKILL.md` — related module with shared Fitness Goals table
