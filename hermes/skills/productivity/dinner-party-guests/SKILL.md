---
name: dinner-party-guests
description: "Look up guest emails from the Baserow People table and send dinner party invitations. Use when the user wants to find guest contact details or send invites to dinner party guests."
version: 1.0.0
author: Geeves
---

# Dinner Party Guests

Look up guest details from Baserow People table and send invitations via AgentMail.

## When to Use

- User mentions sending invites, looking up guest emails, or "send this to the guests"
- After dinner party plan is finalised and approved

## People Table

- **Table name**: `People`
- **Table ID**: 359
- **Key fields**: `Name` (text), `Email` (email), `Phone` (phone_number)
- **Lookup script**: `python3 /root/Geeves/scripts/baserow_api.py find People "<name>"`

## Workflow

### 1. Look Up Guests

For each guest, search the People table:

```bash
python3 /root/Geeves/scripts/baserow_api.py find People "<name>"
```

Returns rows with `field_3297` (Name) and `field_3300` (Email).

**Email field can be empty** for children or contacts without email. In that case:
- Check the household — if parents are listed, use the parent's email
- If no email found for anyone in the household, flag to the user: "No email found for <name>. Should I skip or use a different address?"

### 2. Collect Emails

Build a list of `to` addresses from the People table:

| Guest | Source | Email |
|-------|--------|-------|
| Jill Jacobs | People table (row 243) | jillsjacobs@hotmail.com |
| Adam Redhouse | People table (row 231) | adam@squiresestates.co.uk |
| Sid | No email in People table (row 211) — use parents' | (use Jill or Adam's) |
| Grace | People table (row 208) | graceredhouse@hotmail.com |

**⚠ Do NOT guess emails.** If the field is empty, ask the user or use a household member's address.

### 3. Send Invite

Use the AgentMail REST API (NOT `mcp_agentmail_send_message` — see pitfall below). Send the **guest HTML** as the email body. No attachments — the HTML IS the invite.

```python
import json, urllib.request, subprocess

def get_env_key(var_name):
    r = subprocess.run(["grep", var_name, "/root/.hermes/.env"], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def api(method, path, data=None):
    key = get_env_key("AGENT_MAIL_API")
    url = f"https://api.agentmail.to/v0/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# Get inbox
inboxes = api("GET", "inboxes")
items = inboxes.get("data", inboxes) if isinstance(inboxes, dict) else inboxes
if isinstance(items, dict):
    items = items.get("inboxes", items.get("data", []))
from_inbox = items[0]["inbox_id"] if isinstance(items[0], dict) else items[0]

# Read guest HTML
with open("/root/<event-name>-guest.html") as f:
    guest_html = f.read()

# Send to all guests
result = api("POST", f"inboxes/{from_inbox}/messages/send", {
    "to": ["guest1@email.com", "guest2@email.com"],
    "subject": "You're Invited — <event date>",
    "html": guest_html
})
```

**⚠ PITFALL — `mcp_agentmail_send_message` attachments:** This tool cannot fetch local files or VPS-hosted URLs. Always use the REST API with base64 for attachments, or HTML-only sends (no attachments needed for guest invites).

### 4. Confirm

After sending, report:
- Who was emailed (name + address)
- Who was skipped (no email found)
- Message ID for each send

## Key Principles

- **Always look up from People table first** — never guess emails
- **Children may not have emails** — use parent's email or ask
- **Guest invite is HTML-only** — no PDF, no attachments
- **One email per household is fine** if children share a parent's address
- **Confirm before sending** — show David the guest list and emails, get explicit "yes" before firing
