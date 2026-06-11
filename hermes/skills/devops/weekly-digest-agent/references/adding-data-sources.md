# Adding a New Data Source to the Weekly Digest

## Pattern

To add a new module's data to the weekly digest:

1. **Create a Baserow table** for weekly summaries (e.g. `Listening` for Spotify)
   - Fields typically: Week starting (date), summary fields, text summary
   - Use `table_builder.py` or direct Baserow Platform API (JWT auth) for table/field creation
   - Add entry to `baserow_mapping.json`

2. **Write a `*_fetch.py` script** at `/root/Geeves/scripts/`
   - Fetch data from the source API for the last 7 days
   - Compute summaries (top items, totals, trends, observations)
   - Write one row to the Baserow table
   - Support `--write` flag (dry run by default)
   - Deduplicate: check for existing row for the same week before writing
   - Follow the pattern in `spotify_weekly_fetch.py`

3. **Update the weekly digest cron prompt** (job `b0b836135650`):
   - Add a fetch step between Step 1 (Geeves data) and Step 3 (Build HTML)
   - Make it optional (skip gracefully if it fails)
   - Include key metrics in the Slack summary (Step 6)

4. **Update the skill** (`weekly-digest-agent` SKILL.md):
   - Add row to Data Sources table
   - Add to Dependencies section
   - Document any auth requirements

5. **Update `AGENTS.md`**:
   - Add module to Active Modules table
   - Add script to Scripts table

## Example: Spotify Listening (added June 2026)

- Table: `Listening` (Baserow ID 402)
- Script: `spotify_weekly_fetch.py`
- Auth: `hermes auth spotify` (requires Spotify Developer app, Client ID only — no secret needed for PKCE)
- Data: Top 5 tracks, top 3 artists, total plays, most active day, natural-language summary
- Frequency: Weekly, as part of Sunday 8pm UTC digest cron
