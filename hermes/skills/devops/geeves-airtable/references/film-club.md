# Films Table — Reference

## Overview

Combined film diary + film club in a single table. Film Club is a filter/view, not a separate table.

**Workflow:** 3 club members recommend 1 film each per month → all watch → all discuss → rate → recommend for next month. David's wife (Member 4) also rates films with David but is NOT in the film club.

**Design decision (from thread):** One table rather than separate Film Club + Film Diary tables. Simpler, and David is unlikely to track other people's ratings beyond the 3 club members + his wife. Film Club view = filter where `Film Club = Yes`.

**⚠ Thread decisions supersede this document.** If a user conversation changes a schema decision, the registry and this doc should both be updated to match.

## Table

| Table | Airtable ID | Purpose |
|-------|-------------|---------|
| `Films` | `tblqCpp3EB7wU2ZZ3` | All film records — personal diary + film club |

Film Club view: filter where `Film Club = Yes`.

## Fields (25)

### Core Film Info (every record)

| Field | Type | Source |
|-------|------|--------|
| Film Title | text | Extracted from Slack or CSV import |
| Year | number (precision 0) | IMDb auto-lookup (OMDb) |
| Director | text | IMDb auto-lookup |
| Genre | text | IMDb auto-lookup |
| IMDb Rating | number (precision 1) | IMDb auto-lookup |
| IMDb Votes | number (precision 0) | IMDb auto-lookup |
| Metascore | number (precision 0) | IMDb auto-lookup |
| IMDb URL | url | Auto-generated from IMDb ID |

### Personal Rating (every record)

| Field | Type | Source |
|-------|------|--------|
| My Rating | select (1-10) | Extracted from Slack or CSV import |
| Date Watched | date | Extracted or from CSV |
| Personal Notes | longText | User's personal review |

### Film Club (only for club picks)

| Field | Type | Source |
|-------|------|--------|
| Film Club | select (Yes/No) | Set to "Yes" for club picks |
| Month Picked | text | e.g. "2026-06" — when it was recommended |
| Watched At | select | Hosted (at someone's home) / Remote (streamed remotely) / Cinema / N/A |
| Club Discussion Notes | longText | Group discussion notes |
| Recommended By | multipleRecordLinks → People | Who suggested it |

### Member Ratings (only for club picks)

| Field | Type | Source |
|-------|------|--------|
| Member 2 Name | multipleRecordLinks → People | Club member 2 |
| Member 2 Rating | select (1-10, "Not rated") | Their score |
| Member 2 Notes | longText | Their comments |
| Member 3 Name | multipleRecordLinks → People | Club member 3 |
| Member 3 Rating | select (1-10, "Not rated") | Their score |
| Member 3 Notes | longText | Their comments |
| Member 4 Name | multipleRecordLinks → People | David's wife (rates films, not in club) |
| Member 4 Rating | select (1-10, "Not rated") | Their score |
| Member 4 Notes | longText | Their comments |

## Rating Scale

All ratings use 1-10. The Slack capture handler converts:
- X/5 → doubled (4/5 = "8", 3/5 = "6")
- X/10 → used directly (6/10 = "6")
- ★★★★★ → "10", ★★★★ → "8", etc.
- "rated X" or "gave it X" → scaled (assumes X/10 if X > 5, else X/5 doubled)

## IMDb Auto-Lookup

- **API:** OMDb (omdbapi.com)
- **Key:** In `/root/.hermes/.env` as `OMDB_API_KEY`
- **Rate limit:** 1,000 requests/day (free tier)
- **Pitfall:** Title-only searches may return wrong version (e.g., "Matrix" → 1993 TV film, not 1999). Users can disambiguate with year or IMDb ID.
- **Method:** `?t={title}` for title search, `?i={ttID}` for exact IMDb ID

## IMDb CSV Import

IMDb allows exporting your full ratings history as CSV (`Your Ratings` page → Export CSV). A bulk import script reads the CSV, does OMDb lookups for metadata, and creates Films records. Not yet built.

## Slack Capture Rules

Film Club matches these keywords in `slack_capture.py`:
- "film club", "movie club", "movie night", "film night"
- "just watched", "finished watching"
- "rated X/5", "rated X/10", "rated it X"
- "add to list", "log the film"

**Classification priority:** Film Club rules appear BEFORE Module Request in `CATEGORY_RULES` to ensure film messages route correctly.

## Extraction Patterns

### Film Title
1. Quoted titles: `"The Matrix"` or `'The Matrix'`
2. After verbs: "add X", "watch X", "just watched X", "finished watching X", "rated X"
3. Boundary-word truncation stops at: at, on, in, to, with, from, rated, remote, remotely, film, movie, club, cinema, list, online, zoom

### Rating
Converts to 1-10 scale (see Rating Scale above).

### Watched At
- **Hosted:** "at mine", "at my", "at david's", "hosted", "in person", "together at", "came over", "round at"
- **Remote:** "remote", "streamed", "online", "zoom", "separately", "own homes", "from home"
- **Cinema:** "cinema", "odeon", "vue", "imax", "theatre", "theater"

### Month
- Named months in message text (e.g., "in June")
- Defaults to current month
- Format: "2026-06" (YYYY-MM)

## Integration Points

- **People table:** Recommended By, Member 2/3/4 Name all link to People (tbl1WMPtQhWYW7bTI) — click a person's record to see all films linked to them
- **Output_Log:** Film Club queries/suggestions log to Output_Log with Module="FilmClub"
- **Cron:** The 30-min Slack capture loop processes film club messages alongside other categories

## Legacy Tables (delete manually in Airtable web UI)

These were superseded by the Films table:
- `FilmClub_Data` (tblcHHlQWa0JqtKrQ) — delete manually
- `FilmClub_Log` (tblWdOf902bKaQwWl) — delete manually
