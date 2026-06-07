# Vision API Provider Status

Last tested: June 2026

## Working

| Provider | Model | Endpoint | Notes |
|----------|-------|----------|-------|
| **NVIDIA NIM** | `meta/llama-3.2-11b-vision-instruct` | `https://integrate.api.nvidia.com/v1/chat/completions` | ✅ Works. Free tier available. Key in `NVIDIA_API_KEY`. |

## Not Working (as of June 2026)

| Provider | Model | Error | Notes |
|----------|-------|-------|-------|
| **OpenRouter** | `google/gemini-2.5-flash` | HTTP 402 Payment Required | Needs account credits. Key in `OPENROUTER_API_KEY`. |
| **Google AI Studio** | `gemini-2.0-flash` | HTTP 400 API_KEY_INVALID | Key in `GOOGLE_API_KEY` is invalid/expired. Get new key at https://aistudio.google.com → "Get API key". |
| **Groq** | `llama-3.2-11b-vision-instruct` | HTTP 403 error code 1010 | Key in `GROQ_API_KEY` invalid/expired. |

## Key Extraction Pattern

API keys in `~/.hermes/.env` may contain `=`, `+`, `/` characters. Never embed in source.

```python
import subprocess
result = subprocess.run(
    ["bash", "-c", "grep NVIDIA_API_KEY /root/.hermes/.env | head -1 | sed 's/.*=//'"],
    capture_output=True, text=True
)
api_key = result.stdout.strip()
```

## Updating This Doc

When a provider's status changes (e.g., you add OpenRouter credits or regenerate a Google key), update this table and the provider priority order in `scripts/vision_recipe.py`.
