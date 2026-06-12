---
name: add-film
description: "Add a film to the Films watchlist. Use when David says 'add [film]', 'add to films', 'add to watchlist', 'put [film] on the list', or similar. Handles IMDb lookup, duplicate check, and Baserow insert."
version: 1.0.0
author: Geeves
triggers:
  - "add to films"
  - "add to watchlist"
  - "add film"
  - "put on the list"
  - "add to list"
  - "watch this"
  - "want to watch"
  - "film club pick"
  - a bare film title in context of films/watchlist
---

# Add Film

Streamlined workflow for adding a film to the Films table (Baserow). This is the "quick add" path — for full film club management (member ratings, discussion notes), use `film-club-agent`.

## Table

- **Name:** Films
- **Baserow ID:** 366
- **Script:** `python3 /root/Geeves/scripts/baserow_api.py`

## Workflow

### 1. Identify the Film Title

Extract the film title from David's message using these patterns (in priority order):

1. **Quoted:** `"True Lies"` or `'True Lies'` → extract the quoted string
2. **After verbs:** "add X", "watch X", "put X on the list", "add X to films"
3. **Boundary-word truncation:** Stop at these words: `at`, `on`, `in`, `to`, `with`, `from`, `rated`, `remote`, `film`, `movie`, `club`, `cinema`, `please`, `thx`, `thanks`
4. **IMDb ID:** If David provides a `tt` ID (e.g. `tt0133093`), use it directly

If the title is ambiguous (common name, remake potential), ask David to confirm year or use IMDb ID.

### 2. Check for Duplicates

```bash
python3 /root/Geeves/scripts/baserow_api.py find Films "<title>"
```

If found, tell David it's already in the list and stop.

### 3. IMDb Lookup

Use `terminal()` heredoc (NOT `execute_code()`) to query OMDb:

```bash
python3 << 'PYEOF'
import urllib.request, json, urllib.parse

with open("/root/.hermes/.env") as f:
    for line in f:
        if line.strip().startswith("OMDB_API_KEY"):
            api_key = line.strip().split("=", 1)[1]
            break

title = "THE FILM TITLE"  # replace
url = f"https://www.omdbapi.com/?t={urllib.parse.quote(title)}&apikey={api_key}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    if data.get("Response") == "True":
        print(json.dumps({
            "title": data.get("Title", ""),
            "year": data.get("Year", ""),
            "director": data.get("Director", ""),
            "genre": data.get("Genre", ""),
            "imdb_rating": data.get("imdbRating", ""),
            "imdb_votes": data.get("imdbVotes", ""),
            "metascore": data.get("Metascore", ""),
            "imdb_id": data.get("imdbID", ""),
            "imdb_url": f"https://www.imdb.com/title/{data.get('imdbID', '')}/",
        }))
    else:
        print(f"ERROR:{data.get('Error', 'Not found')}")
except Exception as e:
    print(f"ERROR:{e}")
PYEOF
```

**For ambiguous titles** (e.g. "Matrix", "Heat", "Scarface"), ask David to specify year or provide IMDb ID before proceeding.

### 4. Confirm with David

If the film was already in the list (step 2), skip confirmation — just tell David it's there.

For new films, show:
```
🎬 [Title] ([Year]) — Dir: [Director], Genre: [Genre]
IMDb: [Rating]/10 ([Votes] votes) | Metascore: [Score]
[IMDb URL]
```

Then ask: "Add it? (or say 'film club' if it's a club pick)"

**Exception — multi-film adds:** If David says "add X and Y", add both without asking.

**Exception — "just":** If David says "just add it" or similar, skip confirmation.

### 5. Create Record

```bash
python3 /root/Geeves/scripts/baserow_api.py create-row Films '{
  "Film Title": "Title",
  "Year": 1994,
  "Director": "Director Name",
  "Genre": "Genre string",
  "IMDb Rating": 7.3,
  "IMDb Votes": 298420,
  "Metascore": 63,
  "IMDb URL": "https://www.imdb.com/title/ttXXXXXXXX/",
  "Film Club": "No"
}'
```

**Film Club default:** Always default to `"No"`. Only set `"Yes"` if David explicitly says it's a film club pick.

**Row number:** The script outputs `Created: row N`. Tell David the row number upon success.

### 6. After Adding

Tell David:
```
✅ [Title] added to watchlist (row N).
```

## Edge Cases

- **Not found on IMDb:** Tell David you couldn't find it. Ask for an IMDb ID (`tt...`) or an alternative title/spelling.
- **No IMDb data:** If the API returns `Response: False`, tell David and stop.
- **Ambiguous title:** Ask before adding. Don't guess.
- **Multiple films at once:** Add each one sequentially, report all at the end.
- **TV series:** OMDb will return `Type: series`. Tell David the Films table is for films only, but you can add it if he wants.

## Integration

- For film club picks (monthly rotation, member ratings), hand off to `film-club-agent`
- For bulk import from IMDb CSV, say "not yet built — want me to build it?"
- For rating a film after watching, update via `baserow_api.py update-row`
