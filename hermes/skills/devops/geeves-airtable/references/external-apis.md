# External APIs Reference

Curated APIs for Geeves modules. All have free tiers.

## News & Search

| API | URL | Free Tier | Use Case |
|-----|-----|-----------|----------|
| **World News API** | worldnewsapi.com | 50 requests/day | Real-time news headlines, 210+ countries, sentiment analysis |
| **SerpApi** | serpapi.com | 250 searches/month | Google Search results, Google Finance for stock prices |
| **NewsAPI** | newsapi.org | 100 requests/day | Simple headline fetching |

### World News API
- Auth: `x-api-key` header
- Key endpoints: `/top-news`, `/search-news`, `/front-pages`
- Returns: title, URL, author, image, publish date, sentiment score

### SerpApi
- Auth: `api_key` query param
- Engines: `google`, `google_finance`, `google_news`
- Returns: structured JSON (no HTML scraping)

## Document Generation

| API | URL | Free Tier | Use Case |
|-----|-----|-----------|----------|
| **PDFBolt** | pdfbolt.com | 100 PDFs/month | HTML/URL to PDF, templates, async webhooks, S3 upload |

## Quotes & Facts (already in use by fact_fetch.py)

| API | URL | Used In |
|-----|-----|---------|
| Wikipedia On This Day | api.wikimedia.org | Source 0 |
| NASA APOD | api.nasa.gov | Source 1 |
| Quote Garden | quote-garden.onrender.com | Source 2 |
| Zen Quotes | zenquotes.io | Source 3 |
| Nager.Date | date.nager.at | Source 4 |
| Useless Facts | uselessfacts.jsph.pl | Source 5 |

## Environment & Weather

| API | URL | Use Case |
|-----|-----|----------|
| **Purple Air** | purpleair.com | Real-time air quality (PM2.5) |
| **OpenUV** | openuv.io | UV index forecast |
| Open-Meteo | open-meteo.com | Current weather (in use) |

## Finance (backup stock sources)

| API | URL | Free Tier |
|-----|-----|-----------|
| **Alpha Vantage** | alphavantage.co | 25 requests/day |
| **Finnhub** | finnhub.io | 60 calls/min |
| **Twelve Data** | twelvedata.com | 800 requests/day |

### PDFBolt — Implementation Details
- **Auth:** `API-KEY` header (NOT `Bearer`)
- **HTML must be base64-encoded** before sending
- **Top-level keys:** `format`, `margin`, `printBackground` are top-level (NOT nested under `options`)
- **Correct request format:**
  ```python
  import base64, json, urllib.request
  html_b64 = base64.b64encode(html_content.encode()).decode()
  payload = json.dumps({
      "html": html_b64,
      "format": "A4",
      "printBackground": True,
      "margin": {"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
  }).encode()
  req = urllib.request.Request(url, data=payload, headers={
      "API-KEY": key,
      "Content-Type": "application/json",
  }, method="POST")
  ```
- **Wrong format (returns 400):** nesting under `options`, sending raw HTML without base64, using `Authorization: Bearer`
- Scripts: `/root/Geeves/scripts/digest_to_pdf.py` (standalone), `/root/Geeves/scripts/build_digest_html.py` (HTML builder)

### SerpApi — Implementation Details
- **⚠ `google_news` returns `source` as a dict** (`{"name": "BBC", "icon": "..."}`) not a string — extract with `source.get("name", "")` after `isinstance(source, dict)` check.
- Search script: `/root/Geeves/scripts/serpapi_search.py`

## Hermes Internal Data

### Token Usage Tracking
- **Source:** `/root/.hermes/state.db` SQLite database → `sessions` table
- **Columns:** `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `reasoning_tokens`, `estimated_cost_usd`, `model`, `started_at`
- **Script:** `/root/Geeves/scripts/token_usage.py`
- **Airtable table:** `Token_Usage` (tbl3EjtE3YW1ZUqEv)

- **World News API:** Sign up at worldnewsapi.com -> add WORLD_NEWS_API_KEY to /root/.hermes/.env
- **SerpApi:** Sign up at serpapi.com -> add SERPAPI_KEY to /root/.hermes/.env. Search script: `/root/Geeves/scripts/serpapi_search.py`
- **PDFBolt:** Sign up at pdfbolt.com -> add PDF_BOLT_API_KEY to /root/.hermes/.env
- **Alpha Vantage:** Sign up at alphavantage.co -> add ALPHA_VANTAGE_KEY to /root/.hermes/.env
