---
name: geeves-airtable
description: "Geeves Airtable CRUD + Table Builder — read, create, update, delete records; create tables and fields via the Metadata API. Includes model routing awareness (sensitive data stays local)."
version: 1.7.0
author: Geeves
---

# Geeves — Airtable CRUD + Table Builder

**⚠️ LEGACY — MIGRATION TO BASEROW COMPLETE (June 2026):** The Geeves project has migrated from Airtable to Baserow. This skill is kept for reference only. **Use the `baserow` skill for all database operations.** See `baserow/references/airtable-migration-runbook.md` for migration details.

**Migration status (June 2026) — ✅ COMPLETE:**
- ✅ All data migrated to Baserow (41 tables, all row counts verified)
- ✅ Data reconciliation done (Properties, Books, Workouts, Cycling re-imported)
- ✅ 35/40 tables match Airtable exactly; 5 have expected diffs (Baserow has newer live data from scripts)
- ✅ All scripts migrated (`baserow_api.py`, `slack_capture.py`, all fetch scripts)
- ✅ Cron jobs updated to use Baserow
- ✅ `table_builder.py` — rewritten for Baserow Platform API
- ✅ Module skills — updated to reference Baserow
- **Airtable is now the stale copy. Baserow is the system of record.**

**When to use this skill:**
- Reference for old Airtable table IDs and field definitions
- Schema migration patterns
- Understanding legacy code

**When to use `baserow` skill instead:**
- **ALL** new database operations
- Creating/updating records
- Schema changes
- Building new modules

**When to use this skill:**
- Legacy Airtable operations during migration period
- Reference for existing Airtable table IDs and field definitions
- Schema migration patterns

**When to use `baserow` skill instead:**
- All new database operations
- Creating/updating records
- Schema changes on Baserow

Core Airtable operations for the Geeves project. Two helper scripts:
- `/root/Geeves/scripts/airtable_api.py` — CRUD operations on records
- `/root/Geeves/scripts/table_builder.py` — create tables and fields via Metadata API

## Base
- **Geeves base ID:** `appzvmonQXs4x2AlL`
- **NEVER touch:** `appk0DXJthirMxTZV` (Practice Management)
- **Master Plan:** `/root/Geeves/Geeves_Master_Plan_v2.md` — full vision, 5-phase build plan
- **Schema Reference:** `/root/Geeves/Geeves_Schema_Reference_v2.md` — all 25 modules, table/field definitions, cross-module link map

## Airtable API Capabilities — IMPORTANT

The Metadata API **CAN** create tables and fields:
- `POST meta/bases/{baseId}/tables` — create table with fields ✅
- `POST meta/bases/{baseId}/tables/{tableId}/fields` — add field to existing table ✅

The API **CANNOT** delete tables or fields — that requires the Airtable web UI.
The API **CANNOT** change field types on existing fields — the Metadata API's `PATCH` endpoint rejects type changes (422 INVALID_REQUEST_UNKNOWN). **Workaround:** create a new field with the desired type alongside the old one, migrate data, then hide the old field in the UI. See `references/schema-migration.md` for the full pattern.
The API **CANNOT** create `createdTime` or `lastModifiedTime` fields — neither during table creation nor via the add-field endpoint. These must be added manually in the Airtable web UI.

## Table Builder Script

```bash
# Show current schema
python3 /root/Geeves/scripts/table_builder.py --schema

# Create/fix core tables (delete broken ones in web UI first)
python3 /root/Geeves/scripts/table_builder.py --fix

# Create bulletin tables (Weather_Data, Stock_Prices, Fact_of_the_Day)
python3 /root/Geeves/scripts/table_builder.py --bulletin

# Create Films table (master film diary + film club)
python3 /root/Geeves/scripts/table_builder.py --films

# Create Weekly Digest tables (Intentions)
python3 /root/Geeves/scripts/table_builder.py --weekly

# Verify fitness tables exist (already created — shows schema)
python3 /root/Geeves/scripts/table_builder.py --fitness

# Scaffold a new module (creates Data, Context, Log tables)
python3 /root/Geeves/scripts/table_builder.py --module DinnerParty
```

When adding new table groups, add a dict to `table_builder.py` (following `CORE_TABLES` / `BULLETIN_TABLES` pattern) and a corresponding function + CLI flag in `main()`. **Pitfall:** When patching `main()` to add a new `elif` branch, be careful not to accidentally replace an existing branch — the `--module` flag was once lost this way.

## Core Tables (v2 Schema)

| Table | ID | Purpose |
|-------|----|---------|
| `People` | tbl1WMPtQhWYW7bTI | The people graph — one record per person, links to Person Notes and Conversation Log |
| `Person Notes` | tbl6hnxzXXmWFkVfh | Timestamped freeform notes about a person |
| `Conversation Log` | tbl2dbgksA9XveLcx | Debriefs after seeing someone (Summary, Date, Key things to remember) |
|| `Todos` | tblTcdZQ9AIltQDfu | Tasks with Timeframe, Category, Source; Status: Not started/In progress/Done |
| `Memory_Summaries` | tblXH4eCLwM8S30cn | Periodic long-term memory roll-ups |
| `Output_Log` | tbldJT41dAAX1WTkC | What Hermes generated, when, and rating |
|| `Properties` | tblA0jfgqxhPFJU7S | Property search listings from Rightmove — address, price, score, status |
|| `Property Criteria` | tbl6oeRjhK3sds9TI | Search criteria — Must have/Nice to have/Dealbreaker/Budget |
|| `Sleep Log` | tblTZchsmcXXernI0 | Daily sleep tracking — bedtime, wake time, hours, quality rating |
|| `Habits` | tblS6SryrC3RnRl1L | Habit definitions — name, frequency target, category |
|| `Habit Log` | tbl3YRZ1yoQ7kRPIT | Daily habit completion — date, habit link, completed checkbox |
|| `Workouts` | tblMDYF8Lkl5A15CW | Workout sessions — type, duration, distance, energy, difficulty |
|| `Exercise Log` | tbl8MXDYZ2hajsdIk | Gym exercise detail — exercise, workout link, sets, reps, weight |
|| `Fitness Goals` | tblAM0Grin01IQmdd | Fitness targets — goal type, calorie/protein/workout targets |
|| `Meals` | tblzEBw7Whoomb63E | Meal log — description, date, type, macros, accuracy, source |
|| `Daily Nutrition Summary` | tbl16Z64tClYJaPLZ | Daily nutrition roll-up — date, total calories/protein/carbs/fat |
|| `Digest Log` | tblmihsXrU8sIg4mY | Digest email log — date, type, content, delivery status |
|| `Word List` | tblDpKhGlQ2zQxBfD | Russian vocabulary — word, pronunciation, meaning, example, difficulty |
|| `News Sources` | tblDKPUMuh8Xohoh1 | RSS news sources — name, feed URL, category, active |
|| `Input Log` | `tblwqFHQu3ueh9aFx` | Incoming message log — raw message, channel, intent, routing |
|| `Intentions` | `tbl62rEmak92HLXX2` | Weekly intentions — set, track, and reflect on intentions each week. |
|| `Cycling` | `tblZ7hkoE68IRnQwV` | Cycling ride log — route, distance (miles), speed, elevation, HR, power, bike, people, Strava URL |

**People v2 fields (key changes):**
- `Relationship type` (singleSelect) replaces old `Relationship` (text)
- `Dietary reqs` (multipleSelects) replaces old `Dietary Requirements` (text)
- `Allergy list` (multipleSelects) replaces old `Allergies` (text)
- `Typical contact frequency` (singleSelect) replaces old `Contact Frequency` (text)
- `Gift budget range` (singleSelect) replaces old `Gift Budget` (text)
- `How I know them` (renamed from `How Known`), `Food dislikes` (renamed from `Dietary Dislikes`), `Hobbies & interests` (renamed from `Hobbies`)
- `Tier` values: Tier 1 / Tier 2 / Tier 3 / Tier 4 (old values like "Tier 1 (David)" remapped)

Old fields still exist in the table but should be hidden in the Airtable web UI. See `references/schema-migration.md`.

## Bulletin Tables

Daily data collection tables for the morning digest. Each has its own fetcher script. See `references/bulletin-setup.md` for full details.

| Table | Purpose | Fetcher Script | API Source |
|-------|---------|----------------|------------|
| `Weather_Data` | Daily London weather with highs/lows/rain times | `weather_fetch.py` | Open-Meteo (free, no key) |
| `Stock_Prices` | BTC-GBP, AMZN, GOOGL, META daily prices | `stocks_fetch.py` | yfinance (free, no key) |
| `Fact_of_the_Day` | 6 rotating sources with fallback chain | `fact_fetch.py` | Wikipedia/NASA/Quotes/Holidays |
| `Token_Usage` | Daily Hermes token consumption metrics | `token_usage.py` | Hermes state.db (SQLite) |
| `Star_Wars_Fact` | Random Star Wars character fact | `starwars_fetch.py` | SWAPI.tech (free, no key) |

Fact rotation: day_of_year % 6 → 0=Wikipedia On This Day, 1=NASA APOD, 2=Quote Garden, 3=Zen, 4=Holidays, 5=Useless Facts.

**Email:** Digest sent to `dj@djaccounts.com` via AgentMail with PDF attachment (via PDFBolt). See `references/bulletin-setup.md`.

```bash
python3 /root/Geeves/scripts/airtable_api.py list-tables appzvmonQXs4x2AlL
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "People"
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "People" \
  '{"Full Name": "David", "Tier": "Tier 1 (David)"}'
```

## Auth — CRITICAL
AIRTABLE_API_KEY is **NOT** in `os.environ` for Python. Read via subprocess grep:
```python
r = subprocess.run(["grep", "AIRTABLE_API_KEY", "/root/.hermes/.env"], capture_output=True, text=True)
key = r.stdout.strip().split("\n")[0].split("=", 1)[1]
```
Never use shell interpolation (`$KEY` in curl) — keys with `+`, `/`, `=` break shell quoting.

## API Quirks

### Field Type Name Mapping (Schema Reference → API)
The Schema Reference v2 uses Airtable UI type names. The Metadata API uses different JSON type names. **This is the #1 cause of 422 errors during table creation.**

| Schema Reference (UI name) | API type name | Notes |
|---|---|---|
| `long text` | `multilineText` | `longText` causes 422 INVALID_REQUEST_UNKNOWN |
| `single line text` | `singleLineText` | |
| `multiple record links` | `multipleRecordLinks` | |
| `single select` | `singleSelect` | |
| `multiple select` | `multipleSelects` | |
| `created time` | *not supported* | Cannot be created via API — add manually in web UI |
| `last modified time` | *not supported* | Cannot be created via API — add manually in web UI |

### ⚠ Distance Fields: Miles, Not Kilometres
David uses **miles** for cycling/vehicle distance and **mph** for speed — NOT km/kmh. Always use miles for distance fields. When creating any table with distance or speed fields, default to miles/mph unless explicitly told otherwise.

### ⚠ Pitfall: `patch` with `replace_all=true` on JSON Files
**NEVER use `patch` with `replace_all=true` on schema_registry.json** (or any JSON file with repeated patterns). The patch tool matches `old_string` against the ENTIRE file and replaces ALL occurrences — so if the string appears in every table entry, every table entry gets the replacement, corrupting the entire file.

**Recovery when schema_registry.json is corrupted:**
1. Query Airtable API: `GET meta/bases/{baseId}/tables` — returns all tables with field IDs and types
2. Rebuild the registry from scratch using the API response
3. Write fresh JSON — do NOT try to patch the corrupted file

**Correct approach for JSON files:** Use targeted patches with unique surrounding context (include braces, commas, quotes from adjacent fields to make the match unique). Or rewrite the whole file.

### Table Creation Strategy: Minimal First, Then Add
When creating tables with many fields, the API may reject complex field combinations (e.g., `date` + `multilineText` + `singleSelect` together). **Pattern that works:**
1. Create the table with only the primary field + simple fields (text, select, date, number, checkbox)
2. Add complex fields (`multilineText`, `rating`, `multipleRecordLinks`) via separate `add_field()` calls after the table exists
3. This avoids mysterious 422 INVALID_REQUEST_UNKNOWN errors from field type interactions

### Field Options Required at Creation Time
- `createdTime`/`lastModifiedTime` are auto-managed — skip in create_table()
- `multipleRecordLinks`: Only `{"linkedTableId": "tblXXXX"}` is valid during table creation. Do NOT include `isReversed` or `prefersSingleRecordLink` — they cause 422. Add the link via separate `add_field()` call if creation fails.
- **Date fields require options**: `{"dateFormat": {"name": "local"}}` — without this, table creation fails with `INVALID_FIELD_TYPE_OPTIONS_FOR_CREATE`
- **Number fields require options**: `{"precision": N}` — without this, table creation fails with `INVALID_FIELD_TYPE_OPTIONS_FOR_CREATE`. Always include `"precision": N` in field defs (e.g. `"precision": 2` for prices, `"precision": 1` for temperatures, `"precision": 0` for integers).
- **⚠ multipleSelects fields require options during table creation**: `{"choices": [{"name": "Option1"}, ...]}` — without this, table creation fails with `INVALID_FIELD_TYPE_OPTIONS_FOR_CREATE`. Same format as singleSelect but the field type is `"multipleSelects"`.
- **⚠ Checkbox fields require options during table creation**: `{"icon": "check", "color": "greenBright"}` — without this, table creation fails with `INVALID_FIELD_TYPE_OPTIONS_FOR_CREATE`. The icon/color values are Airtable defaults; any valid combination works.
- Select options: `{"choices": [{"name": "Option1"}, ...]}`
- **⚠ Rating fields require options**: `{"max": 5, "icon": "star", "color": "yellowBright"}` — without icon and color, field creation fails with `INVALID_FIELD_TYPE_OPTIONS_FOR_CREATE`. Valid colors: `yellowBright`, `yellowDark1`, `orangeBright`, `redBright`, `pinkBright`, `purpleBright`, `blueBright`, `cyanBright`, `tealBright`, `greenBright`.

### ⚠ Pitfall: Select Field Options Corruption During Table Creation

**Symptom:** After creating a table, select fields show `['choices']` as their only option (the literal string "choices" instead of the actual option values). The Airtable UI displays a single choice called "choices".

**Cause:** The `build_field_payload()` function in `table_builder.py` has a bug where select field options specified in the MODULE_TABLES dict don't get properly included when the table is created via `create_table()`. The options are silently dropped, and Airtable creates the field with a corrupted placeholder.

**Detection:** After creating any table with select fields, immediately run `--schema` and verify that select fields show the correct choice lists, not `['choices']`.

**Fix:** The API **cannot** fix corrupted select fields — PATCH returns 422 INVALID_REQUEST_UNKNOWN. The table **must be deleted from the Airtable web UI and recreated**. The API cannot delete tables.

**Workaround pattern:** Create tables WITHOUT select fields, then add select fields one-by-one via `add_field()` calls. The `add_field()` path uses the same `build_field_payload()` function but seems to work correctly for select types when called post-creation. Alternatively, exclude select fields from the initial `create_table()` payload and add them all via `add_field()` after the table exists.

**⚠ This also means: always verify select field options immediately after table creation. If corrupted, stop and ask the user to delete the table before proceeding.**
- **⚠ Can't write new select options via the Records API** (without `typecast`). Writing a value to a `singleSelect` field that isn't already a defined choice fails with `INVALID_MULTIPLE_CHOICE_OPTIONS`. **Two workarounds:**
  1. **`typecast=true` on batch PATCH:** `api("PATCH", f"{BASE}/Table", {"records": [...], "typecast": True})` — auto-creates new select options. This is the preferred approach for remapping values (e.g. changing "Tier 1 (David)" → "Tier 1" across all records).
  2. **Metadata API:** `PATCH` the field's `options.choices` array to add options first, then write records using the new option names.
- **Avoid special chars in field names** (°, %, /) — Airtable accepts them but they cause issues in scripts/API. Use spelled-out names: `"Temperature C"` not `"Temperature °C"`, `"Change Pct"` not `"Change %"`.
- **⚠ URL encoding breaks Airtable formula fields** — `urllib.parse.urlencode` mangles `FIND("X",{Field Name})` because curly braces `{}` and inner quotes get percent-encoded, causing 422 INVALID_REQUEST_UNKNOWN. **Workaround:** for simple name/content searches, run `list-records` and grep the output. If you must use filterByFormula programmatically, construct the URL manually (not via `urlencode`) or use the `airtable_api.py` helper which handles quoting internally.
- **⚠ filterByFormula does NOT work for multipleRecordLinks fields** — Formula filters like `{Recipe}='recXXX'` silently return empty results for link fields. **Workaround:** fetch all records (or use a large `maxRecords` value) and filter locally in Python by checking `record['fields'].get('LinkFieldName', [])`. This is slower but is the only reliable approach.
- Rate limit: 5 req/sec per base, 10 records per batch create
- API **cannot** detect if a table has wrong schema — always use `--schema` first, then delete + recreate in web UI if needed
- **⚠ Metadata API field listing endpoint returns 404:** `GET meta/bases/{baseId}/tables/{tableId}/fields` returns 404 Not Found. To list fields for a specific table, use `GET meta/bases/{baseId}/tables` (returns all tables with their fields) and filter client-side by table name or ID.

### ⚠ URL-Encode Table Names With Spaces
Airtable table names containing spaces (e.g., `Sleep Log`, `Habit Log`, `Recipe Context`, `Exercise Log`, `Daily Nutrition Summary`, `Property Criteria`, etc.) **must be URL-encoded** when used in REST API paths. Using the raw name in a URL path raises `http.client.InvalidURL: URL can't contain control characters`.

```python
import urllib.parse
encoded_table = urllib.parse.quote(table_name)
url = f"https://api.airtable.com/v0/{BASE}/{encoded_table}?max_records=100"
```

The `airtable_api.py` helper and `fetch_records()` in digest scripts handle this — but any new script that calls the Airtable API directly must encode table names. Single-word table names (`Todos`, `People`, `Recipes`, `Films`) don't need encoding but encoding them is harmless.

## Google OAuth — Setup (Updated for New Google Auth Platform)

Google has migrated to a new "Google Auth Platform" console. The flow has changed:

### New Console URLs (use these, not old ones)
- **Consent screen**: `https://console.cloud.google.com/apis/credentials/consent`
- **OAuth clients**: `https://console.cloud.google.com/apis/credentials/oauthclient`
- **Auth platform overview**: `https://console.cloud.google.com/auth`

### Key Change: Scopes Are NOT Set During Client Creation
In the new UI, creating an OAuth Desktop client does NOT ask for scopes. Scopes are requested at **authorization time** (when the user opens the auth URL in their browser). This means:
- You do NOT need to pre-configure scopes in the Google Cloud Console
- Just create the Desktop app OAuth client, download the JSON, and register it on the server
- The setup script (`setup.py --auth-url`) will request the scopes when generating the URL

### Step-by-Step (New UI)
1. Create project at `https://console.cloud.google.com/projectselector2/home/dashboard` — select **"No organization"** (not your Workspace org)
2. Enable APIs at `https://console.cloud.google.com/apis/library`: Gmail, Calendar, Drive, People
3. Create OAuth consent screen: set **User type: External**, add your email as test user
4. Create OAuth client: **Desktop app** → download JSON
5. Register JSON on server: `setup.py --client-secret /path/to/client_secret.json`
6. Generate auth URL: `setup.py --auth-url` → open in browser → approve → paste redirect URL back
7. Exchange code: `setup.py --auth-code <code>`

### `org_internal` Error
If you get `Error 403: org_internal`:
- The consent screen is set to **Internal** (org-only) — personal Gmail blocked
- **Fix**: Delete consent screen → recreate as **External** → add email as test user
- Cannot change Internal → External in place; must delete and recreate
- Using "No organization" when creating the project avoids this entirely

### ⚠ USER APPROVAL REQUIRED Before Creating Tables

**Always present the full field list to the user and get explicit approval before creating ANY Airtable table.** This is David's standing rule. Show every field name, type, and option. Wait for "yes" or "go ahead" before running `table_builder.py`. This applies to new tables AND schema changes to existing tables.

### ⚠ Thread Decisions Supersede Reference Docs

When a user conversation changes a schema decision, the conversation is the source of truth — not the reference documents. After a thread-driven change:
1. Update `/root/Geeves/schema_registry.json` with the new fields/decisions
2. Update the relevant `references/<module>.md` file to match
3. Update this SKILL.md if the change affects general patterns

Reference docs are a starting point; the user's live decisions override them.

### ⚠ Design Preference: Consolidated Over Normalized

David prefers **fewer, wider tables** over many narrow linked tables. When designing a new module, default to one table with optional fields rather than splitting into multiple linked tables. Only split if there's a clear functional reason (e.g., one-to-many relationships where the "many" side has its own lifecycle). The Films table is the canonical example: personal diary + film club + member ratings all in one table, filtered by `Film Club = Yes/No`.

### ⚠ Pitfall: Patch Tool Indentation Errors

The `patch` tool with `mode='replace'` silently produces nested/broken code when `old_string` doesn't exactly match the current file state (e.g., after a prior partial edit). **Always re-read the file with `read_file` before patching** — do not rely on a read from earlier in the session. If a patch fails or produces indentation errors, read the whole file fresh and retry.

### ⚠ Pitfall: Accidentally Removing Adjacent List Entries

When patching a list (like `CATEGORY_RULES` in `slack_capture.py` or `elif` chains in `table_builder.py`), the `old_string` must include **exact** surrounding context. If the match is too short or too generic, the patch tool can:
- Replace a middle entry and orphan the entries that followed it (they become unreachable code)
- Match multiple locations and corrupt the file

**Always include the entry BEFORE and AFTER the target** in your `old_string` to make the match unique. For list entries, include the closing `]` of the previous entry and the opening `(` of the next entry. For `elif` chains, include the preceding `elif` and following `elif`.

**Recovery:** If an entry gets orphaned, re-read the file, find the orphaned code, and patch it back into the correct location with proper indentation.

## Building New Modules

**Follow the Module Build Playbook:** `/root/Geeves/Module_Build_Playbook.md`

The playbook is the standard process for every new module. Key principles:

1. **Check first** — `modules_status.json` for current state, `schema_registry.json` for table IDs. **IMPORTANT: Run `table_builder.py --schema` to check if tables ALREADY EXIST in Airtable before assuming they need creation.** Tables may have been created in a prior session without the module being marked "built." If tables exist but there's no skill, skip table creation and proceed directly to skill authoring.
2. **Get approval** — Present full field list to user before creating anything (only needed if tables don't exist yet)
3. **Build in order** — Tables → Skill → Scripts → Slack capture → Cron → Docs → Test
4. **Create a class-level skill** — `/root/.hermes/skills/devops/<module>-agent/SKILL.md` using the template at `/root/Geeves/templates/module-skill-template.md`
5. **Update all docs** — `schema_registry.json`, `modules_status.json`, skill, cross-references
6. **Memory stays lean** — Add only a one-line pointer in memory: `"<Module> → <module>-agent skill"`

**Skill template:** `/root/Geeves/templates/module-skill-template.md`
**Module status tracker:** `/root/Geeves/modules_status.json`
**Schema reference:** `Geeves_Schema_Reference_v2.md` (approved table/field definitions)
**Build checklist:** `references/module-build-checklist.md` — step-by-step checklist with common pitfalls

## Module Scaffold Pattern

### Generic Scaffold (simple modules)
Every module gets 3 tables (Data, Context, Log) via `--module`:
```bash
python3 /root/Geeves/scripts/table_builder.py --module DinnerParty
```
Context feeds into prompts; Log prevents repetition.

### Purpose-Built Modules (complex modules with custom domains)
Some modules need domain-specific fields and external API integration rather than the generic Data/Context/Log pattern. These are built by:

1. **Present the proposed schema to the user for approval FIRST** — show every field
2. Adding a dedicated `MODULE_TABLES` dict in `table_builder.py` (following the `CORE_TABLES` / `BULLETIN_TABLES` pattern) with custom field definitions
3. Writing a `create_<module>_tables()` function + CLI flag in `main()`
4. Adding a classifier category and handler in `slack_capture.py`

**Existing purpose-built modules:**

| Module | Table(s) | Table ID(s) | External API |
|--------|----------|-------------|--------------|
| **Films** | `Films` | `tblqCpp3EB7wU2ZZ3` | OMDb (IMDb lookup, key in `/root/.hermes/.env`). **Full film club workflows, Slack capture, and CRUD: see `film-club-agent` skill.** |
| **Social Events** | Uses `Todos` table | — | Category-routing from Slack captures ("dinner", "party", "social"). No dedicated table — events go into Todos with Module="Social" and Linked Person refs. |
| **Recipe App** | `Recipes`, `Ingredients`, `Dinner Parties`, `Dinner Planner`, `Shopping List`, `Recipe Context`, `Recipe Output Log` | See below | Mealie (port 9925). Sync: Mealie → Airtable. **Full recipe workflows, Mealie API, and meal logging: see `recipes-agent` skill.** |
|| **Dining Preferences** | `Dining Preferences` | `tblzzGIF7yPf37NG5` | Auto-populated by Hermes from recipe ratings, meal frequency, ingredient patterns. Read by Restaurant module for alignment scoring. |
|| **Restaurants** | `Restaurants`, `Restaurant Visits` | See below | SerpApi Google Maps (free tier 250/mo). **Full restaurant workflows, visit logging, and recommendations: see `restaurants-agent` skill.** |
|| **Weekly Digest** | `Intentions` | `tbl62rEmak92HLXX2` | Weekly intentions — set, track, reflect. Sunday 8pm UTC cron. **Full weekly digest pipeline: see `weekly-digest-agent` skill.** |
|| **Books** | `Books` | `tblUfRTBkCMLUe2pY` | Reading list, book tracking, Goodreads references, people-graph recommendations. **Full books workflows: see `books-agent` skill.** |
|| **Fitness** | `Workouts`, `Exercise Log`, `Cycling`, `Fitness Goals` | See below | Slack capture for workout logging, gym sessions, cycling rides. **Garmin Connect auto-import for cycling (daily 7am cron). Full fitness workflows: see `fitness-agent` skill. Garmin integration details: `references/garmin-connect.md`. |

**Recipe App table IDs:**

| Table | ID |
|-------|----|
| `Recipes` | `tblehBgzRMa2Xucjd` |
| `Ingredients` | `tblNsgbYHNK8xWnB7` |
| `Dinner Parties` | `tblwbQrIu3nUWDz3G` |
| `Dinner Planner` | `tblnts17CCckLJoUQ` |
| `Shopping List` | `tbldvpIO91xi72a0K` |
| `Recipe Context` | `tblJRsw77kbCFyoz9` |
|| `Recipe Output Log` | `tblYaJTAZDZzBkcwH` |
|| `Dining Preferences` | `tblzzGIF7yPf37NG5` |

**Restaurant module table IDs:**

| Table | ID |
|-------|----|
| `Restaurants` | `tblvpSxjeoCQvjotM` |
| `Restaurant Visits` | `tblf2k6uAHLW7mA4b` |

`table_builder.py --recipe` creates all 7 tables.

`table_builder.py --recipe` creates all 7 tables.

**Fitness module table IDs:**

| Table | ID |
|-------|----|
| `Workouts` | `tblMDYF8Lkl5A15CW` |
| `Exercise Log` | `tbl8MXDYZ2hajsdIk` |
| `Cycling` | `tblZ7hkoE68IRnQwV` |
| `Fitness Goals` | `tblAM0Grin01IQmdd` |

When adding MCP servers to Hermes, `hermes mcp add` has shell-parsing issues with special characters. Instead, write directly to `~/.hermes/config.yaml` via Python:

```python
import yaml
with open("/root/.hermes/config.yaml") as f:
    config = yaml.safe_load(f)
config["mcp_servers"]["server_name"] = {
    "command": "npx",
    "args": ["-y", "package-name"],
    "env": {"API_KEY": "value"}  # or "${ENV_VAR}" for .env references
}
with open("/root/.hermes/config.yaml", "w") as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
```

The `hermes mcp add` command may swallow arguments containing special chars.
After config change, use `/reload-mcp` in the Hermes chat to activate.
### SWAPI (Star Wars API)
- **⚠ `swapi.dev` has expired SSL** — use `https://swapi.tech` instead
- No auth required. Endpoints: `/api/people/{id}`, `/api/films/{id}`, etc.
- Returns nested `result.properties` structure (not flat)

## Email Setup

- **AgentMail** (preferred): Direct API calls to `api.agentmail.to` with Python (see AgentMail MCP tools)
  - AgentMail inbox: `davidj@agentmail.to` (send FROM address).
  - **⚠ Delivery to work domains unreliable** — emails from `agentmail.to` may be caught by corporate spam filters. Use personal Gmail (`gmail.com`) as primary or verify delivery with a plain-text test first.
  - **⚠ Bug fix (2026-06-03):** Was reading `/root/.env` (line 6) — fixed to read `/root/.hermes/.env`.
  - **BUG FIX (2026-06-03):** Was reading `/root/.env` (line 6) — fixed to read `/root/.hermes/.env`. If AgentMail stops working, verify: `grep AGENT_MAIL_API /root/.hermes/.env`.
  - AgentMail inbox: `davidj@agentmail.to` (send FROM address).
- **Himalaya/Gmail** (backup): not currently configured.
- **Morning digest email:** Sent to `dj@djaccounts.com` daily at 7am UK time via cron job.

### ⚠ Sending Emails with Attachments

`agentmail_helper.py` does **NOT** support attachments — its `send` command only accepts `to`, `subject`, `body`. To send emails with PDF attachments, use this pattern:

```python
import base64, json, urllib.request

def get_agentmail_key():
    with open("/root/.hermes/.env") as f:
        for line in f:
            line = line.strip()
            if line.startswith("AGENT_MAIL_API"):
                return line.split("=", 1)[1]
    return ""

def send_with_attachment(to, subject, body_text, pdf_path, pdf_filename):
    key = get_agentmail_key()
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode()
    data = json.dumps({
        "to": [to],
        "subject": subject,
        "text": body_text,
        "attachments": [{
            "filename": pdf_filename,
            "content": pdf_b64,
            "content_type": "application/pdf"
        }]
    }).encode()
    url = "https://api.agentmail.to/v0/inboxes/davidj@agentmail.to/messages/send"
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

The MCP AgentMail tools (`mcp_agentmail_send_message`) also support attachments via the `attachments` parameter with base64 `content` — prefer this when MCP tools are available.

### ⚠ Airtable list-records Does NOT Support --limit

The `airtable_api.py list-records` command does NOT accept a `--limit` flag. It always returns up to 100 records (`maxRecords=100`). To filter, use `filterByFormula` as the 4th argument:
```bash
python3 airtable_api.py list-records appzvmonQXs4x2All "Stock_Prices" "TICKER='BTC-GBP'"
```

## Slack — Posting TO Slack (Outbound)

The Geeves bot can post messages to Slack channels using `SLACK_BOT_TOKEN` and `SLACK_HOME_CHANNEL` from `/root/.hermes/.env`.

**Env vars:**
- `SLACK_BOT_TOKEN` — Bot OAuth token (starts with `xoxb-`)
- `SLACK_HOME_CHANNEL` — Channel ID (e.g. `C0B7C89HKQ9`)

**Pattern for posting a message:**
```python
import json, urllib.request

def slack_post(channel, text):
    with open("/root/.hermes/.env") as f:
        for line in f:
            line = line.strip()
            if line.startswith("SLACK_BOT_TOKEN="):
                token = line.split("=", 1)[1]
    data = json.dumps({"channel": channel, "text": text, "unfurl_links": False}).encode()
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())
```

Use Markdown formatting (`*bold*`, `• lists`, `:emoji:` names) for readable posts. Set `unfurl_links: False` to keep the message clean.

⚠ **Do NOT use `execute_code` in cron jobs** — write the script to `/tmp/` and run via `terminal`.

This is the outbound complement to `slack_capture.py` (which is Slack → Airtable inbound).

## Bulletin Data Collection

Daily data collection tables for the morning digest. **Full pipeline details, cron job config, email/Slack delivery, and pitfalls are in the `bulletin-agent` skill.** Load that skill for any bulletin work.

Local reference: `references/bulletin-setup.md`.

```bash
# Run all bulletin fetchers
python3 /root/Geeves/scripts/bulletin_fetch.py --write
```

Fact source rotates by day-of-year (day % 6): 0=Wikipedia, 1=NASA, 2=Quote Garden, 3=Zen, 4=Holidays, 5=Useless Facts. Full fallback chain if primary source fails.

## Cron Job Notes

- `repeat=0` in the cron tool means "forever" (infinite recurrence). The schedule field (e.g. `30m`) controls the interval.
- Cron timezone is UTC — adjust for UK time (UTC+0 winter / UTC+1 summer BST).
- Cron delivery: `deliver='origin'` sends the agent's final response back to the current chat. Omit for same same behavior.
- **⚠ `execute_code` is BLOCKED in cron jobs** — the sandbox is denied when no user is present. Use `write_file` to create a `.py` script in `/tmp/`, then `terminal` to run it. This is the standard pattern for cron Python work.
- **⚠ `execute_code` is BLOCKED in cron jobs** — the sandbox is denied when no user is present. Use `write_file` to create a `.py` script in `/tmp/`, then `terminal` to run it. This is the standard pattern for cron Python work.

## External Web Scraping — JS-Rendered Pages

Some websites (Goodreads, etc.) are fully JS-rendered SPAs that return empty HTML via `curl`/`urllib`. The `web_extract` tool uses a headless browser and works correctly.

**Pattern:** When scraping fails with empty HTML, try `web_extract(urls=[...])` instead. It returns structured markdown with the rendered page content.

**Goodreads specifically:**
- Search pages: JS-rendered, use `web_extract`
- Direct book pages (`/book/show/{id}`): work via `urllib` with proper headers
- Extract `ratingValue` and `ratingCount` from JSON-LD or meta tags in the HTML

## Restore & Migration Gotchas

See `references/restore-gotchas.md` for: himalaya asset naming, GPG key import on headless VPS, smart approval blocks on pipe-to-bash, Node.js in Ubuntu repos, SSH reload vs restart, OS version notes, and Airtable key handling.

## Slack Capture Loop

Script: `/root/Geeves/scripts/slack_capture.py` — classifies incoming Slack messages and writes structured data to the correct Airtable table. See `references/slack-capture.md` for architecture, classification rules, handlers, and pitfalls.

**Categories & routing:**
| Category | Trigger keywords | Target table |
|----------|-----------------|--------------|
| Person Note | met, person, friend, dietary, birthday, interests, gift, social, venue | People |
| Todo | todo, task, remind, need to, should, follow up | Todos |
| Memory | remember, note, log, history, previously | Memory_Summaries |
| Recipe | recipe, cook, cooking, bake, meal, dinner, lunch, breakfast, snack, dessert, ingredient, shopping list, dinner party, plan dinner, favourite recipe, email recipe, PDF recipe, mealie | Output_Log (Module=Recipe) |
| Film Club | film club, movie club, movie night, film night, just watched, finished watching, rated X/5, rated X/10, add to list, log the film | Films |
|| Restaurant | restaurant, went to, ate at, dinner at, lunch at, find me a restaurant, recommend a restaurant, booked, menu, fine dining, went out for, we ate, we went | Restaurants + Restaurant Visits |
|| **Fitness** | workout, gym, run, ran, cycling, bike, ride, swim, yoga, walk, trained, training, lift, cardio, weights, bench, squat, deadlift, press, HIIT, strava, peloton, energy X/5, difficulty X/5 | Workouts, Exercise Log, Cycling |
|| Module Request | party, travel, holiday, property, house, recommend, suggest | Output_Log (Module=General) |
| **Books** | book, reading, read, novel, author, audiobook, ebook, hardcover, paperback, goodreads, finished a book, want to read, add to reading list, started reading, gave up on, stopped reading, recommended book | Books |
| General | (fallback) | Skipped — no record |

**⚠ No raw message table for Slack capture.** One Slack message → one useful Airtable record in the correct table. General messages produce no record. The `Input Log` table exists for audit/debugging purposes but is not the primary capture path — David explicitly rejected capture-via-Input-Log as unnecessary bloat.

**⚠ No cron job for Slack capture.** Capture is real-time: David messages in Slack → Hermes classifies and writes to Airtable immediately. A cron loop adds latency and complexity with no benefit since Hermes is already listening.

**Film Club handler details:** Extracts film title, rating (1-10 scale — converts from X/5, X/10, stars, or "rated X"), watched-at (hosted/remote/cinema), and month. Auto-looks up IMDb data via OMDb (year, director, genre, rating, votes, metascore, URL). Creates 1 Films record with `Film Club = Yes`.

**Rating conversion:** The handler converts all rating formats to the 1-10 select: X/5 → doubled (4/5 = "8"), X/10 → used directly, ★★★★★ → "10", "rated X" or "gave it X" → scaled appropriately.

### ⚠ Pitfall: Classification Priority Overlap

Multiple categories can match the same keywords. The `max()` scorer picks the highest-scoring category, but when scores are tied, Python's `max()` returns the **first** matching entry — so **order matters**.

Known overlaps:
- **Film Club vs Module Request**: "film", "movie" → Film Club must appear BEFORE Module Request
- **Books vs Module Request**: "book", "read", "recommend" → Books must appear BEFORE Module Request (book recommendations overlap with Module Request's "recommend")
- **Books vs Film Club**: minimal overlap — Books should appear AFTER Film Club
- **Fitness vs Module Request**: "walk", "travel" → Fitness must appear BEFORE Module Request
- **Fitness vs Sleep/Habit**: "tired", "rest" → Sleep/Habit must appear BEFORE Fitness (sleep messages mention tiredness)
- **Meal vs Recipe**: "dinner", "lunch", "breakfast", "snack" → Recipe must appear BEFORE Meal (recipe requests mention meal types)

**Rule of thumb:** More specific categories should appear BEFORE more general ones. When adding a new category, check for keyword overlap with ALL existing categories and position accordingly.

### Name Extraction — Pitfalls

See `references/slack-capture.md` for regex details. Key pitfalls:

1. **Contractions must normalize BEFORE matching**: `"she's"` → `"she is"`, `"he's"` → `"he is"`.
2. **`re.IGNORECASE` breaks `[A-Z][a-z]+`**: Post-validate — if second word is lowercase, take only first word.
3. **Skip-word filter is essential**: Must include pronouns, common verbs, "David", "Geeves".
4. **Multiple pattern strategies needed**: "met X", "about/add X", "X's birthday", "X is/loves", "X birthday", "new person: X".

### Schema Migration Pattern

When changing field types on populated Airtable tables, the Metadata API cannot do it directly. See `references/schema-migration.md` for the full pattern including: reading data before migration, creating replacement fields, using `typecast=true` for select remapping, and the manual UI steps for cleanup.

## Morning Digest — Full Workflow

The daily digest is a cron-driven pipeline: fetch data → build HTML → generate PDF → email + Slack.

**Scripts involved (in order):**

| Step | Script | Output |
|------|--------|--------|
| 1. Fetch bulletin data | `bulletin_fetch.py --write` | Writes to Airtable (Weather, Stocks, Fact, Token Usage, Star Wars) |
| 2. Build HTML | `build_digest_html.py --save` | `/root/Geeves/digests/digest_YYYY-MM-DD.html` |
| 3. Generate PDF | `digest_to_pdf.py --file <html>` | `/root/Geeves/digests/digest_YYYY-MM-DD.pdf` |
| 4. Send email | AgentMail API (see attachment pattern above) | To `dj@djaccounts.com` with PDF attached |
| 5. Post to Slack | `chat.postMessage` API (see Slack pattern above) | To `SLACK_HOME_CHANNEL` |

**Data flow:** All bulletin data is fetched in parallel by `bulletin_fetch.py` and written to Airtable first. Then `build_digest_html.py` reads the latest records from Airtable to compose the digest. This two-step approach means the digest always uses persisted data.

**⚠ SINGLE SOURCE OF TRUTH:** `build_digest_html.py` is the **only** source for digest content. Both the email body AND the PDF are generated from the same HTML output. The cron job must NOT compose a separate plain text email — it reads the HTML from `build_digest_html.py` and sends it as the email body. This ensures the email and PDF always match exactly. Any change to digest layout, sections, or ordering is made in `build_digest_html.py` and automatically applies to both.

**⚠ Stock data may be from the previous day** — yfinance returns the most recent trading day's close. On weekends/holidays, stocks will show Friday's data. This is expected.

**Cron pattern:** Since `execute_code` is blocked in cron, write each step as a separate `.py` file to `/tmp/` and run via `terminal`. Chain them in a single cron job script or run as separate cron jobs with ordering.

## Bulletin Data Setup

See `references/bulletin-setup.md` for: API sources, field mappings, ticker config, table IDs, cron job details, and known pitfalls.

**⚠ Numbers API broken (as of ~2026-06):** `numbersapi.com` returns 404 on all endpoints. `fact_fetch.py` has a local fallback (calendar/date facts) so it won't crash, but Wikipedia and Useless Facts are the more reliable sources right now.

**⚠ Open-Meteo weather timeouts (intermittent):** `weather_fetch.py` can time out on the default 15s limit, causing the weather section of the digest to be empty. If the weather fetch fails, the digest is still composed and sent with the section skipped. Consider increasing the timeout or adding a retry with backoff in the fetcher script if this recurs.

**⚠ Cron timezone is UTC:** UK is UTC+0 (winter GMT) / UTC+1 (summer BST). To fire at 7am UK time year-round, use `0 6 * * *` in summer and `0 7 * * *` in winter — or just `0 6 * * *` and accept 6am delivery in winter.

## Token Usage Tracking

Script: `/root/Geeves/scripts/token_usage.py` — queries Hermes `state.db` for daily token usage and writes to Airtable.

| Table | Purpose | Table ID |
|-------|---------|----------|
| `Token_Usage` | Daily Hermes token consumption metrics | `tbl3EjtE3YW1ZUqEv` |

Fields: Date, Sessions, Input Tokens, Output Tokens, Cache Read Tokens, Total Active Tokens, Estimated Cost USD, Top Model, Summary.

```bash
python3 /root/Geeves/scripts/token_usage.py              # Yesterday's usage
python3 /root/Geeves/scripts/token_usage.py --today       # Today so far
python3 /root/Geeves/scripts/token_usage.py --days 7      # Last 7 days summary
python3 /root/Geeves/scripts/token_usage.py --write       # Write to Airtable (uses yesterday by default)
python3 /root/Geeves/scripts/token_usage.py --today --write  # Write today's usage
```

Data source: `/root/.hermes/state.db` → `sessions` table (columns: `input_tokens`, `output_tokens`, `cache_read_tokens`, `reasoning_tokens`, `estimated_cost_usd`, `model`).

**Included in the daily digest** — cron job runs `token_usage.py` alongside weather/stocks/facts, and the digest email shows prior day's token count.

## Provider Failover & API Key Stack

Geeves has a priority-ordered provider failover stack for LLM calls outside the Hermes gateway (scripts, cron jobs, application logic):

**File:** `/root/Geeves/lib/provider_failover.py` — `ProviderStack` class
**Companion:** `/root/Geeves/lib/api_usage_tracker.py` — `ApiTracker` class

Stack: OpenRouter → Groq → NVIDIA → Ollama (local). Tested and confirmed working (2026-06-02).

```python
from lib.provider_failover import ProviderStack
stack = ProviderStack()
reply = stack.chat("prompt")
# stack.last_provider, stack.last_model, stack.errors
```

See `hermes-provider-config` skill → `references/cross-provider-failover.md` for architecture, usage, and incident history.

**⚠ `command_allowlist` self-kill**: Ensure `config.yaml` does NOT contain `"stop/restart hermes gateway"` in the `command_allowlist` — this auto-approves gateway restarts from inside agent sessions, killing the gateway. See `hermes-provider-config` skill for the fix.

## SerpApi — Google Search

Script: `/root/Geeves/scripts/serpapi_search.py` — Google search via SerpApi (free tier: 250 searches/month).

```bash
# Web search
python3 /root/Geeves/scripts/serpapi_search.py "London weather" --num 3

# Google News headlines
python3 /root/Geeves/scripts/serpapi_search.py "UK news" --engine google_news --num 5
```

Key: `SERPAPI_KEY` in `/root/.hermes/.env`. Engines: `google`, `google_news`, `google_finance`.

## Garmin Connect Integration

Script: `/root/Geeves/scripts/garmin_fetch.py` — imports cycling from Garmin Connect → Baserow.

```bash
python3 garmin_fetch.py --days 7          # Dry run
python3 garmin_fetch.py --days 7 --write  # Write to Baserow
python3 garmin_fetch.py --backfill --write  # Backfill: one week at a time backwards
```

**Features:** Auto-retry on 429 rate limits, deduplication (date+route+distance), creates Workout + Cycling records.

**Cron:** Job `0d2ddb20ece8`, daily 7am UTC, `--backfill --write` mode.

**Baserow IDs:** Cycling=396, Workouts=392, People=359.

**Known issues:** Garmin rate-limits aggressively (auto-retry after 60s). Dual Garmin setup (bike=cycling, wrist=walking) imports correctly. 2FA may be needed on first login. Units auto-converted from meters/mps to miles/mph. People links not auto-tagged.

See `references/garmin-connect.md` for full details.

## Sensitivity Rules
- Sensitive fields (Phone, Email, Relationship Notes, Conversation Log) → Ollama only
- When sending People data to hosted model, pseudonymise names (PERSON_07 tokens)
- Never dump entire People table into a prompt — pull only what's needed

## Google Contacts Import

See `references/google-contacts-import.md` for the full technique: fetching all contacts via the People API with pagination, mapping Google fields to Geeves People table fields, and bulk-creating in batches of 10.
