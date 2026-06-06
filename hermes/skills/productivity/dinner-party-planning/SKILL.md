---
name: dinner-party-planning
description: "Plan dinner party menus: research recipes, build cooking timelines, and format output for use while cooking. Covers recipe sourcing, parallel-task scheduling, and presentation as HTML cards or text."
version: 1.0.0
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

Add to this table as new themes come up — these give starting suggestions so the user doesn't have to list every dish.

## Output Format (User Preference — FINAL)

The user confirmed this exact order for the final deliverable after one round of feedback ("include the meal summary before the ingredients"):

1. **Meal Summary** — what's on the menu (dish names + one-line descriptions), how the dishes come together logistically (what overlaps, what's make-ahead, how it lands simultaneously)
2. **Combined Shopping List** — all ingredients deduplicated and grouped by aisle: Meat, Dairy, Vegetables, Pantry Dry, Spices & Seasoning, Oils & Vinegar, Pantry Other. Note where one ingredient covers multiple recipes (e.g. "one 600g yoghurt pot covers both tzatziki and marinade"). Notes at the bottom explain quantity breakdowns.
3. **Timetable** — cooking timeline working backwards from serve time. Mark each step as active/passive. Call out same-oven dishes, stovetop vs oven coordination. Highlight day-before prep items.
4. **Individual Recipes** — each dish with full ingredients list and numbered step-by-step method. Include tip boxes for key pitfalls. Cite specific recipe URLs when sourced from a website; label "traditional recipe" when synthesised.
5. **HTML Recipe Card** — styled interactive card with timeline visualisation, recipe cards, print-friendly CSS, mobile-responsive.

## Delivery

- Write full plain text to `/tmp/<event-name>-final.txt` first
- Send **one email** via `agentmail_helper.py`:
```bash
BODY=$(cat /tmp/<event-name>-final.txt)
python3 /root/Geeves/scripts/agentmail_helper.py send "<email>" "<subject>" "$BODY" /root/<event-name>.html
```
- Host the HTML card on nginx: `cp /root/<event-name>.html /var/www/html/<event-name>.html && chmod 644 /var/www/html/<event-name>.html`
- Accessible at `http://77.68.33.121/<event-name>.html`
- **Do NOT rely on Slack attachments** — Slack bot API doesn't support file uploads. Use email + nginx URL instead.

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

## Key Principles

- **Same oven awareness**: if multiple dishes share the oven, note the shared temp and which can go in together
- **Make-ahead calls**: always flag what can/should be done the day before
- **Active vs passive time**: distinguish hands-on cooking from passive oven/resting time
- **Shopping list dedup**: never list "olive oil" three times — combine quantities and add a note explaining the breakdown
- **Source honesty**: cite specific recipe URLs when sourced from a website; label "traditional recipe" when synthesised from general knowledge. Never fabricate a source URL
- **User is not an engineer**: always provide browser-accessible URLs, never assume SSH/command-line access. If a port doesn't work, check the firewall before asking the user to do anything

## Persistence (Optional)

If the user wants the menu saved:
- **Airtable Todos** — add a "Dinner party [date]" todo with guest names in Notes.
- **Airtable People** — link guests via Linked Person field if they exist in the People table.
- **Obsidian** — save full menu + timeline as a note in the vault.
