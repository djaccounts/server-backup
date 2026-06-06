# Mealie API Quick Reference

## Auth
- `POST /api/auth/token` — form-encoded `username` + `password` → JWT
- Use `Authorization: Bearer *** on all API calls

## Recipe CRUD
- `GET /api/recipes` — list (supports pagination, search, filter by category/tag)
- `GET /api/recipes/{slug}` — get one
- `POST /api/recipes` — create from JSON body
- `PUT /api/recipes/{slug}` — full update
- `PATCH /api/recipes/{slug}` — partial update
- `DELETE /api/recipes/{slug}` — delete

## Import
- `POST /api/recipes/create/url` — `{"url": "..."}` → returns slug
- `POST /api/recipes/create/url/bulk` — `{"urls": [...]}` → returns slugs
- `POST /api/recipes/test-scrape-url` — preview without saving
- `POST /api/recipes/create/html-or-json` — from raw HTML or JSON-LD
- `POST /api/recipes/create/zip` — from Mealie ZIP export
- `POST /api/recipes/create/image` — from image (OCR)

## Exporting / Emailing Recipes
- Fetch full recipe via `GET /api/recipes/{slug}` with auth token
- **Deduplicate ingredients**: recipes with variations return ingredients repeated per variation. Use `seen = set()` on the `display` field.
- **Variation headers**: instructions with `text` starting with `"Variation:"` are section dividers, not steps. Split into sections.
- Format as plain text: INGREDIENTS → MAIN RECIPE → VARIATIONS → NUTRITION → Source URL
- Send via AgentMail MCP: `mcp_agentmail_send_message` with `inboxId`, `to`, `subject`, `text`
  - Find inbox ID via `mcp_agentmail_list_inboxes`
  - Sender shows as AgentMail identity (e.g., `davidj@agentmail.to`)
  - Can send to any external address (e.g., `dj@djaccounts.com`)

## Database
- SQLite at `/app/data/mealie.db`
- Users table: `id, full_name, username, email, password (bcrypt), admin, group_id, household_id`
- Password reset: `UPDATE users SET password = ? WHERE email = ?` with bcrypt hash

## Container Paths
- Data: `/app/data/`
- DB: `/app/data/mealie.db`
- Logs: `/app/data/mealie.log`
- Recipe images: `/app/data/recipes/`