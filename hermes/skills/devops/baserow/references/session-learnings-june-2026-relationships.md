# Session Learnings — June 2026 (Relationships Module + Contacts Sync)

## New Tables Created (June 2026)

| Table | ID | Fields | Notes |
|-------|-----|--------|-------|
| Occasions | 403 | Person (link), Occasion Type (single_select), Date, Recurring (bool), Remind Days Before (number), Extra Notes | Auto-created "Notes" field renamed to "Extra Notes" |
| Gift Ideas | 404 | Person (link), Idea (long_text), Estimated Cost (single_select), Occasion (text), Status (single_select), Extra Notes | Same Notes rename |
| Gift History | 405 | Person (link), Gift (long_text), Occasion (text), Date Given, Rating (1-5), Extra Notes | Same Notes rename |
| Social Log | 406 | Date, Type (single_select), Person (link), Summary, Key Things to Remember, Follow-up, Source (single_select) | Merged from Conversation Log |

## Baserow API Gotchas Discovered

### Auto-created "Notes" Field
When creating a table via the Platform API, Baserow auto-creates a "Notes" field. If you also try to add a "Notes" field explicitly, you get `ERROR_FIELD_WITH_SAME_NAME_ALREADY_EXISTS`. Fix: after creating a table, list fields via JWT GET and rename the auto-created one via JWT PATCH (e.g., to "Extra Notes").

### write_file Tool Truncation
The `write_file` tool truncates lines containing `~` (tilde) in paths. Use `os.path.join(os.path.expanduser("~"), ".hermes", "file")` instead of `~/.hermes/file` in strings that will be written. Alternatively, use `cat > file << 'EOF'` via terminal for complex scripts.

### Baserow `phone_number` Field Strict Validation
Baserow's `phone_number` field type rejects spaces, dashes, parentheses, and other formatting characters. Strip to digits-only before writing:
```python
def clean_phone(phone):
    if not phone:
        return ""
    cleaned = phone.strip()
    if cleaned.startswith("+"):
        return "+" + "".join(c for c in cleaned[1:] if c.isdigit())
    return "".join(c for c in cleaned if c.isdigit())
```

### Baserow `date` Field Requires Valid Year
Year `0000` is rejected. Use `1900` as default for yearless dates (e.g., birthdays from Google Contacts in MM-DD format → `1900-MM-DD`).

### Google OAuth Token Exchange
Requires `application/x-www-form-urlencoded` content type, NOT JSON. Both refresh_token and code exchange endpoints need this:
```python
data = urllib.parse.urlencode({
    "client_id": creds["client_id"],
    "client_secret": creds["client_secret"],
    "refresh_token": creds["refresh_token"],
    "grant_type": "refresh_token"
}).encode()
req = urllib.request.Request(url, data=data, headers={
    "Content-Type": "application/x-www-form-urlencoded"
}, method="POST")
```

### Google OAuth Refresh Token Revocation
If the refresh token is revoked or expired, the token exchange returns `{"error": "invalid_grant"}`. This requires full re-consent via the OAuth consent screen URL — a new refresh token cannot be obtained without user interaction.

### Cron Job `repeat` Parameter
- `repeat: 0` means forever (recurring)
- `repeat: 1` means once
- `schedule` field uses cron expression format (`0 8 * * *`), NOT natural language

### Baserow Max Page Size
`?size=1000` returns HTTP 400. Always use `?size=100&page=N` for pagination.

## Select Field Response Shapes
When reading Baserow data via `baserow_api.py --json` or direct API:
- `single_select` fields return `{"id": N, "value": "...", "color": "..."}` dicts, NOT plain strings
- `link_row` fields return `[{"id": N, "value": "...", "order": "..."}]` lists of dicts

Use helper functions:
```python
def extract_select_value(field_val):
    if isinstance(field_val, dict):
        return field_val.get("value", "")
    return field_val or ""

def extract_link_id(field_val):
    if isinstance(field_val, list) and field_val:
        item = field_val[0]
        if isinstance(item, dict):
            return item.get("id")
        return item
    if isinstance(field_val, dict):
        return field_val.get("id")
    return field_val
```

## Recurring Date Logic for Occasions
For recurring occasions (birthdays, anniversaries), the stored year is irrelevant. Compare month/day only:
1. Extract month and day from the stored date
2. Build this year's occurrence
3. If in the past, try next year
4. Check if within the reminder window (default 14 days)

## LLM-Driven Cron Pattern
The morning digest cron is LLM-driven — it reads the bulletin-agent skill and follows its steps. To add new data sources to the digest:
1. Add a step to the skill's pipeline table
2. Create a script that outputs formatted text
3. The LLM cron will pick it up on the next run

No need to modify the cron job itself — it's the skill that defines the steps.

## Google Contacts ↔ Baserow Sync
Script: `google_contacts_sync.py`
- Two-way sync: Google → Baserow and Baserow → Google
- Matching strategy: mapping file → email → phone → name
- Phone numbers must be cleaned (digits-only) before writing to Baserow
- Birthdays must have valid year (1900 default)
- First run builds the mapping file; subsequent runs are incremental
- Cron: daily at 8am UTC (job f03915228d1f)
