---
name: garmin-sync
description: "Garmin Connect sync — fetch cycling activities from Garmin Connect, handle two-Garmin deduplication, and store in Baserow. Use when syncing rides, troubleshooting Garmin auth, or adjusting the sync script."
version: 2.0.0
author: Geeves
---

# Garmin Connect Sync

Fetches cycling activities from Garmin Connect, deduplicates (two-Garmin scenario), and stores in **Baserow** Workouts + Cycling tables.

## Script

`/root/Geeves/scripts/garmin_fetch.py`

## How It Works

1. Authenticates with Garmin Connect (credentials from `.env`)
2. Fetches activities for a date range via `get_activities_by_date`
3. Filters to cycling-type activities (cycling, road_biking, mountain_biking, gravel_cycling, virtual_ride, indoor_cycling)
4. **Deduplicates**: checks Baserow for existing records by date + route + distance via filter formula
5. Creates both a Workout record (Type: Cycle, Source: Garmin) and a Cycling record (linked)
6. Tracks import state in `.garmin_import_state.json`

## Usage

```bash
python3 garmin_fetch.py --days 7          # Dry run
python3 garmin_fetch.py --days 7 --write  # Write to Baserow
python3 garmin_fetch.py --backfill --write  # Backfill: one week at a week backwards
```

## Credentials

Stored in `/root/.hermes/.env`:
```
GARMIN_EMAIL=...
GARMIN_PASSWORD=...
```

## Two-Garmin Scenario

David wears two Garmins simultaneously — one on the bike (records as cycling), one on the wrist (records as walking). Both import correctly as separate activities. The wrist data appears as walking activities and is **not** filtered out — it's genuine activity data.

## Baserow Table IDs

| Table | ID |
|---|---|
| Cycling | 396 |
| Workouts | 392 |
| People | 359 |

## Pitfalls

1. **429 rate limiting**: Garmin returns 429 on login attempts. The script auto-retries after 60 seconds. The library also auto-fallbacks (curl_cffi → requests). These warnings are normal.
2. **Dedup uses Baserow filter formula**: Checks date + route + distance. Records with slightly different distances (e.g., 7.0 vs 7.2) are treated as separate rides.
3. **Backfill mode**: `--backfill` works backwards from the oldest imported date. Each cron run fetches 7 days further back. State tracked in `.garmin_import_state.json`.
4. **Garmin auto-naming**: Garmin sometimes names cycling activities "Walking" (e.g., "Reading Walking" for a 46-mile ride). This is cosmetic — the activity type ID is correct.

## Cron

Job `0d2ddb20ece8` — daily 7am UTC, `--backfill --write` mode.
