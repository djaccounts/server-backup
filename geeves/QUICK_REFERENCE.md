# Geeves — Hermes Quick Reference

*Keep this file short. It's the cheat sheet I read before every session.*

## Project
- **Name:** Geeves
- **Baserow:** Self-hosted at `http://77.68.33.121` — database ID 132, 46 tables
- **Lib path:** `/root/Geeves/lib/`
- **API usage log:** `/root/Geeves/api_usage.jsonl`
- **Master Plan:** `/root/Geeves/Geeves_Master_Plan_v2.md`
- **Schema Reference:** `/root/Geeves/Geeves_Schema_Reference_v2.md`
- **Mapping file:** `/root/Geeves/baserow_mapping.json` (table/field name → ID resolution)

## Model Routing
- **Sensitive** (health, marriage, private third-party) → Ollama local only
- **Ordinary** (recipes, films, todos, travel) → Hosted model (OpenRouter)
- **When in doubt → Sensitive**

## Messaging Targets
- David DM: `slack:user:U0B73K4QWP5`
- Home channel: `slack:C0B7C89HKQ9`

## Email (AgentMail + Himalaya)
- **AgentMail inbox:** `blacksignal723@agentmail.to` (send FROM)
- **Work email:** `dj@djaccounts.com` (receive AT)
- **Himalaya:** v1.2.0, Gmail (daverj1987@gmail.com) — backup sending

## Google Workspace
- ✅ Authenticated (token at /root/.hermes/google_token.json, project geeves-498219)
- Used for: Calendar in morning digest, Contacts already imported

## Ollama Models (local, sensitive)
- `phi3:mini` — general reasoning (3.8B)
- `gemma2:2b` — fast/lightweight (2.6B)
- `nomic-embed-text` — embeddings (137MB)

## API Tracking
Every API call gets logged to `/root/Geeves/api_usage.jsonl`.

## Core Tables (Baserow)
| Table | ID | Notes |
|-------|----|-------|
| People | 359 | 265 records, Tier 1-4 |
| Person Notes | 368 | Timestamped freeform notes per person |
| Conversation Log | 369 | Debriefs after seeing someone |
| Social Log | 406 | Social interactions (dinners, meetups, calls) |
| Occasions | 403 | Birthdays, anniversaries per person |
| Gift Ideas | 404 | Running gift ideas per person |
| Gift History | 405 | Gifts given, with ratings |
| Todos | 362 | Timeframe, Category, Source |
| Memory_Summaries | 360 | Hermes periodic summaries |
| Output_Log | 361 | Generated output + ratings |
| Films | 366 | Film club |
| Books | 398 | Reading list |
| Properties | 380 | Property scan results |
| Property Criteria | 381 | Search criteria |
| Restaurants | 382 | Restaurant reviews |
| Restaurant Visits | 383 | Visited restaurants |
| Workouts | 392 | Fitness workouts |
| Cycling | 396 | Garmin cycling data |
| Fitness Goals | 395 | Fitness targets |
| Recipes | 379 | Mealie recipes |
| Ingredients | 375 | Recipe ingredients |
| Dinner Parties | 376 | Dinner party planning |
| Dinner Planner | 374 | Meal planning |
| Shopping List | 377 | Shopping lists |
| Dining Preferences | 378 | Taste preferences |
| Sleep Log | 389 | Sleep tracking |
| Habits | 385 | Habit tracking |
| Habit Log | 388 | Habit entries |
| Meals | 387 | Meal tracking |
| Daily Nutrition Summary | 386 | Nutrition totals |
| Intentions | 397 | Weekly intentions |
| Digest Log | 390 | Digest history |

## Slack Capture
- Real-time — you message me, I classify and write to Baserow
- Categories: Person Note → People, Todo → Todos, Memory → Memory_Summaries, Module Request → Output_Log, Occasion → Occasions, Gift Idea → Gift Ideas, Social → Social Log, General → skipped
- Script: `/root/Geeves/scripts/slack_capture.py`

## Build Progress
- **Phase 1 (Foundation):** ✅ People graph + Capture
- **Phase 2 (Daily Bulletin):** ✅ Bulletin, Todos, Meals, Sleep, Fitness, Cycling
- **Phase 3 (Weekly Rhythm):** ✅ Weekly Digest, Recipes, Relationships & Occasions
- **Phase 4 (Lifestyle):** ✅ Film Club, Restaurants, Books, Property
- **Remaining:** Travel/Commute, Goals, Documents/Subscriptions, Wardrobe, Events, Watching/Reading, London, Phase 5
