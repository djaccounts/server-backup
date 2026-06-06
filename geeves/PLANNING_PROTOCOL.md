# Geeves Planning Change Protocol

**This file is the standing protocol for ALL planning changes.**
Every time a module is planned or a schema decision is made, the following
checklist MUST be completed before the build is considered planned.

## Checklist — run after EVERY planning session

### 1. Schema Reference
- [ ] Update `/root/Geeves/Geeves_Schema_Reference_v2.md`
  - Module section reflects the final agreed schema
  - All field names, types, and select options match exactly
  - Link fields are noted with `→ [Table]` syntax

### 2. Master Plan
- [ ] Update `/root/Geeves/Geeves_Master_Plan_v2.md`
  - Module description updated if the plan changed
  - Cross-module links noted

### 3. Recipe Module Plan (if recipe-related)
- [ ] Update `/root/Geeves/Recipe_Module_Plan.md`
  - Keep detailed field-level decisions here

### 4. Schema Registry
- [ ] Update `/root/Geeves/schema_registry.json`
  - Add new tables with placeholder IDs (filled in after creation)
  - Add new fields with their Airtable IDs (filled in after creation)
  - Update `last_synced` timestamp
  - Field statuses: active / system / junk / deprecated

### 5. Steward Skill
- [ ] Update `/root/.hermes/skills/geeves/geeves-steward/SKILL.md`
  - Add module to Module Build Order if new
  - Add table IDs to the safety/reference section

### 6. Airtable Skill
- [ ] Update `/root/.hermes/skills/devops/geeves-airtable/SKILL.md`
  - Add new tables to existing tables list with IDs
  - Add CLI flags if table_builder.py updated
  - Add new purpose-built module entry if applicable

### 7. Slack Capture
- [ ] Update `/root/Geeves/scripts/slack_capture.py`
  - Add new classifier category if new module type
  - Update TABLES dict with new table IDs

### 8. Table Builder
- [ ] Update `/root/Geeves/scripts/table_builder.py`
  - Add new TABLES dict for the module
  - Add create function
  - Add CLI flag in main()

## Source of Truth Hierarchy
1. This conversation thread → ground truth for decisions
2. Schema Reference v2 → canonical field definitions
3. Schema Registry JSON → what actually exists in Airtable right now
4. Skill files → operational reference for Hermes

## Thread Decisions Supersede Reference Docs
When a conversation changes a schema decision, the conversation wins.
Update ALL downstream documents to match.
