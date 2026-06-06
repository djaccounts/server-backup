# External Data Lookup: IMDb, OMDb, and Similar APIs

## IMDb Ratings

IMDb (imdb.com) **blocks automated curl/scraping** — returns empty responses. Cannot be accessed directly via curl or execute_code.

### OMDb API (Open Movie Database)

- **URL:** https://www.omdbapi.com/
- **Free tier:** 1,000 requests/day with a free API key
- **Sign up:** https://www.omdbapi.com/apikey.aspx (requires email confirmation — cannot be automated in a headless session)
- **Format:** `https://www.omdbapi.com/?t=Bound&y=1996&apikey=YOUR_KEY`
- **Returns:** JSON with `imdbRating`, `Plot`, `Year`, `Genre`, `Actors`, etc.
- **Get API key:** The user must sign up manually via their browser; the form sends the key via email.

### Alternatives for IMDb Data

- **TMDb API** (https://developer.themoviedb.org/) — free, generous rate limits, includes IMDb ID cross-references
- **Trakt.tv API** — includes rating data
- **Wikipedia API** — does NOT embed IMDb ratings, but links to IMDb in external links section. Use `https://en.wikipedia.org/w/api.php?action=query&titles=<TITLE>&prop=extracts&explaintext=true&format=json`

## IMDB Research Blockers (Known)

When researching film/TV ratings, the following services block automated access:
- **IMDb** — blocks curl, requires browser
- **DuckDuckGo HTML** — returns CAPTCHA challenges for bot-like queries
- **Google** — blocks or returns empty.

**What works:** Wikipedia API for company/product/film factual data (not ratings). OMDb if you have a key.

## General Principle

When a user asks for factual data (ratings, numbers, statistics) and you cannot verify it via a reliable source, **do not fabricate it**. Present what you know from training data with a confidence qualifier ("likely around X"), and offer to look it up or ask the user to verify.
