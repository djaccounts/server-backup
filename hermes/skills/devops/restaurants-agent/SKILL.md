---
name: restaurants-agent
description: "Geeves Restaurants Agent — restaurant tracking, review, and recommendation module. Use when David mentions restaurants, eating out, reviewing a place, or asking for restaurant recommendations."
version: 1.0.0
author: Geeves
---

# Restaurants Agent

Restaurant tracking and review module. Logs visits with detailed feedback (including separate ratings and notes for David and wife), enriches with Google data via SerpApi, and builds alignment scores against the shared `Dining Preferences` table. Over time, enables personalized restaurant recommendations.

## Table(s)

| Table | ID | Purpose |
|-------|----|---------|
| `Restaurants` | `tblvpSxjeoCQvjotM` | Master record for every restaurant visited or want to try |
| `Restaurant Visits` | `tblf2k6uAHLW7mA4b` | Each visit — detailed feedback, ratings, costs |

## Key Fields

### Restaurants
| Field | ID | Type | Purpose |
|-------|----|------|---------|
| Name | `fld2TJDmJIdu1ayii` | singleLineText | Restaurant name |
| Cuisine | `fldLzaKf7a6GPGI6C` | multipleSelects | Italian/Indian/Thai/etc |
| Address | `fld9o0uM3Zpf0J80O` | multilineText | Full address |
| Postcode | `fldg046XloE793VB8` | singleLineText | Postcode |
| Phone | `fldrd5ygZLFigE84x` | singleLineText | Contact number |
| Website | `fldBSectzalK5OqLF` | url | Restaurant website |
| Maps URL | `fldNpo4ew68sDRNa9` | url | Google search link |
| Price Range | `fldlod8Sgu5gpUdYr` | singleSelect | £/££/£££/££££ |
| Food Type | `fldjNyYKI6y8HQzPS` | multipleSelects | Fine dining/Casual/Pub/etc |
| Dietary Friendly | `fld44e6rYBtZGE2JX` | multipleSelects | Vegan-friendly/Gluten-free/etc |
| Ambience | `fldydO2NkeYY0DKd9` | multipleSelects | Romantic/Quiet/Lively/etc |
| Google Rating | `fldJVW6srFaHlD0g5` | number | Google star rating |
| Google Review Count | `fldDHaYjwxJgiJnZd` | number | Number of Google reviews |
| Google Price Level | `fldtsfcW2zo6RbWfT` | number | Google price level 1-4 |
| Google Types | `fld6zBMuMV4jN0gWT` | multilineText | Google place type tags |
| Review Summary | `fldUd7n7y4lfiQqsV` | multilineText | Summary of reviewer sentiment |
| Alignment Score | `fldsqrHaMkJYpKyP4` | singleSelect | Strong match/Moderate/Weak/Unknown |
| Alignment Notes | `fldsIIfrgIYOsTExs` | multilineText | Why this does/doesn't match preferences |
| Source | `fld9Qe5SGyyRvpGZy` | singleSelect | We went/Recommended/Found online/Want to try |
| Recommended By | `fldIQRmAvJB0ATnWw` | link → People | Who recommended it |
| Status | `fldSZQiVDuk4BXgEI` | singleSelect | Want to go/Been — loved it/liked it/meh/avoid |
| Overall Rating | `fldfcXWFuGqKtfi04` | singleSelect | 1-10 |
| Times Visited | `fldUvzoJM3zEL2x8F` | number | Visit count |
| Last Visited | `fldFl8tulnbwaSGjx` | date | Most recent visit |
| Photo | `fldz69M7VRc0IDgQq` | attachment | Photo |
| Notes | `fld8x4FGLxpw5AYsv` | multilineText | Freeform notes |

### Restaurant Visits
| Field | ID | Type | Purpose |
|-------|----|------|---------|
| Restaurant | `fld3ZBz6SKoiDwQdl` | link → Restaurants | Which restaurant |
| Date | `fldgM2cY4CI8EQbMM` | date | When you went |
| People | `fldB05E5NthL9YD9I` | link → People | Who was there |
| Dishes Ordered | `fldtXfW1wMjbkkJ2p` | multilineText | What was ordered |
| Dish Ratings | `fldPHQkSvEjo1oEs3` | multilineText | Per-dish ratings |
| Service Rating | `fldvqEV2aCxBUTvcY` | singleSelect | 1-10 |
| Ambience Rating | `fldk5EuOaHvEGpmaZ` | singleSelect | 1-10 |
| Value Rating | `fldAAlvrbOIGRnMBm` | singleSelect | 1-10 |
| Overall Rating | `fld3XBGqc2GRg4kjK` | singleSelect | 1-10 |
| Wife's Rating | `fldtMDtBq4KkmbV55` | singleSelect | 1-10 |
| Wife's Notes | `fldZfTEtpVnbYYCrB` | multilineText | Wife's separate feedback |
| Would Return | `fldDoqDoRDFL0pBmB` | singleSelect | Definitely/Maybe/No |
| Best Dish | `fldzrOXfMlZQyVGXE` | singleLineText | Standout dish |
| Worst Dish | `fldy8aIJbMXpSUOGw` | singleLineText | Letdown dish |
| Cost Total | `fldr0ucTrFU5HhX7M` | currency | Total bill £ |
| Cost Per Head | `fld77DFACVtPz4CiP` | currency | Per person £ |
| Occasion | `fldwseQBQIXtKjiAW` | singleSelect | Date night/Family meal/Friends/etc |
| Photo | `fldHCsKTJZqNcLraL` | attachment | Photo of meal |
| Notes | `fldeKN2iTYyk81nCV` | multilineText | Detailed feedback |
| Source | `fldTaAKZ0W4RrEUJp` | singleSelect | Slack/Manual |

## Airtable CRUD

Read `AIRTABLE_API_KEY` from `/root/.hermes/.env` via grep (never from `os.environ`).

Base ID: `appzvmonQXs4x2AlL`

Use the Airtable REST API directly via Python (see workflows below).

## Workflows

### 1. Add a Restaurant (via SerpApi lookup)

When David mentions a restaurant name, look it up via SerpApi Google Maps and create a `Restaurants` record with enriched data.

```python
import subprocess, json, urllib.request, urllib.parse

# Get keys from .env
def get_key(var):
    r = subprocess.run(["grep", var, "/root/.hermes/.env"], capture_output=True, text=True)
    return r.stdout.strip().split("\n")[0].split("=", 1)[1]

serpapi_key = get_key("SERPAPI_KEY")
airtable_key = get_key("AIRTABLE_API_KEY")

# Search Google Maps via SerpApi
params = {
    "api_key": serpapi_key,
    "engine": "google_maps",
    "q": "RESTAURANT_NAME London",  # adjust location as needed
    "type": "search",
    "hl": "en",
}
url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
with urllib.request.urlopen(url, timeout=15) as resp:
    data = json.loads(resp.read())

pr = data.get("place_results", {})

# Build Google search URL (reliable format)
search_query = f"{pr.get('title', name)} {pr.get('address', '').split(',')[0]}"
maps_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"

# Create Airtable record
record = {
    "fields": {
        "Name": pr.get("title", name),
        "Address": pr.get("address", ""),
        "Postcode": pr.get("address", "").split(",")[-1].strip() if pr.get("address") else "",
        "Phone": pr.get("phone", ""),
        "Website": pr.get("website", ""),
        "Maps URL": maps_url,
        "Google Rating": pr.get("rating"),
        "Google Review Count": pr.get("reviews"),
        "Google Price Level": pr.get("price_level"),  # may need mapping from price string
        "Google Types": ", ".join(pr.get("type", [])),
        "Source": "We went" if "went" in user_message.lower() else "Want to try",
    }
}

# POST to Airtable
airtable_url = "https://api.airtable.com/v0/appzvmonQXs4x2AlL/Restaurants"
payload = json.dumps(record).encode()
req = urllib.request.Request(airtable_url, data=payload, headers={
    "Authorization": f"Bearer {airtable_key}",
    "Content-Type": "application/json",
}, method="POST")
with urllib.request.urlopen(req, timeout=10) as resp:
    result = json.loads(resp.read())
    record_id = result["id"]
```

### 2. Log a Restaurant Visit

When David describes a visit, create a `Restaurant Visits` record linked to the restaurant.

1. Find or create the `Restaurants` record (use workflow 1 if new)
2. Create `Restaurant Visits` record with David's feedback
3. Update `Restaurants` record: increment `Times Visited`, set `Last Visited`, update `Overall Rating` and `Status`

```python
# Create visit record
visit = {
    "fields": {
        "Restaurant": [restaurant_record_id],
        "Date": "2026-06-06",  # parse from message or use today
        "Dishes Ordered": "Pad Thai, Green Curry",
        "Dish Ratings": "Pad Thai: 9/10, Green Curry: 7/10",
        "Service Rating": "8",
        "Ambience Rating": "7",
        "Value Rating": "8",
        "Overall Rating": "8",
        "Wife's Rating": "7",
        "Wife's Notes": "Enjoyed it but found the curry a bit spicy",
        "Would Return": "Definitely",
        "Best Dish": "Pad Thai",
        "Cost Total": 65.00,
        "Cost Per Head": 32.50,
        "Occasion": "Date night",
        "Notes": "Great atmosphere, service was friendly. Will come back.",
        "Source": "Slack",
    }
}
```

### 3. Restaurant Recommendations

When David asks for restaurant recommendations:

1. Read `Dining Preferences` table for taste profile
2. Read `Restaurants` table — filter by cuisine match, status, rating
3. Read `Restaurant Visits` table — check past ratings and "Would Return"
4. Rank by: alignment score + past ratings + Google rating
5. Return top 3-5 with reasoning and Google search links

### 4. Calculate Alignment Score

Compare restaurant attributes against `Dining Preferences`:

1. Read `Dining Preferences` for the person(s) dining
2. Compare restaurant's Cuisine, Food Type, Ambience, Price Range against preferences
3. Check review summary for keywords matching/preference
4. Set `Alignment Score`: Strong match / Moderate / Weak / Unknown
5. Write explanation to `Alignment Notes`

## Slack Capture

**Trigger keywords:** "restaurant", "went to", "ate at", "dinner at", "lunch at", "find me a restaurant", "recommend a restaurant", "review", "booking", "booked", "menu"

**Classification priority:** After Recipes, before generic chat.

### Extraction Patterns

- **Restaurant name:** Usually after "went to" / "ate at" / "dinner at" / "at the"
- **Ratings:** Look for "X/10" or "X out of 10" patterns
- **Dishes:** Look for dish names, especially after "had" / "ordered" / "ate"
- **Cost:** Look for £ amounts
- **Date:** Parse relative dates ("last night", "Saturday", "yesterday")
- **Wife's input:** Look for "wife thought", "she said", "her rating"

## Cron Jobs

None currently. Future: periodic Dining Preferences analysis based on visit history.

## Dependencies

- **People** → `Restaurants.Recommended By`, `Restaurant Visits.People`
- **Dining Preferences** (shared cross-module) → alignment scoring and recommendations

## Integration Points

- **Dining Preferences table** → alignment scoring, recommendation engine
- **People graph** → who recommended, who visited, dietary constraints
- **SerpApi** → Google Maps data enrichment (rating, reviews, hours, types)
- **Google search links** → reliable restaurant lookup (no direct Maps API available)

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Get David's explicit approval before creating any Airtable table
- Thread decisions supersede reference docs
- Update this skill when conversation changes a decision
- Use Google search links for Maps URLs (direct Maps links are unreliable)
- SerpApi free tier: 250 searches/month — use sparingly, cache results

## Pitfalls

1. **Google Maps direct links don't work reliably** — use Google search links instead: `https://www.google.com/search?q=RESTAURANT_NAME+ADDRESS`
2. **SerpApi rate limit** — 250 searches/month free tier. Don't re-search the same restaurant.
3. **Place name ambiguity** — "The Clove Club" vs "Clove Club" can return different results. Always verify the address matches.
4. **Price level mapping** — SerpApi returns price as "£10–20" strings, not numeric levels. Map manually.
5. **Wife's ratings** — always ask for or infer separately from David's. Don't assume they're the same.
6. **Date parsing** — "last Saturday" needs careful parsing. When in doubt, ask.
7. **Select field 422** — writing undefined choice to a select field fails. Use `typecast=true` or match existing choices exactly.
8. **Link fields require existing records** — create the restaurant record first, then the visit record with the link.

## Reference

- `public-apis` skill — SerpApi Google Maps API details
- `geeves-airtable` skill — Airtable API patterns
- `Geeves_Schema_Reference_v2.md` — full field definitions (Module 22 — Restaurants)
- `Dining Preferences` table ID: `tblzzGIF7yPf37NG5`
