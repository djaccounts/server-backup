# Self-Hosted Service Deployment Patterns

Patterns for deploying web applications on the VPS using Docker and Nginx reverse proxy.

## General Architecture

```
Internet → Nginx (port 80/443) → Docker container (internal port)
```

Nginx handles all external traffic and reverse-proxies to Docker containers on internal ports.

## Nginx Config Editing

**⚠️ The `patch()` tool blocks system paths** like `/etc/nginx/sites-enabled/default`. Use `sudo tee` via terminal:

```bash
sudo tee /etc/nginx/sites-enabled/default > /dev/null << 'NGINX'
# ... config ...
NGINX

sudo nginx -t && sudo systemctl reload nginx
```

Always test with `nginx -t` before reloading.

## Docker Compose Pattern for Web Apps

Standard pattern for a new web app:

```yaml
version: "3.8"
services:
  appname:
    image: org/image:tag
    container_name: appname
    restart: unless-stopped
    environment:
      APP_PUBLIC_URL: http://IP:PORT
    volumes:
      - appname_data:/data
    ports:
      - "127.0.0.1:PORT:CONTAINER_PORT"

volumes:
  appname_data:
    driver: local
```

Key points:
- **Bind to `127.0.0.1` (not `0.0.0.0`)** so only accessible via Nginx — Docker bypasses UFW!
- Use named volumes for data persistence
- Set `restart: unless-stopped` for resilience

## ⚠️ Docker Bypasses UFW

**Docker publishes ports directly to the host network, completely bypassing UFW firewall rules.** A container with `ports: - "0.0.0.0:9925:9000"` exposes port 9925 to the entire internet regardless of UFW.

**Always bind to localhost** unless the port needs to be public:
```yaml
# ✅ Safe — only accessible via Nginx reverse proxy
ports:
  - "127.0.0.1:8080:80"

# ❌ Dangerous — bypasses UFW, exposed to internet
ports:
  - "0.0.0.0:9925:9000"
  - "9925:9000"          # same as 0.0.0.0
```

To fix an already-exposed container:
```bash
docker stop <name> && docker rm <name>
# Recreate with 127.0.0.1 binding
docker run -d --name <name> -p 127.0.0.1:PORT:CONTAINER_PORT ...
```

## Nginx Reverse Proxy Pattern

```nginx
location /apppath {
    proxy_pass http://127.0.0.1:INTERNAL_PORT;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 300s;
    client_max_body_size 10M;
}
```

## Baserow-Specific Notes

### Domain Routing Requirement
**Baserow requires the `Host` header to match `BASEROW_PUBLIC_URL` exactly.** Without the correct Host header, Baserow returns "Site not found" (404). When using Nginx reverse proxy, ensure the Host header is passed through.

### First Startup
- First boot takes 2-3 minutes (database migrations + template sync)
- Set `BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION: "false"` to skip template sync on startup
- Health check: `curl http://localhost:PORT/` should return 302 to `/login`

### Airtable Import — API Job-Based
Baserow v2.2.2 supports Airtable import **via the jobs API** — no UI needed.

**Endpoint:** `POST /api/jobs/` with `type: "airtable"`

**Required:** A **publicly shared Airtable base URL** (not an API key). Format: `https://airtable.com/shrXXXXXXXXXXXXXX`

To create the share link: In Airtable, click "Share" → "Create a shared base link" → set to "Anyone with the link can view". **Disable the share link after import for security.**

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

Returns a job object. Poll `GET /api/jobs/{job_id}/` for progress. States: `pending` → `running` → `done` / `error`.

**Formula syntax differs** — Airtable formulas do NOT map 1:1 to Baserow formulas. Manual review required after import.

### Admin Account Creation
```bash
curl -s -X POST http://HOST/api/user/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Name","email":"email@example.com","password":"password","language":"en","authenticate":true}'
```

### Resource Requirements
- RAM: ~1-2GB for the all-in-one container
- Disk: ~1GB for app + data

## Nginx Location Block Ordering

**⚠️ Nginx processes prefix matches in order of appearance.** A generic `location /` block will catch ALL requests before more specific `location /path` blocks can match. Always put specific paths BEFORE generic ones:

```nginx
# ✅ CORRECT: specific paths first
location /mealie/ {
    proxy_pass http://localhost:9925/;
    ...
}

location / {
    proxy_pass http://127.0.0.1:8080;  # catch-all
}

# ❌ WRONG: / catches everything, /mealie never matches
location / {
    proxy_pass http://127.0.0.1:8080;
}
location /mealie/ {
    proxy_pass http://localhost:9925/;  # unreachable!
}
```

## Serving SPAs Under a Sub-Path with Nginx

When a JavaScript SPA (like Mealie) is built to serve from `/` but you need it at `/apppath`, you need TWO things:

### 1. Trailing Slash on proxy_pass (strips the prefix)

```nginx
location /mealie/ {
    proxy_pass http://localhost:9925/;  # trailing slash = strip /mealie
    ...
}
```

The trailing `/` on `proxy_pass` tells Nginx to strip `/mealie` before forwarding. So `/mealie/_nuxt/foo.js` → `/_nuxt/foo.js` to the backend.

### 2. sub_filter to Rewrite HTML Responses

The SPA's HTML still references root paths (`/_nuxt/...`, `/favicon.ico`). Use Nginx's `http_sub_module` to rewrite them:

```nginx
location /mealie/ {
    proxy_pass http://localhost:9925/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 300s;

    # Rewrite HTML responses to fix asset paths
    sub_filter_once off;
    sub_filter_types text/html;
    sub_filter 'href="/' 'href="/mealie/';
    sub_filter 'src="/' 'src="/mealie/';
    sub_filter 'action="/' 'action="/mealie/';
    sub_filter 'url("/' 'url("/mealie/';
    sub_filter 'base href="/"' 'base href="/mealie/"';
}
```

**Requirements:**
- Nginx must be compiled with `--with-http_sub_module` (check: `nginx -V 2>&1 | grep sub`)
- `sub_filter_once off` — apply to all matches, not just the first
- `sub_filter_types text/html` — only rewrite HTML (avoids corrupting binary assets)

**Also set the app's `BASE_URL`** (if it has one) to the sub-path. For Mealie:
```yaml
environment:
  BASE_URL: http://77.68.33.121/mealie
```

**Also set the app's `BASE_URL`** (if it has one) to the sub-path. For Mealie:
```yaml
environment:
  BASE_URL: http://77.68.33.121/mealie
```

**Redirect bare path to trailing slash:**
```nginx
location = /mealie {
    return 301 /mealie/;
}
```

## Port Allocation Reference

| Service | External Path | Internal Port | Container |
|---------|--------------|---------------|-----------|
| Mealie | /mealie | 9925 | mealie |
| Baserow | / (root) | 8080 | baserow |
