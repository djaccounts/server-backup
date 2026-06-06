---
name: mealie
description: Manage Mealie — self-hosted recipe manager. Install via Docker Compose, authenticate, import recipes from URLs, and troubleshoot auth issues. Use when the user asks to install, configure, or add recipes to Mealie.
---

# Mealie — Self-Hosted Recipe Manager

## Quick Reference

| | |
|---|---|
| **Image** | `ghcr.io/mealie-recipes/mealie:v2.8.0` |
| **Default port** | `9925:9000` |
| **Data** | Docker volume or `/app/data` |
| **Default login** | `changeme@example.com` / `MyPassword123` |

## Docker Compose Setup

```yaml
services:
  mealie:
    image: ghcr.io/mealie-recipes/mealie:v2.8.0
    container_name: mealie
    restart: unless-stopped
    ports:
      - "9925:9000"
    environment:
      - ALLOW_SIGNUP=false
      - PUID=0
      - PGID=0
      - TZ=Etc/UTC
      - MAX_WORKERS=1
      - WEB_CONCURRENCY=1
      - BASE_URL=http://YOUR_IP:9925
    volumes:
      - mealie-data:/app/data
volumes:
  mealie-data:
```

Save to `/opt/mealie/docker-compose.yml`, then:
```bash
cd /opt/mealie && docker compose up -d
```

Verify: `curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:9925` → expect `200`.

## Authentication

### Getting a JWT Token

```bash
curl -s -X POST http://localhost:9925/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=changeme@example.com&password=MyPassword123"
```

Returns `{"access_token": "...", "token_type": "bearer"}`.

**⚠️ IMPORTANT:** Capture the token and use it in the **same shell command chain**. Shell variables do NOT persist across separate `terminal()` calls. Example:

```bash
TOKEN=$(curl -s -X POST http://localhost:9925/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=changeme@example.com&password=MyPassword123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])") \
  && curl -s -X POST http://localhost:9925/api/recipes/create/url \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/recipe"}'
```

### Auth Troubleshooting

If you get `401 Unauthorized` with the default credentials, the password hash in the DB may not match. Reset it directly:

```bash
# Generate a new bcrypt hash
docker exec mealie python3 -c "
import bcrypt
password = b'MyPassword123'
hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)).decode()
print(hashed)
"

# Update the database
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

## Importing Recipes

### From a Single URL

```bash
curl -s -X POST http://localhost:9925/api/recipes/create/url \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/recipe-url"}'
```

Returns the recipe slug on success (e.g., `"greek-chicken-gyros-authentic-cooking-method"`).

### Bulk Import from Multiple URLs

```bash
curl -s -X POST http://localhost:9925/api/recipes/create/url/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://site.com/recipe1", "https://site.com/recipe2"]}'
```

### Test Scrape (Preview Without Saving)

```bash
curl -s -X POST http://localhost:9925/api/recipes/test-scrape-url \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/recipe-url"}'
```

## Useful API Endpoints

| `/api/recipes/{slug}` | PUT | Update recipe |
| `/api/recipes/{slug}` | PATCH | Partial update (name, slug, ingredients, instructions) |
| `/api/recipes/{slug}` | DELETE | Delete recipe |
| `/api/recipes/{slug}/duplicate` | POST | Duplicate a recipe |
| `/api/recipes/{slug}/image` | POST/PUT | Upload/replace recipe image |
| `/api/recipes/{slug}/exports` | GET | List export formats |
| `/api/recipes/{slug}/exports/zip` | GET | Export recipe as ZIP |
| `/api/users/self` | GET | Current user info |
| `/api/groups/categories` | GET | List categories |
| `/api/groups/tags` | GET | List tags |
| `/api/groups/tools` | GET | List kitchen tools |

## Modifying Recipes

### Update recipe name or description
```bash
curl -s -X PATCH http://localhost:9925/api/recipes/{slug} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Name", "description": "Updated description"}'
```

### Change slug (URL-friendly name)
```bash
curl -s -X PATCH http://localhost:9925/api/recipes/old-slug \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slug": "new-slug"}'
```

### Update ingredients
```bash
curl -s -X PATCH http://localhost:9925/api/recipes/{slug} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recipeIngredient": [{"quantity": 3, "unit": "tbsp", "food": "olive oil", "note": "extra virgin"}]}'
```

### Update instructions
```bash
curl -s -X PATCH http://localhost:9925/api/recipes/{slug} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recipeInstructions": [{"title": "Step 1", "text": "New instruction"}]}'
```

### Scale a recipe (double, halve, etc.)
Fetch the recipe, multiply quantities, then PATCH:
```python
import urllib.request, json
# ... get token ...
recipe = json.loads(urllib.request.urlopen(
    urllib.request.Request(
        "http://localhost:9925/api/recipes/{slug}",
        headers={"Authorization": f"Bearer {token}"}
    )
).read())
scale = 2.0  # double
for ing in recipe["recipeIngredient"]:
    if ing.get("quantity"):
        ing["quantity"] = round(ing["quantity"] * scale, 2)
# PATCH updated ingredients back
data = json.dumps({"recipeIngredient": recipe["recipeIngredient"]}).encode()
urllib.request.urlopen(urllib.request.Request(
    "http://localhost:9925/api/recipes/{slug}",
    data=data,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    method="PATCH"
))
print(f"Recipe scaled by {scale}x")
```

### Duplicate a recipe
```bash
curl -s -X POST http://localhost:9925/api/recipes/{slug}/duplicate \
  -H "Authorization: Bearer $TOKEN"
```

### Delete a recipe
```bash
curl -s -X DELETE http://localhost:9925/api/recipes/{slug} \
  -H "Authorization: Bearer $TOKEN"
```
Returns the deleted recipe object on success.

## Searching Recipes

### List all recipes
```bash
curl -s "http://localhost:9925/api/recipes?page=1&perPage=50" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('items', data if isinstance(data, list) else []):
    print(f\"  {r['name']} — {r['slug']}\")
"
```

### Search by keyword
```bash
curl -s "http://localhost:9925/api/recipes?search=chicken" \
  -H "Authorization: Bearer $TOKEN"
```

## Route Introspection

The Mealie SPA catches all non-API routes (including `/api/openapi.json`), returning HTML instead of JSON. To discover routes, use the container's Python:

```bash
docker exec mealie python3 -c "
from mealie.app import app
for route in app.routes:
    if hasattr(route, 'path') and 'api' in route.path.lower():
        print(f'{route.methods} {route.path}')
"
```

## Reference

- `references/api-quickref.md` — condensed API endpoint reference, DB schema, container paths, ingredient deduplication notes, AgentMail email workflow.

## Geeves Integration

### Mealie → Airtable Sync
- Script: `/root/Geeves/scripts/recipe_sync.py <slug>`
- Fetches a recipe from Mealie by slug, creates/updates the Airtable Recipes record, and syncs linked Ingredient records with auto-categorisation and seasonal tagging.
- Usage: `python3 /root/Geeves/scripts/recipe_sync.py the-best-spaghetti-bolognese-recipe`
- Airtable table IDs: Recipes=`tblehBgzRMa2Xucjd`, Ingredients=`tblNsgbYHNK8xWnB7`

### Architecture
- Mealie is the recipe engine (URL scraping, ingredient parsing, method, nutrition, scaling, images)
- Airtable holds slim metadata + cross-module links (People, Meals, Dinner Parties, Shopping Lists)
- Sync direction: Mealie → Airtable (one-way, on-demand)
- Full recipe detail lives in Mealie; Airtable connects recipes to people, meals, dinner parties

## Exporting a Recipe as Email

When the user wants to email a recipe, fetch the full recipe via API, format it as plain text, and send via AgentMail or other email tool.

### Fetching the Full Recipe

```bash
# Single command chain — token + fetch
TOKEN=$(curl -s -X POST http://localhost:9925/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=changeme@example.com&password=MyPassword123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])") \
  && curl -s http://localhost:9925/api/recipes/{slug} \
     -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Formatting Notes

- **Deduplicate ingredients**: The API returns the ingredient list multiple times (once per variation). Use `seen = set()` on the `display` field to filter duplicates before outputting.
- **Variation headers**: `recipeInstructions` entries whose `text` starts with `"Variation:"` (case-insensitive) are section headers, not steps. Split instructions into sections at these boundaries.
- Format with sections: INGREDIENTS → MAIN RECIPE → VARIATION NAME → NUTRITION → Source URL.
- Save the formatted text to a temp file (`/tmp/recipe_email.txt`) for the email tool to read.

### Sending via AgentMail MCP

Use `mcp_agentmail_send_message` with:
- `inboxId`: the sender's AgentMail inbox ID (find via `mcp_agentmail_list_inboxes`)
- `to`: `["recipient@email.com"]`
- `subject`: recipe name
- `text`: the formatted plain-text recipe body

AgentMail can send to any external email address. The sender will show as the AgentMail inbox identity (e.g., `davidj@agentmail.to`), not the recipient's address.

## Reverse Proxy Setup (Port 80 → Mealie)

Port 9925 is blocked by default on the VPS firewall (only 22 and 80 are open). Instead of opening another port, put mealie behind nginx on port 80:

**Step 1:** Update mealie's `BASE_URL` in `/opt/mealie/docker-compose.yml`:
```yaml
BASE_URL=http://77.68.33.121/mealie
```
Then: `cd /opt/mealie && docker compose restart mealie`

**Step 2:** Add location blocks to `/etc/nginx/sites-enabled/default` — **inside** the `server` block, before the closing `}`:
```nginx
\t# Mealie reverse proxy
\tlocation /mealie {
\t\tproxy_pass http://localhost:9925;
\t\tproxy_set_header Host $host;
\t\tproxy_set_header X-Real-IP $remote_addr;
\t\tproxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
\t\tproxy_set_header X-Forwarded-Proto $scheme;
\t\tproxy_http_version 1.1;
\t\tproxy_set_header Upgrade $http_upgrade;
\t\tproxy_set_header Connection "upgrade";
\t\tproxy_read_timeout 300s;
\t\tproxy_connect_timeout 75s;
\t}
```
Then: `nginx -t && nginx -s reload`

**⚠ Pitfall — heredoc tab escaping:** When using `cat >> file << 'EOF'`, tabs are written literally. If nginx needs actual tab indentation, use Python to write the file instead:
```python
with open('/etc/nginx/sites-enabled/default', 'a') as f:
    f.write('\tlocation /mealie {\n')
    f.write('\t\tproxy_pass http://localhost:9925;\n')
    # ... etc
```

**Result:** Mealie accessible at `http://77.68.33.121/mealie` — no port number needed.

## Pitfalls

1. **SPA intercepts non-API routes** — `/api/openapi.json` returns the frontend HTML, not the OpenAPI spec. Use the Python introspection method above.
2. **Shell variable persistence** — Tokens captured in one `terminal()` call are gone in the next. Always chain token capture and API usage in a single command.
3. **Default password may not work** — If `changeme@example.com` / `MyPassword123` returns 401, reset via the SQLite method above.
4. **Port mapping** — Mealie runs on port `9000` inside the container. Map it to an external port (e.g., `9925:9000`).
5. **Duplicate ingredients in API response** — Recipes with variations (bowl, shawarma, etc.) return ingredients repeated for each variation. Always deduplicate by the `display` field before formatting output.
6. **BASE_URL must match access URL** — If you change from port-based (`:9925`) to path-based (`/mealie`) access, you MUST update `BASE_URL` in the docker-compose and restart. Mismatch causes broken redirects and API calls.
6. **POST /api/recipes returns a plain string** — The create recipe endpoint returns the slug as a plain quoted string (e.g. `"chicken-gyros-1"`), NOT a JSON object. Parse with `result.strip().strip('"')`, not `json.load()`.
6. **POST /api/recipes does NOT parse structured ingredients** — Sending `recipeIngredient` arrays via the create API creates a stub recipe with a single placeholder ingredient. The only reliable way to get rich recipe data into Mealie is via URL scraping (`POST /api/recipes/create/url`). For recipes from sites that block scrapers (Reddit, AllRecipes, etc.), manually enter the recipe in Mealie's UI, then use the sync script.
7. **Image upload** — Use `POST /api/recipes/{slug}/image` with multipart form data. The `image` field is `None` until an image is uploaded. Users can also upload via the Mealie web UI.
8. **Firewall blocks port 9925** — Only ports 22 and 80 are open by default. If the user can't access Mealie, either open the port (`ufw allow 9925/tcp`) or set up an nginx reverse proxy on port 80.
