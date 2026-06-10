# Airtable → Baserow Re-import Pattern

Use this when Baserow tables have fewer rows than Airtable (partial import) or after schema changes require data migration.

## The Reliable Pattern

1. **Extract tokens to files first** (avoids shell escaping issues with `)` in tokens):
   ```bash
   grep BASEROW_API_TOKEN /root/.hermes/.env | cut -d= -f2 > /tmp/bw_token.txt
   grep AIRTABLE_API_TOKEN /root/.hermes/.env | cut -d= -f2 > /tmp/at_key.txt
   ```

2. **Delete ALL existing Baserow rows** — loop until count is 0:
   ```python
   def delete_all_until_empty(tid, token):
       for attempt in range(30):
           ids = fetch_all_row_ids(tid, token)  # paginate
           if not ids: return attempt
           for rid in ids:
               DELETE /api/database/rows/table/{tid}/{rid}/
   ```

3. **Fetch all Airtable rows** via offset pagination (100 per page)

4. **Transform values** before sending to Baserow:
   - Numbers: `round(value, decimal_places)` using Baserow field's `number_decimal_places`
   - Select options: pass raw NAME (not ID) — `resolve_fields` handles ID lookup
   - Dates: truncate to `YYYY-MM-DD`, skip empty strings
   - Linked rows: skip (AT IDs ≠ BW IDs)
   - Auto fields: skip `Created`, `Last Modified`

5. **Create rows** via direct API call (not `baserow_post` — avoids double-resolution bug):
   ```python
   # Convert field names to field_XXXX
   bw_fields = {f"field_{finfo[fname]['id']}": value for fname, value in fields.items()}
   POST /api/database/rows/table/{tid}/ with bw_fields
   ```

6. **Verify**: count rows in both systems, check for value-level duplicates

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Bash `)` in token | `syntax error near unexpected token` | Read tokens from files in Python, never use `$TOKEN` in curl |
| Double select resolution | 400 error | Pass raw option names, not pre-resolved IDs |
| Decimal places | `max_decimal_places` 400 error | `round(value, decimal_places)` before sending |
| Empty date strings | "Date has wrong format" 400 error | Skip empty/null date values |
| `baserow_post` double-resolution | Select options fail | Use direct API calls with `field_XXXX` keys |
| Airtable value duplicates | More rows than expected | Expected — some AT tables have duplicates |

## Verification Script Template

```python
# After import, verify:
# 1. Row counts match
at_count = len(at_fetch_all(at_id))  # offset pagination
bw_count = count_rows(bw_id)  # page pagination

# 2. No unexpected duplicates
all_rows = fetch_all_rows(bw_id)
seen, dupes = set(), 0
for row in all_rows:
    key = "|".join(f"{k}:{v}" for k,v in sorted(row.items()) if k not in ("id","order"))
    if key in seen: dupes += 1
    seen.add(key)
```
