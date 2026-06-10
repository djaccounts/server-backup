---
name: mcp-integrations
description: "Model Context Protocol (MCP) integrations: native MCP client for connecting tool servers, and TouchDesigner MCP for real-time visual programming. Use when adding MCP servers to Hermes (filesystem, GitHub, databases, APIs) or when controlling TouchDesigner via the twozero MCP plugin for creative coding, audio-reactive visuals, and GLSL shaders."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, integrations, tools, TouchDesigner, twozero, creative-coding, real-time-visuals]
    related_skills: [mcp-integrations]
---

# MCP Integrations

Model Context Protocol (MCP) integrations for Hermes Agent.

---

## 1. Native MCP Client

**Use when:** Connecting MCP servers (filesystem, GitHub, databases, APIs) to Hermes Agent. Tools from MCP servers appear alongside built-in tools.

### Prerequisites

```bash
pip install mcp
# Node.js required for npx-based servers
# uv required for uvx-based servers (Python-based servers)
```

### Configuration

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  # Stdio transport (command-based):
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
    timeout: 30

  # HTTP transport (remote server):
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
    timeout: 180
```

**⚠️ Important:** `hermes config set` does NOT support nested keys under `env:` (e.g., `mcp_servers.firecrawl.env.FIRECRAWL_API_KEY` will fail with "Invalid environment variable name"). Use the Python yaml method below for reliable edits.

#### Reliable Config Editing (Python yaml)

```python
import yaml
with open("/root/.hermes/config.yaml") as f:
    config = yaml.safe_load(f)
config.setdefault("mcp_servers", {})["server_name"] = {
    "command": "npx",
    "args": ["-y", "package-name"],
    "env": {"API_KEY": "${ENV_VAR_NAME}"},
    "timeout": 60
}
with open("/root/.hermes/config.yaml", "w") as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
```

After editing, use `/reload-mcp` — no restart needed.

### Adding an MCP Server — Complete Workflow

Use this checklist every time you add a new MCP server:

1. **Get the API key** (if required) from the service's dashboard
2. **Store the key in `~/.hermes/.env`**:
   ```bash
   echo 'SERVICE_API_KEY=your-key-here' >> ~/.hermes/.env
   ```
   The `.env` file is Hermes's credential store — never read it directly, never commit it.
3. **Add the server block to `~/.hermes/config.yaml`** using the Python yaml method above. Use `${SERVICE_API_KEY}` syntax to reference the `.env` variable.
4. **Reload**: Type `/reload-mcp` in the chat
5. **Verify**: The new tools appear as `mcp_{server_name}_{tool_name}`

### Tool Naming Convention

MCP tools are registered as: `mcp_{server_name}_{tool_name}`

Examples:
- `mcp_filesystem_read_file`
- `mcp_github_list_issues`
- `mcp_time_get_current_time`

### All Config Options

| Option | Default | Description |
|--------|---------|-------------|
| `command` | — | Executable (stdio) |
| `args` | `[]` | Arguments |
| `env` | `{}` | Environment variables (reference `.env` vars with `${VAR_NAME}`) |
| `url` | — | Server URL (HTTP transport) |
| `headers` | `{}` | HTTP headers |
| `timeout` | 120 | Per-tool timeout (seconds) |
| `connect_timeout` | 60 | Connection timeout (seconds) |

### Security

- Only safe baseline env vars inherited (PATH, HOME, LANG, etc.)
- API keys must be explicitly added via `env` config
- Credential redaction in error messages
- Failed servers don't block other servers

### Troubleshooting

1. **"MCP SDK not available"** → `pip install mcp`
2. **"Requires HTTP transport"** → `pip install --upgrade mcp`
3. **Tools not appearing** → Check YAML indentation, look for `mcp_{server}_{tool}` prefix pattern
4. **`hermes config set` fails on nested `env` keys** → Use the Python yaml method instead (see above)
5. **Server connects but tools fail** → Verify the API key resolves: `hermes config show | grep -i servername` should show the key (masked)

### See Also

- `references/mcp-servers-2026-06.md` — catalog of MCP servers evaluated, with status and key learnings

---

## 2. TouchDesigner MCP (twozero)

**Use when:** Controlling a running TouchDesigner instance for creative coding, audio-reactive visuals, generative art, GLSL shaders, VJ sets, or real-time installations.

### Architecture

```
Hermes Agent → MCP (Streamable HTTP) → twozero.tox (port 40404) → TD Python
```

36 native tools. Free plugin (no payment/license — confirmed April 2026).

### Setup

```bash
# Run the setup script:
bash "${HERMES_HOME:-$HOME/.hermes}/skills/creative/touchdesigner-mcp/scripts/setup.sh"

# Manual steps (one-time):
# 1. Drag ~/Downloads/twozero.tox into TD network editor → Install
# 2. Enable MCP: twozero icon → Settings → mcp → "auto start MCP" → Yes
# 3. Restart Hermes session

# Verify:
nc -z 127.0.0.1 40404 && echo "twozero MCP: READY"
```

### Critical Rules

1. **NEVER guess parameter names.** Call `td_get_par_info` for the op type FIRST.
2. **If `tdAttributeError` fires, STOP.** Call `td_get_operator_info` on the failing node.
3. **NEVER hardcode absolute paths** in script callbacks. Use `me.parent()`.
4. **Prefer native MCP tools over `td_execute_python`.**

### Workflow

1. **Discover:** `td_get_par_info`, `td_get_hints`, `td_get_focus`, `td_get_network`
2. **Build:** `td_create_operator` (one per call), `td_set_operator_pars`, wire with `td_execute_python`
3. **Verify:** `td_get_errors`, `td_get_perf`
4. **Capture:** `td_get_screenshot`

### Environment Notes

- **Non-Commercial TD** caps resolution at 1280×1280
- **Codecs:** `prores` (macOS) or `mjpa` as fallback. H.264/H.265/AV1 require Commercial license

### Audio-Reactive GLSL (Proven Recipe)

```
AudioFileIn CHOP → AudioSpectrum CHOP (FFT=512, timeslice=ON, outlength=256)
  → Math CHOP (gain=10) → CHOP to TOP (dataformat=r, layout=rowscropped)
  → GLSL TOP input 1 (spectrum texture)
Constant TOP (rgba32float) → GLSL TOP input 0 (time)
```

Key rules: TimeSlice must stay ON for AudioSpectrum. Do NOT use Lag/Filter CHOP for spectrum smoothing. Smoothing belongs in the GLSL shader.
