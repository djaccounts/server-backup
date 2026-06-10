# Quick Capture Module — Design Note

**Status:** Planned — awaiting Baserow transfer
**Proposed by:** David, June 2026
**Phase:** Post-Baserow migration

## Purpose

A lightweight "things to pick up / ideas" list — non-urgent items that are adjacent to the Todo list but not urgent enough for it. Gift ideas, household needs, things to buy, remember, or investigate later.

## Schema

**Table name:** Quick Capture

| Field | Type | Notes |
|-------|------|-------|
| Item | singleLineText | The thing you want/buy/remember |
| Category | singleSelect | `Gift`, `Household`, `DIY`, `Tech`, `Clothing`, `Other` |
| For | multipleRecordLinks → People | Who it's for (optional — links to People graph) |
| Priority | singleSelect | `Low`, `Medium`, `High` |
| Est. Cost | singleLineText | Rough cost (free text — "£20-30", "free", etc.) |
| Notes | multilineText | Where you saw it, links, ideas, etc. |
| Purchased | checkbox | Tick when bought/done |
| Source | singleLineText | Where the idea came from (optional) |

## Classification Keywords (for Slack capture)

Trigger words: `want`, `gift`, `buy`, `pick up`, `look into`, `idea for`, `should get`, `need to get`, `wish list`, `NB`, `note to self`, `remember to`

## Notes

- Inspired by David's comment that these items feel adjacent to Todos but are "non-urgish"
- Links to People graph for gift ideas (`For` field)
- `Purchased` checkbox — tick when done, no need to delete
- To be implemented in Baserow (not Airtable) once migration is complete
- May warrant its own skill (`quick-capture-agent`) if workflows develop

## TODO (when implementing)

- [ ] Create table in Baserow
- [ ] Add to schema_registry (Baserow equivalent)
- [ ] Add Slack capture classification rules in `slack_capture.py`
- [ ] Update `modules_status.json`
- [ ] Update `Geeves/AGENTS.md` active modules table
