#!/bin/bash
# Server Backup Script
# Backs up configs, scripts, and Mealie data to a private Git repo
# Run via cron — nightly at 2am

set -e

BACKUP_DIR="/root/server-backup"
REPO_URL="git@github.com:djaccounts/server-backup.git"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="$BACKUP_DIR/backup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Backup started ==="

# --- 1. Git repo setup / pull latest ---
if [ ! -d "$BACKUP_DIR/.git" ]; then
    log "Cloning repo..."
    git clone "$REPO_URL" "$BACKUP_DIR" 2>&1 | tee -a "$LOG_FILE"
fi

cd "$BACKUP_DIR"
git pull origin main 2>&1 | tee -a "$LOG_FILE" || git pull origin master 2>&1 | tee -a "$LOG_FILE" || true

# --- 2. Nginx configs ---
log "Backing up Nginx configs..."
mkdir -p "$BACKUP_DIR/nginx"
rsync -a --delete /etc/nginx/ "$BACKUP_DIR/nginx/"

# --- 3. Systemd services (custom ones) ---
log "Backing up custom systemd services..."
mkdir -p "$BACKUP_DIR/systemd"
for svc in /etc/systemd/system/*.service; do
    [ -f "$svc" ] && cp "$svc" "$BACKUP_DIR/systemd/" 2>/dev/null || true
done

# --- 4. Cron jobs ---
log "Backing up crontab..."
crontab -l > "$BACKUP_DIR/crontab.txt" 2>/dev/null || echo "# No crontab" > "$BACKUP_DIR/crontab.txt"

# --- 5. Docker config ---
log "Backing up Docker config..."
mkdir -p "$BACKUP_DIR/docker"
cp /etc/docker/daemon.json "$BACKUP_DIR/docker/" 2>/dev/null || true
# Docker compose files
find / -maxdepth 3 -name "docker-compose*.yml" -o -name "docker-compose*.yaml" 2>/dev/null | while read f; do
    cp "$f" "$BACKUP_DIR/docker/" 2>/dev/null || true
done

# --- 6. Mealie data dump ---
log "Backing up Mealie data..."
mkdir -p "$BACKUP_DIR/mealie"
# Backup Mealie volume files (recipes, images) — sqlite3 not in container
docker run --rm \
    --volumes-from mealie \
    -v "$BACKUP_DIR/mealie:/backup" \
    alpine tar czf /backup/mealie_volume.tar.gz -C /app/data . 2>/dev/null && \
    log "Mealie volume backup OK" || log "WARNING: Mealie volume backup failed"

# --- 7. Geeves / Airtable files ---
log "Backing up Geeves files..."
mkdir -p "$BACKUP_DIR/geeves"
rsync -a --exclude='client_secret_*.json' /root/Geeves/ "$BACKUP_DIR/geeves/"

# --- 8. Hermes config (excluding secrets) ---
log "Backing up Hermes config..."
mkdir -p "$BACKUP_DIR/hermes"
cp ~/.hermes/config.yaml "$BACKUP_DIR/hermes/" 2>/dev/null || true
cp ~/.hermes/SOUL.md "$BACKUP_DIR/hermes/" 2>/dev/null || true
cp ~/.hermes/rulebook.md "$BACKUP_DIR/hermes/" 2>/dev/null || true
# Skills
rsync -a ~/.hermes/skills/ "$BACKUP_DIR/hermes/skills/" 2>/dev/null || true
# Cron jobs config
rsync -a ~/.hermes/cron/ "$BACKUP_DIR/hermes/cron/" 2>/dev/null || true
# Memories
rsync -a ~/.hermes/memories/ "$BACKUP_DIR/hermes/memories/" 2>/dev/null || true

# --- 9. SSH config (public keys only) ---
log "Backing up SSH config..."
mkdir -p "$BACKUP_DIR/ssh"
cp /root/.ssh/config "$BACKUP_DIR/ssh/" 2>/dev/null || true
cp /root/.ssh/*.pub "$BACKUP_DIR/ssh/" 2>/dev/null || true
cp /root/.ssh/authorized_keys "$BACKUP_DIR/ssh/" 2>/dev/null || true

# --- 10. Installed packages list ---
log "Backing up package list..."
dpkg --get-selections > "$BACKUP_DIR/installed_packages.txt" 2>/dev/null || true

# --- 11. Git commit and push ---
log "Committing and pushing..."
cd "$BACKUP_DIR"

# Ensure .gitignore exists
if [ ! -f .gitignore ]; then
    cat > .gitignore << 'GITIGNORE'
*.log
backup.log
mealie/mealie.db
mealie/mealie_volume.tar.gz
hermes/memories/
GITIGNORE
fi

git add -A 2>&1 | tee -a "$LOG_FILE"

if git diff --cached --quiet; then
    log "No changes to commit."
else
    git commit -m "Backup: $TIMESTAMP" 2>&1 | tee -a "$LOG_FILE"
    git push origin main 2>&1 | tee -a "$LOG_FILE" || \
    git push origin master 2>&1 | tee -a "$LOG_FILE" || \
    log "WARNING: Push failed"
fi

log "=== Backup complete ==="
