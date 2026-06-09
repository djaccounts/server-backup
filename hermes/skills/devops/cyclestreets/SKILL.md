---
name: cyclestreets
description: "UK cycle journey planner — plan routes, find leisure rides, check infrastructure, collision data, and upload GPS tracks. Uses the CycleStreets API v2 (REST, JSON). Free API key required."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cycling, routing, uk, maps, gps, infrastructure]
---

# CycleStreets API v2

UK cycle journey planner built on OpenStreetMap. Plan routes, find leisure rides, explore cycling infrastructure, and upload GPS tracks.

## API Key

1. Sign up at https://www.cyclestreets.net/
2. Apply for an API key at https://www.cyclestreets.net/api/apply/
3. Free for non-commercial use

Store the key as `CYCLESTREETS_API_KEY` in your environment or pass directly.

## Base URL

```
https://www.cyclestreets.net/api/
```

## Endpoints

### Plan a Journey

```bash
curl -sL "https://www.cyclestreets.net/api/journey.json?key=${CYCLESTREETS_API_KEY}&plan=quietest&start=LAT,LNG&end=LAT,LNG"
```

| Param | Values | Description |
|-------|--------|-------------|
| `plan` | `fastest`, `quietest`, `balanced` | Route preference |
| `start` | `lat,lng` | Start point |
| `end` | `lat,lng` | End point |
| `via` | `lat,lng` | Optional waypoint (repeatable) |

Returns: route geometry, distance, time, turn-by-turn directions, elevation profile.

### Plan Leisure (Circular) Route

```bash
curl -sL "https://www.cyclestreets.net/api/journey.json?key=${CYCLESTREETS_API_KEY}&plan=leisure&start=LAT,LNG&distance=20"
```

| Param | Description |
|-------|-------------|
| `distance` | Target distance in miles |
| `time` | Target time in minutes (alternative to distance) |

### Retrieve a Journey

```bash
curl -sL "https://www.cyclestreets.net/api/journey.json?key=${CYCLESTREETS_API_KEY}&plan=retrieve&id=JOURNEY_ID"
```

### Isochrones (Reachable Area)

```bash
curl -sL "https://www.cyclestreets.net/api/isochrone.json?key=${CYCLESTREETS_API_KEY}&lat=LAT&lng=LNG&time=600"
```

Returns polygon of reachable area within X seconds.

### Geocoder

```bash
curl -sL "https://www.cyclestreets.net/api/geocoder.json?key=${CYCLESTREETS_API_KEY}&query=Cambridge"
```

Search streets, towns, postcodes, stations → lat/lng.

### Collisions Data

```bash
curl -sL "https://www.cyclestreets.net/api/collisions.json?key=${CYCLESTREETS_API_KEY}&lat=LAT&lng=LNG&radius=500"
```

Cycle collision data near a point.

### Traffic Counts

```bash
curl -sL "https://www.cyclestreets.net/api/trafficcounts.json?key=${CYCLESTREETS_API_KEY}&lat=LAT&lng=LNG&radius=500"
```

### Cycle Infrastructure

```bash
# Popup cycleways being implemented
curl -sL "https://www.cyclestreets.net/api/popupcycleways.json?key=${CYCLESTREETS_API_KEY}&type=implemented&bbox=LAT1,LNG1,LAT2,LNG2"

# Suggested popup cycleways
curl -sL "https://www.cyclestreets.net/api/popupcycleways.json?key=${CYCLESTREETS_API_KEY}&type=suggested&bbox=LAT1,LNG1,LAT2,LNG2"

# LTN modal filters
curl -sL "https://www.cyclestreets.net/api/ltns.json?key=${CYCLESTREETS_API_KEY}&type=modalfilters&bbox=LAT1,LNG1,LAT2,LNG2"
```

### Photomap (Cycling Infrastructure Photos)

```bash
# Get photos near a location
curl -sL "https://www.cyclestreets.net/api/photomap.json?key=${CYCLESTREETS_API_KEY}&lat=LAT&lng=LNG&radius=500"

# Photo of the day
curl -sL "https://www.cyclestreets.net/api/photomap.json?key=${CYCLESTREETS_API_KEY}&photooftheday=true"
```

### Upload GPS Track

```bash
curl -sL -X POST "https://www.cyclestreets.net/api/gpstrack.json?key=${CYCLESTREETS_API_KEY}" \
  -F "file=@/path/to/ride.gpx" \
  -F "description=Morning commute"
```

### Routing Coverage

```bash
curl -sL "https://www.cyclestreets.net/api/coverage.json?key=${CYCLESTREETS_API_KEY}"
```

Shows areas the router covers (UK + some international).

### API Status

```bash
curl -sL "https://www.cyclestreets.net/api/status.json?key=${CYCLESTREETS_API_KEY}"
```

## Python Helper

```python
import os, json, urllib.request, urllib.parse

CYCLESTREETS_KEY = os.environ.get("CYCLESTREETS_API_KEY", "YOUR_KEY")
BASE = "https://www.cyclestreets.net/api/"

def cs_get(endpoint, **params):
    params["key"] = CYCLESTREETS_KEY
    url = BASE + endpoint + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read())

# Plan a route
route = cs_get("journey.json", plan="quietest", start="52.2053,0.1218", end="51.5074,-0.1278")
print(f"Distance: {route['route']['distance']} miles")
print(f"Time: {route['route']['time']} minutes")

# Geocode
results = cs_get("geocoder.json", query="Cambridge")
for r in results['results']:
    print(r['name'], r['latitude'], r['longitude'])

# Collisions near a point
collisions = cs_get("collisions.json", lat="52.2053", lng="0.1218", radius="500")
for c in collisions.get('collisions', []):
    print(c['date'], c['severity'], c['description'])
```

## Integration with Airtable Cycling Module

Use this skill to:
1. **Plan routes** between two points → store distance/time in Cycling table
2. **Log leisure rides** → suggest circular routes by distance
3. **Upload GPX tracks** from rides
4. **Check collision data** for regular routes
5. **Find new cycleways** near your area

## When to Use

- Planning a cycle route (fastest/quietest/balanced)
- Finding circular leisure rides
- Looking up cycling infrastructure photos
- Checking collision hotspots
- Uploading GPS tracks from Strava/Garmin exports
- Geocoding UK postcodes/addresses
