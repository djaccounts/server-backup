# Slack Capture — Reference

## Architecture

```
Slack message → Hermes classifies in real-time → writes to correct Airtable table
```

**No cron job.** Capture is real-time — David messages in Slack, Hermes reads it, classifies it, and writes to Airtable immediately. A cron loop was initially built but David rejected it as unnecessary complexity.

**No raw message table.** One message → one useful Airtable record. General messages produce no record.

## Classification Rules (Keyword-Based)

Messages are scored against keyword lists per category. Highest score wins. Ties go to whichever category appears **first** in `CATEGORY_RULES`. No matches → "General" (skipped).

### Classification Priority (Order Matters!)

Categories are evaluated in order. **More specific categories must come BEFORE general ones** that share overlapping keywords. If two categories tie on score, the earlier one wins.

**Rule: If keyword K appears in both category A and B, and A should win, then A must appear before B in CATEGORY_RULES.**

Example: "dinner" keyword was in both Recipe and Restaurant. "Went to X for dinner" was matching Recipe because Recipe came first. Fix: moved Restaurant before Recipe-originating patterns, and removed "for dinner/lunch" from Recipe.

### Current Categories (in order)

| Priority | Category | Example Keywords | Target Table(s) |
|----------|----------|-----------------|-----------------|
| 1 | Todo | todo, task, remind, don't forget, need to, should, must, follow up, action | Todos |
| 2 | Person Note | met, person, friend, contact, dietary, allerg, birthday, interests, hobbies, gift, social, venue | People, Person Notes |
| 3 | Memory | remember, note, log, history, last time, previously, before | Memory_Summaries |
| 4 | Recipe | recipe, cook, cooking, bake, baking, ingredient, snack, dessert, dinner party, mealie, INGREDIENTS | Output_Log (for processing) |
| 5 | Meal | ate, had, for lunch, for dinner, for breakfast, calories, macros, protein, carbs, fat, food log, nutrition | Meals |
| 6 | Restaurant | restaurant, for dinner, for lunch, went to, ate at, dinner at, booking, menu, Google Rating | Restaurants, Restaurant Visits |
| 7 | Sleep/Habit | slept, sleep, bed, woke, wake, tired, rest, habit, routine, streak, completed, did my | Sleep Log, Habits, Habit Log |
| 8 | Module Request | movie, party, travel, holiday, property, house, recommend, suggest | Output_Log |
| 9 | Film Club | film club, movie club, just watched, finished watching, rated the film | Films |

## Name Extraction Algorithm

1. **Normalize contractions**: `she's` → `she is`, `he've` → `he have`, etc.
2. **Run patterns** (first match wins): "met X", "about/add X", "X's birthday", "X is/loves", "X birthday", "new person: X"
3. **Post-validate**: Skip-word list (pronouns, common verbs, "David", "Geeves")
4. **Multi-word cleanup**: If second word lowercase, take only first word

## Category Handlers

### Person Note
- Extract name → search People table
- **If found**: Create a Person Notes record linked to the person (do NOT write to a text field on People)
- **If not found**: Create new People record (Tier 4), then create a Person Note with the context
- **No name found**: Store in Memory_Summaries
- ⚠️ **Bug fixed v1.0.1**: Was incorrectly writing to non-existent `Conversation Log` text field on People table. Person Notes and Conversation Log are separate linked tables — always create records in those tables, never write link data to the People record directly.

### Todo
- Strip prefixes, extract date → create Todos record (Status="Not started", Priority=Medium)

### Memory
- Create Memory_Summaries record (Period="Ad-hoc")

### Module Request
- Create Output_Log record (Module="General")

### Meal
- Extract food description (strip prefixes like "I ate", "had", "for lunch")
- Detect meal type from keywords or time-of-day fallback
- Create Meals record with Accuracy="Estimated", Source="Slack"
- Macro estimation done by the skill (not slack_capture) when logged via conversation

### Sleep/Habit
- **Sleep**: Extract bedtime, wake time, hours slept, quality → create Sleep Log record
- **Habit**: Extract habit name → find or create Habit record → create Habit Log entry (Completed=true)
- Auto-creates habit records on first mention

## Key Pitfalls

1. **re.IGNORECASE breaks [A-Z] capture**: Post-validate names — if captured text contains lowercase words, truncate
2. **Contractions must normalize BEFORE matching**: "she's" → "she is" etc.
3. **No cron, no batch** — process each message as it arrives in conversation
4. **No Slack_Capture table** — don't create or write to one
5. **film/movie keywords match both Film Club AND Module Request** — use double-weight for Film Club strong signals; order matters
6. **airtable_post return value**: When creating records that need to be linked, `airtable_post` must return `(bool, record_id)`
7. **Restaurant name apostrophes**: Names like "England's Lane" require `(?:\\'[a-z]+)?` in regex
8. **Restaurant boundary words**: Include location words ("park", "last", "night") in boundary list
9. **Google Maps URL formats**: Use `https://www.google.com/search?q={name}+restaurant+{city}` as the reliable fallback
10. **Classification overlap**: When adding a new category, check ALL existing categories for shared keywords. If overlap exists, ensure the more specific category comes first in CATEGORY_RULES.

## Script Location

`/root/Geeves/scripts/slack_capture.py` — can also be run standalone for testing:

```bash
echo '[{"text":"met Sarah","sender":"David","sender_id":"U0B73K4QWP5","ts":"2026-06-03T12:00:00"}]' | python3 slack_capture.py --stdin --dry-run
```

## Reading API Keys in Python

```python
r = subprocess.run(["grep", "AIRTABLE_API_KEY", "/root/.hermes/.env"], capture_output=True, text=True)
key = r.stdout.strip().split("\n")[0].split("=", 1)[1]
```

Never use `os.environ.get()` — keys live in Hermes `.env`, not the shell environment.
