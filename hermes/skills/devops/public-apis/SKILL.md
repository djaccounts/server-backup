---
name: public-apis
description: "Public APIs reference for Geeves — curated free-tier APIs, rate limits, auth patterns, and implementation notes. Use when any module needs an external API (news, weather, stocks, facts, PDF, search, air quality, quotes)."
version: 1.0.0
author: Geeves
---

# Public APIs — Geeves Reference

Curated free-tier APIs used across Geeves modules. All have free tiers; keys stored in `/root/.hermes/.env`.

## Quick Lookup

| API | Env Var | Free Tier | Used By |
|-----|---------|-----------|---------|
| Open-Meteo | *(none)* | Unlimited | Bulletin weather |
| yfinance | *(none)* | Unlimited | Bulletin stocks |
| SWAPI.tech | *(none)* | Unlimited | Bulletin Star Wars |
| Wikipedia On This Day | *(none)* | Unlimited | Bulletin fact |
| NASA APOD | `NASA_API_KEY` (or DEMO_KEY) | Unlimited | Bulletin fact |
| Quote Garden | *(none)* | Unlimited | Bulletin fact |
| Zen Quotes | *(none)* | Unlimited | Bulletin fact |
| Nager.Date | *(none)* | Unlimited | Bulletin fact |
| Useless Facts | *(none)* | Unlimited | Bulletin fact |
| icanhazdadjoke | *(none)* | Unlimited | Bulletin fact (fallback) |
| World News API | `WORLD_NEWS_API_KEY` | 50/day | News/Search |
| SerpApi | `SERPAPI_KEY` | 250/mo | Google Search |
| PDFBolt | `PDFBOLT_API_KEY` | 100 PDFs/mo | Digest PDF, recipe PDF |
| OMDb | `OMDB_API_KEY` | 1,000/day | Film Club IMDb lookup |
| Alpha Vantage | `ALPHA_VANTAGE_KEY` | 25/day | Backup stocks |
| Finnhub | `FINNHUB_KEY` | 60 calls/min | Backup stocks |
| Twelve Data | `TWELVE_DATA_KEY` | 800/day | Backup stocks |
| Purple Air | `PURPLE_AIR_KEY` | Unlimited | Air quality |
| OpenUV | `OPENU_V_KEY` | Unlimited | UV index |

## Auth Pattern (All APIs)

All keys are read from `/root/.hermes/.env` via grep — never from `os.environ`:

```python
import subprocess
def get_key(var_name):
    r = subprocess.run(["grep", var_name, "/root/.hermes/.env"], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""
```

---

## News & Search

### World News API
- **URL:** `https://api.worldnewsapi.com`
- **Auth:** `x-api-key` header
- **Key:** `WORLD_NEWS_API_KEY`
- **Endpoints:** `/top-news`, `/search-news`, `/front-pages`
- **Returns:** title, URL, author, image, publish date, sentiment score
- **Rate limit:** 50 requests/day

### SerpApi
- **URL:** `https://serpapi.com/search`
- **Auth:** `api_key` query param
- **Key:** `SERPAPI_KEY`
- **Engines:** `google`, `google_finance`, `google_news`
- **Script:** `/root/Geeves/scripts/serpapi_search.py`
- **Rate limit:** 250 searches/month
- **⚠ `google_news` returns `source` as dict** (`{"name": "BBC", "icon": "..."}`) not a string — extract with `source.get("name", "")` after `isinstance(source, dict)` check.

### NewsAPI (backup)
- **URL:** `https://newsapi.org/v2`
- **Auth:** `X-Api-Key` header
- **Rate limit:** 100 requests/day

---

## Document Generation

### PDFBolt
- **URL:** `https://api.pdfbolt.com/v1/convert`
- **Auth:** `API-KEY` header (**NOT** `Bearer`)
- **Key:** `PDFBOLT_API_KEY`
- **Rate limit:** 100 PDFs/month
- **⚠ HTML must be base64-encoded** before sending
- **⚠ Top-level keys:** `format`, `margin`, `printBackground` are top-level (NOT nested under `options`)
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
- **Scripts:** `/root/Geeves/scripts/digest_to_pdf.py`, `/root/Geeves/scripts/build_digest_html.py`

---

## Quotes & Facts

### Wikipedia On This Day
- **URL:** `https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/selected/{month}/{day}`
- **Auth:** None
- **Returns:** Historical events for this date

### NASA APOD
- **URL:** `https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY` (or `NASA_API_KEY`)
- **Auth:** `api_key` query param
- **Returns:** Astronomy Picture of the Day

### Quote Garden
- **URL:** `https://quote-garden.onrender.com/api/v3/quotes/random`
- **Auth:** None
- **⚠ Intermittent 503** — have fallback ready

### Zen Quotes
- **URL:** `https://zenquotes.io/api/random`
- **Auth:** None

### Nager.Date
- **URL:** `https://date.nager.at/api/v3/PublicHolidays/{year}/{countryCode}`
- **Auth:** None
- **Returns:** Public holidays for 90+ countries

### Useless Facts
- **URL:** `https://uselessfacts.jsph.pl/api/v2/facts/random`
- **Auth:** None

### icanhazdadjoke (fallback)
- **URL:** `https://icanhazdadjoke.com/`
- **Auth:** None — set `Accept: application/json` header

### Numbers API
- **⚠ BROKEN as of June 2026** — all endpoints return 404. Removed from rotation.

---

## Weather & Environment

### Open-Meteo (in use)
- **URL:** `https://api.open-meteo.com/v1/forecast`
- **Auth:** None
- **Params:** `&current=temperature_2m,relative_humidity_2m,...&daily=temperature_2m_max,temperature_2m_min,...&hourly=weather_code,precipitation_probability,precipitation,temperature_2m&timezone=Europe%2FLondon&forecast_days=1`
- **Script:** `/root/Geeves/scripts/weather_fetch.py`

### Purple Air
- **URL:** `https://api.purpleair.com/v1/sensors`
- **Auth:** `X-API-Key` header
- **Key:** `PURPLE_AIR_KEY`
- **Returns:** Real-time air quality (PM2.5)

### OpenUV
- **URL:** `https://api.openuv.io/api/v1/uv`
- **Auth:** `x-access-token` header
- **Key:** `OPENU_V_KEY`
- **Returns:** UV index forecast

---

## Finance

### yfinance (in use)
- **Python library:** `pip install yfinance`
- **Auth:** None
- **Tickers:** `BTC-GBP`, `AMZN`, `GOOGL`, `META`
- **Script:** `/root/Geeves/scripts/stocks_fetch.py`
- **⚠ Returns last closing price before market open** — correct for morning digest

### Alpha Vantage (backup)
- **URL:** `https://www.alphavantage.co/query`
- **Auth:** `apikey` query param
- **Key:** `ALPHA_VANTAGE_KEY`
- **Rate limit:** 25 requests/day

### Finnhub (backup)
- **URL:** `https://finnhub.io/api/v1`
- **Auth:** `token` query param
- **Key:** `FINNHUB_KEY`
- **Rate limit:** 60 calls/min

### Twelve Data (backup)
- **URL:** `https://api.twelvedata.com`
- **Auth:** `apikey` query param
- **Key:** `TWELVE_DATA_KEY`
- **Rate limit:** 800 requests/day

---

## Entertainment

### SWAPI.tech (Star Wars)
- **URL:** `https://www.swapi.tech/api/people/{id}/`
- **Auth:** None
- **⚠ `swapi.dev` has expired SSL** — use `swapi.tech`
- **⚠ Requires `User-Agent` header** — requests without it get 403
- **Response structure:** `data["result"]["properties"]` — nested, not flat
- **Homeworld:** URL that needs a second API call to resolve
- **Script:** `/root/Geeves/scripts/starwars_fetch.py`

### OMDb (IMDb lookup)
- **URL:** `https://www.omdbapi.com/`
- **Auth:** `apikey` query param
- **Key:** `OMDB_API_KEY`
- **Rate limit:** 1,000 requests/day
- **Method:** `?t={title}` for title search, `?i={ttID}` for exact IMDb ID
- **⚠ Title-only searches may return wrong version** — users can disambiguate with year or IMDb ID

---

## Hermes Internal

### Token Usage Tracking
- **Source:** `/root/.hermes/state.db` SQLite → `sessions` table
- **Columns:** `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `reasoning_tokens`, `estimated_cost_usd`, `model`, `started_at`
- **Script:** `/root/Geeves/scripts/token_usage.py`
- **Airtable table:** `Token_Usage` (tbl3EjtE3YW1ZUqEv)

---

## Pitfalls

1. **Numbers API broken** — 404 on all endpoints since ~June 2026
2. **PDFBolt auth** — `API-KEY` header (not `Bearer`), HTML must be base64-encoded, `format`/`margin` are top-level
3. **SerpApi `google_news` source field** — returns dict not string
4. **SWAPI** — use `swapi.tech` not `swapi.dev` (expired SSL), needs `User-Agent` header
5. **Quote Garden 503** — intermittent, have fallback ready
6. **Open-Meteo timeouts** — can timeout on 15s limit; consider retry with backoff
7. **OMDb title ambiguity** — "Matrix" → 1993 TV film, not 1999; use year or IMDb ID to disambiguate
