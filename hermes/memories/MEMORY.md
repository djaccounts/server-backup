Airtable: Geeves base (appzvmonQXs4x2AlL) only. NEVER touch Practice Management. Schema changes via geeves-steward skill — thread decisions supersede docs. Registry: schema_registry.json. Build new modules: Module_Build_Playbook.md + modules_status.json.
§
Public APIs ref: public-apis skill (devops/public-apis) — all API docs consolidated there.
§
Bulletin: Digest to dj@djaccounts.com via AgentMail + PDF (PDFBolt). Single source of truth: build_digest_html.py — same HTML for email body AND PDF. Skill: bulletin-agent (devops/bulletin-agent). Cron job ID: 813b03d1a3e1 (6am UTC daily).
§
Film Club = Films table (tblqCpp3EB7wU2ZZ3). 3 club members + wife (Member 4) rate films 1-10. IMDb/OMDb lookup in Slack capture. Skill: film-club-agent (devops/film-club-agent). Legacy tables FilmClub_Data/FilmClub_Log — delete in UI. Title ambiguity: "Matrix" → 1993 TV film, not 1999 — use year or IMDb ID.
§
David's prefs: no raw log tables, no cron for chat, modules on-demand, simple consolidated designs. Explicit approval before any schema change. Wife rates films.
§
GarminDB: installed at /root/GarminDB with venv. Ready for health/fitness module.
§
Mealie: /opt/mealie, port 9925. Login changeme@example.com/MyPassword123. Skill: recipes-agent (devops/recipes-agent). Also mealie skill (productivity/mealie) for Docker/auth.
§
Skill architecture: memory holds pointers (not details), skills hold procedures, reference docs hold data. Build new modules via Module_Build_Playbook.md. Skill template at templates/module-skill-template.md. Status in modules_status.json.
§
Airtable API tips: filterByFormula fails on multipleRecordLinks (filter locally). Mealie POST /api/recipes only works with URL scraping. Planning protocol: update all 7 steward files after each session (see PLANNING_PROTOCOL.md).
§
Slack: 1 input channel (#hermes). Deleted module-specific channels (#food, #health, #workautomation, #geeves). Keep #private-agent. User wants single channel long-term (Telegram/WhatsApp possible).