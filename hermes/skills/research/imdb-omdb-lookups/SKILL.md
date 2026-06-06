---
name: imdb-and-omdb-lookups
description: "Look up film/TV IMDb ratings and metadata using the OMDb API. Covers the reliable Python-via-heredoc pattern for API queries."
platforms: [linux, macos, windows]
---

# IMDb / OMDb Lookups

## When to use

When you need IMDb ratings, vote counts, genres, plots, or other film/TV metadata. IMDb blocks automated browser/curl access, so use the OMDb API.

## API Key

The user's OMDb API key is saved in memory. If missing, request the user sign up at `https://www.omdbapi.com/apikey.aspx` (free tier: 1,000 requests/day).

## Why not direct IMDb?

- IMDb blocks curl/scraping (returns empty responses)
- Google and DuckDuckGo return bot-detection CAPTCHAs
- Wikipedia API links to IMDb but doesn't embed ratings
- Browser may be unavailable or broken on the VPS

## Reliable query pattern

Use `curl` via `terminal` to hit OMDb. The API returns JSON with `imdbRating`, `imdbVotes`, `Genre`, `Plot`, etc.

### Single lookup

```bash
curl -s "http://www.omdbapi.com/?t=The+Piano&y=1993&apikey=KEY"
```

### Batch lookup (recommended)

When checking many films, write a Python script to `/tmp/` via `terminal` heredoc, then run it. This avoids `execute_code` syntax issues with special characters in API keys or strings.

```bash
cat > /tmp/ratings.py << 'PYEOF'
import subprocess, json, os
os.environ["OMDB_KEY"] = "KEY"
candidates = [("Film Title", "Year"), ...]
for title, year in candidates:
    url = f"http://www.omdbapi.com/?t={title.replace(' ', '+')}&y={year}&apikey={os.environ['OMDB_KEY']}"
    r = subprocess.run(["curl", "-s", url], capture_output=True, text=True, timeout=10)
    d = json.loads(r.stdout)
    if d.get("Response") == "True":
        print(f"{d['Title']} ({d['Year']}): {d['imdbRating']}/10")
PYEOF
python3 /tmp/ratings.py
```

### By IMDb ID (most accurate)

```bash
curl -s "http://www.omdbapi.com/?i=tt0115736&apikey=KEY"
```

Using `i=` (IMDb ID) is more reliable than `t=` (title) which can return wrong matches.

## Response fields

| Field | Description |
|-------|-------------|
| `imdbRating` | IMDb score out of 10 (string, e.g. "7.5") |
| `imdbVotes` | Number of votes (string with commas) |
| `Genre` | Comma-separated genres |
| `Plot` | Short plot summary |
| `Response` | "True" or "False" — always check this |
| `Error` | Error message when Response is "False" |

## Common pitfalls

- **Wrong match**: Title search can return a different film with the same name. Always verify the year matches. Use IMDb ID (`i=`) when possible.
- **Rate limiting**: Free tier is 1,000/day. Batch queries with small delays if needed.
- **execute_code syntax errors**: Special characters in API keys or strings can cause `execute_code` to fail with cryptic errors. Use the heredoc-to-file pattern above instead.
- **NEVER fabricate ratings**: If you can't verify a rating, say so. Fabricated numbers destroy trust.

## References

- `references/verified_imdb_ids_1980_1999.md` — Verified IMDb IDs and ratings for 1980-1999 films with sexuality themes
- `scripts/omdb_batch_lookup.py` — Reusable batch lookup script (copy, edit OMDB_KEY, run via terminal)
