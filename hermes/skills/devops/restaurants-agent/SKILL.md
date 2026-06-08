---
name: restaurants-agent
description: "Geeves Restaurant Agent — restaurant reviews, Google Maps lookup via SerpApi, Airtable CRUD for Restaurants and Restaurant Visits tables, Slack capture handling, and recommendation engine. Use when adding restaurants, logging visits, reviewing restaurants, or handling restaurant-related Slack messages."
version: 1.0.0
author: Geeves
---

# Restaurant Agent

Manages the Restaurants and Restaurant Visits tables. Handles Google Maps lookups via SerpApi, Airtable CRUD, Slack capture, and restaurant recommendations.

## Tables

| Table | ID | Purpose |
|-------|----|---------|
| `Restaurants` | `tblvpSxjeoCQvjotM` | Master restaurant records — every restaurant been to or want to try |
| `Restaurant Visits` | `tblf2k6uAHLW7mA4b` | Individual visit records — detailed feedback per visit |

## Key Fields

### Restaurants
- **Name** (primary), **Cuisine** (multiSelect), **Address**, **Postcode**, **Phone**, **Website**
- **Maps URL** (url) — Google search link for the restaurant
- **Price Range** (select: £/££/£££/££££), **Food Type** (multiSelect), **Dietary Friendly** (multiSelect), **Ambience** (multiSelect)
- **Google Rating**, **Google Review Count**, **Google Price Level**, **Google Types**, **Review Summary**
- **Alignment Score** (select: Strong match/Moderate/Weak/Unknown), **Alignment Notes**
- **Source** (select: We went/Recommended/Found online/Want to try)
- **Status** (select: Want to go/Been — loved it/Been — liked it/Been — meh/Been — avoid)
- **Overall Rating** (select 1-10), **Times Visited**, **Last Visited**, **Photo**, **Notes**
- **Recommended By** (→ People), **Restaurant Visits** (→ Restaurant Visits)

### Restaurant Visits
- **Date**, **Restaurant** (→ Restaurants), **People** (→ People)
- **Dishes Ordered**, **Dish Ratings** (free text, e.g. "Pizza: 9/10, Pasta: 7/10")
- **Service Rating**, **Ambience Rating**, **Value Rating**, **Overall Rating** (all select 1-10)
- **Wife's Rating** (select 1-10), **Wife's Notes** (long text — her separate feedback)
- **Would Return** (select: Definitely/Maybe/No)
- **Best Dish**, **Worst Dish**, **Cost Total** (£), **Cost Per Head** (£)
- **Occasion** (select: Date night/Family meal/Friends/Birthday/Casual/Business/Anniversary)
- **Photo**, **Notes**, **Source** (select: Slack/Manual)

## Google Maps Lookup (SerpApi)

- **API:** `https://serpapi.com/search` (engine: `google_maps`)
- **Key:** `SERPAPI_KEY` in `/root/.hermes/.env`
- **Free tier:** 250 searches/month
- **Search:** `?engine=google_maps&q={restaurant_name}+{city}&type=search&hl=en`

```python
import subprocess, json, urllib.request, urllib.parse

def serpapi_key():
    r = subprocess.run(["grep", "SERPAPI_KEY", "/root/.hermes/.env"], capture_output=True, text=True)
    return r.stdout.strip().split("\n")[0].split("=", 1)[1]

def lookup_restaurant(name, location="London"):
    key = serpapi_key()
    params = {
        "api_key": key,
        "engine": "google_maps",
        "q": f"{name} {location}",
        "type": "search",
        "hl": "en",
    }
    url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    pr = data.get("place_results", {})
    if not pr:
        return None
    gps = pr.get("gps_coordinates", {})
    return {
        "name": pr.get("title", ""),
        "rating": pr.get("rating", ""),
        "reviews": pr.get("reviews", ""),
        "price": pr.get("price", ""),
        "types": pr.get("type", []),
        "address": pr.get("address", ""),
        "phone": pr.get("phone", ""),
        "website": pr.get("website", ""),
        "hours": pr.get("hours", []),
        "open_state": pr.get("open_state", ""),
        "lat": gps.get("latitude"),
        "lon": gps.get("longitude"),
        "place_id": pr.get("place_id", ""),
        "data_id": pr.get("data_id", ""),
        "review_summary": pr.get("rating_summary", []),
        "extensions": pr.get("extensions", []),
    }
```

### Building the Maps URL

Use Google search format (reliable across all devices):

```python
def build_maps_url(name, location="London"):
    query = f"{name} {location}"
    return f"https://www.google.com/search?q={urllib.parse.quote(query)}"
```

Store this in the `Maps URL` field. When tapped, it opens Google search results with the Maps card showing rating, reviews, hours, and directions.

## Alignment Score

Compare restaurant data against `Dining Preferences` table to generate an alignment score:

1. Read `Dining Preferences` for the active user
2. Compare restaurant types, price level, ambience against preferences
3. Weight by confidence (Strong > Moderate > Emerging)
4. Set `Alignment Score` and write explanation in `Alignment Notes`

Example: *"High Google rating (4.8★) but alignment is Moderate — you prefer quiet fine dining; reviews mention 'bustling atmosphere' and 'lively'. Dishoom is casual Indian, not fine dining."*

## Airtable CRUD

Use `/root/Geeves/scripts/airtable_api.py`:

```bash
# List restaurants
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "Restaurants"

# Create restaurant
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "Restaurants" \
  '{"Name": "Dishoom King'\''s Cross", "Cuisine": ["Indian"], "Price Range": "££"}'

# Create visit
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "Restaurant Visits" \
  '{"Date": "2026-06-06", "Overall Rating": "9", "Wife'\''s Rating": "8"}'

# Update record
python3 /root/Geeves/scripts/airtable_api.py update-record appzvmonQXs4x2AlL "Restaurants" "<record_id>" \
  '{"Overall Rating": "9", "Times Visited": 3}'
```

**Auth:** Read `AIRTABLE_API_KEY` from `/root/.hermes/.env` via grep (never from `os.environ`).

## Adding a Restaurant (Manual Workflow)

1. User says: *"We went to England's Lane in Belsize Park"*
2. Hermes searches SerpApi → gets rating, address, hours, etc.
3. Hermes creates `Restaurants` record with auto-filled data
4. Hermes creates `Restaurant Visits` record linked to the restaurant
5. User adds personal ratings and notes (or provides them in the message)
6. Hermes calculates alignment score from `Dining Preferences`

## Logging a Visit

When user reports a visit:
1. Find or create the `Restaurants` record
2. Create a `Restaurant Visits` record with:
   - Restaurant link, Date, People link
   - Dishes, ratings, costs
   - Wife's separate rating and notes
3. Update `Restaurants.Times Visited` and `Restaurants.Last Visited`

## Restaurant Recommendations

When user asks for recommendations:
1. Read `Dining Preferences` table for taste profile
2. Read `Restaurants` for previously visited + rated places
3. Optionally search SerpApi for new candidates
4. Score each candidate by alignment with preferences
5. Return ranked list with reasoning

## Slack Capture

Script: `/root/Geeves/scripts/slack_capture.py`

**Trigger keywords:** "restaurant", "went to", "ate at", "dinner at", "lunch at", "find me a restaurant", "recommend a restaurant", "restaurant review", "rating", "booked", "reservation"

### Extraction Patterns

**Restaurant Name:**
1. After "went to", "ate at", "dinner at", "lunch at", "booked"
2. Quoted names: `"Dishoom"` or `'The Wolseley'`
3. Boundary-word truncation: at, in, for, with, from, rated, restaurant

**Ratings:**
- "X/10" or "X out of 10" → Overall Rating
- "wife rated X" or "she gave it X" → Wife's Rating
- "X stars" → convert (4/5 = "8")

**Dishes:**
- After "had", "ordered", "tried"
- Before "was" (e.g. "the pizza was amazing")

**Cost:**
- "£XX" or "£XX per head" → Cost Total / Cost Per Head
- "bill was £XX" → Cost Total

**People:**
- "with [name]" or "with [name] and [name]" → People link

**Would Return:**
- "definitely going back", "will return" → Definitely
- "maybe go back", "might return" → Maybe
- "never going back", "won't return" → No

## Integration Points

- **People table:** Recommended By (Restaurants), People (Restaurant Visits) both link to People (tbl1WMPtQhWYW7bTI)
- **Dining Preferences:** Cross-module table (tblzzGIF7yPf37NG5) — alignment scoring reads from here
- **Output_Log:** Recommendation queries log to Output_Log with Module="Restaurants"

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Thread decisions supersede reference docs
- Get David's explicit approval before creating any Airtable table
- Wife's rating and notes are always separate fields — never merge with David's

## Reference

- `public-apis` skill — SerpApi details
- `geeves-airtable` skill — Airtable CRUD patterns
- `geeves-steward` skill — schema changes
