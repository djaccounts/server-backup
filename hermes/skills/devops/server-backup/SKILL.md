---
name: server-backup
description: Set up and maintain automated server backups using Git. Use when the user wants to back up server configs, Docker volumes, databases, or application data to a private Git repository. Covers initial setup (SSH auth, backup script, cron), ongoing maintenance, and adding new services to the backup scope.
---

# Server Backup

Automated server backup system using a private Git repository. Backs up configs, scripts, Docker volumes, and application data on a schedule.

## What Gets Backed Up

Typical backup scope for a VPS:
- **Nginx configs** — `/etc/nginx/` (full tree)
- **Systemd services** — custom services from `/etc/systemd/system/`
- **Crontab** — current schedule
- **Docker config** — `daemon.json`, compose files
- **Application data** — Docker volumes (via `docker run --volumes-from`)
- **Project files** — scripts, schemas, reference docs
- **Hermes config** — config.yaml, SOUL.md, rulebook, skills, cron, memories
- **SSH config** — public keys, authorized_keys, SSH config (NOT private keys)
- **Installed packages** — `dpkg --get-selections` output

## Initial Setup

### 1. SSH Key for GitHub

Generate a dedicated key on the server:
```bash
ssh-keygen -t ed25519 -C "server-backup@<IP>" -f /root/.ssh/server_backup -N ""
```

Add to `~/.ssh/config`:
```
Host github.com
    HostName github.com
    User git
    IdentityFile /root/.ssh/server_backup
    StrictHostKeyChecking no
```

Add the **public** key to GitHub → Settings → SSH Keys. Test with `ssh -T git@github.com`.

### 2. Create Private Repo

Create a private repo on GitHub. **Do NOT initialize with README** (we push to it). Note the SSH URL: `git@github.com:<user>/<repo>.git`

### 3. Backup Script

Place at `/root/server-backup/backup.sh`. Key sections:

```bash
#!/bin/bash
set -e
BACKUP_DIR="/root/server-backup"
REPO_URL="git@github.com:<user>/<repo>.git"

# Pull latest
cd "$BACKUP_DIR" && git pull origin main 2>/dev/null || true

# Nginx
rsync -a --delete /etc/nginx/ "$BACKUP_DIR/nginx/"

# Systemd (custom only)
cp /etc/systemd/system/*.service "$BACKUP_DIR/systemd/" 2>/dev/null || true

# Crontab
crontab -l > "$BACKUP_DIR/crontab.txt" 2>/dev/null || true

# Docker volumes (alpine tar method — works even when container lacks tar)
docker run --rm --volumes-from <container> \
    -v "$BACKUP_DIR/<app>:/backup" \
    alpine tar czf /backup/<app>_volume.tar.gz -C /data/path .

# Project files (exclude secrets!)
rsync -a --exclude='client_secret_*.json' /root/<project>/ "$BACKUP_DIR/<project>/"

# Hermes (specific files, not whole directory — avoids secrets)
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

### 4. .gitignore

**Critical** — must be in place BEFORE the first commit:

```
# Secrets — NEVER commit these
geeves/client_secret_*.json
hermes/auth.json
hermes/google_client_secret.json
hermes/google_token.json
ssh/server_backup
*.pem
*.key

# Large binaries
mealie/mealie_volume.tar.gz
mealie/mealie.db
*.pyc
__pycache__/

# Logs
*.log
backup.log

# Temp files
geeves/scripts/tmp/
```

### 5. Git Identity

```bash
git config --global user.email "server@<IP>"
git config --global user.name "Server Backup"
```

### 6. Cron Job

Nightly at 2am via Hermes cron:
```
Schedule: 0 2 * * *
Prompt: Run bash /root/server-backup/backup.sh and report results (last 20 lines). Report success/failure and any warnings.
```

## Pitfalls

- **GitHub Push Protection**: Scans ALL commits in history, not just the latest. If a secret was ever committed, `git rm --cached` is NOT enough — the old commit still contains it. Fix: delete `.git`, reinitialize, and commit fresh with `.gitignore` in place first.
- **`gh auth login --web` over Slack**: The device auth code expires in ~90 seconds. Slack latency makes this unreliable. Use SSH key auth instead — it's better for automated backups anyway (no tokens to expire).
- **Docker container missing tools**: Many containers (e.g., Mealie) don't include `sqlite3` or `tar`. Use `docker run --rm --volumes-from <container>` with an alpine image to access volume data instead of `docker exec`.
- **rsync copies secrets**: Always use `--exclude` patterns for credential files when using `rsync` on directories that contain secrets. Better yet, copy specific files with `cp` rather than whole directories.
- **First commit must be clean**: If you accidentally commit a secret, GitHub will block ALL pushes to that repo until the secret is purged from history. When in doubt, reinitialize the repo.

## Adding New Services

When setting up a new service on the server:
1. Add a section to the backup script for its config/data
2. Add any secret file patterns to `.gitignore`
3. Test with a manual run: `bash /root/server-backup/backup.sh`
4. Verify the push succeeded on GitHub

## References

- `references/backup-script-template.md` — full annotated backup script template
