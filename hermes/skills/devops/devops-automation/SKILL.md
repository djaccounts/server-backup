---
name: devops-automation
description: "DevOps automation: server backups via Git, webhook subscriptions for event-driven agent runs. Use when setting up automated server backups to a private Git repo, or when configuring webhooks to trigger Hermes agent runs from external services (GitHub, Stripe, CI/CD, IoT)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [devops, backup, webhook, automation, git, cron, server, events]
    related_skills: [devops-automation]
---

# DevOps Automation

Server backups via Git and webhook subscriptions for event-driven agent runs.

---

## 1. Server Backups (Git-based)

**Use when:** Backing up server configs, Docker volumes, databases, or application data to a private Git repository.

### Initial Setup

#### SSH Key for GitHub

```bash
ssh-keygen -t ed25519 -C "server-backup@<IP>" -f /root/.ssh/server_backup -N ""
# Add public key to GitHub → Settings → SSH Keys
```

Add to `~/.ssh/config`:
```
Host github.com
    HostName github.com
    User git
    IdentityFile /root/.ssh/server_backup
    StrictHostKeyChecking no
```

#### Backup Script

```bash
#!/bin/bash
set -e
BACKUP_DIR="/root/server-backup"
REPO_URL="git@github.com:<user>/<repo>.git"

cd "$BACKUP_DIR" && git pull origin main 2>/dev/null || true

# Nginx configs
rsync -a --delete /etc/nginx/ "$BACKUP_DIR/nginx/"

# Systemd services
cp /etc/systemd/system/*.service "$BACKUP_DIR/systemd/" 2>/dev/null || true

# Crontab
crontab -l > "$BACKUP_DIR/crontab.txt" 2>/dev/null || true

# Docker volumes (alpine tar method)
docker run --rm --volumes-from <container> \
    -v "$BACKUP_DIR/<app>:/backup" \
    alpine tar czf /backup/<app>_volume.tar.gz -C /data/path .

# Hermes config (specific files, not whole directory)
cp ~/.hermes/config.yaml "$BACKUP_DIR/hermes/" 2>/dev/null || true
rsync -a ~/.hermes/skills/ "$BACKUP_DIR/hermes/skills/" 2>/dev/null || true

# Commit and push
cd "$BACKUP_DIR"
git add -A
if git diff --cached --quiet; then
    echo "No changes"
else
    git commit -m "Backup: $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
fi
```

#### .gitignore

```
# Secrets — NEVER commit these
hermes/auth.json
ssh/server_backup
*.pem
*.key

# Large binaries
*.tar.gz
*.pyc
__pycache__/
```

#### Cron Job

Schedule via Hermes cron:
```
Schedule: 0 2 * * *
Prompt: Run bash /root/server-backup/backup.sh and report results.
```

### Pitfalls

- **GitHub Push Protection:** Scans ALL commits in history. If a secret was ever committed, `git rm --cached` is NOT enough — must purge from history or reinitialize.
- **`gh auth login --web` over Slack:** Code expires in ~90s. Use SSH key auth for automated backups.
- **Docker containers missing tools:** Many containers lack `sqlite3`/`tar`. Use `docker run --rm --volumes-from` with alpine.
- **First commit must be clean:** If accidentally committed, GitHub blocks ALL pushes until purged.

---

## 2. Webhook Subscriptions

**Use when:** External services need to trigger Hermes agent runs by POSTing events.

### Setup

Enable in `~/.hermes/config.yaml`:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "generate-a-strong-secret-here"
```

Or env vars:
```bash
WEBHOOK_ENABLED=true
WEBHOOK_PORT=8644
WEBHOOK_SECRET=your-secret
```

Verify: `curl http://localhost:8644/health` → `{"status": "ok"}`

### Create Subscription

```bash
hermes webhook subscribe github-issues \
  --events "issues" \
  --prompt "New GitHub issue #{issue.number}: {issue.title}\nAction: {action}\nBody:\n{issue.body}\n\nPlease triage." \
  --deliver telegram \
  --deliver-chat-id "-100123456789"
```

Returns webhook URL and HMAC secret. Configure service to POST to that URL.

### Common Patterns

```bash
# GitHub PRs:
hermes webhook subscribe github-prs \
  --events "pull_request" \
  --prompt "PR #{pull_request.number} {action}: {pull_request.title}" \
  --skills "github-code-review" \
  --deliver github_comment

# Stripe payments:
hermes webhook subscribe stripe-payments \
  --events "payment_intent.succeeded,payment_intent.payment_failed" \
  --prompt "Payment {data.object.status}: {data.object.amount} cents" \
  --deliver telegram --deliver-chat-id "-100123456789"

# CI/CD notifications:
hermes webhook subscribe ci-builds \
  --events "pipeline" \
  --prompt "Build {object_attributes.status} on {project.name}" \
  --deliver discord --deliver-chat-id "1234567890"
```

### Direct Delivery (No Agent, Zero LLM Cost)

For simple push notifications where no reasoning is needed:

```bash
hermes webhook subscribe alerts \
  --deliver telegram --deliver-chat-id "123456789" \
  --deliver-only \
  --prompt "🎉 New match: {match.user_name} matched!"
```

### Prompt Templates

Use `{dot.notation}` for nested fields:
- `{issue.title}` — GitHub issue title
- `{pull_request.user.login}` — PR author
- `{data.object.amount}` — Stripe amount

### Security

- Each subscription gets auto-generated HMAC-SHA256 secret
- Signatures validated on every POST
- Subscriptions persist to `~/.hermes/webhook_subscriptions.json`

### Troubleshooting

1. **Gateway not running:** `systemctl --user status hermes-gateway`
2. **Port not listening:** `curl http://localhost:8644/health`
3. **Signature mismatch:** Verify secret matches `hermes webhook list`
4. **Firewall/NAT:** URL must be reachable from the service (use ngrok for local dev)
