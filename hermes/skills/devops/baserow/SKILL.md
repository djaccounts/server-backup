---
name: baserow
description: "Baserow self-hosted no-code database. Use when managing, configuring, or migrating data to/from Baserow. Covers: Docker deployment, Nginx reverse proxy setup, Airtable import, API usage, and troubleshooting."
version: 1.0.0
author: OWL
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [baserow, database, self-hosted, docker, nginx, airtable-migration]
    related_skills: [hermes-dev-admin, geeves-airtable]
---

# Baserow — Self-Hosted No-Code Database

Baserow is an open-source no-code database platform. Self-hosted on the VPS at `http://77.68.33.121`.

## Current Deployment

| Property | Value |
|----------|-------|
| URL | http://77.68.33.121 |
| Version | 2.2.2 (all-in-one) |
| Docker | `baserow/baserow:2.2.2` |
| Compose | `/root/baserow/docker-compose.yml` |
| Volume | `baserow_data` |
| Internal port | 8080 (Nginx proxies to it) |
| Admin email | daverj1987@gmail.com |
| Workspace | Geeves (id=95) |

## Nginx Config

Baserow serves from root (`/`). Mealie is at `/mealie`. Config: `/etc/nginx/sites-enabled/default`.

**⚠️ Editing Nginx config:** The `patch()` tool blocks system paths. Use:
```bash
sudo tee /etc/nginx/sites-enabled/default > /dev/null << 'NGINX'
# ... config ...
NGINX
sudo nginx -t && sudo systemctl reload nginx
```

## Baserow Domain Routing

**Baserow requires the `Host` header to match `BASEROW_PUBLIC_URL`.** Without correct Host header, returns "Site not found" (404). Ensure Nginx passes `Host: $host` in proxy headers.

**⚠️ When using a non-standard port (not 80/443), `BASEROW_PUBLIC_URL` MUST include the port:**
```
# ✅ Correct
BASEROW_PUBLIC_URL=http://77.68.33.121:8080

# ❌ Wrong — Baserow won't match requests without the port
BASEROW_PUBLIC_URL=http://77.68.33.121
```

## Airtable Migration

### Import Method — API Job-Based (NOT UI-only)
Baserow v2.2.2 supports Airtable import **via the jobs API** — no UI needed.

**Endpoint:** `POST /api/jobs/` with `type: "airtable"`

**Required:** A **publicly shared Airtable base URL** (not an API key). Format: `https://airtable.com/shrXXXXXXXXXXXXXX`

To create the share link: In Airtable, click "Share" → "Create a shared base link" → set to "Anyone with the link can view". **Disable the share link after import for security.**

**API call:**
```bash
curl -s -X POST http://77.68.33.121/api/jobs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: JWT TOKEN" \
  -d '{
    "type": "airtable",
    "workspace_id": 95,
    "airtable_share_url": "https://airtable.com/shrXXXXXXXXXXXXXX",
    "skip_files": true
  }'
```

**Response:** Returns a job object with `id`, `state: "pending"`. Poll `GET /api/jobs/{job_id}/` to track progress. States: `pending` → `running` → `done` / `error`.

**What it imports:** tables→tables, fields→fields, records→records, linked records, select options, dates, attachments (unless `skip_files: true`).

**Formula syntax differs** — Airtable formulas do NOT map 1:1 to Baserow formulas. Manual review required after import.

### Alternative CLI Tool
- `github.com/abgulati/airtable-to-baserow` for programmatic migration without public share link

### Migration Steps
1. Create a public share link for the Airtable base (disable after import)
2. Get Baserow JWT token via `POST /api/user/token-auth/`
3. Create import job via `POST /api/jobs/` with `type: "airtable"`
4. Poll job status via `GET /api/jobs/{job_id}/`
5. Verify data integrity (record counts, linked records, select options)
6. Review and fix formulas manually
7. Update all Geeves scripts/skills to use Baserow API instead of Airtable

## Baserow API

### Authentication
```bash
# Get token
curl -s -X POST http://77.68.33.121/api/user/token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"email":"daverj1987@gmail.com","password":"PASSWORD"}'
# Returns: {"token": "JWT_TOKEN", ...}

# Use token in subsequent requests
curl -s http://77.68.33.121/api/workspaces/ \
  -H "Authorization: JWT TOKEN"
```

### Key Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/user/token-auth/` | POST | Login, get JWT |
| `/api/workspaces/` | GET/POST | List/create workspaces |
| `/api/applications/workspace/{id}/` | GET/POST | List/create databases |
| `/api/database/tables/{db_id}/` | GET | List tables |
| `/api/database/rows/table/{table_id}/` | GET/POST | List/create rows |
| `/api/database/fields/table/{table_id}/` | GET/POST | List/create fields |

### API Quirks
- All write requests need `Authorization: JWT <token>` header
- Row format: `{"fields": {"field_name": value}}`
- Linked records: pass array of row IDs
- Select fields: pass the option name string
- Date fields: ISO 8601 format (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`)
- Pagination: use `page` and `size` query params

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Site not found" (404) | Host header mismatch | Ensure `BASEROW_PUBLIC_URL` matches access URL; check Nginx `proxy_set_header Host` |
| Slow first startup | Template sync | Set `BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION: "false"` |
| Container won't start | Port conflict | Check `docker ps` and `ss -tlnp` for port 8080 |
| Import fails | Airtable API limits | Wait for rate limit reset or use different API key |
| Data loss fear | Volume not persisted | Data is in named Docker volume `baserow_data`; survives container restart |

## Backup

Baserow data is in Docker volume `baserow_data`. To backup:
```bash
docker run --rm -v baserow_data:/data -v /tmp:/backup alpine tar czf /backup/baserow_backup_$(date +%Y%m%d).tar.gz -C /data .
```

## Updating

```bash
cd /root/baserow
docker compose pull
docker compose up -d
```
