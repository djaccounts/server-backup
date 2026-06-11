# Session Learnings — June 2026 (Relationships & Occasions Build)

## Baserow: Auto-Created "Notes" Field

When creating a table via the Platform API, Baserow **auto-creates a "Notes" field** (long_text).

**Fix:** After creating a table, check for auto-created Notes and rename it:
```python
fields = api("GET", f"/api/database/fields/table/{new_table_id}/")
for f in fields:
    if f["name"] == "Notes":
        api("PATCH", f"/api/database/fields/{f['id']}/", {"name": "Extra Notes"})
        break
```

## write_file Tool: Path Truncation with Tilde

The `write_file` tool truncates lines containing `~` in paths. Use `os.path.join()` instead:
```python
# BAD: TOKEN_PATH=***  # gets mangled
# GOOD: TOKEN_PATH=*** ".hermes", ".env")
```

## Google OAuth: Refresh Token Can Be Revoked

Refresh token revocation returns `invalid_grant`. Requires full re-consent in Google Cloud Console.

**Token refresh requires form-encoded data**, NOT JSON:
```python
data = urllib.parse.urlencode({...}).encode()
headers = {"Content-Type": "application/x-www-form-urlencoded"}
```

**Token exchange (code → tokens) also requires form-encoded data**, same pattern.

## Module Build: Relationships & Occasions (June 2026)

4 new tables created:

| Table | ID | Key Fields |
|-------|-----|-----------|
| Occasions | 403 | Person, Occasion Type, Date, Recurring, Remind Days Before |
| Gift Ideas | 404 | Person, Idea, Estimated Cost, Occasion, Status |
| Gift History | 405 | Person, Gift, Occasion, Date Given, Rating |
| Social Log | 406 | Date, Type, Person, Summary, Key Things, Follow-up, Source |

All link to People (359). "Extra Notes" naming because Baserow auto-creates "Notes".

## slack_capture.py: Adding New Categories

Three-step pattern:
1. Add regex patterns to CATEGORY_RULES array
2. Write handler function (use `find_person()`, `baserow_post()`)
3. Register in HANDLERS dict

## Google Contacts ↔ Baserow Sync (June 2026)

### Phone Number Cleaning
Baserow's `phone_number` field type is strict. Google Contacts returns numbers in various formats (spaces, dashes, parentheses). Clean before writing:
```python
def clean_phone(phone):
    if not phone:
        return ""
    cleaned = phone.strip()
    if cleaned.startswith("+"):
        return "+" + "".join(c for c in cleaned[1:] if c.isdigit())
    return "".join(c for c in cleaned if c.isdigit())
```

### Birthday Date Format
Google Contacts birthdays may be `MM-DD` (no year). Baserow's `date` field requires `YYYY-MM-DD` with a valid year. Use `1900` as default:
```python
def clean_birthday(birthday):
    if not birthday:
        return ""
    parts = birthday.split("-")
    if len(parts) == 3:
        return birthday  # Already YYYY-MM-DD
    elif len(parts) == 2:
        return f"1900-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
    return birthday
```
**Note:** `0000` as year is rejected by Baserow. Use `1900`.

### OAuth Code Exchange
Google OAuth callback may fire twice (two redirects). The code is one-time use — if the first exchange fails, use the second code from the second callback.

### Sync Script
Script at `/root/Geeves/scripts/google_contacts_sync.py`. Supports `--dry-run`, `--direction google-to-baserow|baserow-to-google|both`, `--status`. Uses local mapping file (`google_contacts_mapping.json`) to track Google resource_name ↔ Baserow row_id.
