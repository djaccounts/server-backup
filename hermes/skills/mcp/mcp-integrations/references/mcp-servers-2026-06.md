# MCP Servers Evaluated — June 2026

Session: User asked about multiple APIs and wanted to add Firecrawl, PDFGate, DuckDuckGo, and CycleStreets.

## Added / Actioned

| Server | Transport | Package | Key Required | Status |
|--------|-----------|---------|-------------|--------|
| **Firecrawl** | MCP (stdio) | `firecrawl-mcp` (npm) | Yes — free tier, fc-... format | ✅ Config added to mcp_servers |
| **PDFGate** | MCP (stdio) | `@pdfgate/mcp-server` (npm) | Yes — free tier | ⏳ Pending API key from pdfgate.com |
| **DuckDuckGo** | Python skill | `ddgs` (pip) | No | ✅ Skill created in research/duckduckgo-search |
| **CycleStreets** | REST API skill | N/A (curl/Python) | Yes — free, cyclestreets.net | ✅ Skill created in devops/cyclestreets |

## Evaluated But Not Added

| Server | Type | Why Not Added |
|--------|------|--------------|
| **FutureSearch** | MCP + Python SDK | Not requested for installation; $20 free credit available |
| **LMCP** (lanchuske/local-mcp-releases) | macOS local MCP | macOS-only; user runs Ubuntu VPS. 143 tools for Mail, iMessage, Teams, Slack, etc. |
| **buYoung/skills** | Claude Code skill marketplace | Not an MCP server; Claude Code plugin format |

## Key Learnings

1. **`hermes config set` cannot write nested `env:` keys** — it tries to save to `.env` and throws "Invalid environment variable name". Always use the Python yaml method for MCP servers that need env vars.

2. **API key pattern**: Store key in `~/.hermes/.env` → reference as `${VAR_NAME}` in config.yaml → `/reload-mcp`

3. **DuckDuckGo `ddgs` package** is the maintained successor to `duckduckgo_search`. Already installed on this machine. No API key needed.

4. **No CycleStreets MCP package exists** on npm. Create a REST API skill instead (curl/Python).

5. **Firecrawl MCP** (`firecrawl-mcp` npm package) v3.20.2 confirmed working.

## Commands Cheat Sheet

```bash
# Add key to credential store
echo 'SERVICE_API_KEY=*** >> ~/.hermes/.env

# Verify key resolves (shows masked)
hermes config show | grep -i service

# Reload MCP servers (run in chat, not CLI)
/reload-mcp

# Test an MCP server directly
npx -y firecrawl-mcp --help

# Test DuckDuckGo search
python3 -c "from ddgs import DDGS; [print(r['title']) for r in DDGS().text('test', max_results=3)]"
```
