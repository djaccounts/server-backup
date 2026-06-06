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
| `multipleRecordLinks` | `options.linkedTableId` | `{"linkedTableId": "tblXXXXX"}` |

**Error without options:** `INVALID_FIELD_TYPE_OPTIONS_FOR_CREATE` (422)

## Implementation in table_builder.py

The `build_field_payload()` function in `/root/Geeves/scripts/table_builder.py` handles these mappings. When adding a new field type, add its options logic there.

## Recipe Module Tables — Creation Order

When creating tables with inter-table links:
1. Create all base tables first (without `multipleRecordLinks` fields)
2. Collect the returned table IDs
3. Add link fields in a second pass using `add_field()`

This is the pattern used in `create_recipe_tables()`.
