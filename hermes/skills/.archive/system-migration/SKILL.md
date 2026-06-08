---
name: system-migration
description: Guidelines and scripts for migrating a Linux VPS between OS versions or after a reinstall, including restoration of Hermes Agent, SSH keys, and custom projects.
---
# System Migration

This skill captures a repeatable process for restoring a freshly installed VPS from a backup archive created before the migration.

## Prerequisites
- Backup archive (`full-backup.tar.gz`) placed in `/root/`
- Root access on the target VPS
- Internet connectivity for package installation

## Steps
1. **Run the included `restore.sh` script** located at `/root/os-migration-20260603/restore.sh`. It performs:
   - System update and base package installation
   - Restoration of SSH keys
   - Restoration of Hermes Agent configuration, memories, and skills
   - Reinstallation of Hermes Agent via `uv`
   - Restoration of custom projects (e.g., Geeves)
   - Installation of Node.js, `himalaya`, GitHub CLI, Ollama, and required models
   - Firewall (UFW) and Fail2ban setup
   - Verification of critical components
2. Review `/root/restore.log` for any warnings or errors.
3. Verify functionality:
   - SSH login
   - `hermes --version`
   - `ollama list`
   - Run your custom services (e.g., Geeves).

## Pitfalls & Tips
- **Backup location**: Ensure the archive is at `/root/full-backup.tar.gz` before running the script. The script expects this exact path.
- **Full extraction first**: After migration, extract the ENTIRE backup in one shot (`cd / && tar xzf /root/os-migration-YYYYMMDD/full-backup.tar.gz`) BEFORE running the staged restore script. The staged per-directory approach silently drops files if any single tar call fails or if the archive wasn't created with the expected paths. One-shot extraction is atomic; staged is fragile.
- **Existing Hermes installation**: If `/usr/local/lib/hermes-agent` already exists, the script updates it via `git pull`. Verify the repo URL if you have a fork.
- **Node.js**: On Ubuntu 24.04+/26.04+, Node.js 22 is already in the default `apt` repos — use `apt install -y nodejs npm` directly instead of the Nodesource setup script (which gets blocked by smart-approval for pipe-to-bash).
- **Himalaya download URL**: The restore script uses `himalaya-${ARCH}.tar.gz` with `ARCH=x86_64-unknown-linux-musl` but the actual release on GitHub is named `himalaya.x86_64-linux.tgz` (dot-separated, no `-musl` suffix). Double-check the actual asset name via the GitHub API before downloading: `curl -sL https://api.github.com/repos/pimalaya/himalaya/releases/tags/v1.2.0`.
- **Docker GPG key on headless VPS**: `gpg --dearmor` fails with "cannot open '/dev/tty'" on headless servers. Workaround: download the key with `curl -fsSL ... -o /tmp/docker-key.gpg`, then write it directly to `/etc/apt/keyrings/docker.gpg` (the raw PGP file works as a keyring). Do NOT pipe through `gpg --dearmor`.
- **Ollama models**: The script pulls `gemma2:2b` (1.6 GB), `phi3:mini` (2.2 GB), and `nomic-embed-text:latest` (274 MB). Total ~4 GB — takes 3-5 min. Can run pulls in parallel with background processes.
- **Firewall rules**: UFW opens SSH (22) and HTTP (80). Add extra ports for your services as needed.
- **Log review**: Always inspect `/root/restore.log` after execution; the script logs both stdout and errors.

## References
- `references/restore_script.md` – detailed analysis of the restore script and its sections.
- `templates/restore.sh` – the original restore script template used in this skill.

## Usage
Execute:
```bash
bash /root/os-migration-20260603/restore.sh
```
or copy the template to a new location and customize variables before running.
