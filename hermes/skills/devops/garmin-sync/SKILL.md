---
name: garmin-sync
description: "Garmin Connect sync — fetch cycling activities from Garmin Connect, handle two-Garmin deduplication, and store in Airtable. Use when syncing rides, troubleshooting Garmin auth, or adjusting the sync script."
version: 1.0.0
author: Geeves
---

# Garmin Connect Sync

Fetches cycling activities from Garmin Connect, deduplicates (two-Garmin scenario), and stores in Airtable Workouts + Cycling tables.

## Script

`/root/Geeves/scripts/garmin_sync.py`

## How It Works

1. Authenticates with Garmin Connect (credentials from `.env`, tokens cached at `~/.garminconnect/`)
2. Fetches last 7 days of activities via `get_activities_by_date`
3. Separates cycling-type and walking-type activities
4. **Deduplicates**: matches walking → cycling by same day + distance within ±1 mile. Keeps cycling, discards walking duplicate
5. Filters out short walks (< 3 miles) — likely genuine walks, not cycling duplicates
6. Stores each ride as both a Workout record (Type: Cycle, Source: Garmin) and a Cycling record (linked)

## Credentials

Stored in `/root/.hermes/.env`:
```
GARMIN_EMAIL=...
GARMIN_PASSWORD=...
```

## Garmin Activity Type IDs

### Cycling types (keep)
| ID | Type |
|----|------|
| 2 | cycling |
| 5 | mountain_biking |
| 10 | road_biking |
| 19 | cyclocross |
| 21 | track_cycling |
| 22 | recumbent_cycling |
| 25 | indoor_cycling / turbo |
| 143 | gravel_cycling |
| 152 | virtual_ride |
| 175 | e_bike_mountain |
| 176 | e_bike_fitness |
| 197 | hand_cycling |
| 198 | indoor_hand_cycling |

### Walking types (dedup against cycling)
| ID | Type |
|----|------|
| 3 | hiking |
| 9 | walking |
| 15 | casual_walking |
| 16 | speed_walking |

## API Reference

See `references/api.md` for `python-garminconnect` method signatures and quirks.

## Two-Garmin Scenario

David wears two Garmins simultaneously — one set to cycling, one to walking. This is the dedup script's primary purpose.

Strategy:
1. Match walking to cycling: same date + distance within ±1 mile → keep cycling, discard walking
2. Walking without cycling match but ≥3mi → keep (could be Garmin auto-naming a ride as "Walking")
3. Walking without cycling match and <3mi → filter out (genuine walk)

Adjust the distance tolerance (`1.0` miles) and short-walk threshold (`3.0` miles) in the script constants if needed.

## Pitfalls

1. **`get_activities()` vs `get_activities_by_date()`**: The main `get_activities(start, limit, activitytype)` takes offset/limit, NOT dates. Use `get_activities_by_date(startdate, enddate)` for date ranges.
2. **429 rate limiting**: Garmin returns 429 on login attempts. The library auto-fallbacks (curl_cffi → requests). These warnings are normal — don't treat them as fatal.
3. **Garmin auto-naming**: Garmin sometimes names cycling activities "Walking" (e.g., "Reading Walking" for a 46-mile ride). This is cosmetic — the activity type ID is correct (2 = cycling). The name in Airtable's Route field will show Garmin's name.
4. **Dedup uses `id(w)`**: The in-run walking dedup uses Python's `id()` to track which walking activities to remove. This works because we're comparing within a single list instance, not across runs.

## Cron

Job `0d2ddb20ece8` — daily 7am UTC.
