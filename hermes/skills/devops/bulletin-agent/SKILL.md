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
  → bulletin_fetch.py --write    (fetch all data → Airtable)
  → build_digest_html.py --save  (read Airtable → HTML)
  → digest_to_pdf.py             (HTML → PDF via PDFBolt)
  → AgentMail API                (HTML body + PDF attachment → dj@djaccounts.com)
  → Slack API                    (summary post → SLACK_HOME_CHANNEL)
```

**Single source of truth:** `build_digest_html.py` is the ONLY source for digest content. Both email body AND PDF come from the same HTML output. Never compose a separate plain text email.

## Scripts (in order)

| Step | Script | Output |
|------|--------|--------|
| 1. Fetch data | `bulletin_fetch.py --write` | Writes to Airtable tables |
| 2. Build HTML | `build_digest_html.py --save` | `/root/Geeves/digests/digest_YYYY-MM-DD.html` |
| 3. Generate PDF | `digest_to_pdf.py --file <html>` | `/root/Geeves/digests/digest_YYYY-MM-DD.pdf` |
| 4. Send email | AgentMail API (see below) | To `dj@djaccounts.com` |
| 5. Post to Slack | `chat.postMessage` API | To `SLACK_HOME_CHANNEL` |

## Data Sources

All scripts are in `/root/Geeves/scripts/`.

| Fetcher | Table | API | Key |
|---------|-------|-----|-----|
| `weather_fetch.py` | `Weather_Data` (tblFd4kAahIUozJsf) | Open-Meteo | None |
| `stocks_fetch.py` | `Stock_Prices` (tblI1oXlNIFXrVm7f) | yfinance | None |
| `fact_fetch.py` | `Fact_of_the_Day` (tblUTCWleQD61Ti2v) | 6 rotating sources | None |
| `starwars_fetch.py` | `Star_Wars_Fact` (tblAvJ4PG6HbAXruj) | SWAPI.tech | None |
| `token_usage.py` | `Token_Usage` (tbl3EjtE3YW1ZUqEv) | Hermes state.db | None |

**Fact rotation:** `day_of_year % 6` → 0=Wikipedia, 1=NASA, 2=Quote Garden, 3=Zen, 4=Holidays, 5=Useless Facts. Full fallback chain if primary fails.

**Stock tickers:** `BTC-GBP`, `AMZN`, `GOOGL`, `META`

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

**⚠ Cron is always UTC.** Adjust schedule at DST transitions (late Oct → `0 7 * * *` for 7am GMT).

## Adding a New Section

1. Write a fetcher script in `/root/Geeves/scripts/` that writes to an Airtable table
2. Add it to `bulletin_fetch.py` `SCRIPTS` list
3. Add a section block to `build_digest_html.py`
4. Both email and PDF update automatically (single source of truth)

## Pitfalls

1. **No deduplication** — Running `--write` twice creates duplicates. Only run once per day.
2. **execute_code blocked in cron** — Use `write_file` + `terminal` pattern for Python scripts.
3. **Stock data may be from previous day** — yfinance returns most recent trading day's close. Expected on weekends/holidays.
4. **Weather timeouts** — Open-Meteo can timeout on 15s limit. Digest still sends with section skipped.
5. **Select field 422** — Writing undefined choice to singleSelect fails. Reuse existing labels.
6. **agentmail_helper.py does NOT support attachments** — Use AgentMail REST API directly.
7. **Digest section order** is defined in `build_digest_html.py` only. Current order: Weather → Star Wars → Fact → Markets → Token Usage.

## Reference

- `public-apis` skill — API details, rate limits, auth patterns
- `geeves-airtable/references/bulletin-setup.md` — full setup docs, field mappings, table IDs
- `/root/Geeves/Module_Build_Playbook.md` — standard module build process (for extending bulletin with new sections)
