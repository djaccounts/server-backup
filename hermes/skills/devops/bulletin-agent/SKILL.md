---
name: bulletin-agent
description: "Geeves Bulletin Agent — fetch daily data, build HTML digest, generate PDF, and deliver via email + Slack. Runs as a cron job at 6am UTC. Use this skill when maintaining, debugging, or extending the bulletin/digest pipeline."
version: 1.0.0
author: Geeves
---

# Bulletin Agent

Fetches daily data, builds an HTML digest, generates a PDF, and delivers via email + Slack.

## Architecture

```
Cron (6am UTC)
  → bulletin_fetch_parallel.py --write  (fetch weather, stocks, fact, star wars, token_usage → Baserow)
  → build_digest_baserow.py --save      (read ALL data from Baserow → HTML)
  → digest_to_pdf.py                    (HTML → PDF via PDFBolt)
  → AgentMail API                       (HTML body + PDF attachment → dj@djaccounts.com)
  → Slack API                           (summary post → SLACK_HOME_CHANNEL)
```

**Single source of truth:** `build_digest_baserow.py` is the ONLY source for digest content. Both email body AND PDF come from the same HTML output. Never compose a separate plain text email.

**Migration status (June 2026):** Fully migrated to Baserow. All fetcher scripts write to Baserow via `baserow_api.py`. The legacy `legacy_airtable/` scripts are kept for reference only.

## Scripts (in order)

| Step | Script | Output |
|------|--------|--------|
| 1. Fetch data (parallel) | `bulletin_fetch_parallel.py --write` | Writes weather, stocks, fact, star wars, token_usage to Baserow |
| 1b. Fetch occasions | `python3 /root/Geeves/scripts/upcoming_occasions.py` | Upcoming birthdays/anniversaries for digest |
| 2. Build HTML | `build_digest_baserow.py --save` | `/root/Geeves/digests/digest_YYYY-MM-DD.html` |
| 3. Generate PDF | `digest_to_pdf.py --file <html>` | `/root/Geeves/digests/digest_YYYY-MM-DD.pdf` |
| 4. Send email | AgentMail API (see below) | To `dj@djaccounts.com` |
| 5. Post to Slack | `chat.postMessage` API | To `SLACK_HOME_CHANNEL` |

**⚠️ If `build_digest_html.py` fails** (e.g. Airtable data stale/missing), compose HTML directly from Baserow reads using `baserow_api.py` or raw API calls. The single-source-of-truth principle still applies: both email body and PDF must come from the same HTML.

## Data Sources

All scripts are in `/root/Geeves/scripts/`. All write to Baserow tables (migrated from Airtable June 2026).

| Fetcher | Baserow Table | Table ID | API | Key |
|---------|--------------|----------|-----|-----|
| `weather_fetch.py` | `Weather_Data` | 364 | Open-Meteo | None |
| `stocks_fetch.py` | `Stock_Prices` | 365 | yfinance | None |
| `fact_fetch.py` | `Fact_of_the_Day` | 363 | 6 rotating sources | None |
| `token_usage.py` | `Token_Usage` | 367 | Hermes state.db | None |
| `starwars_fetch.py` | `Star_Wars_Fact` | 371 | SWAPI.tech | None |
| `upcoming_occasions.py` | `Occasions` | 403 | Baserow | None |

**Fact rotation:** `day_of_year % 6` → 0=Wikipedia, 1=NASA, 2=Quote Garden, 3=Zen, 4=Holidays, 5=Useless Facts. Full fallback chain if primary fails.

**Stock tickers:** `BTC-GBP`, `AMZN`, `GOOGL`, `META`

**Star Wars:** Random character from SWAPI.tech people API (IDs 1–83). Fact varies: homeworld, physical stats, film count. Written to `Star_Wars_Fact` table in Baserow.

**⚠ Baserow writes require `baserow_api.py` helper** — field names auto-resolve to `field_XXXX` IDs. Use `baserow_api.baserow_post()` for all writes.

## Email Delivery

- **To:** `dj@djaccounts.com`
- **From:** `davidj@agentmail.to` (AgentMail inbox)
- **Body:** HTML from `build_digest_html.py` (NOT plain text)
- **Attachment:** PDF from `digest_to_pdf.py`

### Sending with Attachment (Python)

```python
import base64, json, urllib.request, subprocess

def get_env_key(var_name):
    r = subprocess.run(["grep", var_name, "/root/.hermes/.env"], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def send_digest(html_path, pdf_path, date_str):
    key = get_env_key("AGENT_MAIL_API")
    with open(html_path) as f:
        html_body = f.read()
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode()

    data = json.dumps({
        "to": ["dj@djaccounts.com"],
        "subject": f"Geeves Daily Digest — {date_str}",
        "html": html_body,
        "attachments": [{
            "filename": f"digest_{date_str}.pdf",
            "content": pdf_b64,
            "content_type": "application/pdf"
        }]
    }).encode()

    url = "https://api.agentmail.to/v0/inboxes/davidj@agentmail.to/messages/send"
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

**⚠ AgentMail MCP tools** (`mcp_agentmail_send_message`) also support attachments — prefer those when MCP is available.

**⚠ Delivery to work domains unreliable** — `agentmail.to` may be caught by corporate spam filters. Send to personal Gmail as primary or verify with a plain-text test first.

## Slack Delivery

```python
import json, urllib.request, subprocess

def slack_post(text):
    r = subprocess.run(["grep", "SLACK_BOT_TOKEN", "/root/.hermes/.env"], capture_output=True, text=True)
    token = r.stdout.strip().split("\n")[0].split("=", 1)[1]
    r2 = subprocess.run(["grep", "SLACK_HOME_CHANNEL", "/root/.hermes/.env"], capture_output=True, text=True)
    channel = r2.stdout.strip().split("\n")[0].split("=", 1)[1]
    data = json.dumps({"channel": channel, "text": text, "unfurl_links": False}).encode()
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())
```

## Cron Job

- **Job ID:** `813b03d1a3e1`
- **Schedule:** `0 6 * * *` UTC (= 7am UK BST summer; 6am GMT winter)
- **Script:** `bulletin_fetch_write.sh`
- **Delivery:** `local`
- **Toolsets:** `terminal`, `file`, **skills** (loads this skill)

**⚠ Cron is always UTC.** Adjust schedule at DST transitions.

## Digest Sections (in order)

| Section | Source Table | Table ID | Filter |
|---------|-------------|----------|--------|
| 🌤️ London Weather | `Weather_Data` | 364 | Latest record (today or yesterday) |
| 📋 Short-Term Todos | `Todos` | 362 | Status ≠ Done, Due Date ≤ 7 days from today |
| 💡 Fact of the Day | `Fact_of_the_Day` | 363 | Today's date |
| ⚔️ Star Wars Fact | `Star_Wars_Fact` | 371 | Today's date |
| 📈 Markets | `Stock_Prices` | 365 | Today's date, deduplicated by ticker |
| 📊 Token Usage | `Token_Usage` | 367 | Yesterday's date |
| 🏠 New Property Listings | `Properties` | 380 | Status = New, First Seen ≤ 7 days, top 5 by score |

**Section order is defined in `build_digest_baserow.py` only.** Both email body AND PDF come from the same HTML output (single source of truth).

**⚠ Baserow field access patterns:**
- `single_select` fields return `{"id": N, "value": "..."}` — use `get_select_value()` helper
- Date fields are naive — add `.replace(tzinfo=timezone.utc)` before comparison
- Number fields may return strings — cast to `int()` before `f"{val:,}"` formatting
- Use `baserow_api.py list-rows <table_id> --limit N --json` for machine-readable output

## Pitfalls

1. **No deduplication** — Running `--write` twice creates duplicates. Only run once per day.
2. **execute_code blocked in cron** — Use `write_file` + `terminal` pattern for Python scripts.
3. **Stock data may be from previous day** — yfinance returns most recent trading day's close. Expected on weekends/holidays.
4. **Weather timeouts** — Open-Meteo can timeout on 15s limit. Digest still sends with section skipped.
5. **Baserow select option 422** — Writing undefined choice to singleSelect fails. Use exact option values.
6. **Baserow number field `min_value`** — If Airtable import set `number_negative=False`, negative values fail. Fix via JWT PATCH to `/api/database/fields/{id}/`.
7. **agentmail_helper.py does NOT support attachments** — Use AgentMail REST API directly.
8. **Digest section order** is defined in `build_digest_baserow.py` only.
9. **Baserow date field filtering** — `filter__field_XXXX__equal` returns `ERROR_VIEW_FILTER_TYPE_UNSUPPORTED_FIELD` for date fields. Fetch with `size=N` and filter client-side by inspecting the `field_XXXX` value.
10. **`build_digest_html.py` is Airtable-only legacy** — Located at `scripts/legacy_airtable/build_digest_html.py`. Do NOT use — it reads from the deprecated Airtable. Use `build_digest_baserow.py` instead. The `digest_to_pdf.py` at `scripts/legacy_airtable/digest_to_pdf.py` takes an HTML file path and works regardless of data source.
11. **Baserow API gotchas for digest builder** — `single_select` returns dicts (`{"id": N, "value": "..."}`), date fields are naive (add `.replace(tzinfo=timezone.utc)`), number fields may return strings (cast to `int()` before formatting). Always use `baserow_api.py --json` for machine-readable output.
12. **Properties section requires Status="New"** — The scan script sets this via `baserow_api.py create-row` which resolves select option names to IDs. Direct API calls with string values fail silently.
13. **Star Wars fetcher is in the parallel pipeline** — `starwars_fetch.py` runs as part of `bulletin_fetch_parallel.py` (5 fetchers, ~2s total). If Star Wars disappears from the digest, check: (a) is it in the `FETCHERS` list? (b) does `build_digest_baserow.py` have the Star Wars section? (c) is the `Star_Wars_Fact` table ID correct (371)?
14. **Migrating a legacy Airtable fetcher to Baserow** — Pattern: (1) copy script to `/root/Geeves/scripts/`, (2) replace `AIRTABLE_API_KEY` / base URL with `baserow_api.baserow_post()`, (3) add to `bulletin_fetch_parallel.py` `FETCHERS` list, (4) add section to `build_digest_baserow.py`, (5) update this skill.

## Related Pipelines

- **Weekly Digest + Intentions** — Sunday 8pm UTC cron. Reflective weekly summary + intentions review. Skill: `weekly-digest-agent`. Scripts: `weekly_digest_fetch.py` + `build_weekly_digest_html.py`. Same HTML→PDF→email+Slack pattern.

## Reference

- `references/baserow-migration-pattern.md` — Step-by-step pattern for migrating Airtable fetchers to Baserow, with field access patterns and common pitfalls.
- `/root/Geeves/baserow_mapping.json` — Full Baserow mapping (all 41 tables, generated by baserow_api.py)
- `/root/Geeves/Module_Build_Playbook.md` — Standard module build process
- `baserow` skill → `references/airtable-to-baserow-migration-pattern.md` — Pattern for migrating Airtable scripts to Baserow
