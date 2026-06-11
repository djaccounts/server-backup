Bulletin: 6am UTC daily via AgentMail + PDF. Skill: bulletin-agent. Cron: 813b03d1a3e1.
Weekly Digest: Sunday 8pm UTC. Intentions tbl62rEmak92HLXX2. Skill: weekly-digest-agent. Cron: b0b836135650. Scripts: weekly_digest_fetch.py + build_weekly_digest_html.py.
§
David's prefs: no raw log tables, no cron for chat, modules on-demand, simple consolidated designs. Explicit approval before schema changes. Wife rates films. Likes to paste raw data and have me fill in the rest ("I'll trust you to fill in the rest"). Wants real data, not estimates. Reading: science, philosophy, history, sci-fi, self-help, biography. Asked about Kindle API (no official API exists).
§
Todos: skill built v1.1.0 at devops/todos-agent, table tblTcdZQ9AIltQDfu. When adding: ask priority, timeframe, category, due date. User can say "just add it" to skip.
§
Recipe Module: Live June 2026. Tables: Recipes (tblehBgzRMa2Xucjd), Ingredients (tblNsgbYHNK8xWnB7), Dinner Parties, Dinner Planner, Shopping List, Recipe Context, Recipe Output Log. Skill: recipes-agent v1.1.0.
§
Backup: Private Git repo github.com/djaccounts/server-backup via SSH key. Script: /root/server-backup/backup.sh. Cron: nightly 2am UTC (job d3761ebbc9ac). Backs up Nginx, systemd, crontab, Docker, Mealie volume, Geeves, Hermes, SSH config, packages. Secrets excluded via .gitignore. Live since June 6 2026.
§
Property scan: Firecrawl + HTML fallback at property_scan_firecrawl.py. Exclude Dudley Road, Queen Elizabeth Drive (refurb), no repeats. Don't show Property Criteria in digest.
§
Baserow migration: property_scan_firecrawl.py done. Recipe scripts still on Airtable. Pitfalls: single_select=dict, naive dates, string numbers. baserow_api.py create-row outputs text. Digest builder has Properties+Todos.
§
David's home address: 43 Englands Lane, NW3 4YD. Prefers AgentMail replies posted to Slack only when there are actual new messages (no empty notifications). Guest invites: HTML-only email, no PDF. Cooking version: PDF attachment. Design: white background, compact, vertical guest list.