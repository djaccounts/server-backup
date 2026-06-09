# Geeves Module Build Checklist

The complete checklist for building a new Geeves module. Follow this every time — skip steps and things break.

## Pre-build

1. **Check current state:**
   - Read `modules_status.json` — what phase? what status?
   - Run `table_builder.py --schema` — do tables already exist?
   - Check `schema_registry.json` for existing table/field IDs
   - **Tables may exist without a skill** — don't recreate them

2. **Get user approval:**
   - Present full field list (name, type, options) for every table
   - Wait for explicit "yes" or "go ahead"
   - This is David's standing rule — no exceptions

## Build order

3. **Tables** (only if they don't exist):
   - Add `MODULE_TABLES` dict to `table_builder.py`
   - Add `create_<module>_tables()` function
   - Add CLI flag in `main()`
   - Run and verify with `--schema`

4. **Skill:**
   - Create `/root/.hermes/skills/devops/<module>-agent/SKILL.md`
   - Follow the pattern from existing skills (meals-agent, sleep-agent)
   - Include: Tables, Key Fields, CRUD examples, Workflows, Slack Capture, Dependencies, Pitfalls

5. **Slack capture:**
   - Add table IDs to `TABLES` dict in `slack_capture.py`
   - Add category to `CATEGORY_RULES` (check for keyword overlap with ALL existing categories!)
   - Add handler function
   - Register in `HANDLERS` dict
   - **Test classification priority** — run dry-run with messages that could overlap

6. **Cross-references:**
   - Update `geeves-airtable` SKILL.md: Core Tables, Purpose-Built Modules table, table IDs
   - Update `table_builder.py` CLI flags list
   - Update `modules_status.json`: status → "active", add skill name, update notes
   - Update `schema_registry.json`: `last_synced` timestamp
   - Update `Geeves/AGENTS.md`: Active Modules table

7. **Test:**
   - Create a test record via `airtable_api.py`
   - Delete the test record
   - Run `slack_capture.py --dry-run` with sample messages
   - Verify classification is correct for edge cases (overlapping keywords)

## Post-build

8. **Update memory** — one line: `"<Module> → <module>-agent skill"`
9. **Update planning protocol checklist** if the build revealed a missing step

## Common pitfalls

- **Patch tool orphans entries:** When patching `CATEGORY_RULES` or `elif` chains, include surrounding context (previous + next entry) to make the match unique
- **Tables already exist:** Always run `--schema` first. The fitness module's tables existed for days before the skill was written
- **Classification overlap:** New categories must be positioned before more general ones. Check ALL existing categories for keyword overlap
- **Select field 422s:** Writing undefined select options fails. Use exact values from the schema
- **Linked record format:** Links must be arrays: `["recXXXXXX"]`, not plain strings
