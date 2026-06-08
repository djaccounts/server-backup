# Ollama Local Provider Reference

## Quick Config for Private Profile

`~/.hermes/profiles/private/config.yaml`:

```yaml
_config_version: 25

model:
  default: llama3.2
  provider: ollama-local
  base_url: http://localhost:11434/v1
  api_mode: chat_completions

providers:
  ollama-local:
    base_url: http://localhost:11434/v1
    api_mode: chat_completions
    api_key: "ollama"

agent:
  max_turns: 150

gateway:
  strict: false

display:
  personality: helpful
  compact: true
```

## Verified Models (as of June 2026)

| Model | Size | Tool support | Notes |
|-------|------|-------------|-------|
| `llama3.2` | ~2GB | ✅ Yes | Recommended for private profiles |
| `phi3:mini` | ~2.2GB | ❌ No | Fails with HTTP 400 "does not support tools" |
| `gemma2:2b` | ~1.6GB | ❌ No | Fails with HTTP 400 "does not support tools" |

## Performance (CPU-only, 8GB RAM VPS)

| Task | Latency |
|------|---------|
| Simple query | 5–30s |
| Single tool call | 1–3 min |
| Multi-tool workflow | 3–10 min |

## Setup Checklist

1. Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
2. Pull a tool-capable model: `ollama pull llama3.2`
3. Verify Ollama is running: `systemctl status ollama`
4. Create profile: `hermes profile create private`
5. Write config (see above)
6. Test: `hermes -p private chat -q "Reply with just: OK"`
7. Test tools: `hermes -p private chat -q "Run ls /root using terminal"`

## Common Issues

- **"does not support tools"**: Wrong model. Use llama3.2, not phi3:mini or gemma2:2b
- **Timeout on CPU**: Normal. Use `timeout 300` or higher for tool-calling queries
- **Ollama not running**: `systemctl start ollama`
- **Model not found**: Run `ollama list` to see downloaded models
