# Garmin Connect API Gotchas

## Rate Limiting (429)

Garmin aggressively rate-limits the unofficial API. Every login attempt can trigger a 429 response.

**Symptoms**: `mobile+cffi returned 429: Mobile login returned 429 — IP rate limited by Garmin`

**Handling**: The `garminconnect` library auto-fallbacks from `curl_cffi` to `requests`. Scripts should catch 429s and retry after 60 seconds. Multiple consecutive 429s are normal — just wait.

**Impact on bulk imports**: A bulk import of 500+ rides can take 15-20 minutes due to rate limit delays. Plan accordingly — run in background, not in a blocking session.

## Activity Fetching

### Date-range method (`get_activities_by_date`)
```python
activities = client.get_activities_by_date("2023-03-01", "2023-03-31")
```
- Returns ALL activity types — filter client-side for cycling
- Good for targeted date ranges
- Slower for large historical datasets (many API calls)

### Offset-based method (`get_activities`) — PREFERRED for bulk
```python
activities = client.get_activities(offset=0, limit=100)
```
- Paginates through ALL activities regardless of date
- Much faster for bulk imports
- Use `limit=100` (max reliable batch size)
- Continue until empty response

## Cycling Activity Types

Filter for these `activityType.typeKey` values:
- `cycling` — Road cycling
- `road_biking` — Road biking
- `mountain_biking` — MTB
- `gravel_cycling` — Gravel
- `virtual_ride` — Turbo trainer
- `indoor_cycling` — Indoor cycling

## Activity Details

`client.get_activity_details(activityId)` returns richer data including:
- `averageHR` / `maxHR` — Heart rate
- `avgPower` — Power (watts)
- `calories` — Calories burned
- `deviceName` — Which Garmin device recorded it

This is a separate API call per activity — use sparingly during bulk imports to avoid rate limits.

## Two-Garmin Setup

David wears two Garmins simultaneously:
- One on the bike → records as cycling
- One on the wrist → records as walking

Both import correctly as separate activities. The wrist data appears as walking activities and is **not** filtered out — it's genuine activity data.

## Auto-Naming Quirk

Garmin sometimes auto-names cycling activities "Walking" (e.g., "Reading Walking" for a 46-mile ride). This is cosmetic — the `activityType.typeKey` is correct. Don't filter by name.

## Session Expiry

Garmin sessions expire. If you get `GarminConnectAuthenticationError: Not authenticated`, re-login. The `garminconnect` library doesn't auto-reauth.
