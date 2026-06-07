---
name: todos-agent
description: "Geeves Todos Agent — manage tasks in the Airtable Todos table. Use when adding, completing, listing, or updating todos, or when the user mentions tasks, to-dos, things to do, reminders, or action items."
version: 1.2.0
author: Geeves
---

# Todos Agent

Manages the `Todos` table — tasks across short, medium, and long time horizons. Handles Airtable CRUD, Slack capture, and listing/filtering.

## Table

| Table | ID | Purpose |
|-------|----|---------|
| `Todos` | `tblTcdZQ9AIltQDfu` | All tasks — personal, work, household, health, errands |

## Key Fields

| Field | Type | Purpose |
|-------|------|---------|
| `Task` | single line text | What needs doing (primary field) |
| `Status` | single select | Not started / In Progress / Done |
| `Priority` | single select | Low / Medium / High |
| `Timeframe` | single select | Short term / Mid term / Long term |
| `Category` | single select | Personal / Work / Household / Health / Errand / Other |
| `Due Date` | date | When it's due (optional) |
| `Completed Date` | date | When it was completed |
| `Notes` | long text | Additional details |
| `Source` | single select | Manual / Slack / Voice / Goal auto-gen |
| `Module` | single line text | Which module this belongs to |

## Status Options

**Must use exact values** — Airtable select fields are case-sensitive:
- `"Not started"` — default for new tasks
- `"In Progress"` — actively being worked on
- `"Done"` — completed

**⚠ Do NOT use `"Todo"`** — it's not a valid option and will cause a 422 error.

## Airtable CRUD

Use `/root/Geeves/scripts/airtable_api.py`:

```bash
# Create a todo
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "Todos" \
  '{"Task": "Fix the gutter", "Status": "Not started", "Priority": "Medium", "Timeframe": "Short term", "Category": "Household", "Source": "Slack"}'

# Update a todo (e.g., mark in progress)
python3 /root/Geeves/scripts/airtable_api.py update-record appzvmonQXs4x2AlL "Todos" "<record_id>" \
  '{"Status": "In Progress"}'

# Mark done
python3 /root/Geeves/scripts/airtable_api.py update-record appzvmonQXs4x2AlL "Todos" "<record_id>" \
  '{"Status": "Done", "Completed Date": "2026-06-06"}'

# List all todos
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "Todos"

# List only not-done todos
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "Todos" "filterByFormula=NOT({Status}='Done')"
```

**Auth:** Read `AIRTABLE_API_KEY` from `/root/.hermes/.env` via grep (never from `os.environ`).

## Workflows

### Adding a Todo

1. Extract the task description from the user's message
2. **Ask for categorisation feedback** — before creating the record, ask the user to confirm or provide:
   - **Priority:** Low / Medium / High (default: Medium if not specified)
   - **Timeframe:** Short term / Mid term / Long term (default: Short term if not specified)
   - **Category:** Personal / Work / Household / Health / Errand / Other (default: Personal if not specified)
   - **Due date:** Ask "When does this need to be done?" — accept natural language ("tomorrow", "next week", "by Friday", "no rush")
   - **Notes:** Ask "Any extra details?" — e.g. links, people involved, sub-steps
3. If the user provides multiple tasks at once, ask the questions once and apply sensible defaults to each (they can differ)
4. If the user says "just add it" or "you decide", skip the questions and use defaults
5. Create the record with `Status: "Not started"` and `Source: "Slack"`
6. Confirm back to the user with the task name and the details that were set

**Priority heuristics (when not explicitly asked):**
- "urgent", "asap", "important" → High
- "when you can", "someday", "eventually" → Low
- Default → Medium

**Timeframe heuristics (when not explicitly asked):**
- "today", "tomorrow", "this week" → Short term
- "this month", "soon" → Mid term
- "someday", "eventually", "one day" → Long term

**Category heuristics (when not explicitly asked):**
- "work", "office", "job" → Work
- "home", "house", "garden", "gutter", "fix", "kindle", "netflix", "firestick", "tech" → Household
- "doctor", "dentist", "gym", "health" → Health
- "buy", "shop", "pick up", "get" → Errand
- Default → Personal

### Completing a Todo

1. Find the matching record (search by task name)
2. Update `Status` to `"Done"` and set `Completed Date` to today
3. Confirm completion to the user

### Listing Todos

1. Fetch records from Airtable
2. Filter out done tasks unless user asks for all
3. Group by status or priority
4. Format as a readable list with record IDs (for reference)

### Updating a Todo

1. Find the matching record
2. Update only the fields that changed
3. Confirm the update

## Slack Capture

Script: `/root/Geeves/scripts/slack_capture.py`

**Trigger keywords:** "todo", "task", "remind", "don't forget", "need to", "should", "have to", "must", "action", "follow up", "follow-up"

**Classification priority:** Todo appears BEFORE Person Note, Memory, Recipe, and Module Request in `CATEGORY_RULES`.

### Extraction Patterns

**Task text:**
- Strip leading "todo:", "task:", "remind me:", "don't forget:", "follow up:" prefixes
- Remaining text = the task

**Due date:**
- "today" → today's date
- "tomorrow" → tomorrow's date
- "by <date>" → extract date
- "next week" → 7 days from now
- DD/MM/YYYY or DD-MM-YYYY formats

**Priority (from context):**
- "urgent", "asap", "important", "critical" → High
- "low priority", "when you can", "someday" → Low
- Default → Medium

**Category (from context):**
- "work", "office", "job" → Work
- "home", "house", "garden", "gutter", "fix" → Household
- "doctor", "dentist", "gym", "health" → Health
- "buy", "shop", "pick up", "get" → Errand
- Default → Personal

## Cron Jobs

None yet. Future: evening digest reads from Todos (planned, not built).

## Dependencies

- **Output_Log** — Todo queries can log to Output_Log with Module="Todos"
- **People** — Tasks can reference a person via `Linked Person` field (free text, not a link yet)
- **Goals** (Phase 3) — Tasks may link to goals when Goals module is built

## Integration Points

- **Evening Digest** (planned) — reads open todos for the evening briefing
- **Morning Digest** (planned) — could include high-priority todos
- **Goals module** (Phase 3) — tasks may be auto-generated from goals

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Get David's explicit approval before creating any Airtable table
- Thread decisions supersede reference docs
- Update this skill when conversation changes a decision
- **Never use `"Todo"` as a Status value** — always `"Not started"`, `"In Progress"`, or `"Done"`

## Pitfalls

1. **Status value mismatch:** The old `handle_todo` in slack_capture.py used `"Status": "Todo"` which is NOT a valid select option. The correct default is `"Not started"`. Fixed in v1.0.0 of this skill.
2. **filterByFormula on select fields:** Airtable's formula engine can filter by select values, but the comparison is case-sensitive. Use exact values: `{Status}='Not started'`.
3. **Date format:** Always use `YYYY-MM-DD` format for Airtable date fields.
4. **Select field 422 errors:** Writing an undefined select option fails with 422. Always use the exact choice values listed in the Key Fields table.
5. **Linked Person is text, not a link:** The `Linked Person` field is currently `singleLineText`, not a `multipleRecordLinks` field. Don't try to link it to the People table — it's just a name string.
6. **slack_capture.py handler is basic:** The `handle_todo` function in `slack_capture.py` only sets Priority=Medium and doesn't extract category/priority/due date from message text. When adding todos via the skill (not slack_capture), use the full feedback protocol and heuristics. The slack_capture path is a fallback — the skill path is the primary interface.

## Reference

- `geeves-airtable/SKILL.md` — Airtable CRUD patterns
- `Geeves_Schema_Reference_v2.md` — full field definitions (Module 5 — To-Do List)
- `geeves-airtable/references/slack-capture.md` — classification rules, extraction patterns
