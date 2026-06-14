Bulletin: 6am UTC daily. Skill: bulletin-agent v1.2.0. Cron: 813b03d1a3e1. 6 parallel fetchers: weather, stocks, fact, star wars, tokens, word_of_day. Word of Day: Baserow table 407, Free Dict API + MyMemory RU/HE.
§
David's prefs: no raw log tables, no cron for chat, modules on-demand, simple consolidated designs. Explicit approval before schema changes. Wife rates films. Likes to paste raw data and have me fill in the rest ("I'll trust you to fill in the rest"). Wants real data, not estimates. Reading: science, philosophy, history, sci-fi, self-help, biography. Asked about Kindle API (no official API exists). Home: 43 Englands Lane, NW3 4YD.
§
Todos: skill built v1.1.0 at devops/todos-agent, table tblTcdZQ9AIltQDfu. When adding: ask priority, timeframe, category, due date. User can say "just add it" to skip.
§
Recipe Module: Live June 2026. Baserow tables: Recipes, Ingredients, Dinner Parties, Dinner Planner, Shopping List. Skills: recipes-agent v1.1.0, meals-agent v1.1.0 (photo logging). Meals Baserow id=387. Photo pipeline: meal_photo_pipeline.py. Vision tool needs 'vision' in toolsets.
§
Backup: github.com/djaccounts/server-backup via SSH. Script: /root/server-backup/backup.sh. Cron: nightly 2am UTC (d3761ebbc9ac). Backs up Nginx, systemd, crontab, Docker, Mealie, Geeves, Hermes, SSH, packages. Live since June 6 2026.
§
Garmin API: HR/calories in summary fields, NOT details. Baserow filter_by_formula unreliable — filter locally. Garmin 429s on login — retry 60s. Bulk import: get_activities(offset,limit) pagination.
§
Baserow: DB token = row CRUD only. JWT (table_builder.py) = schema ops (create/delete tables, add/delete fields, list tables). Regenerate baserow_mapping.json manually after JWT schema ops.
§
Mac Mini M4 Refurb Scanner: Daily 10am UTC (cron 4baaa029632d). Firecrawl JS rendering (waitFor:8000) required — static HTML always shows "Add to Bag". IDs: fcyt4b (£849), g1cg1b (£1019), fcx44b (£1189). Only alert when in stock.
§
Vision: `vision_analyze` unreliable. Use OpenRouter API: `anthropic/claude-sonnet-4` (best), `gemini-2.5-flash` (ok). Groq 403. Env var: `GOOGLE_API_KEY` not `GEMINI_API_KEY`.
§
Russian chicken cutlets recipe