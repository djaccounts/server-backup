---
name: film-club-agent
description: "Geeves Film Club Agent — IMDb lookups via OMDb, Airtable CRUD for Films table, Slack capture handling, and film club workflows. Use when adding films, looking up IMDb data, managing film club picks, or handling film-related Slack messages."
version: 1.0.0
author: Geeves
---

# Film Club Agent

Manages the Films table — film diary + film club in one table. Handles IMDb lookups, Airtable CRUD, and Slack capture.

## Table

| Table | ID | Purpose |
|-------|----|---------|
| `Films` | `tblqCpp3EB7wU2ZZ3` | All film records — personal diary + film club |

Film Club view: filter where `Film Club = Yes`.

## Key Fields

### Core (every record)
- Film Title, Year, Director, Genre, IMDb Rating, IMDb Votes, Metascore, IMDb URL

### Personal (every record)
- My Rating (select 1-10), Date Watched, Personal Notes

### Film Club (club picks only)
- Film Club (Yes/No), Month Picked (YYYY-MM), Watched At (Hosted/Remote/Cinema/N/A), Club Discussion Notes, Recommended By (→ People)

### Member Ratings (club picks only)
- Member 2/3/4 Name (→ People), Rating (select 1-10), Notes

**Club:** 3 members recommend 1 film each per month → all watch → discuss → rate.
**Member 4** = David's wife. Rates films with David but NOT in the film club.

## IMDb Lookup (OMDb)

- **API:** `https://www.omdbapi.com/`
- **Key:** `OMDB_API_KEY` in `/root/.hermes/.env`
- **Rate limit:** 1,000/day
- **Title search:** `?t={title}`
- **Exact ID:** `?i={ttID}` (preferred when available)

```python
import subprocess, json, urllib.request

def omdb_lookup(title=None, imdb_id=None):
    r = subprocess.run(["grep", "OMDB_API_KEY", "/root/.hermes/.env"], capture_output=True, text=True)
    key = r.stdout.strip().split("\n")[0].split("=", 1)[1]
    if imdb_id:
        url = f"https://www.omdbapi.com/?i={imdb_id}&apikey={key}"
    elif title:
        url = f"https://www.omdbapi.com/?t={title}&apikey={key}"
    else:
        return None
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    if data.get("Response") == "False":
        return None
    return {
        "title": data.get("Title", ""),
        "year": data.get("Year", ""),
        "director": data.get("Director", ""),
        "genre": data.get("Genre", ""),
        "imdb_rating": data.get("imdbRating", ""),
        "imdb_votes": data.get("imdbVotes", ""),
        "metascore": data.get("Metascore", ""),
        "imdb_id": data.get("imdbID", ""),
        "imdb_url": f"https://www.imdb.com/title/{data.get('imdbID', '')}/",
    }
```

**⚠ Title ambiguity:** "Matrix" → 1993 TV film, not 1999. Use year or IMDb ID to disambiguate.

## Airtable CRUD

Use `/root/Geeves/scripts/airtable_api.py`:

```bash
# List records
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "Films"

# Create record
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "Films" \
  '{"Film Title": "The Matrix", "Year": 1999, "Film Club": "Yes"}'

# Update record
python3 /root/Geeves/scripts/airtable_api.py update-record appzvmonQXs4x2AlL "Films" "<record_id>" \
  '{"My Rating": "8"}'
```

**Auth:** Read `AIRTABLE_API_KEY` from `/root/.hermes/.env` via grep (never from `os.environ`).

## Rating Conversion

All ratings converted to 1-10 select:
- X/5 → doubled (4/5 = "8")
- X/10 → used directly (6/10 = "6")
- ★★★★★ → "10", ★★★★ → "8", etc.
- "rated X" or "gave it X" → scaled (assumes X/10 if X > 5, else X/5 doubled)

## Slack Capture

Script: `/root/Geeves/scripts/slack_capture.py`

**Trigger keywords:** "film club", "movie club", "movie night", "film night", "just watched", "finished watching", "rated X/5", "rated X/10", "add to list", "log the film"

**Classification priority:** Film Club rules appear BEFORE Module Request in `CATEGORY_RULES`.

### Extraction Patterns

**Film Title:**
1. Quoted: `"The Matrix"` or `'The Matrix'`
2. After verbs: "add X", "watch X", "just watched X"
3. Boundary-word truncation: at, on, in, to, with, from, rated, remote, film, movie, club, cinema

**Watched At:**
- Hosted: "at mine", "at my", "hosted", "in person", "together at"
- Remote: "remote", "streamed", "online", "zoom", "separately"
- Cinema: "cinema", "odeon", "vue", "imax", "theatre"

**Month:** Named months in text → "2026-06" format. Defaults to current month.

## Adding a Film (Manual Workflow)

1. Look up IMDb data via OMDb
2. Create Films record in Airtable with core fields + personal fields
3. If Film Club pick: set `Film Club = Yes`, `Month Picked`, `Recommended By`
4. After watching: update member ratings

## IMDb CSV Import

IMDb allows exporting full ratings history as CSV. A bulk import script reads the CSV, does OMDb lookups, and creates Films records. **Not yet built** — create when needed.

## Integration Points

- **People table:** Recommended By, Member 2/3/4 Name all link to People (tbl1WMPtQhWYW7bTI)
- **Output_Log:** Film Club queries log to Output_Log with Module="FilmClub"

## Legacy Tables (delete manually in Airtable UI)

- `FilmClub_Data` (tblcHHlQWa0JqtKrQ)
- `FilmClub_Log` (tblWdOf902bKaQwWl)

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Thread decisions supersede reference docs
- Get David's explicit approval before creating any Airtable table

## Reference

- `public-apis` skill — OMDb API details
- `geeves-airtable/references/film-club.md` — full field docs, schema decisions
- `geeves-airtable/references/slack-capture.md` — classification rules, extraction patterns
