# Digest Composition Guide

## Architecture

The digest is built in 3 stages:
1. **Data Fetch:** `bulletin_fetch.py` runs fetcher scripts, writes to Airtable
2. **HTML Build:** `build_digest_html.py` reads from Airtable, composes HTML
3. **PDF Convert:** `digest_to_pdf.py` sends HTML to PDFBolt, saves PDF
4. **Email:** AgentMail sends HTML + PDF attachment

## Adding a New Section

1. Create fetcher script in `/root/Geeves/scripts/` (follow patterns)
2. Create Airtable table (via Metadata API)
3. Add entry to `SCRIPTS` list in `bulletin_fetch.py`
4. Add fetch + section HTML in `build_digest_html.py`
5. Update the footer to credit the new data source
6. Update `references/bulletin-setup.md`

## Removing a Section

1. Remove entry from `SCRIPTS` list in `bulletin_fetch.py`
2. Remove the fetch + section HTML in `build_digest_html.py`
3. Update the footer to remove the data source credit
4. Update `references/bulletin-setup.md`
5. Old Airtable data remains but won't be included. Optionally delete old table via Airtable web UI.

## Current Sections (2026-06-04)

| Section | Table | Fetcher | Status |
|---------|-------|---------|--------|
| Weather | Weather_Data | weather_fetch.py | Active |
| Markets | Stock_Prices | stocks_fetch.py | Active |
| Fact of the Day | Fact_of_the_Day | fact_fetch.py | Active |
| Star Wars | Star_Wars_Fact | starwars_fetch.py | Active |
| Token Usage | Token_Usage | token_usage.py | Active |
| News (removed) | News_Headlines | news_fetch.py | Removed per user request |

## Email Delivery Notes

- **Work email (dj@djaccounts.com):** May be blocked by corporate spam filters
- **Personal Gmail (daverj1987@gmail.com):** More reliable fallback
- **Test first:** Send plain-text test before HTML+PDF when changing email content