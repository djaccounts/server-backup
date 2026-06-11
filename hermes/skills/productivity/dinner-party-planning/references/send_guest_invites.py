#!/usr/bin/env python3
"""Send guest invite to Jill, Adam, Sidney, and Grace."""
import json, urllib.request, subprocess

ENV_PATH = "/root/.hermes/.env"

def get_env_key(var_name):
    r = subprocess.run(["grep", var_name, ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def api(method, path, data=None):
    key = get_env_key("AGENT_MAIL_API")
    url = f"https://api.agentmail.to/v0/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": json.loads(e.read()), "status": e.code}

with open("/root/dinner-party-jill-adam-20june-guest.html") as f:
    guest_html = f.read()

inboxes = api("GET", "inboxes")
items = inboxes.get("data", inboxes) if isinstance(inboxes, dict) else inboxes
if isinstance(items, dict):
    items = items.get("inboxes", items.get("data", []))
from_inbox = items[0]["inbox_id"] if isinstance(items[0], dict) else items[0]

# Send to all 4 guests
guests = [
    ("jillsjacobs@hotmail.com", "Jill"),
    ("adam@squiresestates.co.uk", "Adam"),
    ("sidneyredhouse@hotmail.com", "Sidney"),
    ("graceredhouse@hotmail.com", "Grace"),
]

for email, name in guests:
    result = api("POST", f"inboxes/{from_inbox}/messages/send", {
        "to": [email],
        "subject": "You're Invited — Saturday 20th June",
        "html": guest_html
    })
    status = result.get("message_id", result.get("error", "unknown"))
    print(f"{name} ({email}): {status}")
