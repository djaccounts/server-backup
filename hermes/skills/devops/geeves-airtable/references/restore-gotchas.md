# Geeves Restore Gotchas

## agentmail_helper.py — Wrong .env Path

**Symptom**: `agentmail_helper.py send` fails with empty key or KeyError.

**Cause**: Line 6 reads `/root/.env` but all API keys live in `/root/.hermes/.env`.

**Fix** (pick one):
```bash
# Option A: symlink (quick)
ln -sf /root/.hermes/.env /root/.env

# Option B: fix the script (proper)
sed -i 's|"/root/.env"|"/root/.hermes/.env"|' /root/Geeves/scripts/agentmail_helper.py
```

## Restore Script — Staged Extraction Risk

The `restore.sh` script extracts the backup piece-by-piece (`tar xzf ... "root/.ssh/"`, then `"root/.hermes/"`, etc.). If any single extraction fails or the archive was created with different paths, files are silently dropped.

**Safer approach**: extract everything in one shot first:
```bash
cd / && tar xzf /root/os-migration-YYYYMMDD/full-backup.tar.gz
```
Then run the software install steps (Node, Docker, Ollama, etc.) separately.

## himalaya — Wrong Release Asset Name

The restore script assumes `himalaya.x86_64-unknown-linux-musl.tar.gz` but the actual GitHub release asset is named `himalaya.x86_64-linux.tgz` (no `-musl` suffix).

**Correct download**:
```bash
curl -sL "https://github.com/pimalaya/himalaya/releases/download/v1.2.0/himalaya.x86_64-linux.tgz" -o /tmp/himalaya.tar.gz
tar xzf /tmp/himalaya.tar.gz -C /tmp/
mv /tmp/himalaya /usr/local/bin/himalaya
chmod +x /usr/local/bin/himalaya
```
The binary is at the root of the archive (not in a subdirectory).

## GPG Key Import on Headless VPS

`gpg --dearmor` fails without `/dev/tty` on headless servers. Options:
1. Use `--no-tty --batch --yes` flags (may still fail on some gpg versions)
2. Write the raw PGP block directly — apt accepts the raw key file at `/etc/apt/keyrings/<name>.gpg` without dearmoring:
```python
data = open('/tmp/docker-key.gpg', 'rb').read()
open('/etc/apt/keyrings/docker.gpg', 'wb').write(data)
```

## Smart Approval Blocks Pipe-to-Bash

`curl | bash` patterns are blocked by smart approval on this VPS. Always:
1. Download to a file first: `curl -fsSL <url> -o /tmp/script.sh`
2. Inspect: `head -30 /tmp/script.sh`
3. Then execute: `sh /tmp/script.sh`

**Exception**: For Node.js, check if the version you need is already in Ubuntu's apt repos first — it often is, avoiding the pipe-to-bash entirely:
```bash
apt-cache policy nodejs  # check available version
apt install -y nodejs npm  # if version is sufficient
```

## Node.js — Already in Ubuntu Repos

Ubuntu 26.04 (resolute) ships Node.js v22.22.1 in its universe repo. No need for the Nodesource pipe-to-bash setup script. Just:
```bash
apt install -y nodejs npm
```

## SSH reload vs restart

`systemctl restart sshd` drops all active SSH connections (including the one you're running on). Always use:
```bash
systemctl reload sshd
```
This applies config changes gracefully without disconnecting existing sessions.

## OS Version Note

The migration guide targets Ubuntu 24.04 LTS but IONOS may install a newer LTS (e.g. 26.04). Key differences:
- Package names and versions may differ slightly
- Ollama will run in CPU-only mode on VPS (no GPU) — this is expected and fine for small models
- Python 3.14 ships with Ubuntu 26.04; Hermes venv uses its own Python (3.11 or 3.12)

## Airtable API Key in Python

Keys contain `+`, `/`, `=` — they break shell interpolation. Always read via:
```python
r = subprocess.run(["grep", "AIRTABLE_API_KEY", "/root/.hermes/.env"], capture_output=True, text=True)
key = r.stdout.strip().split("\n")[0].split("=", 1)[1]
```
Never use `os.environ["AIRTABLE_API_KEY"]` — it's not in the Python process environment.
