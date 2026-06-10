# Geeves — Agent Brief

*Read this first. Everything here is a rule, not a suggestion. Where it conflicts with other docs, this wins for how to act; the Master Plan and Schema Reference win for what to build.*

---

## What is Geeves?

Geeves is David's personal AI assistant — a self-improving software butler.
**Core bet: data compounds.** Every captured detail about people, preferences, and history makes every future interaction better.

**Stack:** Hermes Agent (VPS) + Baserow (system of record) + Slack (input) + AgentMail (output).
No n8n, no Glide, no Railway.

**Baserow:** Self-hosted at `http://77.68.33.121` — 41 tables, database ID 132. API token in `BASEROW_API_TOKEN` env var. Use `baserow_api.py` for all CRUD. Mapping file: `baserow_mapping.json`.

**Migration status (June 2026):** All data and scripts migrated from Airtable to Baserow. Airtable is no longer used.

**Read these in order:**
1. This file — rules and current state
2. `QUICK_REFERENCE.md` — IDs, paths, contacts
3. `Geeves_Hermes_Brief.md` — operating principles, module pattern
4. `Geeves_Master_Plan_v2.md` — full architecture and roadmap

---

## Rules

1. **Baserow is the system of record.** All durable facts — people, recipes, todos, workouts — live in Baserow (database ID: 132). Use `baserow_api.py` for all CRUD operations. Mapping file: `/root/Geeves/baserow_mapping.json`.
2. **Schema changes go through the steward.** Load the `geeves-steward` skill before any schema modification. Update `baserow_mapping.json` after.
3. **Follow the planning protocol.** Before building any new module, read `PLANNING_PROTOCOL.md`. After planning, complete the full downstream-doc checklist — no exceptions.
4. **People graph is the spine.** Every module links to People (`tbl1WMPtQhWYW7bTI`). Never duplicate person data. See tier structure in the Brief §6.
5. **Model routing — HARD RULE:**
   - **Sensitive** (health, marriage, private third-party details) → local Ollama only. Data never leaves the VPS.
   - **Ordinary** (recipes, films, todos, travel) → hosted OpenRouter model.
   - **When in doubt → Sensitive.**
6. **Fail loudly.** If a cron job or write fails, message David on Slack immediately. Silent failures are worse than no feature.
7. **No raw log tables.** David doesn't want to see them. Use Output_Log for generated output; Memory_Summaries for rolled-up history.

---

## Active Modules

| Module | Skill | Phase | Status | Key Tables |
|--------|-------|-------|--------|------------|
| People graph | `people-agent` | 1 | ✅ Built | People, Person Notes, Conversation Log |
| Morning digest | `bulletin-agent` | 2 | ✅ Daily 6am UTC | Weather_Data, Stock_Prices, Fact_of_the_Day, News_Headlines |
| Todos | `todos-agent` | 2 | ✅ Slack capture | Todos |
| Meals | `meals-agent` | 2 | ✅ Slack capture | Meals, Daily Nutrition Summary |
| Sleep & Habits | `sleep-agent` | 2 | ✅ Slack capture | Sleep Log, Habits, Habit Log |
|| Fitness | `fitness-agent` | 2 | ✅ Slack capture + Garmin auto-import | Workouts, Exercise Log, Cycling, Fitness Goals |
|| Cycling | — | 2 | ✅ Garmin auto-import (daily 7am) | Cycling (linked to Workouts + People) |
| Weekly digest | `weekly-digest-agent` | 3 | ✅ Sun 8pm UTC | Intentions |
| Recipes | `recipes-agent` | 3 | ✅ Mealie integrated | Recipes, Ingredients, Dinner Parties, Dinner Planner, Shopping List, Dining Preferences |
| Film club | `film-club-agent` | 2+ | ✅ OMDb lookup | Films |
| Restaurants | `restaurants-agent` | 4 | ✅ SerpApi | Restaurants, Restaurant Visits |
| Books | `books-agent` | 4 | ✅ Slack capture | Books |
| Property | `property-agent` | 4 | ✅ Rightmove scan 5am | Properties, Property Criteria |

**Active cron jobs:**
- `813b03d1a3e1` — Morning Digest, daily 6am UTC
- `b0b836135650` — Weekly Digest + Intentions, Sunday 8pm UTC
- `cea50fc34ab0` — Property Scan, daily 5am UTC
- `0d2ddb20ece8` — Garmin Cycling Import, daily 7am UTC

**Modules not yet built (on demand):** Fitness, Travel/Commute, Relationships & Occasions, Goals, Documents/Subscriptions, Wardrobe, Events, Watching/Reading, London, plus all Phase 5.

---

## Universal Module Pattern

Every module uses the same four parts:
1. **Data table** — the records
2. **Context table** — permanent knowledge/preferences, always fed into prompts
3. **Output log** — what was generated, when, how David rated it (prevents repetition)
4. **Feedback hook** — David rates/edits → written back to Airtable

Full definition and build checklist in `Geeves_Hermes_Brief.md` §§7–11.

---

## Scripts

All at `/root/Geeves/scripts/`:

| Script | Purpose |
|--------|---------|
| `baserow_api.py` | CRUD on Baserow records (with field name→ID resolution) |
| `airtable_api.py` | Legacy — kept for reference, no longer used |
| `table_builder.py` | Legacy — Airtable Metadata API (needs Baserow rewrite for new modules) |
| `slack_capture.py` | Classifies Slack messages → Baserow writes |
| `*_fetch.py` | Bulletin/data fetchers → Baserow (weather, stocks, fact, token_usage) |
| `schema_checker.py` | Legacy — Airtable registry sync |
| `serpapi_search.py` | Google Maps / local business lookup |

**All scripts now write to Baserow.** Airtable is no longer used.

API usage tracking: `/root/Geeves/lib/api_usage_tracker.py` → logs to `api_usage.jsonl`.

---

## User Context

- **David** — primary user, non-engineer VPS owner (77.68.33.121). Slack U0B73K4QWP5. Email daverj1987@gmail.com.
- **Wife** — uses shared bot, owns opinions on films and properties, Tier 2 in People graph.
- **Style:** Build one piece at a time. Confirm with David before any schema change. Explain server tasks step-by-step. Prefer pragmatic over "proper."

---

*Last updated: June 2026. Module status tracked in `modules_status.json`.*
