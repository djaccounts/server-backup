# Geeves — Hermes Quick Reference

*Keep this file short. It's the cheat sheet I read before every session.*

## Project
- **Name:** Geeves
- **Airtable base:** `appzvmonQXs4x2AlL` (NEVER touch `appk0DXJthirMxTZV`)
- **Lib path:** `/root/Geeves/lib/`
- **API usage log:** `/root/Geeves/api_usage.jsonl`
- **Master Plan:** `/root/Geeves/Geeves_Master_Plan_v2.md`
- **Schema Reference:** `/root/Geeves/Geeves_Schema_Reference_v2.md`

## Model Routing
- **Sensitive** (health, marriage, private third-party) → Ollama local only
- **Ordinary** (recipes, films, todos, travel) → Hosted model (OpenRouter)
- **When in doubt → Sensitive**

## Messaging Targets
- Main channel: `slack:#geeves` (C0B7DJU5412)
- David DM: `slack:user:U0B73K4QWP5`
- Use `resolve()` from `/root/Geeves/lib/messaging.py` for named targets

## Email (AgentMail + Himalaya)
- **AgentMail inbox:** `blacksignal723@agentmail.to` (send FROM)
- **Work email:** `dj@djaccounts.com` (receive AT)
- **Himalaya:** v1.2.0, Gmail (daverj1987@gmail.com) — backup sending
- **Digest schedule:** Daily 07:00, Weekly Monday 07:00

## Google Workspace
- ✅ Authenticated (token at /root/.hermes/google_token.json, project geeves-498219)
- Used for: Calendar in morning digest, Contacts already imported

## Ollama Models (local, sensitive)
- `phi3:mini` — general reasoning (3.8B)
- `gemma2:2b` — fast/lightweight (2.6B)
- `nomic-embed-text` — embeddings (137MB)

## API Tracking
Every API call gets logged to `/root/Geeves/api_usage.jsonl`.
```python
import sys; sys.path.insert(0, "/root/Geeves/lib")
from api_usage_tracker import track
track("airtable", tokens=0, note="what I did")
```

## Core Tables (v2 schema)
| Table | ID | Notes |
|-------|----|----|
| People | tbl1WMPtQhWYW7bTI | 261 records, Tier 1-4 |
| Person Notes | tbl6hnxzXXmWFkVfh | Timestamped freeform notes per person |
| Conversation Log | tbl2dbgksA9XveLcx | Debriefs after seeing someone |
| Todos | tblTcdZQ9AIltQDfu | Timeframe, Category, Source added |
| Memory_Summaries | tblXH4eCLwM8S30cn | Hermes periodic summaries |
| Output_Log | tbldJT41dAAX1WTkC | Generated output + ratings |
| Weather_Data | tblFd4kAahIUozJsf | Daily bulletin |
| Stock_Prices | tblI1oXlNIFXrVm7f | Daily bulletin |
| Fact_of_the_Day | tblUTCWleQD61Ti2v | Daily bulletin |

## Slack Capture
- Real-time — you message me, I classify and write to Airtable
- Categories: Person Note → People, Todo → Todos, Memory → Memory_Summaries, Module Request → Output_Log, General → skipped
- Script: `/root/Geeves/scripts/slack_capture.py`

## Build Progress
- **Phase 1 (Foundation):** ✅ People graph + Capture
- **Phase 2 (Daily Bulletin):** 🔲 Wire bulletin into digest, Evening digest, Sleep/Habit/Fitness/Meal trackers
- **Phase 3+ build on demand** — ask when you need a module
