Baserow is the system of record (replaced Airtable June 2026). http://77.68.33.121, DB ID 132, 41 tables. API: BASEROW_API_TOKEN in .env, use baserow_api.py helper. Pitfalls: field_XXXX IDs for writes, number_negative=False fix via JWT PATCH, DB token can't list tables, 204 on DELETE = success.
§
Bulletin: 6am UTC daily via AgentMail + PDF. Skill: bulletin-agent. Cron: 813b03d1a3e1.
Weekly Digest: Sunday 8pm UTC. Intentions tbl62rEmak92HLXX2. Skill: weekly-digest-agent. Cron: b0b836135650. Scripts: weekly_digest_fetch.py + build_weekly_digest_html.py.
§
David's prefs: no raw log tables, no cron for chat, modules on-demand, simple consolidated designs. Explicit approval before schema changes. Wife rates films. Likes to paste raw data and have me fill in the rest ("I'll trust you to fill in the rest"). Wants real data, not estimates. Reading: science, philosophy, history, sci-fi, self-help, biography. Asked about Kindle API (no official API exists).
§
Todos: skill built v1.1.0 at devops/todos-agent, table tblTcdZQ9AIltQDfu. When adding: ask priority, timeframe, category, due date. User can say "just add it" to skip.
§
Recipe Module: Live June 2026. Tables: Recipes (tblehBgzRMa2Xucjd), Ingredients (tblNsgbYHNK8xWnB7), Dinner Parties, Dinner Planner, Shopping List, Recipe Context, Recipe Output Log. Skill: recipes-agent v1.1.0.
§
Sleep Log tblTZchsmcXXernI0: Bedtime, Wake time, Hours slept, Quality, Notes, Night bathroom visits (fldZqK4F3MeWj3ko0, added 2026-06-08), Logged.
§
Backup: Private Git repo github.com/djaccounts/server-backup via SSH key. Script: /root/server-backup/backup.sh. Cron: nightly 2am UTC (job d3761ebbc9ac). Backs up Nginx, systemd, crontab, Docker, Mealie volume, Geeves, Hermes, SSH config, packages. Secrets excluded via .gitignore. Live since June 6 2026.
§
Property scan: Firecrawl + HTML fallback at property_scan_firecrawl.py. Exclude Dudley Road, Queen Elizabeth Drive (refurb), no repeats. Don't show Property Criteria in digest.
§
Garmin sync: python-garminconnect v0.3.2 installed. Script at garmin_sync.py. Needs GARMIN_EMAIL + GARMIN_PASSWORD in .env. Unofficial API first, official Garmin Developer key TBD.