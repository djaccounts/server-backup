# OpenRouter Free Tier Details

## Free Model Access

OpenRouter offers ~21 free models (as of June 2026) using the `:free` suffix convention.
These models cost exactly $0 — no prepaid credits or billing required.

Free models confirmed working:
- `openrouter/owl-alpha` — Hermes's primary model
- `meta-llama/llama-3.3-70b-instruct:free` — 131K ctx
- `meta-llama/llama-3.2-3b-instruct:free` — 131K ctx
- `openai/gpt-oss-120b:free` — 131K ctx
- `openai/gpt-oss-20b:free` — 131K ctx
- `qwen/qwen3-next-80b-a3b-instruct:free` — 262K ctx
- `qwen/qwen3-coder:free` — 1M ctx
- `google/gemma-4-26b-a4b-it:free` — 262K ctx
- `google/gemma-4-31b-it:free` — 262K ctx
- `nvidia/nemotron-3-super-120b-a12b:free` — 1M ctx
- `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` — 256K ctx
- `nvidia/nemotron-3-nano-30b-a3b:free` — 256K ctx
- `nvidia/nemotron-nano-9b-v2:free` — 128K ctx
- `nvidia/nemotron-nano-12b-v2-vl:free` — 128K ctx
- `z-ai/glm-4.5-air:free` — 131K ctx
- `moonshotai/kimi-k2.6:free` — 262K ctx
- `liquid/lfm-2.5-1.2b-thinking:free` — 32K ctx
- `liquid/lfm-2.5-1.2b-instruct:free` — 32K ctx
- `poolside/laguna-xs.2:free` — 262K ctx
- `poolside/laguna-m.1:free` — 262K ctx
- `cognitivecomputations/dolphin-mistral-24b-venice-edition:free` — 32K ctx
- `nousresearch/hermes-3-llama-3.1-405b:free` — 131K ctx

Note: The free model list changes. Check `https://openrouter.ai/api/v1/models` and filter for `:free`.

## Rate Limits

- **No daily token cap** — the free tier is not quota-based like Gemini
- **Per-minute rate limits** apply (typically 20-50 requests per minute per free model)
- **No `limit`/`limit_remaining` fields** in the auth key API — if these are `null`, the key is truly uncapped
- Standard HTTP 429 with `Retry-After` header when rate limited — just wait and retry

## Key Properties (from `/api/v1/auth/key`)

```json
{
  "is_free_tier": true,
  "limit": null,
  "limit_remaining": null,
  "usage": 0,
  "is_provisioning_key": false
}
```

- `limit: null` = no spending cap (free tier)
- `usage: 0` = no prepaid credits consumed
- The `rate_limit` field in the response is deprecated and can be ignored

## Checking Your Usage

See `references/local-usage-query.md` for the SQLite query to check today's token usage locally.

## Cost

Free models always show `"prompt": "0"` and `"completion": "0"` in the pricing. The actual cost is $0 regardless of token volume. You can process millions of tokens per day at zero cost, limited only by rate limits.
