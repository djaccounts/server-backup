# Slack Capture — Reference

## Architecture

```
Slack message → Hermes classifies in real-time → writes to correct Airtable table
```

**No cron job.** Capture is real-time — David messages in Slack, Hermes reads it, classifies it, and writes to Airtable immediately. A cron loop was initially built but David rejected it as unnecessary complexity — Hermes is already listening, so a 30-minute polling loop adds latency with no benefit.

**No raw message table.** One message → one useful Airtable record. General messages produce no record. David explicitly rejected an intermediate Slack_Capture/Input Log table as unnecessary bloat.

## Classification Rules (Keyword-Based)

Messages are scored against keyword lists per category. Highest score wins. Ties go to whichever category appears **first** in `CATEGORY_RULES`. No matches → "General" (skipped).

| Category | Example Keywords | Target Table(s) |
|----------|-----------------|-----------------|
| Person Note | met, person, friend, contact, dietary, allerg, birthday, interests, hobbies, gift, social, venue | People |
| Todo | todo, task, remind, don't forget, need to, should, must, follow up, action | Todos |
| Memory | remember, note, log, history, last time, previously, before | Memory_Summaries |
| Module Request | dinner, party, travel, holiday, property, movie, film, recommend, suggest | Output_Log |

## Name Extraction Algorithm

1. **Normalize contractions**: `she's` → `she is`, `he've` → `he have`, etc.
2. **Run patterns** (first match wins): "met X", "about/add X", "X's birthday", "X is/loves", "X birthday", "new person: X"
3. **Post-validate**: Skip-word list (pronouns, common verbs, "David", "Geeves")
4. **Multi-word cleanup**: If second word lowercase, take only first word

## Category Handlers

### Person Note
- Extract name → search People table → append to Conversation Log or create new (Tier 4)
- No name found → store in Memory_Summaries

### Todo
- Strip prefixes, extract date → create Todos record (Status="Not started", Priority=Medium)

### Memory
- Create Memory_Summaries record (Period="Ad-hoc")

### Module Request
- Create Output_Log record (Module="General")

## Key Pitfalls

1. **re.IGNORECASE breaks [A-Z] capture**: Post-validate names — if captured text contains lowercase words, truncate
2. **Contractions must normalize BEFORE matching**: "she's" → "she is" etc.
3. **No cron, no batch** — process each message as it arrives in conversation
4. **No Slack_Capture table** — don't create or write to one

## Script Location

`/root/Geeves/scripts/slack_capture.py` — can also be run standalone for testing:

```bash
echo '[{"text":"met Sarah","sender":"David","sender_id":"U0B73K4QWP5","ts":"2026-06-03T12:00:00"}]' | python3 slack_capture.py --stdin --dry-run
```

## Reading API Keys in Python

```python
r = subprocess.run(["grep", "AIRTABLE_API_KEY", "/root/.hermes/.env"], capture_output=True, text=True)
key = r.stdout.strip().split("\n")[0].split("=", 1)[1]
```

Never use `os.environ.get()` — keys live in Hermes `.env`, not the shell environment.
