---
name: travel-agent
description: "Geeves Travel & Commute Agent — plan journeys, check TfL status, and add travel info to the morning digest. Use when the user asks about travel, commute, journey planning, tube status, cycling directions, or getting somewhere. Also runs automatically as part of the morning digest to check calendar events with locations and provide travel advice."
version: 1.0.0
author: Geeves
---

# Travel & Commute Agent

Plans journeys, checks live transit status, and adds travel information to the morning digest. Works both automatically (via digest) and ad-hoc (via Slack).

## Data Sources

| Source | Purpose | Auth |
|--------|---------|------|
| Google Calendar | Find events with locations today | `google_token.json` (already configured) |
| Baserow Routes table | Known routes with coordinates | `baserow_api.py` |
| OSRM (OpenStreetMap) | Cycling/walking/driving routing | Free, no key |
| TfL API | Live Tube/bus line status | Free, no key |
| Nominatim (OSM) | Geocode addresses to coordinates | Free, no key (1 req/s) |

## Tables

| Table | Baserow ID | Purpose |
|-------|-----------|---------|
| `Routes` | 892 | Known routes: from/to, mode, typical duration, coordinates |

### Routes Table Fields

| Field | ID | Type | Notes |
|-------|----|------|-------|
| Route | 8225 | text | Primary field, e.g. "Home → King's Cross" |
| From | 8228 | text | Origin name |
| From lat | 8232 | number | Origin latitude |
| From lon | 8233 | number | Origin longitude |
| To | 8229 | text | Destination name |
| To lat | 8234 | number | Destination latitude |
| To lon | 8235 | number | Destination longitude |
| Default Mode | 8230 | single_select | Tube / Bus / Walk / Cycle / Train / Drive |
| Typical Duration (mins) | 8231 | number | Usual journey time |
| Notes | 8226 | long_text | Route hints, line names, etc. |
| Active | 8227 | boolean | Include in digest checks |

## How It Works

### Morning Digest Integration

When the morning digest runs (6am UTC), the travel section:

1. **Read today's calendar** — query Google Calendar for events with locations/addresses
2. **Match against Routes table** — check if destination matches a known route
3. **Get live routing** — use OSRM for cycling/walking/driving time
4. **Check TfL status** — if mode is Tube/Bus, check line disruptions
5. **Add to digest** — append travel section with journey time + any disruptions

### Ad-Hoc Use

When David asks "how do I get to X?" or "what's the tube status?":

1. **Geocode destination** — use Nominatim via maps_client.py
2. **Route via OSRM** — get distance + duration for requested mode
3. **Check TfL** — if transit mode, check relevant lines
4. **Return formatted answer** — journey time, distance, any disruptions

## Scripts

### travel_fetch.py

Fetches travel data for the morning digest.

```bash
python3 /root/Geeves/scripts/travel_fetch.py
```

Returns JSON:
```json
{
  "has_travel": true,
  "journeys": [
    {
      "destination": "King's Cross",
      "event_time": "09:00",
      "mode": "cycle",
      "duration_mins": 17,
      "distance_km": 6.4,
      "route_notes": "Via Hampstead Rd",
      "tfl_disruptions": []
    }
  ],
  "tfl_summary": "All lines good service"
}
```

### journey_check.py

Ad-hoc journey planner.

```bash
python3 /root/Geeves/scripts/journey_check.py "King's Cross" --mode cycling
python3 /root/Geeves/scripts/journey_check.py "King's Cross" --mode tube
python3 /root/Geeves/scripts/journey_check.py --tfl-status
```

## OSRM Routing

Uses the public OSRM instance at `https://router.project-osrm.org`.

**Modes supported:**
- `cycling` — bike routes (David's most common)
- `walking` — pedestrian routes
- `driving` — car routes

**API pattern:**
```
GET /route/v1/{mode}/{from_lon},{from_lat};{to_lon},{to_lat}?overview=false
```

**Response:** duration (seconds), distance (meters)

## TfL API

Free, no API key required.

**Line status:**
```
GET https://api.tfl.gov.uk/Line/Mode/{mode}/Status
```

Modes: `tube`, `bus`, `dlr`, `overground`, `tflrail`, `tram`

**Journey planner:**
```
GET https://api.tfl.gov.uk/Journey/JourneyResults/{from_lat},{from_lon}/to/{to_lat},{to_lon}
```

## Geocoding

Use the existing maps skill:
```bash
python3 ~/.hermes/skills/productivity/maps/scripts/maps_client.py search "King's Cross Station, London"
```

Returns lat/lon for use with OSRM.

## Prompt Skeleton

```
ROLE: You are Geeves, David's personal assistant.
TASK: Plan travel / check journey status for David.

CONTEXT:
- Home: 43 Enginals Lane, Camden, NW3 4YD (51.5567, -0.1879)
- Known routes: {routes_table_data}
- Today's calendar events with locations: {calendar_events}
- Live TfL status: {tfl_status}
- OSRM route data: {routing_data}

OUTPUT: Clear, concise travel advice. Include:
- Journey time and distance
- Recommended mode
- Any disruptions or delays
- Leave-by time if there's a calendar event

TONE: Practical, brief. David just wants to know how long it takes and if there are problems.
```

## Adding New Routes

When David mentions a destination:

1. Geocode it: `python3 ~/.hermes/skills/productivity/maps/scripts/maps_client.py search "<destination>"`
2. Get coordinates from result
3. Create row in Routes table via `baserow_api.py create-row Routes '{...}'`
4. Route will now appear in morning digest checks

## Error Handling

- OSRM unavailable → fall back to Typical Duration from Routes table
- TfL API down → skip disruption check, note "TfL status unavailable"
- Calendar empty → no travel section in digest
- Geocoding fails → ask David for clarification

## Integration Checklist

- [x] Routes table created in Baserow (id=892)
- [x] baserow_mapping.json updated
- [ ] travel_fetch.py written
- [ ] journey_check.py written
- [ ] Morning digest updated with travel section
- [ ] Skill registered in modules_status.json
- [ ] Tested end-to-end
