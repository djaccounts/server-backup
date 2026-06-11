# Baserow + Google OAuth — Session Learnings (June 2026)

## write_file Tool Line Truncation

The `write_file` tool has a line length limit that mangles long lines. Symptoms:
- Lines with long strings (e.g., file paths with `~` expansion, URLs, tokens) get truncated
- The tool may report "file modified since last read" warnings

**Workaround:** Use `terminal` with heredoc or `python3 -c` to write files with long lines:
```bash
cat > /tmp/script.py << 'PYEOF'
# ... content with long lines ...
PYEOF
```

Or use Python:
```bash
python3 -c "
with open('/tmp/file.py', 'w') as f:
    f.write('long content...')
"
```

## Google OAuth Token Refresh

The Google OAuth token at `~/.hermes/google_token.json` expires regularly. The refresh token can also be revoked/expired.

**Symptoms:** API calls return 401 `UNAUTHENTICATED` or `invalid_grant`.

**Fix attempt:** POST to `https://oauth2.googleapis.com/token` with form-encoded data (NOT JSON):
```python
import urllib.parse, urllib.request
data = urllib.parse.urlencode({
    "client_id": creds["client_id"],
    "client_secret": creds["client_secret"],
    "refresh_token": creds["refresh_token"],
    "grant_type": "refresh_token"
}).encode()
req = urllib.request.Request(
    "https://oauth2.googleapis.com/token",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST"
)
```

**If refresh token is revoked** (`invalid_grant`): Full re-auth required. The user must re-grant OAuth consent at the Google consent screen.

**Required scopes for Geeves:**
- `https://www.googleapis.com/auth/contacts.readonly` — Google Contacts sync
- `https://www.googleapis.com/auth/calendar` — Calendar events for morning digest
- `https://www.googleapis.com/auth/gmail.send` — AgentMail sending

## Baserow Field Deletion Requires JWT

Confirmed: Database token (`BASEROW_API_TOKEN`) can GET (list/read) fields but **cannot** DELETE or PATCH them. Field deletion returns 401 with "Authentication credentials were not provided."

**Fix:** Get JWT via `POST /api/user/token-auth/` with admin email+password. The admin password is NOT stored in any file — David must provide it.

```bash
curl -X POST http://77.68.33.121/api/user/token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"email": "daverj1987@gmail.com", "password": "..."}'
```

Returns `{"token": "..."}`. Use as `Authorization: JWT <token>`.
