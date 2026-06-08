---
name: people-agent
description: "Geeves People Graph Agent — manage the People table, Person Notes, and Conversation Log. Use when adding people, looking up people, adding notes about people, logging conversations, or when the user mentions a person by name, relationships, dietary needs, allergies, birthdays, gift interests, or social preferences."
version: 1.0.0
author: Geeves
---

# People Graph Agent

Manages the `People` table and its linked companions (`Person Notes`, `Conversation Log`). The spine of the Geeves system — every other module links back to People.

## Tables

| Table | ID | Purpose |
|-------|----|---------|
| `People` | `tbl1WMPtQhWYW7bTI` | Everyone David knows |
| `Person Notes` | `tbl6hnxzXXmWFkVfh` | Timestamped freeform notes about a person |
| `Conversation Log` | `tbl2dbgksA9XveLcx` | Debrief notes after seeing someone |

## Key Fields (People)

### Core
| Field | Type | Purpose |
|-------|------|---------|
| `Name` | single line text | Full name (primary field) |
| `Relationship type` | single select | Me / Spouse / Family / Close friend / Friend / Colleague / Acquaintance / Other |
| `Tier` | single select | Tier 1 / Tier 2 / Tier 3 / Tier 4 |
| `Birthday` | date | No year required if unknown |
| `Phone` | phoneNumber | For contact matching |
| `Email` | email | Email address |
| `Photo` | multipleAttachments | For guest briefings |

### Food & Diet
| Field | Type | Purpose |
|-------|------|---------|
| `Dietary reqs` | multipleSelects | Vegetarian / Vegan / Pescatarian / Halal / Kosher / Gluten-free / Dairy-free / None |
| `Allergy list` | multipleSelects | Nuts / Shellfish / Eggs / Dairy / Gluten / Soy / Other |
| `Food dislikes` | multilineText | Foods they dislike |
| `Food preferences` | multilineText | Foods they love |
| `Portion notes` | singleLineText | e.g. "small eater" / "big appetite" |

### Social & Personal
| Field | Type | Purpose |
|-------|------|---------|
| `How I know them` | singleLineText | Origin of the relationship |
| `Hobbies & interests` | multilineText | What they're into |
| `Topics they love` | multilineText | Good conversation territory |
| `Topics to avoid` | multilineText | Sensitive subjects |
| `Social style` | singleLineText | How they like to socialise |
| `Venue preferences` | multilineText | e.g. "hates loud places" |
| `Gift interests` | multilineText | What to consider for presents |
| `Gift budget range` | singleSelect | Under £20 / £20–50 / £50–100 / £100+ |
| `Anniversaries` | multilineText | Wedding, other recurring dates |

### Tracking
| Field | Type | Purpose |
|-------|------|---------|
| `Last seen` | date | Updated after each interaction |
| `Typical contact frequency` | singleSelect | Weekly / Monthly / Quarterly / Yearly / Rarely |
| `Relationship notes` | multilineText | Freeform relationship notes |

### Linked Tables
| Field | Type | Purpose |
|-------|------|---------|
| `Person Notes` | multipleRecordLinks | → Person Notes table |
| `Conversation Log` | multipleRecordLinks | → Conversation Log table |
| `Dinner Parties` | multipleRecordLinks | → Dinner Parties table |
| `Restaurant Visits` | multipleRecordLinks | → Restaurant Visits table |
| `Restaurants` | multipleRecordLinks | → Restaurants table |
| `Workouts` | multipleRecordLinks | → Workouts table |

## Airtable CRUD

Use `/root/Geeves/scripts/airtable_api.py`:

```bash
# Create a person
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "People" \
  '{"Name": "Oran", "Tier": "Tier 2", "Relationship type": "Friend"}'

# Look up a person
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "People" "filterByFormula={Name}='Oran'"

# Update a person
python3 /root/Geeves/scripts/airtable_api.py update-record appzvmonQXs4x2AlL "People" "<record_id>" \
  '{"Last seen": "2026-06-07", "Hobbies & interests": "Cycling, running"}'

# Add a person note
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "Person Notes" \
  '{"Note": "Training for a marathon", "Person": ["<people_record_id>"], "Source": "Slack"}'

# List all people
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "People"
```

**Auth:** Read `AIRTABLE_API_KEY` from `/root/.hermes/.env` via grep (never from `os.environ`).

## Workflows

### Adding a Person

1. Extract the person's name from the user's message
2. Check if they already exist in the People table
3. If new, create a People record with:
   - `Name`: the person's name
   - `Tier`: "Tier 4" (default, can be upgraded later)
   - `Relationship type`: infer from context or default to "Friend"
4. Create a Person Note with the context that was mentioned
5. Confirm back to the user

### Adding a Note About a Person

1. Extract the person's name
2. Find the person in the People table
3. Create a Person Note linked to that person
4. If the note contains dietary/allergy info, also update the relevant fields on the People record

### Looking Up a Person

1. Search the People table by name
2. Show their key details: tier, relationship, dietary, allergies, last seen
3. Show recent Person Notes (last 5)
4. Format as a readable profile summary

### Updating Person Details

1. Find the person
2. Update only the fields that changed
3. If the update is about food/dietary, update both the specific field AND add a Person Note for context
4. Confirm the update

### Logging a Conversation

1. Extract the person's name(s)
2. Create a Conversation Log record linked to the person(s)
3. Update `Last seen` on the People record
4. Extract any follow-up commitments and create Todo records

### Tier Management

Tiers represent data richness:
- **Tier 1**: David (most complete)
- **Tier 2**: Spouse, family, close friends (full profiles)
- **Tier 3**: Regular contacts (essentials)
- **Tier 4**: Everyone else (sparse — name + whatever has been captured)

Upgrade tier when enough data accumulates. The system should suggest tier upgrades when a person's record grows.

## Slack Capture

Script: `/root/Geeves/scripts/slack_capture.py`

**Trigger keywords:** "met", "person", "friend", "contact", "know", "relationship", "dietary", "allergy", "birthday", "interests", "hobbies", "gift", "social", "venue"

**Classification priority:** Person Note appears AFTER Todo, BEFORE Memory in `CATEGORY_RULES`.

### Extraction Patterns

**Person name extraction:**
- "met X" / "add X" / "about X" → X is the name
- "X's birthday" / "X is allergic" → X is the name
- "X loves/hates/likes" → X is the name
- Multi-word names: "Oran", "Sam", "John Smith"

**Dietary info:**
- "allergic to X" → Allergy list
- "doesn't eat X" / "hates X" → Food dislikes
- "loves X" / "prefers X" → Food preferences
- "vegetarian" / "vegan" / "gluten-free" → Dietary reqs

**Social info:**
- "birthday is X" → Birthday
- "into X" / "loves X" → Hobbies & interests
- "anniversary" → Anniversaries

## Cron Jobs

None yet. Future: relationship nudge (scan People.last_seen → suggest who to contact).

## Dependencies

- **All modules** — People is the spine. Recipes, Restaurants, Meals, Fitness, Events, Gifts, Occasions all link to People.

## Integration Points

- **Recipes** — cross-reference guest dietary data against recipe ingredients
- **Restaurants** — recommend based on who's dining
- **Meals** — link meal logging to people at the table
- **Fitness** — link workouts to training partners
- **Events** — guest lists link to People
- **Gifts** — gift ideas and history link to People
- **Dinner Parties** — guest lists link to People

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Get David's explicit approval before creating any Airtable table
- Thread decisions supersede reference docs
- Update this skill when conversation changes a decision
- **Never delete a person** — use Tier 4 and uncheck Active if needed

## Pitfalls

1. **Tier value mismatch:** Use exact values: `"Tier 1"`, `"Tier 2"`, `"Tier 3"`, `"Tier 4"` — NOT `"Tier 4 (other)"`.
2. **Relationship type mismatch:** Use exact values: `"Me"`, `"Spouse"`, `"Family"`, `"Close friend"`, `"Friend"`, `"Colleague"`, `"Acquaintance"`, `"Other"`.
3. **Dietary/Allergy select values:** Use exact values from the Key Fields table. MultipleSelects accept arrays: `["Nuts", "Dairy"]`.
4. **Person Notes is a separate table:** Don't try to write notes to the People table directly. Always create Person Notes records linked to the person.
5. **Name matching:** `find_person` uses exact match on the Name field. "Oran" won't match "oran". Always use proper capitalization.
6. **Linked record format:** When linking to People, pass an array of record IDs: `["recXXXX"]`.
7. **filterByFormula on linked fields:** Cannot filter People by Person Notes content directly.

## Reference

- `geeves-airtable/SKILL.md` — Airtable CRUD patterns
- `Geeves_Schema_Reference_v2.md` — full field definitions (Module 1 — People Graph)
- `geeves-airtable/references/slack-capture.md` — classification rules, extraction patterns
