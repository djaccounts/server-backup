# Google Contacts → Airtable People Import

## Technique

Use the People API directly (not the gws `contacts list` command, which only returns name/email/phone).

### Fetch All Contacts (Python)

```python
import json, urllib.request

with open("/root/.hermes/google_token.json") as f:
    token_data = json.load(f)
try:
    access_token = json.loads(token_data['token'])['access_token']
except:
    access_token = token_data['token']

all_contacts = []
next_page = "https://people.googleapis.com/v1/people/me/connections?pageSize=100&personFields=names,emailAddresses,phoneNumbers,birthdays,addresses,biographies,organizations,urls"

while next_page:
    req = urllib.request.Request(next_page, headers={"Authorization": "Bearer " + access_token})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    all_contacts.extend(data.get("connections", []))
    token = data.get("nextPageToken")
    next_page = "https://people.googleapis.com/v1/people/me/connections?pageSize=100&personFields=names,emailAddresses,phoneNumbers,birthdays,addresses,biographies,organizations,urls&pageToken=" + token if token else None
```

### Mapping: Google Contact → Geeves People Table

| Google Field | Geeves Field | Notes |
|---|---|---|
| `names[0].displayName` | `Name` | Required |
| `phoneNumbers[0].value` | `Phone` | |
| `emailAddresses[0].value` | `Email` | |
| `birthdays[0].date` | `Birthday` | Format: `YYYY-MM-DD`. If year unknown, use `2000-MM-DD` |
| `organizations[0].name` | `How Known` | Best-guess default |
| `organizations[0].title` | `Social Notes` | Job title |
| `addresses[0]` (joined) | `Venue Preferences` | Street + city + region + postcode |
| `biographies[0].value` | `Relationship Notes` | |
| `urls[0].value` | `Topics They Love` | Least-bad mapping |
| — | `Tier` | Default all imports to `'Tier 4 (other)'` |

### Bulk Create (Python)

Airtable allows max 10 records per batch POST, rate limit 5 req/sec:

```python
import time

batch = []
for contact in all_contacts:
    fields = {'Name': contact['names'][0]['displayName']}
    # ... extract other fields ...
    fields['Tier'] = 'Tier 4 (other)'
    batch.append(fields)
    if len(batch) >= 10:
        airtable_post('appzvmonQXs4x2AlL/People', {'records': [{'fields': f} for f in batch]})
        batch = []
        time.sleep(0.2)
if batch:
    airtable_post('appzvmonQXs4x2AlL/People', {'records': [{'fields': f} for f in batch]})
```

### Typical Contact Data

From a real import of 259 contacts: names (100%), phones (99%), emails (26%), birthdays (36%), companies (17%), addresses (10%), notes (4%), URLs (12%). Most contacts are phone-only — this is normal for mobile-synced contacts.

### Post-Import

- Re-tier important people (Tier 1/2/3) manually in Airtable
- Review and fix field mappings that don't fit (e.g., company → "How Known" is a rough default)
- The gws `contacts list` command only returns name/email/phone — use the People API directly for full data
