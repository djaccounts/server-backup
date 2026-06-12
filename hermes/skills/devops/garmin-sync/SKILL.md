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

1. **429 rate limiting**: Garmin returns 429 on login attempts. The script auto-retries after 60 seconds. The library also auto-fallbacks (curl_cffi → requests). These warnings are normal. During bulk imports, rate limiting can add significant time — expect ~2 min per batch of 100 activities.
2. **Dedup must be client-side**: Baserow's `filter_by_formula` is unreliable with field names containing spaces/special characters (e.g., `Distance (miles)`). It silently returns ALL records instead of filtering. **Always fetch all Baserow records and filter locally in Python** for dedup checks. The `activity_exists()` function in `garmin_fetch.py` does this correctly.
3. **Backfill state must advance even on empty batches**: If a date range has 0 cycling activities, the state file must still advance the `oldest_imported` date. Otherwise the script gets stuck re-fetching the same empty range forever. Fixed in v2.1.0.
4. **Garmin auto-naming**: Garmin sometimes names cycling activities "Walking" (e.g., "Reading Walking" for a 46-mile ride). This is cosmetic — the activity type ID is correct.
5. **Bulk import is faster than week-by-week backfill**: For large historical datasets (4+ years), use `garmin_bulk_import.py` which uses `client.get_activities(offset, limit)` pagination instead of date-range queries. Much faster than the week-by-week `--backfill` approach. The bulk script supports resume via `.garmin_bulk_state.json`.

## Bulk Import Script

`/root/Geeves/scripts/garmin_bulk_import.py` — One-time bulk import using Garmin's offset-based pagination.

```bash
python3 garmin_bulk_import.py           # Dry run — shows count
python3 garmin_bulk_import.py --write   # Write all to Baserow
```

- Fetches all activities in batches of 100 via `client.get_activities(offset, limit)`
- Filters client-side for cycling types
- Deduplicates against existing Baserow records (client-side comparison)
- State tracked in `.garmin_bulk_state.json` — supports resume if interrupted
- Sorts oldest-first before writing

## Cron

Job `0d2ddb20ece8` — daily 7am UTC, `--backfill --write` mode for incremental new rides.

## Reference

- `references/garmin-api-gotchas.md` — Garmin API quirks, rate limiting, activity types, two-Garmin setup
