#!/usr/bin/env python3
"""Email updated dinner party PDFs to David (v3 - corrected guest names)."""
import base64, json, urllib.request, subprocess

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
    html_body = f.read()
with open("/root/dinner-party-jill-adam-20june-cooking.pdf", "rb") as f:
    pdf_cooking_b64 = base64.b64encode(f.read()).decode()
with open("/root/dinner-party-jill-adam-20june-guest.pdf", "rb") as f:
    pdf_guest_b64 = base64.b64encode(f.read()).decode()

text_body = """Dinner Party — Saturday 20th June at 1:30pm
43 Englands Lane, NW3 4YD

You're invited to a Middle Eastern-inspired lunch with family.

On the menu:
- Chicken Shawarma (spit-roasted with warm spices)
- Homemade Pita Bread (warm, soft, pillowy)
- Hummus (creamy, lemony, made from scratch)
- Pickled Red Onions (tangy, crisp, bright pink)
- Quinoa Salad with Roasted Vegetables

All dishes are dairy-free and kosher-friendly.

Come hungry. Leave happy.

— Geeves

Two PDFs attached:
1. GUEST VERSION — Invite card to send to Jill & Adam
2. COOKING VERSION — Full card with timeline, shopping list, recipes

HTML versions:
- Guest: http://77.68.33.121/dinner-party-jill-adam-20june-guest.html
- Cooking: http://77.68.33.121/dinner-party-jill-adam-20june.html"""

inboxes = api("GET", "inboxes")
items = inboxes.get("data", inboxes) if isinstance(inboxes, dict) else inboxes
if isinstance(items, dict):
    items = items.get("inboxes", items.get("data", []))
from_inbox = items[0]["inbox_id"] if isinstance(items[0], dict) else items[0]

result = api("POST", f"inboxes/{from_inbox}/messages/send", {
    "to": ["daverj1987@gmail.com"],
    "subject": "Dinner Party — Jill & Adam, 20th June (final)",
    "text": text_body,
    "html": html_body,
    "attachments": [
        {"filename": "dinner-party-20june-guest.pdf", "content": pdf_guest_b64, "type": "application/pdf"},
        {"filename": "dinner-party-20june-cooking.pdf", "content": pdf_cooking_b64, "type": "application/pdf"}
    ]
})

print(json.dumps(result, indent=2))
