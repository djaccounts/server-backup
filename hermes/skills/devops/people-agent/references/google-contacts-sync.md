# Google Contacts Sync — Reference

## Script

`/root/Geeves/scripts/google_contacts_sync.py` — Two-way sync between Google Contacts and Baserow People table.

## Auth Requirements

- **Google OAuth:** Requires `contacts.readonly` scope (Google→Baserow) and `contacts` scope (Baserow→Google write)
- **Baserow:** Uses `BASEROW_API_TOKEN` from `~/.hermes/.env`
- **Token file:** `~/.hermes/google_token.json`

## Usage

```bash
# Dry run
python3 /root/Geeves/scripts/google_contacts_sync.py --dry-run

# Full two-way sync
python3 /root/Geeves/scripts/google_contacts_sync.py --direction both

# Check status
python3 /root/Geeves/scripts/google_contacts_sync.py --status
```

## Known Issues (June 2026)

- **Refresh token expired:** The Google OAuth refresh token was revoked/expired in June 2026. Re-auth needed.
- **Write scope missing:** Current token has `contacts.readonly`; Baserow→Google needs full `contacts` scope.

## Field Mapping (Google → Baserow)

| Google Field | Baserow Field |
|--------------|---------------|
| `names[0].displayName` | `Name` |
| `emailAddresses[0].value` | `Email` |
| `phoneNumbers[0].value` | `Phone` |
| `birthdays[0].date` | `Birthday` |
