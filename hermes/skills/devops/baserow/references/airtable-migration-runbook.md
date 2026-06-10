# Baserow — Airtable Migration Runbook

## Status (June 2026) — ✅ MIGRATION COMPLETE

All data and scripts have been migrated from Airtable to Baserow. Airtable is no longer used as the system of record.

## What's Migrated

| Component | File | Status |
|-----------|------|--------|
| `baserow_api.py` | `/root/Geeves/scripts/baserow_api.py` | ✅ Full CRUD with field name resolution |
| `baserow_mapping.json` | `/root/Geeves/baserow_mapping.json` | ✅ 41 tables, all fields mapped |
| `table_builder.py` | `/root/Geeves/scripts/table_builder.py` | ✅ Rewritten for Baserow Platform API (JWT, table/field CRUD, schema compare) |
| `slack_capture.py` | `/root/Geeves/scripts/slack_capture.py` | ✅ Migrated and tested live |
| `weather_fetch.py` | `/root/Geeves/scripts/weather_fetch.py` | ✅ Migrated and tested write |
| `stocks_fetch.py` | `/root/Geeves/scripts/stocks_fetch.py` | ✅ Migrated (fixed `number_negative` constraint) |
| `fact_fetch.py` | `/root/Geeves/scripts/fact_fetch.py` | ✅ Migrated and tested write |
| `token_usage.py` | `/root/Geeves/scripts/token_usage.py` | ✅ Migrated and tested write |
| `bulletin_fetch.py` | `/root/Geeves/scripts/bulletin_fetch.py` | ✅ Updated |
| `bulletin_fetch_parallel.py` | `/root/Geeves/scripts/bulletin_fetch_parallel.py` | ✅ Updated |
| Baserow deployment | Docker + Nginx | ✅ Live at http://77.68.33.121 |
| Skill SKILL.md files | `~/.hermes/skills/devops/*/` | ✅ Updated (Baserow as system of record) |
| Cron jobs | 4 active jobs | ✅ Updated |
| AGENTS.md | `/root/Geeves/AGENTS.md` | ✅ Updated |
| Data verification | Full schema + row count comparison | ✅ Schema perfect, 35/40 row counts match (5 diffs = new data from scripts) |

## Post-Import Data Reconciliation

The initial Airtable→Baserow import was **partial** for some tables (Properties, Books, Workouts, Cycling lost rows). A second pass re-imported the missing data:

### Re-import Pattern

For each table needing reconciliation:

1. **Delete all existing Baserow rows** (Baserow API: paginate to get row IDs, then `DELETE` each)
2. **Fetch all rows from Airtable** (Airtable API: offset-based pagination)
3. **Transform values**:
   - Number fields: round to `number_decimal_places` (e.g., 0 decimal places → `int()`, 2 → `round(v, 2)`)
   - Select options: convert name strings → Baserow option IDs (lookup via field metadata)
   - Multi-select: convert name list → option ID list
   - Linked rows: skip in first pass, update via PATCH in second pass (needs ID remapping)
   - Dates: truncate to `YYYY-MM-DD`
   - Ratings: `int(round(value))`
4. **Create rows in Baserow** via `baserow_post()` (Database Token auth)
5. **Second pass for link fields**: remap Airtable record IDs → Baserow row IDs, PATCH link fields

### Decimal Place Gotcha

Airtable stores numbers with arbitrary precision. Baserow number fields have fixed `number_decimal_places`. Sending `7.5` to a field with `number_decimal_places: 0` causes:
```
ERROR_REQUEST_BODY_VALIDATION: Ensure that there are no more than 0 decimal places.
```
**Fix**: Read field constraints from `GET /api/database/fields/table/{id}/`, round values before writing.

### Select Option ID Gotcha

Baserow select option IDs are auto-incrementing integers (e.g., `1455`). The mapping file's `select_options` array stores both `value` (name) and `id`. Always resolve name → ID when writing rows.

### Linked Row ID Remapping

Airtable record IDs (`recXXXXXXXX`) and Baserow row IDs are completely different. When re-importing linked data:
- First pass: create all rows, build `at_id → bw_id` map
- Second pass: PATCH link fields using the ID map

## table_builder.py — What It Does Now

Rewritten from Airtable Metadata API to Baserow Platform API. Key changes:

| Feature | Old (Airtable) | New (Baserow) |
|---------|-----------------|-----------------|
| Auth | `AIRTABLE_API_KEY` | JWT via `/api/user/token-auth/` |
| Table creation | `POST /meta/bases/{id}/tables` | `POST /api/database/tables/database/132/` |
| Field creation | `POST /meta/bases/{id}/tables/{tid}/fields` | `POST /api/database/fields/table/{tid}/` |
| Table listing | `GET /meta/bases/{id}/tables` | `GET /api/database/tables/database/132/` |
| Table deletion | Not supported | `DELETE /api/database/tables/{id}/` ✅ |
| Schema check | N/A | `--check` and `--schema` flags |
| `--fix` | Create Airtable tables | Create Baserow tables |
| Module scaffolding | Same | Same |

See SKILL.md for full Platform API field type mapping and payloads.

## What's Still on Airtable (Legacy — Read Only)

| Component | File | Notes |
|-----------|------|-------|
| `airtable_api.py` | `/root/Geeves/scripts/airtable_api.py` | Legacy reference, not used |
| `schema_checker.py` | `/root/Geeves/scripts/schema_checker.py` | Legacy Airtable registry sync |

Airtable itself still exists as read-only backup at `appzvmonQXs4x2AlL`.

## Baserow API Key

- **Type**: Database token (not JWT)
- **Location**: `/root/.hermes/.env` as `BASEROW_API_TOKEN`
- **Auth header**: `Authorization: Token <key>`
- **Permissions**: Full CRUD on Geeves database (id=132)

## Baserow Admin

- **Email**: daverj1987@gmail.com
- **Password**: TempPass123! (should be changed)
- **JWT login**: `POST /api/user/token-auth/` with email + password

## Known Import Limitations

- Airtable `currency` → Baserow `number` with `number_prefix: "£"` (functionally equivalent)
- Airtable phone cells with Unicode direction markers (`\u202a`) fail validation and are left empty
- Airtable automations and interfaces are not imported (Baserow doesn't support them)
- Initial import may be partial — always verify row counts after import
- Rating fields need `max_value` set explicitly during creation

## Rollback Plan

If Baserow migration causes issues:
1. Airtable base is still intact (import was a copy — base `appzvmonQXs4x2AlL`)
2. `airtable_api.py` still works
3. Switch scripts back to Airtable imports
4. No data loss — both systems have copies
