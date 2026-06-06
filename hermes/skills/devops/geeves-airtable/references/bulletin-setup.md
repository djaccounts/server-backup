# Bulletin Data Setup

## API Sources & Reliability

| Script | API | Key Required | Status | Notes |
|--------|-----|:---:|---|---|
| `weather_fetch.py` | Open-Meteo | No | ✅ Reliable | Free, no key. Uses forecast endpoint with daily + hourly data. |
| `stocks_fetch.py` | yfinance (Yahoo Finance) | No | ✅ Reliable | Pulls BTC-GBP, AMZN, GOOGL, META |
| `fact_fetch.py` | Rotating (6 sources) | No | ✅ Reliable | See Fact of the Day section below |
| `token_usage.py` | Hermes state.db | No | ✅ Reliable | Query SQLite for session token metrics |
| `starwars_fetch.py` | SWAPI.tech | No | ✅ Reliable | Random Star Wars character fact (see Star Wars section) |

## Master Script

```bash
python3 /root/Geeves/scripts/bulletin_fetch.py        # dry run
python3 /root/Geeves/scripts/bulletin_fetch.py --write # fetch all + write to Airtable
```

Calls `weather_fetch.py`, `stocks_fetch.py`, `fact_fetch.py`, `starwars_fetch.py`, and `token_usage.py` in sequence.

⚠️ **No deduplication:** Running `--write` twice creates duplicate records. Only run once per day.

## Weather Data

**Open-Meteo endpoint:** `GET /v1/forecast` with params:
```
&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m
&daily=temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum
&hourly=weather_code,precipitation_probability,precipitation
&timezone=Europe%2FLondon
&forecast_days=1
```

**Fields in `Weather_Data` table:** Date, Location, Temperature C, Feels Like C, **High C**, **Low C**, Humidity Pct, Wind Speed KPH, Condition, **Daily Condition**, **Rain Expected**, **Rain Times**, **Precipitation MM**, **Morning Temp C**, **Morning Condition**, **Morning Rain Prob**, **Afternoon Temp C**, **Afternoon Condition**, **Afternoon Rain Prob**, **Evening Temp C**, **Evening Condition**, **Evening Rain Prob**, Description.

**Weather URL now includes `temperature_2m` in hourly block** (needed for morning/afternoon/evening splits):
```
&hourly=weather_code,precipitation_probability,precipitation,temperature_2m
```

**Morning/Afternoon/Evening periods** are calculated from hourly data:
- Morning: 6:00–12:00 London time (avg temp, most common condition, max rain probability)
- Afternoon: 12:00–18:00 London time
- Evening: 18:00–22:00 London time
- Rain probability badge (🌧️) shown in digest when ≥50%

**Rain detection:** WMO codes {51,53,55,56,57,61,63,65,66,67,80,81,82,95,96,99}. Also flags precip>0 or prob≥50%. Groups consecutive hours into periods.

**⚠ Timezone pitfall:** Normalize hourly timestamps with `.replace(tzinfo=timezone.utc)` before comparing to `datetime.now(timezone.utc)`.

**⚠ Avoid Airtable `sort` with URL brackets.** Fetch unsorted, pick latest client-side: `max(records, key=lambda r: r['fields']['Date'])`.

## Fact of the Day

**6 rotating sources** (cycles by `day_of_year % 6`):

| Idx | Source | API | Label | Content |
|-----|--------|-----|-------|---------|
| 0 | Wikipedia On This Day | `api.wikimedia.org/feed/v1/wikipedia/en/onthisday/selected/{M}/{D}` | Wikipedia | Historical events for this date |
| 1 | NASA APOD | `api.nasa.gov/planetary/apod?api_key=DEMO_KEY` | Wikipedia | Astronomy Picture of the Day |
| 2 | Quote Garden | `quote-garden.onrender.com/api/v3/quotes/random` | Useless Fact | Famous quotes (→ icanhazdadjoke fallback) |
| 3 | Zen Quotes | `zenquotes.io/api/random` | Useless Fact | Mindfulness quotes |
| 4 | Nager.Date | `date.nager.at/api/v3/PublicHolidays/{yr}/{cc}` | Wikipedia | Public holidays in 10 countries |
| 5 | Useless Facts | `uselessfacts.jsph.pl/api/v2/facts/random` | Useless Fact | Random trivia |

**Fallback chain:** If primary fails, tries ALL others in order. Always produces a fact.

**Force a source:** `python3 fact_fetch.py --source nasa`

**⚠ Select reuse:** Category field choices are `Wikipedia`, `Numbers`, `Useless Fact`. Cannot create new ones via API — reuse existing labels.

**Numbers API (`numbersapi.com`) is DOWN** — all endpoints 404 as of June 2026. Removed from rotation.

## Star Wars Fact

**API:** SWAPI.tech (`https://www.swapi.tech/api/people/{id}/`)
**⚠ `swapi.dev` has expired SSL** — use `swapi.tech` instead.
**⚠ Requires `User-Agent` header** — requests without it get 403 Forbidden.

**Airtable table:** `Star_Wars_Fact` (ID: `tblAvJ4PG6HbAXruj`)
**Fields:** Date, Name, Height, Mass, Hair Color, Eye Color, Gender, Birth Year, Homeworld, Films Count, Fact, Source URL

**How it works:** Picks a random character ID (1-83), fetches from SWAPI, resolves homeworld name, picks a random fact template from 4 variations. Each day gets a different character.

```bash
python3 /root/Geeves/scripts/starwars_fetch.py        # dry run
python3 /root/Geeves/scripts/starwars_fetch.py --write # write to Airtable
```

**SWAPI response structure:** `data["result"]["properties"]` — nested, not flat. Homeworld is a URL that needs a second API call to resolve.

## Stock Prices

**Tickers:** `BTC-GBP`, `AMZN`, `GOOGL`, `META`. Each writes a separate Stock_Prices record.

**⚠ yfinance** returns last closing price before market open — correct for morning digest.

## Token Usage Tracking

**Script:** `/root/Geeves/scripts/token_usage.py`
**Data source:** `/root/.hermes/state.db` → `sessions` table
**Airtable table:** `Token_Usage` (ID: `tbl3EjtE3YW1ZUqEv`)

**Fields:** Date, Sessions, Input Tokens, Output Tokens, Cache Read Tokens, Total Active Tokens, Estimated Cost USD, Top Model, Summary.

**Columns queried from state.db:** `input_tokens`, `output_tokens`, `cache_read_tokens`, `reasoning_tokens`, `estimated_cost_usd`, `model`, `started_at`.

Default: reports yesterday's usage (midnight to midnight). Use `--today` for current day.

## Table IDs

| Table | ID |
|-------|----|
| Weather_Data | `tblFd4kAahIUozJsf` |
| Stock_Prices | `tblI1oXlNIFXrVm7f` |
| Fact_of_the_Day | `tblUTCWleQD61Ti2v` |
| Token_Usage | `tbl3EjtE3YW1ZUqEv` |
| Star_Wars_Fact | `tblAvJ4PG6HbAXruj` |

## Email Delivery

- **To:** `dj@djaccounts.com`
- **From:** `blacksignal723@agentmail.to`
- **Script:** `python3 /root/Geeves/scripts/agentmail_helper.py send <to> <subject> <body>`

**⚠ Bug fix (2026-06-03):** `agentmail_helper.py` was reading `/root/.env` — fixed to read `/root/.hermes/.env`. If email breaks, verify: `grep AGENT_MAIL_API /root/.hermes/.env`.

## PDF Digest Generation

**Script:** `/root/Geeves/scripts/build_digest_html.py` → `/root/Geeves/scripts/digest_to_pdf.py`
**API:** PDFBolt (100 PDFs/month free, key: `PDFBOLT_API_KEY` in `.env`)
**Output:** `/root/Geeves/digests/digest_YYYY-MM-DD.pdf`

Pipeline:
```bash
python3 /root/Geeves/scripts/build_digest_html.py --save                          # Build HTML from Airtable data
python3 /root/Geeves/scripts/digest_to_pdf.py --file /root/Geeves/digests/digest_YYYY-MM-DD.html  # Convert to PDF
```

**PDFBolt auth:** `API-KEY` header (NOT `Bearer`). HTML must be base64-encoded. See `references/external-apis.md` for full request format.

**Email with PDF:** Include `MEDIA:/path/to/digest.pdf` in the agentmail body — the platform delivers it as a native attachment.

## Cron Job — Geeves Morning Digest

- **Schedule:** `0 6 * * *` UTC (= 7am UK BST summer; 6am GMT winter)
- **What:** Fetches bulletin data → builds HTML via `build_digest_html.py` → generates PDF via `digest_to_pdf.py` → sends email (HTML body + PDF attachment) via AgentMail
- **Single source of truth:** Email body = HTML from `build_digest_html.py`. PDF = same HTML converted via PDFBolt. Both always match.
- **Winter DST adjust:** Late Oct → bump to `0 7 * * *` for 7am GMT
- **Cron is always UTC**
- **Cron prompt instructs agent to:** (1) run `bulletin_fetch.py --write`, (2) run `build_digest_html.py --save`, (3) run `digest_to_pdf.py --file <html>`, (4) send email with HTML body + PDF attachment to `dj@djaccounts.com`

## Public APIs Reference

Curated from `github.com/toddmotto/public-apis`. Key free APIs for future modules:
- Science: NASA api.nasa.gov, math.tools, arXiv
- Quotes: Quote Garden, Zen Quotes, icanhazdadjoke, kanye.rest, Advice Slip, Inspiration.goprogram.ai
- Holidays: Nager.Date (90+ countries, no key)
- Dictionary: Free Dictionary (dictionaryapi.dev)
- Weather: Open-Meteo (current), MetaWeather (no key)
- Finance: Alpha Vantage, Finnhub, Twelve Data (free tiers)
- Environment: OpenUV, Purple Air (air quality)
- Search: SerpApi (250/month free, key=SERPAPI_KEY, script=/root/Geeves/scripts/serpapi_search.py)
- News: World News API (50/day free, 210+ countries, sentiment)
- PDF: PDFBolt (100/month free, HTML→PDF)

## Pitfalls

1. **Select field 422:** Writing undefined choice → `INVALID_MULTIPLE_CHOICE_OPTIONS`. Reuse existing labels.
2. **Duplicate records:** bulletin_fetch has no dedup. Run once daily only.
3. **Numbers API broken:** 404 on all endpoints since ~June 2026.
4. **Cron is UTC:** Review schedule at DST transitions (Oct/Mar).
5. **Timezone comparison:** Always normalize datetime objects before comparing.
6. **Duplicate stock records** accumulate on re-runs. Clean by date if needed.
7. **Quote Garden 503:** Returns 503 intermittently — fact_fetch falls back to icanhazdadjoke automatically.
8. **PDFBolt auth:** Uses `API-KEY` header (not `Bearer`), HTML must be base64-encoded, `format`/`margin` are top-level keys (not nested under `options`). Wrong format → 400 error.
9. **SerpApi `google_news` source field:** Returns `source` as a dict `{"name": "BBC"}` not a string — check `isinstance(source, dict)` before accessing.
10. **`execute_code` blocked in cron:** Use `write_file` + `terminal` pattern for Python scripts in cron jobs.
11. **AgentMail delivery to work domains:** Emails from `agentmail.to` domains may be caught by spam filters or blocked by corporate email servers (e.g., `dj@djaccounts.com`). **Workaround:** Send to personal Gmail (`gmail.com`) as primary, or send a plain-text test email first to verify delivery before sending HTML+PDF. Check spam folder if email doesn't arrive within 5 minutes.
12. **PDFBolt base64 encoding:** HTML must be base64-encoded before sending to API (`base64.b64encode(html.encode()).decode()`). Wrong format (raw HTML) → 400 error. Use `API-KEY` header, not `Bearer`.
13. **Digest section order** is defined in `build_digest_html.py` only. Current order: Weather → Star Wars → Fact of the Day → Markets → Token Usage. To reorder, edit `build_digest_html.py` section blocks — both email and PDF update automatically.
14. **`agentmail_helper.py` does NOT support attachments.** Its `send` command only takes `to`, `subject`, `body`. For PDF attachments, use the AgentMail REST API directly with base64-encoded attachment content (see Email with Attachments pattern in SKILL.md).
15. **Adding weather hourly temperature:** Must add `temperature_2m` to the hourly params in `weather_fetch.py` URL. Without it, the morning/afternoon/evening split code crashes with `KeyError`.
