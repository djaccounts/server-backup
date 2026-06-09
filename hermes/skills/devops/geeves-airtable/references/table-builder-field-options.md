# Airtable Table Builder — Field Type Options Reference

## Field Types Requiring `options` During Table Creation

The Airtable Metadata API rejects table creation if these field types don't include their required `options`:

| Field Type | Required Options | Example |
|---|---|---|
| `singleSelect` | `options.choices` array | `{"choices": [{"name": "Option1"}, {"name": "Option2"}]}` |
| `multipleSelects` | `options.choices` array | Same as singleSelect |
| `checkbox` | `options.icon` + `options.color` | `{"icon": "check", "color": "greenBright"}` |
| `date` | `options.dateFormat` | `{"dateFormat": {"name": "local"}}` |
| `number` | `options.precision` | `{"precision": 0}` for integers, `{"precision": 1}` for 1 decimal |
| `rating` | `options.max` + `options.icon` + `options.color` | `{"max": 5, "icon": "star", "color": "yellowBright"}` |
| `multipleRecordLinks` | `options.linkedTableId` | `{"linkedTableId": "tblXXXXX"}` — can be included in table creation OR added via `add_field()` after both tables exist. If creation fails, fall back to `add_field()`. |

**Error without options:** `INVALID_FIELD_TYPE_OPTIONS_FOR_CREATE` (422)

**⚠ `longText` is NOT a valid API field type.** The Airtable UI shows "Long text" but the API requires `multilineText`. Using `longText` in API calls causes 422 INVALID_REQUEST_UNKNOWN. Always use `multilineText` in table_builder.py and direct API calls.

## ⚠ Select Field Options Corruption — Known Bug

When creating tables with `singleSelect` or `multipleSelects` fields via `table_builder.py`, the select options may silently corrupt — the field is created with a single option `choices` instead of the actual list. This is a known bug in the `build_field_payload()` → `create_table()` path.

**Immediate post-creation check:** Always run `python3 table_builder.py --schema` after creating a table with select fields. Verify the choice lists are correct.

**If corrupted:** The table must be manually deleted from the Airtable web UI and recreated. The API cannot fix or delete corrupted select fields.

**Workaround:** Exclude select fields from initial table creation. Create the table with only simple types (text, date, number, attachment, checkbox), then add select fields via separate `add_field()` calls. This path is more reliable.

## Implementation in table_builder.py

The `build_field_payload()` function in `/root/Geeves/scripts/table_builder.py` handles these mappings. When adding a new field type, add its options logic there.

## Recipe Module Tables — Creation Order

When creating tables with inter-table links:
1. Create all base tables first (without `multipleRecordLinks` fields)
2. Collect the returned table IDs
3. Add link fields in a second pass using `add_field()`

This is the pattern used in `create_recipe_tables()`.
