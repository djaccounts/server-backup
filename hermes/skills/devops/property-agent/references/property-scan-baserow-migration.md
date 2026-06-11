# Property Scan — Baserow Migration Notes

## Migration Summary (June 2026)

The property scan script (`property_scan_firecrawl.py`) was migrated from Airtable to Baserow. Key changes:

### Before (Airtable)
- Used `AIRTABLE_API_KEY` from `.env`
- Wrote to Airtable base `appzvmonQXs4x2AlL`, table `tblA0jfgqxhPFJU7S`
- Used `airtable_request()` function with Airtable REST API

### After (Baserow)
- Uses `BASEROW_API_TOKEN` from `.env`
- Writes to Baserow table ID `380` (Properties), table ID `381` (Property Criteria)
- Uses `baserow_api.py create-row` subprocess calls for proper field resolution
- Uses `baserow_api.py list-rows --json` for reading existing records

### Critical Implementation Details

1. **Always use `baserow_api.py` helper** for writes — it handles:
   - Field name → `field_XXXX` ID resolution
   - Select option name → option ID resolution
   - Proper JSON encoding

2. **Never use direct Baserow API for writes** — select options sent as string names (not IDs) fail silently

3. **Deduplication** — fetch existing Rightmove IDs via `list-rows --json`, then filter new properties client-side

4. **Date handling** — `First Seen` field uses `datetime.now().strftime("%Y-%m-%d")` (naive date string)

### Table IDs

| Table | Baserow ID | Legacy Airtable ID |
|-------|-----------|-------------------|
| Properties | 380 | tblA0jfgqxhPFJU7S |
| Property Criteria | 381 | tbl6oeRjhK3sds99TI |

### Exclusion Rules (hard-coded in scan script)
- Dudley Road — always exclude
- Queen Elizabeth Drive — exclude (too much refurb)
- No repeats (dedup by Rightmove ID)
