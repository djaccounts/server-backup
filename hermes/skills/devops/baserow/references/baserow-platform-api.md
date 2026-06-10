# Baserow Platform API — Field Creation Reference

## Auth

JWT token required for all table/field operations:

```python
import json, urllib.request

def get_jwt():
    data = json.dumps({"email": "daverj1987@gmail.com", "password": "TempPass123!"}).encode()
    req = urllib.request.Request("http://77.68.33.121/api/user/token-auth/",
        data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["token"]
```

## Table Operations

```python
JWT = "Authorization: JWT <token>"
DB_ID = 132

# List tables
GET /api/database/tables/database/132/

# Create table
POST /api/database/tables/database/132/
Body: {"name": "My Table"}

# Delete table
DELETE /api/database/tables/{table_id}/
```

## Field Operations

```python
# List fields
GET /api/database/fields/table/{table_id}/

# Create field
POST /api/database/fields/table/{table_id}/
Body: see field payloads below

# Delete field
DELETE /api/database/fields/{field_id}/

# Update field
PATCH /api/database/fields/{field_id}/
Body: partial field payload
```

## Field Payloads (tested & confirmed)

### Text
```json
{"name": "My Text", "type": "text"}
```

### Long Text
```json
{"name": "My Notes", "type": "long_text"}
```

### Number (with decimal places)
```json
{"name": "Price", "type": "number", "number_decimal_places": 2, "number_negative": true}
```
⚠️ `number_decimal_places` and `number_negative` are REQUIRED. Omitting them causes 400.

### Date
```json
{"name": "Start Date", "type": "date", "date_format": "ISO", "date_include_time": false}
```
⚠️ `date_format` and `date_include_time` are REQUIRED for date fields.

### Single Select
```json
{"name": "Priority", "type": "single_select", "select_options": [
    {"value": "Low", "color": "green-light"},
    {"value": "Medium", "color": "yellow-light"},
    {"value": "High", "color": "red-light"}
]}
```
⚠️ `select_options` must be an array of `{"value": str, "color": str}` objects, NOT `{"choices": [...]}` (that's Airtable format).

### Multiple Select
```json
{"name": "Tags", "type": "multiple_select", "select_options": [
    {"value": "Urgent", "color": "red-light"},
    {"value": "Review", "color": "blue-light"}
]}
```

### Checkbox
```json
{"name": "Done", "type": "boolean"}
```

### Link Row (linked table)
```json
{"name": "Person", "type": "link_row", "link_row_table_id": 359}
```
⚠️ Auto-creates a reverse link field on the target table. This is normal Baserow behavior.

### URL
```json
{"name": "Website", "type": "url"}
```

### Email
```json
{"name": "Contact Email", "type": "email"}
```

### Phone
```json
{"name": "Phone", "type": "phone_number"}
```

### Rating
```json
{"name": "My Rating", "type": "rating", "max_value": 10}
```
⚠️ `max_value` is REQUIRED.

### Created Time (auto)
```json
{"name": "Created", "type": "created_on"}
```
Auto-managed by Baserow. Skip during manual field creation unless specifically needed.

## Auto-managed Fields (skip in creation)
- `created_on` — auto
- `last_modified` — auto
- `created_by` — auto

## Color Options for Select Fields
Any valid Baserow color: `red-light`, `orange-light`, `yellow-light`, `green-light`, `blue-light`, `purple-light`, `pink-light`, `gray-light`, `red-dark1`, `orange-dark1`, `yellow-dark1`, `green-dark1`, `blue-dark1`, `purple-dark1`, `pink-dark1`, `gray-dark1`

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 401 "Authentication credentials were not provided" | Using DB token instead of JWT | Switch to JWT auth |
| 400 on number field | Missing `number_decimal_places` or `number_negative` | Add both fields to payload |
| 400 on date field | Missing `date_format` / `date_include_time` | Add `date_format: "ISO"`, `date_include_time: false` |
| 400 on rating field | Missing `max_value` | Add `max_value: N` |
| 204 on delete | This is SUCCESS, not error | Check response code, not body |
