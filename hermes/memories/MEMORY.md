Airtable: Geeves base (appzvmonQXs4x2AlL) only. NEVER touch Practice Management. Schema changes via geeves-steward skill. Registry: schema_registry.json. Schema Ref v2 + module status + planning protocol at /root/Geeves/. NOTE: Module_Build_Playbook.md does NOT exist on disk.
§
Restaurant Module (Phase 4): Built June 2026. Tables: Restaurants (tblvpSxjeoCQvjotM), Restaurant Visits (tblf2k6uAHLW7mA4b). Skill: restaurants-agent (devops/restaurants-agent). SerpApi Google Maps lookup. Google search link for Maps URL. Wife's separate rating/notes. Cross-module Dining Preferences (tblzzGIF7yPf37NG5) for alignment scoring. Slack capture creates records.
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
Phase 2 modules (June 2026): All tables built including Cycling (miles, links to Workouts+People, Strava/Garmin). Workouts has People link. Meals has From recipe link. Evening digest removed. Key API learnings: longText→multilineText; NEVER patch replace_all on JSON; rebuild registry from GET meta/bases/{baseId}/tables if corrupted; miles not km for distance.
§
Google Contacts sync: Option A (one-time import) already done. Option B (live two-way sync) planned for future — needs cron job, Google People API polling, conflict resolution/dedup logic.