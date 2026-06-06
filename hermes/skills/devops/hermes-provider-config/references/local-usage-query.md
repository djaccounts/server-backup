# Local Token Usage Query (state.db)

Hermes stores all session token usage in a local SQLite database at `~/.hermes/state.db`.
No API call is needed — query it directly to get today's usage, per-session breakdowns, and cost.

## Schema

The `sessions` table contains:
- `id` — session identifier (e.g. `20260601_071808_0253e4e3`)
- `model` — model used (e.g. `openrouter/owl-alpha`)
- `billing_provider` — which provider was billed
- `input_tokens` — total input tokens
- `output_tokens` — total output tokens
- `cache_read_tokens` — tokens served from prompt cache
- `cache_write_tokens` — tokens written to cache
- `reasoning_tokens` — reasoning/thinking tokens
- `estimated_cost_usd` — estimated cost
- `actual_cost_usd` — actual cost (if known)
- `message_count` — number of messages in the session
- `started_at` — Unix epoch when session started
- `title` — human-readable session title (may be null)

The `messages` table contains individual messages with `token_count` per message.

## Today's Token Usage

```python
import sqlite3
from datetime import datetime, timezone

# Calculate today's start epoch (midnight UTC)
today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
today_epoch = int(today.timestamp())

conn = sqlite3.connect('/root/.hermes/state.db')
conn.row_factory = sqlite3.Row

# Per-session breakdown
rows = conn.execute("""
    SELECT id, model, input_tokens, output_tokens,
           cache_read_tokens, reasoning_tokens,
           COALESCE(actual_cost_usd, estimated_cost_usd) as cost,
           message_count
    FROM sessions
    WHERE started_at >= ?
    ORDER BY input_tokens DESC
""", (today_epoch,)).fetchall()

for r in rows:
    print(f"{r['id']}: in={r['input_tokens']:,} out={r['output_tokens']:,} "
          f"cache_r={r['cache_read_tokens']:,} cost=${r['cost']:.6f} msgs={r['message_count']}")

# Daily totals
agg = conn.execute("""
    SELECT SUM(input_tokens) as ti, SUM(output_tokens) as to2,
           SUM(cache_read_tokens) as tc,
           SUM(COALESCE(actual_cost_usd, estimated_cost_usd)) as cost,
           SUM(message_count) as msgs,
           COUNT(*) as sessions
    FROM sessions WHERE started_at >= ?
""", (today_epoch,)).fetchone()

total = (agg['ti'] or 0) + (agg['to2'] or 0)
print(f"\nToday: {total:,} tokens | ${agg['cost'] or 0:.6f} | {agg['msgs']} msgs | {agg['sessions']} sessions")
conn.close()
```

## All-Time Usage

```python
import sqlite3
conn = sqlite3.connect('/root/.hermes/state.db')
conn.row_factory = sqlite3.Row

agg = conn.execute("""
    SELECT SUM(input_tokens) as ti, SUM(output_tokens) as to2,
           SUM(cache_read_tokens) as tc,
           SUM(COALESCE(actual_cost_usd, estimated_cost_usd)) as cost,
           SUM(message_count) as msgs,
           COUNT(*) as sessions,
           MIN(started_at) as first_session,
           MAX(started_at) as last_session
    FROM sessions
""").fetchone()

print(f"All-time: {(agg['ti']+agg['to2']):,} tokens | ${agg['cost'] or 0:.6f}")
print(f"Sessions: {agg['sessions']} | Messages: {agg['msgs']}")
conn.close()
```

## Quick Shell Version

```bash
# Today's total tokens
python3 -c "
import sqlite3
conn = sqlite3.connect('/root/.hermes/state.db')
from datetime import datetime, timezone
today = int(datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0).timestamp())
r = conn.execute('SELECT SUM(i), SUM(o) FROM (SELECT input_tokens as i, output_tokens as o FROM sessions WHERE started_at >= ?)', (today,)).fetchone()
print(f'Today: {(r[0] or 0)+(r[1] or 0):,} tokens')
conn.close()
"
```

## Notes

- `started_at` is Unix epoch (seconds since 1970-01-01 UTC)
- `cache_read_tokens` can be much larger than `input_tokens` — this is normal (prompt cache hits)
- `actual_cost_usd` may be null; fall back to `estimated_cost_usd`
- Sessions with 0 tokens are empty/inactive sessions
- The DB is safe to query read-only while Hermes is running
- No API key needed — this is purely local
