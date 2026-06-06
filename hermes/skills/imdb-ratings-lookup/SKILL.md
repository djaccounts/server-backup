---
name: imdb-ratings-lookup
description: Look up IMDb ratings and film metadata via OMDb API. Use when the user asks for movie/TV ratings, release years, directors, plot summaries, or any IMDb metadata. NEVER fabricate ratings from memory.
triggers:
  - "what's the rating of"
  - "IMDb rating"
  - "how good is"
  - "movie rating"
  - "film score"
  - "rotten tomatoes"  # redirect to OMDb which also has RT scores
metadata: {"clack":{"emoji":"🎬","requires":{"bins":["python3"]},"config":{"env":{"OMDB_API_KEY":{"description":"OMDb API key from omdbapi.com (free tier: 1,000 req/day)","required":true}}}}}
---

# IMDb Ratings Lookup via OMDb API

Look up film/TV metadata reliably. **Never guess or fabricate ratings** — if the API call fails, say so.

## API Key

Get a free key at <http://omdbapi.com/apikey.aspx> (1,000 requests/day). The key should be stored in Hermes `.env` or passed via terminal.

## How to Query

**ALWAYS use `terminal()` with a heredoc script**, NOT `execute_code()` — the sandbox mangles API key strings.

### By Title

```bash
python3 << 'PYEOF'
import urllib.request, json, os

api_key = os.environ.get("OMDB_API_KEY", "YOUR_KEY_HERE")
title = "The Matrix"

url = f"http://www.omdbapi.com/?t={urllib.parse.quote(title)}&apikey={api_key}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    if data.get("Response") == "True":
        print(f"Title: {data.get('Title')}")
        print(f"Year: {data.get('Year')}")
        print(f"IMDb Rating: {data.get('imdbRating')}")
        print(f"IMDb Votes: {data.get('imdbVotes')}")
        print(f"Metascore: {data.get('Metascore')}")
        print(f"Rotten Tomatoes: next((r['Value'] for r in data.get('Ratings', []) if r['Source'] == 'Rotten Tomatoes'), 'N/A')")
        print(f"Director: {data.get('Director')}")
        print(f"Plot: {data.get('Plot')}")
    else:
        print(f"Not found: {data.get('Error')}")
except Exception as e:
    print(f"Error: {e}")
PYEOF
```

### By IMDb ID (for ambiguous titles)

```python
# Use ?i=tt0133093 instead of ?t=...
url = f"http://www.omdbapi.com/?i=tt0133093&apikey={api_key}"
```

### Batch Lookup (multiple titles)

```python
# Deduplicate first to save API calls!
titles = list(set(titles))  # remove duplicates before querying
for title in titles:
    # ... query each one, track count vs 1,000/day limit
```

## Key Rules

1. **NEVER fabricate ratings** — if you can't verify, say "I can't verify that"
2. **Use `terminal()` heredoc**, not `execute_code()` for API key safety
3. **Deduplicate** titles before batch queries (1,000/day limit)
4. **Use IMDb IDs** (`tt...`) for ambiguous titles (remakes, common names)
5. **Web scraping IMDb/Google is blocked** on most VPS setups — OMDb API is the reliable path
6. **Check `Response: "True"`** before reading fields — missing films return `False`

## Common Pitfalls

- `execute_code()` sandbox mangles API key strings → use `terminal()` heredoc
- Forgetting URL encoding on titles with special characters → use `urllib.parse.quote()`
- Not handling the `Response: "False"` case → always check before reading data
- Exceeding 1,000 req/day → deduplicate, cache results, batch wisely
