---
name: <module>-agent
description: "Geeves <Module> Agent — <one-line description>. Use when <trigger conditions>."
version: 1.0.0
author: Geeves
---

# <Module> Agent

<2-3 sentence overview of what this module does and how it fits into Geeves.>

## Table(s)

| Table | ID | Purpose |
|-------|----|---------|
| `<Table>` | `<tblXXXXXXXXXXXX>` | <What it stores> |

<If multiple tables, list all. Get IDs from `/root/Geeves/schema_registry.json`.>

## Key Fields

<List only the most important fields — the ones the agent actually uses. Don't list all 50+ fields.>

| Field | Type | Purpose |
|-------|------|---------|
| `<Field>` | `<type>` | <What it's for> |

## Airtable CRUD

Use `/root/Geeves/scripts/airtable_api.py`:

```bash
# Create record (adapt field names to actual schema)
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "<Table>" \
  '{"<Field>": "<value>"}'

# Update record
python3 /root/Geeves/scripts/airtable_api.py update-record appzvmonQXs4x2AlL "<Table>" "<record_id>" \
  '{"<Field>": "<value>"}'

# List records
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "<Table>"
```

**Auth:** Read `AIRTABLE_API_KEY` from `/root/.hermes/.env` via grep (never from `os.environ`).

## Workflows

### <Workflow Name>
<Numbered steps for the main workflow. Include exact commands.>

1. Step one
2. Step two
3. Step three

### <Another Workflow>
<...>

## Slack Capture

<If this module receives Slack input. Delete this section if not applicable.>

**Script:** `/root/Geeves/scripts/slack_capture.py`

**Trigger keywords:** "<keyword1>", "<keyword2>", "<keyword3>"

**Classification priority:** <Where this should appear in CATEGORY_RULES relative to other modules.>

### Extraction Patterns

<How to extract data from Slack messages.>

- **<Data point>:** <Pattern/extraction rule>
- **<Data point>:** <Pattern/extraction rule>

## Cron Jobs

<If this module has scheduled tasks. Delete this section if not applicable.>

| Job ID | Schedule | What it does |
|--------|----------|--------------|
| `<job_id>` | `<cron expr>` | <Description> |

**⚠ Cron is always UTC.** Adjust for UK time (UTC+0 winter / UTC+1 summer BST).
**⚠ `execute_code` is BLOCKED in cron.** Use `write_file` + `terminal` pattern.

## Dependencies

<What other modules/tables does this module link to?>

- **People** → `<Table>` (for <reason>)
- **<Other module>** → `<Table>` (for <reason>)

<Get the dependency right — it affects what other skills need to be loaded.>

## Integration Points

<How this module connects to other modules.>

- <Integration point 1>
- <Integration point 2>

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Get David's explicit approval before creating any Airtable table
- Thread decisions supersede reference docs
- Update this skill when conversation changes a decision

## Pitfalls

<Pick 5-10 known issues. Number them.>

1. **<Pitfall name>:** <Description and workaround>
2. **<Pitfall name>:** <Description and workaround>

## Reference

- `public-apis` skill — <if this module uses external APIs>
- `geeves-airtable/references/<module>.md` — <if a detailed reference doc exists>
- `Geeves_Schema_Reference_v2.md` — full field definitions
