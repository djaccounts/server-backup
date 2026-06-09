Airtable: Geeves base (appzvmonQXs4x2AlL). NEVER touch Practice Management. Schema via geeves-steward. HIT API RATE LIMITS June 2026 — migrating to Baserow.
§
Bulletin: 6am UTC daily via AgentMail + PDF. Skill: bulletin-agent. Cron: 813b03d1a3e1.
Weekly Digest: Sunday 8pm UTC. Intentions tbl62rEmak92HLXX2. Skill: weekly-digest-agent. Cron: b0b836135650. Scripts: weekly_digest_fetch.py + build_weekly_digest_html.py.
§
David's prefs: no raw log tables, no cron for chat, modules on-demand, simple consolidated designs. Explicit approval before any schema change. Wife rates films.
§
Todos: skill built v1.1.0 at devops/todos-agent, table tblTcdZQ9AIltQDfu. When adding: ask priority, timeframe, category, due date. User can say "just add it" to skip.
§
Recipe Module: Live June 2026. Tables: Recipes (tblehBgzRMa2Xucjd), Ingredients (tblNsgbYHNK8xWnB7), Dinner Parties, Dinner Planner, Shopping List, Recipe Context, Recipe Output Log. Skill: recipes-agent v1.1.0.
§
Phase 2 modules (June 2026): Cycling, Workouts, Meals links. Key API learnings: longText→multilineText; never patch replace_all on JSON; rebuild registry from GET meta/bases/{baseId}/tables if corrupted. Sleep Log tblTZchsmcXXernI0.
§
Sleep Log tblTZchsmcXXernI0: Bedtime, Wake time, Hours slept, Quality, Notes, Night bathroom visits (fldZqK4F3MeWj3ko0, added 2026-06-08), Logged.
§
Backup: Private Git repo github.com/djaccounts/server-backup via SSH key. Script: /root/server-backup/backup.sh. Cron: nightly 2am UTC (job d3761ebbc9ac). Backs up Nginx, systemd, crontab, Docker, Mealie volume, Geeves, Hermes, SSH config, packages. Secrets excluded via .gitignore. Live since June 6 2026.
§
Baserow: Self-hosted at http://77.68.33.121 (Nginx → Docker port 8080). v2.2.2. Admin: daverj1987@gmail.com. Workspace "Geeves" (id=95). Compose: /root/baserow/docker-compose.yml. Nginx: Baserow serves root, Mealie at /mealie. Migration from Airtable in progress.
§
Books: table tblUfRTBkCMLUe2pY, skill books-agent v1.0.0. Fields: Title, Author, Status/Genre/Format/Source selects, My rating (1-5), Date started/finished, Recommended by (→People). Slack capture active.