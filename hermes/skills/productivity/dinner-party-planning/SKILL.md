---
name: dinner-party-planning
description: "Plan dinner party menus: research recipes, build cooking timelines, and format output for use while cooking. Covers recipe sourcing, parallel-task scheduling, and presentation as HTML cards or text."
version: 1.5.0
author: Geeves
---

# Dinner Party Planning

Plan a complete meal for a dinner party — research recipes from the web, schedule oven/hob/stove usage, and produce a cooking timeline that avoids bottlenecks.

## When to Use

User mentions: dinner party, hosting, cooking for guests, menu planning, meal plan, supper club, or asks for recipes + a cooking plan in one go.

## Workflow

1. **Gather requirements** — date, guest count, dietary restrictions, theme/cuisine, specific dishes mentioned. If the user names dishes, use those; otherwise suggest options for the theme.
2. **Web-search each recipe** — find 2–3 sources per dish, pick the best one (prefer UK measurements, accessible ingredients, clear steps). Record: ingredients list, step-by-step method, prep time, cook time, active vs passive time.
3. **Build a cooking timeline** — work backwards from serving time:
   - Identify passive-cook items (oven chips, slow-marinate) — these can overlap.
   - Identify active-prep items (chopping, assembling, pan-frying) — these need hands.
   - Flag the bottleneck (usually hob space or active-prep overlap).
   - Schedule in 15-min blocks, grouping passive items into the same oven slot where possible.
4. **Generate a shopping list** — deduplicated ingredients across all dishes, grouped by supermarket section.
5. **Present output** — ask user preference:
   - **HTML recipe card** (via `claude-design` skill) — phone/tablet friendly while cooking.
   - **Plain text in chat** — quick reference.
   - **Obsidian note** (via `obsidian` skill) — if they want it saved to the vault.

### Timeline Format

```
TIME        TASK                          OVEN/HOB/ACTIVE
─────────────────────────────────────────────────────────
17:00–17:15 Marinate chicken              — / — / ACTIVE
17:15–17:30 Prep salad + tzatziki         — / — / ACTIVE
17:30–18:00 Flatbread dough rest          — / — / PASSIVE
18:00–18:20 Oven chips IN                 200°C / — / PASSIVE
18:20–18:40 Chicken gyros IN              200°C / — / PASSIVE
18:20–18:35 Flatbread cook                — / HOB / ACTIVE
18:40        PLATE & SERVE
```

## Theme Shortcuts

Common themes the user has mentioned:

| Theme | Typical dishes |
|-------|---------------|
| Greek | Chicken gyros, homemade flatbread, oven chips, Greek salad, tzatziki |
| Italian | Pasta course, bruschetta, tiramisu |
| Mexican | Tacos, guacamole, salsa, rice & beans |
| Middle Eastern | Chicken shawarma, homemade pita, hummus, pickled red onions, quinoa salad with roasted vegetables |

Add to this table as new themes come up — these give starting suggestions so the user doesn't have to list every dish.

## Output Format (User Preference — FINAL)

The user confirmed this exact order for the final deliverable after one round of feedback ("include the meal summary before the ingredients"):

1. **Meal Summary** — what's on the menu (dish names + one-line descriptions), how the dishes come together logistically (what overlaps, what's make-ahead, how it lands simultaneously)
2. **Combined Shopping List** — all ingredients deduplicated and grouped by aisle: Meat, Dairy, Vegetables, Pantry Dry, Spices & Seasoning, Oils & Vinegar, Pantry Other. Note where one ingredient covers multiple recipes (e.g. "one 600g yoghurt pot covers both tzatziki and marinade"). Notes at the bottom explain quantity breakdowns.
3. **Timetable** — cooking timeline working backwards from serve time. Mark each step as active/passive. Call out same-oven dishes, stovetop vs oven coordination. Highlight day-before prep items.
4. **Individual Recipes** — each dish with full ingredients list and numbered step-by-step method. Include tip boxes for key pitfalls. Cite specific recipe URLs when sourced from a website; label "traditional recipe" when synthesised.
5. **HTML Recipe Card** — styled interactive card with timeline visualisation, recipe cards, print-friendly CSS, mobile-responsive.
   - **Cooking version**: White/light background (not dark). Compact spacing — reduce padding, tighten gaps between sections. Efficient use of page space.
   - **Guest version**: Clean, elegant, minimal. White background. Small padding. Guests listed vertically.

## Delivery

### Two Separate Files

Always produce **two separate HTML files** — they serve different audiences:

1. **Cooking version** (`<event-name>.html`): Full interactive card with all tabs (Invite → Summary → Shopping List → Timeline → Recipes). For the cook.
2. **Guest version** (`<event-name>-guest.html`): Standalone invite/cover page only. Clean, elegant, no cooking details. For the guests.

**Guest invite: email only, no PDF.** The guest version is sent as the email body (HTML). Do NOT generate a PDF for the guest invite — the HTML in the email is the invite.

**Cooking version: PDF + email.** Generate a PDF of the cooking version and attach it to the email along with the HTML body.

Both get hosted on nginx.

### Hosting on Nginx

```bash
cp /root/<event-name>.html /var/www/html/<event-name>.html
cp /root/<event-name>-guest.html /var/www/html/<event-name>-guest.html
chmod 644 /var/www/html/<event-name>.html /var/www/html/<event-name>-guest.html
```

Accessible at:
- `http://77.68.33.121/<event-name>.html` (cooking)
- `http://77.68.33.121/<event-name>-guest.html` (guest)

**⚠ PITFALL — Nginx static file serving:** If nginx `location /` proxies to another service (e.g. Baserow on port 8080), static files in `/var/www/html` will 404. Fix: use `try_files $uri @baserow;` so static files are served first, proxy as fallback. Verify with `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/<filename>` after hosting.

**⚠ PITFALL — AgentMail `mcp_agentmail_send_message` attachments:** The `url` parameter requires a publicly accessible HTTP URL. Since the VPS (77.68.33.121) is often not reachable from the public internet, this method fails. The **only reliable method** is the AgentMail REST API with **base64-encoded** attachments (see Email Delivery section). Write a Python script to `/tmp/` and run it — do NOT use the MCP tool for attachments.

### PDF Generation

Install weasyprint if not present: `pip3 install weasyprint`

Generate PDF for the **cooking version only** (no guest PDF needed):

```bash
weasyprint /root/<event-name>.html /root/<event-name>-cooking.pdf
```

Host PDF alongside HTML:
```bash
cp /root/<event-name>-cooking.pdf /var/www/html/<event-name>-cooking.pdf
chmod 644 /var/www/html/<event-name>-cooking.pdf
```

### Email Delivery

**⚠ PITFALL — AgentMail attachments:** The `mcp_agentmail_send_message` tool's `attachments` parameter with `url` requires a **publicly accessible HTTP URL**. Since the VPS (77.68.33.121) is often not reachable from the public internet, this method fails. The **only reliable method** is the AgentMail REST API with **base64-encoded** attachments (same pattern as the bulletin cron):

```python
import base64, json, urllib.request, subprocess

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

# Guest version: HTML only (no PDF)
with open("/root/<event-name>-guest.html") as f:
    guest_html = f.read()

# Cooking version: PDF attachment
with open("/root/<event-name>-cooking.pdf", "rb") as f:
    pdf_cooking_b64 = base64.b64encode(f.read()).decode()

# Send to cook (David) — cooking PDF + guest HTML as body
result = api("POST", f"inboxes/{from_inbox}/messages/send", {
    "to": ["daverj1987@gmail.com"],
    "subject": "Dinner Party — <date>",
    "text": "<plain text invitation with address>",
    "html": guest_html,
    "attachments": [
        {"filename": "dinner-party-cooking.pdf", "content": pdf_cooking_b64, "type": "application/pdf"}
    ]
})

# Send to guests — guest HTML only (no PDF, no attachments)
# Use the people-lookup skill to find guest emails first
result = api("POST", f"inboxes/{from_inbox}/messages/send", {
    "to": ["guest1@email.com", "guest2@email.com"],
    "subject": "You're Invited — <date>",
    "html": guest_html
})
```

**Email body text** should be the simple invitation text (date, time, address, brief menu mention) — NOT a feature list of what's in the card. The PDFs carry the detail.

**Guest invite email:** HTML-only, no attachments. The HTML itself is the invite.

**Cooking email to David:** Guest HTML as body + cooking PDF as attachment.

- Find inboxId via `mcp_agentmail_list_inboxes` if unsure
- For the sender's own email: use `daverj1987@gmail.com`

### Word docx

- Write full plain text to `/tmp/<event-name>-final.txt` first
- **Do NOT rely on Slack attachments** — Slack bot API doesn't support file uploads. Use email + nginx URL instead.

## Guest Invite

The guest invite is a **separate HTML file** (`<event-name>-guest.html`), not just a tab in the cooking version. This keeps it clean and shareable.

### Guest HTML content:

1. **Cover card** with event date, time, and menu preview
2. **Guest names** listed **vertically** (one per line, block display) — NOT in a horizontal row of chips
3. **Host address** prominently displayed (e.g., "43 Englands Lane, NW3 4YD") — include on both the HTML and PDF
4. **Dietary notes** prominently displayed (e.g., "All dishes are dairy-free · Kosher-friendly")
5. Keep the invite concise — dish names + one-line descriptions only
6. **No cooking details** — no timeline, no shopping list, no recipes
7. Closing line: "Come hungry. Leave happy."
8. **Style**: Clean, white or light background. Elegant but compact — avoid large padded boxes that waste space. Use small padding (0.3–0.5rem), tight gaps, and minimal visual weight.

### Guest HTML style guidelines (confirmed June 2026):

- **Background**: White/light only — no dark backgrounds
- **Guests**: Listed **vertically** (block display, one per line) — NOT in a horizontal row of chips
- **Address**: Always include the host's full address prominently on the invite
- **Spacing**: Compact — small padding (0.3–0.5rem), tight gaps, minimal visual weight. Avoid large padded boxes.
- **Width**: Max ~520px for the invite card
- **Closing line**: "Come hungry. Leave happy."
- See `references/guest-invite-template.html` for the canonical example

### Cooking HTML style guidelines (confirmed June 2026):

- **Background**: White/light only — no dark backgrounds
- **Spacing**: Compact — reduce padding, tighten gaps between sections, efficient page space usage
- **Recipe cards**: Collapsed by default (expandable), compact ingredient lists
- See `references/cooking-card-template.html` for the canonical example

**Invite → Summary → Shopping List → Timeline → Recipes**

The Invite tab in the cooking version can mirror the guest version's cover page for consistency.

## Mealie Integration

After creating recipes, also add them to Mealie (self-hosted recipe manager):

1. Check if running: `docker ps | grep mealie` (port 9925)
2. Authenticate: POST to `http://localhost:9925/api/auth/token` with form-encoded `username=changeme@example.com&password=MyPassword123`
3. Create each recipe: POST to `http://localhost:9925/api/recipes` with JSON body (`name`, `description`, `servings`, `recipeIngredient`, `recipeInstructions`, `tags`)
4. **API quirk:** Create endpoint returns the slug as a **plain string**, not JSON. Parse with `result.strip().strip('"')`
5. Tags: always include `dinner-party` + cuisine tag + dish-type tags
6. Source URL: PATCH `orgURL` after creation if recipe came from a specific website
7. Images: upload via `POST /api/recipes/{slug}/image` or through the Mealie web UI
8. **Firewall:** Port 9925 is blocked by default. If user can't access, either `ufw allow 9925/tcp` or set up nginx reverse proxy on port 80
9. **⚠ PITFALL — Mealie auth:** Default credentials (`changeme@example.com` / `MyPassword123`) may return 401. Reset directly via SQLite:
```bash
docker exec mealie python3 -c "
import sqlite3, bcrypt
hashed = bcrypt.hashpw(b'MyPassword123', bcrypt.gensalt(rounds=12)).decode()
conn = sqlite3.connect('/app/data/mealie.db')
cursor = conn.cursor()
cursor.execute('UPDATE users SET password = ? WHERE email = ?', (hashed, 'changeme@example.com'))
conn.commit()
print(f'Updated {cursor.rowcount} user(s)')
conn.close()
"
```

## Key Principles

- **Same oven awareness**: if multiple dishes share the oven, note the shared temp and which can go in together
- **Make-ahead calls**: always flag what can/should be done the day before
- **Active vs passive time**: distinguish hands-on cooking from passive oven/resting time
- **Shopping list dedup**: never list "olive oil" three times — combine quantities and add a note explaining the breakdown
- **Source honesty**: cite specific recipe URLs when sourced from a website; label "traditional recipe" when synthesised from general knowledge. Never fabricate a source URL
- **User is not an engineer**: always provide browser-accessible URLs, never assume SSH/command-line access. If a port doesn't work, check the firewall before asking the user to do anything
- **HTML card design**: See `references/html-card-template.md` for style guidelines (white background, compact spacing, vertical guest list, address on invite)
- **Email delivery**: Use `scripts/send_dinner_party_email.py` for reliable AgentMail delivery with base64 attachments
- **Reply handling**: AgentMail replies are monitored by cron job `13d764e11d46` (every 15 min) and posted to Slack home channel. Script: `scripts/agentmail_replies_to_slack.py`
- **Confirmed guest emails for 20th June 2026**: Jill Jacobs (jillsjacobs@hotmail.com), Adam Redhouse (adam@squiresestates.co.uk), Sidney Redhouse (sidneyredhouse@hotmail.com), Grace Pearl Redhouse (graceredhouse@hotmail.com)

## Persistence (Optional)

If the user wants the menu saved:
- **Baserow Dinner Parties** — add a dinner party record with guest names, date, and linked recipes.
- **Baserow People** — link guests via Linked Person field if they exist in the People table.
- **Obsidian** — save full menu + timeline as a note in the vault.
