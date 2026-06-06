# Application-Level Cross-Provider Failover

**Pattern**: `ProviderStack` — a Python class that implements true cross-provider failover by catching HTTP errors and re-issuing requests to different base URLs.

**Source**: `/root/Geeves/lib/provider_failover.py`
**Companion**: `/root/Geeves/lib/api_usage_tracker.py` (granular per-provider token/cost tracking → `/root/Geeves/data/api_usage.jsonl`)

## When to Use

- Hermes's built-in `fallback_providers` only switches models *within the same provider*. Use `ProviderStack` when you need resilience against an entire provider being down.
- Also use when you need per-call tracking of which provider actually responded (for cost tracking, debugging, or logging).

## Provider Stack (Geeves Default)

| Priority | Provider | Base URL | Models Tried |
|----------|----------|----------|--------------|
| 1 | OpenRouter | `https://openrouter.ai/api/v1` | `openrouter/owl-alpha` |
| 2 | Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile`, then `llama-3.1-8b-instant` |
| 3 | NVIDIA | `https://integrate.api.nvidia.com/v1` | `meta/llama-3.1-70b-instruct`, then `meta/llama-3.1-8b-instruct` |
| 4 | Ollama (local) | `http://localhost:11434/v1` | `qwen2.5:7b`, then `llama3.1:8b`, then `mistral:7b` |

## Usage

```python
from lib.provider_failover import ProviderStack
from lib.api_usage_tracker import ApiTracker

stack = ProviderStack()
reply = stack.chat("your prompt")
# stack.last_provider → e.g. "nvidia"
# stack.last_model    → e.g. "meta/llama-3.1-70b-instruct"
# stack.errors        → {"openrouter/openrouter/owl-alpha": "RuntimeError: HTTP 401 ...", ...}

tracker = ApiTracker()
tracker.log(stack.last_provider, stack.last_model,
            tokens_in=..., tokens_out=...)
```

### Force a specific provider
```python
reply = stack.chat("prompt", provider="groq")
```

### Check status
```python
print(stack.status())  # {providers: [...], last_provider: ..., errors: {}}
```

### Tracker summaries
```python
tracker = ApiTracker()
print(tracker.summary())              # human-readable multi-line
print(tracker.totals_by_provider())   # dict
print(tracker.totals_by_model())      # dict
print(tracker.recent(10))             # last N calls
```

## Live Test Results (2026-06-02)

- **OpenRouter primary**: responded in ~5s ✅
- **Failover test** (OpenRouter key corrupted, Groq 403/1010): fell through to NVIDIA successfully ✅
- **Confirmed**: When OpenRouter and Groq both fail, NVIDIA picks up transparently

## Incident History

### 2026-06-02: OpenRouter provider outage
- Session was on `openrouter/free` (free tier)
- OpenRouter returned errors after 3 retries → session died with `API call failed after 3 retries: ERROR`
- Agent had no fallback — could not respond to the user at all
- **Lesson**: Application-level failover (`ProviderStack`) prevents this for scripts/cron, but the Hermes **gateway itself** still needs native `fallback_providers` configured in config.yaml for agent-level resilience

### 2026-06-03 and 2026-06-04: Gateway self-kill
- Not a provider issue — see the `command_allowlist` pitfall in the main SKILL.md
- Agent tried `systemctl --user restart hermes-gateway` after config changes → auto-approved → SIGTERM → gateway dead
- Each outage lasted 2-3 hours until manual restart

## Gotchas

- Ollama returns "no key" status when the server isn't running — the stack skips it silently
- Groq 403/1010 means free-tier plan revoked or key expired — don't assume it'll recover without user action. In testing, a previously valid Groq key returned 403 with error code 1010 without any code changes, suggesting Groq can revoke or expire free-tier access silently
- Ollama models must be pulled before use: `ollama pull qwen2.5:7b`
- The `ApiTracker` companion logs to `/root/Geeves/data/api_usage.jsonl` — one JSON line per call
- ProviderStack reads API keys from `/root/.hermes/.env` (parsed directly, not from `os.environ`) — this matches the Hermes convention where `.env` keys are NOT in the Python process environment
- **Cost estimation**: `ApiTracker` has built-in per-1K-token pricing for known models (see `MODEL_COSTS` dict). Ollama models are $0. Override or pass `cost=` explicitly for unlisted models
