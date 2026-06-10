---
name: baserow
description: "Baserow self-hosted no-code database. Use when managing, configuring, or migrating data to/from Baserow. Covers: Docker deployment, Nginx reverse proxy setup, Airtable import, API usage, and troubleshooting."
version: 1.1.0
author: OWL
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [baserow, database, self-hosted, docker, nginx, airtable-migration]
    related_skills: [hermes-dev-admin, geeves-airtable]
---

# Baserow — Self-Hosted No-Code Database

Baserow is an open-source no-code database platform. Self-hosted on the VPS at `http://77.68.33.121`.

## Current Deployment

| Property | Value |
|----------|-------|
| URL | http://77.68.33.121 |
| Version | 2.2.2 (all-in-one) |
| Docker | `baserow/baserow:2.2.2` |
| Compose | `/root/baserow/docker-compose.yml` |
| Volume | `baserow_data` |
| Internal port | 8080 (Nginx proxies to it) |
| Admin email | daverj1987@gmail.com |
| Workspace | Geeves (id=95) |
| Database ID | 132 |
| API Token | `BASEROW_API_TOKEN` in `/root/.hermes/.env` |
| Tables | 41 (imported from Airtable June 2026) |

## Mapping File

**`/root/Geeves/baserow_mapping.json`** — auto-generated file mapping table names → IDs and field names → `field_XXXX` IDs. Used by `baserow_api.py` for auto-resolution. Regenerate after schema changes:

```bash
python3 /root/Geeves/scripts/baserow_api.py refresh-mapping
# Or manually via JWT: query /api/database/tables/database/132/ + /api/database/fields/table/{id}/
```

## Nginx + Docker Security

### ⚠️ Docker Bypasses UFW
Docker publishes ports directly, **bypassing UFW**. Fix: bind to localhost only when not public:
```bash
-p 127.0.0.1:9925:9000  # ✅ Localhost only
-p 9925:9000             # ❌ Public (bypasses UFW)
```
Verify: `ss -tlnp | grep :PORT` — `127.0.0.1` = localhost only, `0.0.0.0` = public.

### Nginx Path Routing Order
More specific paths MUST come BEFORE `location /`. Nginx processes prefix matches in order.

### SPAs Under a Path (Mealie under /mealie/)
Use `sub_filter` to rewrite HTML asset paths. Trailing slash on `proxy_pass` strips the prefix.

## Baserow API

### Two APIs — Know Which to Use

Baserow has **two separate APIs** with different auth and capabilities:

| API | Auth | Capabilities | Base Path |
|-----|------|--------------|-----------|
| **Database API** | `Token <key>` from `BASEROW_API_TOKEN` env var | Row CRUD, field read, search | `/api/database/rows/`, `/api/database/fields/` |
| **Platform API** | JWT via `POST /api/user/token-auth/` | Table CRUD, field CRUD, user management, everything | `/api/database/tables/`, `/api/database/fields/`, `/api/user/` |

**⚠️ Critical:** The Database Token **cannot** create or delete tables. It **cannot** list tables either. For any schema changes (tables/fields), you MUST use the Platform API with JWT auth.

### Authentication

**Database Token (for row operations):** `Authorization: Token <key>` in `BASEROW_API_TOKEN` env var. Works for row CRUD, field read, search.

**JWT Token (for schema operations):** Login via `POST /api/user/token-auth/` with email/password. Returns `token` field. Use as `Authorization: JWT <token>`. Works for ALL endpoints.

### Field Type Mapping (Airtable → Baserow)

When migrating table definitions or creating new tables, use these Baserow Platform API field types:

| Airtable type | Baserow type | Notes |
|---|---|---|
| `singleLineText` | `text` | |
| `multilineText` | `long_text` | |
| `singleSelect` | `single_select` | Use `select_options` array with `{"value": "...", "color": "..."}` |
| `multipleSelects` | `multiple_select` | Same `select_options` format |
| `multipleRecordLinks` | `link_row` | Use `link_row_table_id` (integer) |
| `checkbox` | `boolean` | |
| `number` | `number` | Requires `number_decimal_places` and `number_negative` in payload |
| `currency` | `number` | Baserow has no separate currency type. Use `number_prefix: "£"` for currency display. |
| `date` | `date` | Requires `date_format: "ISO"`, `date_include_time: false` |
| `url` | `url` | |
| `email` | `email` | |
| `phoneNumber` | `phone_number` | |
| `rating` | `rating` | Requires `max_value` (e.g., 5 or 10) |
| `createdTime` | `created_on` | Auto-managed, skip in creation |
| `lastModifiedTime` | `last_modified` | Auto-managed, skip in creation |

**Select option colors** (cycle through): `red-light`, `orange-light`, `yellow-light`, `green-light`, `blue-light`, `purple-light`, `pink-light`, `gray-light`

### Platform API Endpoints (JWT auth required)

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List tables | GET | `/api/database/tables/database/{databaseId}/` |
| Create table | POST | `/api/database/tables/database/{databaseId}/` + `{"name": "..."}` |
| Delete table | DELETE | `/api/database/tables/{tableId}/` |
| List fields | GET | `/api/database/fields/table/{tableId}/` |
| Create field | POST | `/api/database/fields/table/{tableId}/` + field payload |
| Delete field | DELETE | `/api/database/fields/{fieldId}/` |
| Update field | PATCH | `/api/database/fields/{fieldId}/` + partial payload |
| JWT login | POST | `/api/user/token-auth/` + `{"email": "...", "password": "..."}` |

### Row Operations (Database Token auth)

| Operation | Endpoint | Notes |
|-----------|----------|-------|
| List | `GET /api/database/rows/table/{id}/?size=N` | Paginated |
| Create | `POST /api/database/rows/table/{id}/` | Body: `{field_XXXX: value}` |
| Update | `PATCH /api/database/rows/table/{id}/{row_id}/` | Body: `{field_YYYY: value}` |
| Delete | `DELETE /api/database/rows/table/{id}/{row_id}/` | Returns 204 |
| Search | `GET /api/database/rows/table/{id}/?search=term` | Full-text |

## Data Verification & Reconciliation

After any Airtable→Baserow import, verify with a full comparison:

1. **Schema check**: `python3 scripts/table_builder.py --check` — compares field names, types, and select options
2. **Row count check**: accurate pagination-based counting for all 40 tables
3. **Reconciliation**: see `references/reimport-pattern.md` for the delete-all + re-import pattern with proper decimal rounding and select option handling

**Known gotchas for data re-import:**
- **Decimal places**: Baserow number fields have fixed `number_decimal_places`. Airtable values with more decimals cause 400 errors. Fix: `round(value, decimal_places)` or `int(round(value))` for 0 decimals. **The `baserow_api.py` `resolve_fields` does NOT round — the caller must pre-round all number values.**
- **Select option IDs**: Must resolve name → Baserow option ID before writing. Use mapping file `select_options` array. **⚠️ Do NOT pre-resolve select options then pass to `baserow_post`** — `resolve_fields` will try to resolve already-resolved IDs again, causing 400 errors. Pass raw option NAMES to `baserow_post` and let `resolve_fields` handle the ID lookup.
- **Linked row IDs**: Airtable record IDs ≠ Baserow row IDs. Two-pass approach: create all rows first (build ID map), then PATCH link fields.
- **Auto fields**: Skip `Created`, `Last Modified`, `created_on`, `last_modified` when importing.
- **Empty date strings**: Baserow date fields reject empty strings with "Date has wrong format". Always skip empty/null date values — never send `""` to a date field.
- **Airtable data may contain duplicates**: Some Airtable tables (e.g., Properties) have value-level duplicates (same field values, different record IDs). Baserow will faithfully replicate these. This is expected, not a bug.
- **Shell escaping with API tokens**: Tokens containing `)` break bash interpolation. Always read tokens from files in Python scripts: `open("/tmp/token.txt").read().strip()`. Never use `$TOKEN` in curl commands.

### Accurate Row Counting

The Baserow API `count` parameter is unreliable. Use pagination:

```python
# Baserow: page-based pagination
def bw_count_rows(table_id, token):
    total, page = 0, 1
    while True:
        url = f"http://77.68.33.121/api/database/rows/table/{table_id}/?page={page}&size=100"
        req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            total += len(result.get("results", []))
            if not result.get("next"):
                break
            page += 1
    return total

# Airtable: offset-based pagination
def at_count_rows(table_id, token):
    total, offset = 0, None
    while True:
        url = f"https://api.airtable.com/v0/{AT_BASE}/{table_id}?pageSize=100"
        if offset: url += f"&offset={offset}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            total += len(result.get("records", []))
            offset = result.get("offset")
            if not offset: break
    return total
```

### ⚠️ Critical Pitfalls

0. **Two APIs, two auth methods** — Database Token for row CRUD, JWT for table/field CRUD. Using the wrong auth gives 401 or 403.
1. **Field writes require `field_XXXX` IDs** — NOT field names. Use `baserow_api.py` helper.
2. **Select options must match exactly** — Writing unknown values fails silently.
3. **Number field `number_negative` constraint** — Airtable imports may set `False` on fields needing negatives (e.g., stock price changes). Causes 400 `min_value` error. Fix via JWT PATCH to `/api/database/fields/{id}/` with `{"number_negative": true}`.
4. **204 on DELETE** = success, not error. 404 on delete = already deleted (also OK).
5. **Database token can't list tables** — Use JWT for `/api/database/tables/database/{id}/`.
6. **Nginx path order** — Specific paths (`/mealie/`) MUST come before generic (`/`) in Nginx config.
7. **Link fields auto-create reverse links** — When creating a `link_row` field, Baserow automatically creates a reverse field on the linked table. This is normal.

## Airtable → Baserow Type Mapping (complete)

When migrating table definitions or comparing schemas, use this full mapping:

| Airtable type | Baserow type | Notes |
|---|---|---|
| `singleLineText` | `text` | |
| `multilineText` | `long_text` | |
| `singleSelect` | `single_select` | `select_options` not `choices` |
| `multipleSelects` | `multiple_select` | Same format |
| `multipleRecordLinks` | `link_row` | `link_row_table_id` (int) |
| `checkbox` | `boolean` | |
| `number` | `number` | Requires `number_decimal_places` + `number_negative` |
| `currency` | `number` | Use `number_prefix: "£"` for currency display. Baserow has no separate currency type. |
| `date` | `date` | Requires `date_format` + `date_include_time` |
| `url` | `url` | |
| `email` | `email` | |
| `phoneNumber` | `phone_number` | |
| `rating` | `rating` | Requires `max_value` |
| `createdTime` | `created_on` | Auto-managed |
| `lastModifiedTime` | `last_modified` | Auto-managed |
| `multipleAttachments` | `file` | |
| `singleCollaborator` | `created_by` | Auto-managed |

## Airtable Migration

### Import via API Job
`POST /api/jobs/` with `type: "airtable"` and a publicly shared Airtable base URL. Poll `GET /api/jobs/{id}/` for status.

### Migration Status (June 2026) — ✅ COMPLETE
- ✅ 41 tables imported, `baserow_api.py` helper, all scripts migrated
- ✅ `slack_capture.py` — migrated to Baserow
- ✅ `bulletin_fetch.py` and `bulletin_fetch_parallel.py` updated
- ✅ All fetch scripts migrated (weather, stocks, fact, token_usage)
- ✅ Skills and cron jobs updated
- ✅ `table_builder.py` — rewritten for Baserow Platform API (JWT auth, table/field CRUD)
- ✅ `geeves-airtable` skill marked as legacy
- ✅ Data reconciliation — re-imported missing rows (Properties, Books, Workouts, Cycling) with decimal + select option handling
- ✅ Full row-count verification: 35/40 tables match exactly; 5 have expected diffs (Baserow has newer live data)
- ⏳ `build_digest_html.py`, `build_weekly_digest_html.py` — still read from Airtable (low priority — display only)

### Post-Import Fixes
After import, check: number fields (negative allowed?), select options (all present?), linked records (table IDs correct?). Fix via JWT PATCH.

## Comparing Airtable ↔ Baserow

Use `references/compare_schemas.py` for full schema + row count comparison:

```bash
python3 ~/.hermes/skills/devops/baserow/references/compare_schemas.py
```

This script:
- Compares all table names, field names, field types, and select options
- Reports MISSING, EXTRA, TYPE MISMATCH, and OPTIONS diffs
- Compares row counts using accurate pagination (not the unreliable `count` parameter)

**Known import limitations:**
- Airtable `currency` → Baserow `number` with `number_prefix: "£"` (functionally equivalent)
- Airtable phone cells with Unicode direction markers (`\u202a`) may fail validation and be left empty
- Import can be **partial** — verify row counts after import
- Rating fields, select options, and link fields may need post-import fixes via JWT PATCH

## Scripts Using Baserow (`/root/Geeves/scripts/`)

| Script | Purpose |
|--------|---------|
| `baserow_api.py` | CRUD helper with field name→ID resolution |
| `table_builder.py` | Table/field creation via Platform API (JWT auth) — for new modules |
| `slack_capture.py` | Slack → Baserow |
| `weather_fetch.py` | London weather → Weather_Data |
| `stocks_fetch.py` | Stock prices → Stock_Prices |
| `fact_fetch.py` | Daily fact → Fact_of_the_Day |
| `token_usage.py` | Hermes usage → Token_Usage |
| `bulletin_fetch.py` | Master sequential fetch |
| `bulletin_fetch_parallel.py` | Master parallel fetch |

## Platform API Reference

See `references/baserow-platform-api.md` for field payloads, auth patterns, and common errors.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Site not found" | Host header / BASEROW_PUBLIC_URL mismatch | Check Nginx proxy_set_header |
| 401 on tables list | DB token can't access | Use JWT |
| 400 `min_value` | `number_negative=False` | PATCH with JWT |
| Select write fails | Unknown option value | Use exact option name |
