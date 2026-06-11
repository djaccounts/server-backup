# Relationships & Occasions Module — Design Notes

## Status: ✅ Built (June 2026)

Phase 3 module. Tracks birthdays, anniversaries, social occasions, gift ideas, and gift history. Links to People graph.

## Baserow Table IDs

| Table | ID | Fields |
|-------|-----|--------|
| Occasions | 403 | Person (link→359), Occasion Type (single_select), Date, Recurring (boolean), Remind Days Before (number), Extra Notes (long_text), Created |
| Gift Ideas | 404 | Person (link→359), Idea (long_text), Estimated Cost (single_select), Occasion (text), Status (single_select), Extra Notes (long_text), Created |
| Gift History | 405 | Person (link→359), Gift (long_text), Occasion (text), Date Given, Rating (single_select 1-5), Extra Notes (long_text), Created |
| Social Log | 406 | Date, Type (single_select), Person (link→359), Summary (long_text), Key Things to Remember (long_text), Follow-up (long_text), Source (single_select), Created |

**Note:** "Extra Notes" naming because Baserow auto-creates a "Notes" field on new tables via Platform API.

## Decisions

- **Social Log merges Conversation Log** — Conversation Log table (369) deprecated, data migration optional
- **Gift Ideas → Occasions link is free text** (not a link field) — simpler, no circular dependency
- **Remind days before is per-person** on Occasions table (number field)
- **Calendar integration** — future: auto-match Google Calendar events to Social Log records
- **Junk fields deleted from People:** Films (field_3318) and Books text (field_3336) removed via JWT

## Cross-Module Links
- People → Occasions (birthdays/anniversaries enrich person records)
- People → Gift Ideas (feeds future unified shopping list in Phase 5)
- Recipes → Social Log (dinner parties → recipes cooked)
- Restaurants → Social Log (restaurant meals → social occasions)
- Calendar → Social Log (future: auto-match calendar events)

## Slack Capture
- "It's Sam's birthday on the 15th" → Occasions
- "Sam would love a new cookbook" → Gift Ideas
- "Gave Sam the cookbook, she loved it" → Gift History
- "Had dinner with Sam and Jane" → Social Log

## Build Checklist
- [x] Create Occasions table in Baserow (id=403)
- [x] Create Gift Ideas table in Baserow (id=404)
- [x] Create Gift History table in Baserow (id=405)
- [x] Create Social Log table in Baserow (id=406)
- [x] Update baserow_mapping.json
- [x] Write relationships-agent skill
- [x] Update Schema Reference
- [x] Update Master Plan
- [x] Update AGENTS.md
- [x] Update modules_status.json
- [x] Add Slack capture for occasions/gifts/social
- [ ] Migrate Conversation Log data → Social Log (optional, low priority)
- [ ] Morning digest: surface upcoming occasions
