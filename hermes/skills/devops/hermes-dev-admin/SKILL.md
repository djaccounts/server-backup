---
name: hermes-dev-admin
description: "Hermes Agent development, administration, and Docker deployment. Use when configuring Hermes providers, managing Docker/s6 containers, debugging TUI slash commands, authoring skills, troubleshooting gateway issues, or self-hosting web applications (Baserow, etc.) with Docker + Nginx. Covers: provider config, Docker/s6 supervision tree, TUI debugging, skill authoring conventions, Nginx reverse proxy patterns, self-hosted app deployment."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, setup, configuration, docker, s6, tui, debugging, skill-authoring, providers, gateway, administration]
    related_skills: [hermes-dev-admin]
---

# Hermes Development & Administration

Configure, extend, debug, and deploy Hermes Agent.

## When to Use

- Configuring Hermes providers, fallback chains, credentials
- Docker/s6 container deployment and supervision tree
- Debugging TUI slash commands
- Authoring in-repo skills
- Troubleshooting gateway, config, or Docker issues
- Managing multi-profile gateways
- **Self-hosting web applications** (Baserow, etc.) with Docker + Nginx reverse proxy — see `references/self-hosted-services.md`

## Table of Contents

1. [Provider & Credential Configuration](#1-provider--credential-configuration)
2. [Docker / s6 Container Deployment](#2-docker--s6-container-deployment)
3. [TUI Slash Command Debugging](#3-tui-slash-command-debugging)
4. [Skill Authoring (In-Repo)](#4-skill-authoring-in-repo)
5. [Gateway & Admin](#5-gateway--admin)

---

## 1. Provider & Credential Configuration

### Config Layout

| File | Purpose |
|------|---------|
| `~/.hermes/config.yaml` | Main config (protected — use `hermes config set`) |
| `~/.hermes/.env` | API keys (redacted by `read_file`) |
| `~/.hermes/auth.json` | OAuth tokens, credential pools |

### Editing config.yaml

```bash
# Single keys (preferred):
hermes config set model.default "gemini/gemini-2.0-flash"

# Bulk edits: use Python via terminal()
```

### Fallback Providers

```yaml
fallback_providers:
  - provider: openrouter
    model: openrouter/owl-alpha
  - provider: nvidia
    model: meta/llama-3.1-70b-instruct
```

> **⚠️ `fallback_providers` ≠ Cross-Provider Failover:** Built-in fallbacks switch models within the same provider. For true cross-provider failover, use an application-level `ProviderStack` pattern.

### Credential Pools

```bash
hermes auth add openrouter --api-key sk-or-...-key
hermes auth list
```

Strategies: `fill_first` (default), `round_robin`, `least_used`, `random`

### Local / Private Profiles (Data Privacy)

For sensitive data, run a separate Hermes profile with local Ollama:

```bash
hermes profile create private
# Write config to ~/.hermes/profiles/private/config.yaml:
# model.default: llama3.2, provider: ollama-local, base_url: http://localhost:11434/v1
```

Verified tool-calling models: `llama3.2` ✅, `phi3:mini` ❌, `gemma2:2b` ❌

### Multi-Profile Gateway

> **🔴 CRITICAL:** Same Slack bot token cannot be used by two gateways. Socket Mode allows only one active WebSocket connection per app token. To run two independent agents on Slack, create a **second Slack app** with its own tokens.

### Key Pitfalls

- **Don't use `patch()` or `write_file()` on `config.yaml`** — it's protected
- **Don't try `hermes fallback add` from non-interactive session** — edit YAML directly
- **Can't restart gateway from inside itself** — user must run from SSH
- **`command_allowlist` self-kill bug:** Remove "stop/restart hermes gateway" from allowlist to prevent agents from killing their own gateway
- **Gemini key types:** AI Studio keys (`AQ.`) have 0 API inference quota. Use Cloud Console keys (`AIza`) with service account binding

---

## 2. Docker / s6 Container Deployment

### Architecture

```
/init (PID 1, s6-overlay v3.2.3.0)
├── cont-init.d/ (oneshot setup, runs as root)
│   ├── 01-hermes-setup (UID remap, chown, seed, skills sync)
│   └── 02-reconcile-profiles (restore profile gateway slots)
├── s6-rc.d/ (static services)
│   ├── main-hermes/run (no-op sleep infinity)
│   └── dashboard/run (conditional)
├── /run/service/ (tmpfs, s6-svscan watches)
│   └── gateway-<profile>/ (per-profile, runtime-registered)
└── CMD: /opt/hermes/docker/main-wrapper.sh
```

### Key Files

| Path | Role |
|------|------|
| `Dockerfile` | s6-overlay install + wiring |
| `docker/stage2-hook.sh` | UID remap, chown, seed, skills sync |
| `docker/main-wrapper.sh` | Container CMD, routes user args |
| `hermes_cli/service_manager.py` | S6 service registration/management |
| `hermes_cli/container_boot.py` | Profile reconciliation on boot |

### Quick Recipes

```sh
# Verify s6 is PID 1:
docker exec <c> sh -c 'cat /proc/1/comm'

# Inspect a profile gateway:
docker exec <c> /command/s6-svstat /run/service/gateway-<name>

# Bring up/down:
docker exec <c> /command/s6-svc -u /run/service/gateway-<name>

# Watch reconciler log:
docker exec <c> tail -n 50 /opt/data/logs/container-boot.log
```

### Adding a New Static Service

1. Create `docker/s6-rc.d/<name>/type` with `longrun\n`
2. Create `docker/s6-rc.d/<name>/run` (use `#!/command/with-contenv sh`)
3. Create empty `docker/s6-rc.d/<name>/dependencies.d/base`
4. Create empty `docker/s6-rc.d/user/contents.d/<name>`

### Common Pitfalls

- **`/command/` not on PATH for `docker exec`** — use absolute paths
- **`docker exec` defaults to root** — pass `--user hermes` or rely on stage2 chown
- **Gateway starts then exits** — profile has no model/auth configured
- **Reconciler skips profile** — missing `SOUL.md` in profile dir

---

## 3. TUI Slash Command Debugging

### Architecture

```
Python backend (hermes_cli/commands.py) → TUI gateway (tui_gateway/server.py) → Ink/TypeScript frontend
```

`COMMAND_REGISTRY` in `hermes_cli/commands.py` is the source of truth for CLI, gateway, Telegram, Slack, and autocomplete.

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Command in TUI but not autocomplete | Missing from `COMMAND_REGISTRY` | Add `CommandDef` entry |
| Command in autocomplete but doesn't work | Missing handler in gateway or frontend | Add handler in `tui_gateway/server.py` |
| Works in CLI but not TUI | Different implementations | Check both `cli.py` and TUI local handler |
| Config persists but UI doesn't update | Nanostore state not patched | Update both config and UI state |

### Adding a Slash Command

1. Add `CommandDef` to `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. Add handler in `HermesCLI.process_command()` in `cli.py`
3. (Optional) Add gateway handler in `gateway/run.py`
4. Rebuild TUI: `npm --prefix ui-tui run build`

---

## 4. Skill Authoring (In-Repo)

### Two Locations

1. **User-local:** `~/.hermes/skills/<category>/<name>/SKILL.md` — personal, created via `skill_manage(action='create')`
2. **In-repo:** `skills/<category>/<name>/SKILL.md` — committed, shipped with package. Use `write_file` + `git add`. `skill_manage(action='create')` does NOT target this tree.

### Required Frontmatter

```yaml
---
name: my-skill-name
description: Use when <trigger>. <one-line behavior>.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill]
---
```

### Size Limits

- Description: ≤ 1024 chars
- Full SKILL.md: ≤ 100,000 chars
- Peer skills: 8-14k chars (aim for this range)

### Peer-Matched Structure

```
# Title
## Overview
## When to Use
## <Topic sections>
## Common Pitfalls
## Verification Checklist
```

### Common Pitfalls

1. Using `skill_manage(action='create')` for in-repo skills — writes to `~/.hermes/skills/`, not repo
2. Leading whitespace before `---` — validator checks `content.startswith("---")`
3. Description too generic — start with "Use when..."
4. Expecting current session to see new skill — loader cached at session start

---

## 5. Gateway & Admin

### Key Paths

```
~/.hermes/config.yaml          Main config
~/.hermes/.env                 API keys
~/.hermes/auth.json            OAuth tokens, credential pools
~/.hermes/sessions/            Session store
~/.hermes/state.db             SQLite session store (FTS5)
~/.hermes/logs/                Gateway and error logs
~/.hermes/profiles/<name>/     Per-profile config, skills, sessions
```

### Provider Quick Reference

| Provider | Env var |
|----------|---------|
| OpenRouter | `OPENROUTER_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Google Gemini | `GOOGLE_API_KEY` or `GEMINI_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |
| Ollama (local) | `api_key: "ollama"` (placeholder) |

### After Config Changes

User must run from SSH (not from inside the agent):
```bash
hermes gateway restart
```

### Toolset Loading

Optional toolsets (like `vision`, `computer_use`, etc.) must be **explicitly listed** in the `toolsets:` array to load. Defining them at the bottom of config as plugins is not enough.

```yaml
# ~/.hermes/config.yaml
toolsets:
- hermes-cli
- vision        # ← must be listed here to load vision_analyze
```

If a tool appears in the manifest but isn't callable, check:
1. Is the toolset in the `toolsets:` list? `hermes config get toolsets`
2. Add it: `hermes config set toolsets '["hermes-cli", "vision"]'`
3. Restart the gateway from SSH

**Note:** `disabled_toolsets: []` being empty is not sufficient — that only means "don't disable anything", not "enable everything". The `toolsets:` list is opt-in.
