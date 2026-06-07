Airtable: Geeves base (appzvmonQXs4x2AlL) only. NEVER touch Practice Management. Schema changes via geeves-steward skill. Registry: schema_registry.json. Schema Ref v2 + module status + planning protocol at /root/Geeves/. NOTE: Module_Build_Playbook.md does NOT exist on disk.
§
Restaurant Module (Phase 4): Restaurants (tblvpSxjeoCQvjotM) + Restaurant Visits (tblf2k6uAHLW7mA4b). Skill: restaurants-agent (devops/restaurants-agent). SerpApi Google Maps lookup. Google search links for Maps URLs. Links to People + Dining Preferences. Wife has separate Rating + Notes. Slack capture active.
§
Bulletin: Digest to dj@djaccounts.com via AgentMail + PDF (PDFBolt). Single source of truth: build_digest_html.py — same HTML for email body AND PDF. Skill: bulletin-agent (devops/bulletin-agent). Cron job ID: 813b03d1a3e1 (6am UTC daily).
§
Film Club = Films table (tblqCpp3EB7wU2ZZ3). 3 club members + wife (Member 4) rate films 1-10. IMDb/OMDb lookup in Slack capture. Skill: film-club-agent (devops/film-club-agent). Legacy tables FilmClub_Data/FilmClub_Log — delete in UI. Title ambiguity: "Matrix" → 1993 TV film, not 1999 — use year or IMDb ID.
§
David's prefs: no raw log tables, no cron for chat, modules on-demand, simple consolidated designs. Explicit approval before any schema change. Wife rates films.
§
Todos: skill built v1.1.0 at devops/todos-agent, table tblTcdZQ9AIltQDfu. When adding: ask priority, timeframe, category, due date. User can say "just add it" to skip.
§
Airtable API tips: filterByFormula fails on multipleRecordLinks (filter locally). Mealie POST /api/recipes only works with URL scraping. Planning protocol: update all 7 steward files after each session (see PLANNING_PROTOCOL.md).