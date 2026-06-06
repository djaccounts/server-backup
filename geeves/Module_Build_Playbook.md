# Module Build Playbook

*How to build a new Geeves module. Follow this process every time for consistency.*

## When to Use This

Every time a new module is being built — whether Phase 1 foundation or Phase 5 intelligence. The playbook ensures the same structure, the same documents, and the same agent/skill setup every time.

## Pre-Build Checklist

Before writing any code or creating any tables:

1. **Check `modules_status.json`** — Is this module already built? In progress? What phase is it in?
2. **Check `schema_registry.json`** — Do the table IDs already exist? What's the current schema status?
3. **Review the Schema Reference** (`Geeves_Schema_Reference_v2.md`) — What are the approved table and field definitions?
4. **Identify dependencies** — Does this module link to existing tables? (e.g., Recipes → People, Meals → Recipes)
5. **Get user approval** — Present the full field list. Wait for "yes" or "go ahead" before creating anything.

## Build Steps (In Order)

### Step 1: Create Airtable Tables

```bash
# Check current schema
python3 /root/Geeves/scripts/table_builder.py --schema

# Create tables (use existing --flag or add a new one)
python3 /root/Geeves/scripts/table_builder.py --<module>
```

- Add a `MODULE_TABLES` dict in `table_builder.py` following the existing pattern
- Add a `create_<module>_tables()` function + CLI flag in `main()`
- **Record all table IDs** in `schema_registry.json` immediately

### Step 2: Create the Skill

Create `/root/.hermes/skills/devops/<module>-agent/SKILL.md` using the [skill template](file:///root/Geeves/templates/module-skill-template.md).

The skill must include:
- **Trigger conditions** — when should this skill be loaded?
- **Table IDs** — from `schema_registry.json`
- **Key fields** — the most important fields (not all 50+ fields)
- **CRUD examples** — how to create/update records
- **Slack capture rules** — if this module receives Slack input
- **Cron jobs** — if this module has scheduled tasks
- **Dependencies** — what other modules/tables does this link to?
- **Pitfalls** — known issues and gotchas

### Step 3: Create Fetcher/Script (if needed)

If the module fetches external data:
- Create `/root/Geeves/scripts/<module>_fetch.py`
- Add to `bulletin_fetch.py` SCRIPTS list if it's a bulletin section
- Add to `build_digest_html.py` if it appears in the digest
- Reference the `public-apis` skill for API details

### Step 4: Add Slack Capture (if needed)

If the module receives Slack input:
- Add a classifier category in `/root/Geeves/scripts/slack_capture.py`
- Add extraction patterns for the data this module needs
- **Check classification priority** — order matters in `CATEGORY_RULES`
- Test with sample messages

### Step 5: Create Cron Jobs (if needed)

If the module has scheduled tasks:
- Create the cron job with `cronjob(action='create')`
- Set `skills` to load the module's skill + `public-apis` if needed
- Set `enabled_toolsets` to the minimum required (usually `terminal`, `file`, `skills`)
- Set `deliver` appropriately (`local` for silent, `origin` for chat delivery)
- Record the job ID in the skill and in `modules_status.json`

### Step 6: Update Documents

After building, update ALL of these:

1. **`schema_registry.json`** — table IDs, field IDs, status
2. **`modules_status.json`** — mark module as built, record skill name, cron job IDs
3. **`Geeves_Schema_Reference_v2.md`** — if schema changed from the original plan
4. **`<module>-agent` skill** — final pass, make sure everything is accurate
5. **`geeves-airtable/SKILL.md`** — add to the module table if it's a purpose-built module
6. **Memory** — add a one-line pointer: "<Module> → <module>-agent skill"

### Step 7: Test End-to-End

- Create a test record in Airtable
- Run any fetcher scripts
- Trigger any Slack capture with a sample message
- Run any cron jobs manually
- Verify the output is correct

## Module Status Tracking

Every module has a status in `modules_status.json`:

| Status | Meaning |
|--------|---------|
| `planned` | In the master plan, not yet started |
| `in_progress` | Currently being built |
| `built` | Tables created, skill written, tested |
| `active` | Running in production, receiving data |
| `paused` | Built but temporarily disabled |

## Skill Template

See `/root/Geeves/templates/module-skill-template.md` for the standard skill structure.

## Cron Job Standards

- **Schedule is always UTC** — adjust for UK time (UTC+0 winter / UTC+1 summer BST)
- **`execute_code` is BLOCKED in cron** — use `write_file` + `terminal` pattern
- **Load minimum skills** — only the module's skill + `public-apis` if needed
- **Set `enabled_toolsets`** — usually `["terminal", "file", "skills"]`
- **Record job ID** in the skill and `modules_status.json`

## Cross-Module Links

When building a module that links to existing tables:

1. Add the link field to the new table (or existing table)
2. Update the cross-module link map in `Geeves_Schema_Reference_v2.md`
3. Update the dependency note in the skill
4. Update `schema_registry.json` with the link field

## Common Pitfalls

1. **Forgetting to update `schema_registry.json`** — always update immediately after creating tables
2. **Missing skill dependencies** — if your module links to People, note it in the skill
3. **Classification priority** — new Slack capture rules must be ordered correctly
4. **Cron timezone** — always UTC, adjust for DST
5. **execute_code in cron** — blocked, use write_file + terminal
6. **Select field 422** — writing undefined choice fails; reuse existing labels or use `typecast=true`
