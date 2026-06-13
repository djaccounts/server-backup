# Vision Tool Setup Reference

## How `vision_analyze` works

The `vision_analyze` tool is a Hermes built-in that sends an image to a vision-capable LLM for analysis. It requires:

1. **`vision` in the `toolsets:` list** in `~/.hermes/config.yaml`
2. **A vision-capable model** configured at the top-level `vision:` block
3. **Gateway restart** after any config change (tools load at session start, not mid-session)

## Config structure in `~/.hermes/config.yaml`

```yaml
# Toolsets list — vision must be listed here
toolsets:
- hermes-cli
- vision

# ... later in file ...

# Vision model config (top-level, NOT under auxiliary:)
vision:
  model: openrouter/anthropic/claude-sonnet-4  # must be vision-capable
```

## Checking if vision is available

The tool appears in the agent's available tools list at session start. If it's missing:
1. Check `hermes config show toolsets` includes `vision`
2. Check `vision.model` is set to a vision-capable model
3. Restart gateway: `hermes gateway restart`

## Known vision-capable models (via OpenRouter)

- `openrouter/anthropic/claude-sonnet-4` ✅
- `openrouter/anthropic/claude-sonnet-4.5` ✅
- `openrouter/google/gemini-2.0-flash` ✅
- `openrouter/google/gemini-2.5-flash` ✅
- `openrouter/owl-alpha` ❓ (may be text-only — unconfirmed)

## Common mistakes

- **Editing config but not restarting gateway** — config is only read at startup
- **Setting model under `auxiliary: vision:` instead of top-level `vision:`** — the auxiliary block is for a different purpose
- **Using a text-only model** — the tool won't load if the model doesn't support image input
- **Assuming the tool is available mid-session** — it's loaded once at session start; config changes require a new session

## Fallback when vision is unavailable

If `vision_analyze` is not available:
1. Ask the user to describe the meal in text
2. Estimate macros from the description using nutritional knowledge
3. Log to Baserow with `Source: "Slack"` and `Accuracy: "Estimated"`
4. Note: the photo download pipeline (`meal_photo_pipeline.py`) still works — only the analysis step is affected
