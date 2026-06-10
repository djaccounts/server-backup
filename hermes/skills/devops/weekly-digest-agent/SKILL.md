---
name: weekly-digest-agent
description: "Geeves Weekly Digest + Intentions Agent — fetch weekly data, build reflective HTML digest, prompt for intentions, and deliver via email + Slack. Runs as a cron job on Sundays at 8pm UTC. Use this skill when maintaining, debugging, or extending the weekly digest pipeline."
version: 1.0.0
author: Geeves
---

# Weekly Digest + Intentions Agent

Fetches the past 7 days of data from across Geeves modules, composes a reflective weekly summary, reviews last week's intentions, suggests new ones, and delivers via email + Slack. Runs every Sunday at 8pm UTC (9pm BST summer / 8pm GMT winter).

## Architecture

```\nCron (Sunday 8pm UTC)\n  → weekly_digest_fetch.py       (fetch week's data → Baserow)\n  → build_weekly_digest_html.py  (read Baserow → HTML)  [⚠️ still reads Airtable, migration pending]\n  → digest_to_pdf.py             (HTML → PDF via PDFBolt)\n  → AgentMail API                (HTML body + PDF attachment → dj@djaccounts.com)\n  → Slack API                    (summary post → SLACK_HOME_CHANNEL)\n```\n\n**Single source of truth:** `build_weekly_digest_html.py` is the ONLY source for digest content. Both email body AND PDF come from the same HTML output.\n\n**⚠️ Migration status (June 2026):** `weekly_digest_fetch.py` still reads from Airtable. `build_weekly_digest_html.py` still reads from Airtable. Migration pending.

## Table(s)

| Table | Baserow ID | Purpose |
|-------|-----------|---------|
| `Intentions` | 397 | Weekly intentions — set, track, reflect |
| `Digest Log` | 390 | Digest email log (Type = Weekly) |

**All data is in Baserow** (migrated from Airtable June 2026). Use `baserow_api.py` for all CRUD operations.

## Key Fields

### Intentions

| Field | Type | Purpose |
|-------|------|---------|
| Intention | singleLineText | What you intend to do/focus on |
| Week starting | date | The Monday of the week |
| Type | singleSelect | Accomplish / Let go of / Focus |
| Status | singleSelect | Set / Achieved / Missed / Carried over |
| Source | singleSelect | Suggested / Manual |
| Reflection | multilineText | End-of-week reflection |

## Data Sources

The weekly digest pulls from all active Phase 2+ modules:

| Module | Tables | What's summarised |
|--------|--------|-------------------|
| Todos | `Todos` | Tasks completed, created, still pending |
| Fitness | `Workouts`, `Exercise Log`, `Cycling` | Workouts logged, distance, types |
| Sleep | `Sleep Log` | Average sleep hours, quality trend |
| Habits | `Habits`, `Habit Log` | Habit completion rates |
| Meals | `Meals` | Meals logged, nutrition summary |
| Intentions | `Intentions` | Last week's intentions: achieved/missed |

## Baserow CRUD

Use `/root/Geeves/scripts/baserow_api.py` for all operations:

```bash
# Create intention
python3 /root/Geeves/scripts/baserow_api.py create-row Intentions \
  '{"Intention": "Go to the gym 3x", "Week starting": "2026-06-09", "Type": "Accomplish", "Status": "Set", "Source": "Suggested"}'

# List intentions
python3 /root/Geeves/scripts/baserow_api.py list-rows Intentions

# Update intention
python3 /root/Geeves/scripts/baserow_api.py update-row Intentions <row_id> \
  '{"Status": "Achieved", "Reflection": "Made it to the gym 3 times!"}'
```

## Workflows

### Weekly Digest (Cron)

1. Run `weekly_digest_fetch.py --write` to collect the past 7 days of data
2. Run `build_weekly_digest_html.py --save` to compose the HTML digest
3. Run `digest_to_pdf.py --file <html>` to generate PDF
4. Send via AgentMail with PDF attachment
5. Post summary to Slack

### Setting Intentions

Intentions can be:
- **Suggested** by Hermes (based on patterns in the data)
- **Manual** (David sets them in Slack or Airtable directly)

To set via Slack, David says something like:
> "This week I want to focus on sleeping earlier"

This creates an `Intentions` record with `Source: Manual`.

### Reviewing Intentions

At the end of each week (Sunday cron), the digest:
1. Shows last week's intentions with their status
2. Lets David update status (Achieved / Missed / Carried over)
3. Suggests new intentions for the coming week

## Slack Capture

**Script:** `/root/Geeves/scripts/slack_capture.py`

**Trigger keywords:** "intention", "this week I want", "focus on", "goal for the week"

**Classification priority:** After Todo, before General.

### Extraction Patterns

- **Intention text:** "I want to X", "focus on X", "goal: X", "intention: X"
- **Week:** Defaults to next Monday if not specified
- **Type:** Inferred from context — "stop X" → Let go of, "start X" → Accomplish, "focus on X" → Focus

## Cron Jobs

| Job ID | Schedule | What it does |
|--------|----------|--------------|
| `b0b836135650` | `0 20 * * 0` (Sunday 8pm UTC) | Fetch → HTML → PDF → email + Slack |

**⚠ Cron is always UTC.** 8pm UTC = 9pm BST (summer) / 8pm GMT (winter).
**⚠ `execute_code` is BLOCKED in cron.** Use `write_file` + `terminal` pattern.

## Dependencies

This module depends on data from other modules. The more modules that are active, the richer the weekly digest. Minimum viable: Todos + Intentions.

- **Todos** → Tasks completed/created this week
- **Fitness** → Workouts logged
- **Sleep** → Sleep quality trend
- **Habits** → Habit completion rates
- **Meals** → Nutrition summary
- **People** → Social interactions (future)

## Integration Points

- **Morning Digest:** Weekly digest complements the daily morning digest. Morning = forward-looking, Weekly = reflective.
- **Intentions → Todos:** An intention can spawn multiple todos.
- **Cross-module patterns:** The weekly digest can surface correlations (e.g., "You slept better on days you worked out").

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/baserow_mapping.json`
- Get David's explicit approval before creating any Baserow table
- Thread decisions supersede reference docs
- Update this skill when conversation changes a decision

## Pitfalls

1. **No deduplication** — Running `--write` twice creates duplicates. Only run once per week.
2. **execute_code blocked in cron** — Use `write_file` + `terminal` pattern for Python scripts.
3. **Empty data** — If a module has no data for the week, skip that section gracefully.
4. **Select field 422** — Writing undefined choice to singleSelect fails. Reuse existing labels.
5. **Digest Log Type** — Must use "Weekly" (not "Morning") when writing to Digest Log.

## Reference

- `bulletin-agent` skill — morning digest pipeline (similar pattern)
- `geeves-airtable/references/bulletin-setup.md` — full setup docs
- `/root/Geeves/Module_Build_Playbook.md` — standard module build process
