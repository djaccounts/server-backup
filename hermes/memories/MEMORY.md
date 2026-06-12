Bulletin: 6am UTC daily. Skill: bulletin-agent v1.2.0. Cron: 813b03d1a3e1. 6 fetchers in parallel: weather, stocks, fact, star wars, tokens, word_of_day. Word of Day: Baserow table 407, Free Dict API + MyMemory RU/HE, 40-word list.
§
David's prefs: no raw log tables, no cron for chat, modules on-demand, simple consolidated designs. Explicit approval before schema changes. Wife rates films. Likes to paste raw data and have me fill in the rest ("I'll trust you to fill in the rest"). Wants real data, not estimates. Reading: science, philosophy, history, sci-fi, self-help, biography. Asked about Kindle API (no official API exists).
§
Todos: skill built v1.1.0 at devops/todos-agent, table tblTcdZQ9AIltQDfu. When adding: ask priority, timeframe, category, due date. User can say "just add it" to skip.
§
Recipe Module: Live June 2026. Baserow tables: Recipes, Ingredients, Dinner Parties, Dinner Planner, Shopping List. Skill: recipes-agent v1.1.0. Meal Tracking: meals-agent v1.1.0 (photo logging added), Baserow Meals (id=387). Photo pipeline: meal_photo_pipeline.py. Vision tool needs 'vision' in toolsets: list.
§
Backup: Private Git repo github.com/djaccounts/server-backup via SSH key. Script: /root/server-backup/backup.sh. Cron: nightly 2am UTC (job d3761ebbc9ac). Backs up Nginx, systemd, crontab, Docker, Mealie volume, Geeves, Hermes, SSH config, packages. Secrets excluded via .gitignore. Live since June 6 2026.
§
Garmin API: HR/calories in summary fields, NOT details. Baserow filter_by_formula unreliable — filter locally. Garmin 429s on login — retry 60s. Bulk import: get_activities(offset,limit) pagination.
§
Baserow: DB token = row CRUD only. JWT (table_builder.py) = schema ops (create/delete tables, add/delete fields, list tables). Regenerate baserow_mapping.json manually after JWT schema ops.
§
David's home address: 43 Englands Lane, NW3 4YD. Prefers AgentMail replies posted to Slack only when there are actual new messages (no empty notifications). Guest invites: HTML-only email, no PDF. Cooking version: PDF attachment. Design: white background, compact, vertical guest list.