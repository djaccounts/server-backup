# Dinner Party HTML Card — Delivery Reference

## File Structure

Two files per event:
- `<event-name>.html` — Cooking version (full interactive card)
- `<event-name>-guest.html` — Guest version (invite/cover only)

Both get PDFs generated via weasyprint.

## Cooking HTML — Tab Order

1. **Invite** — Cover page (mirrors guest version)
2. **Summary** — Meal overview, how dishes overlap, make-ahead calls
3. **Shopping List** — Interactive checkboxes, grouped by aisle, deduped
4. **Timeline** — Day-before through to serve, active/passive tags
5. **Recipes** — Expandable cards per dish, ingredients + method + tips + source

## Guest HTML — Content

- Date badge
- "You're Invited" heading
- Subtitle (cuisine/theme)
- Guest name chips
- Menu list (dish name + one-line description each)
- Dietary note
- Closing line ("Come hungry. Leave happy.")
- **No cooking details whatsoever**

## Design System

Dark theme (Geeves standard):
- Background: `#1a1a2e`
- Card: `#16213e`
- Surface: `#0f3460`
- Accent: `#e94560`
- Green: `#4ecca3`
- Orange: `#f5a623`
- Text: `#eee`
- Muted: `#aaa`

CSS: Self-contained in `<style>` block. No external dependencies.
JS: Minimal — tab switching + recipe expand/collapse only.

## Nginx Hosting Checklist

1. Copy files to `/var/www/html/`
2. `chmod 644` both files
3. Verify: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/<filename>`
4. If 404: check nginx config has `try_files $uri @baserow;` in `location /` block
5. Generate PDFs: `weasyprint <input.html> <output.pdf>`
6. Host PDFs in `/var/www/html/` too

## Email Checklist

1. Host all 4 files on nginx (2 HTML + 2 PDF)
2. Use `mcp_agentmail_send_message` with public URLs for attachments
3. Inbox ID: `davidj@agentmail.to` (verify via `mcp_agentmail_list_inboxes`)
4. Recipient: guest email addresses from People table or as provided
