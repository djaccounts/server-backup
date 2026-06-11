---
name: people-agent
description: "Geeves People Graph Agent — manage the People table, Person Notes, and Conversation Log. Use when adding people, looking up people, adding notes about people, logging conversations, or when the user mentions a person by name, relationships, dietary needs, allergies, birthdays, gift interests, or social preferences."
version: 1.0.0
author: Geeves
---

# People Graph Agent

Manages the `People` table and its linked companions (`Person Notes`, `Conversation Log`). The spine of the Geeves system — every other module links back to People.

## Tables (Baserow)

| Table | Baserow ID | Purpose |
|-------|------------|---------|
| `People` | 359 | Everyone David knows |
| `Person Notes` | 368 | Timestamped freeform notes about a person |
| `Conversation Log` | 369 | **DEPRECATED** — merged into Social Log (2026-06) |
| `Social Log` | 406 | Merged from Conversation Log + social interactions (dinners, meetups, calls). Fields: Date, Type (single select), Person (link, multi), Summary, Key things to remember, Follow-up, Source |
| `Occasions` | 403 | Birthdays, anniversaries per person. Fields: Person (link), Occasion Type (single select), Date, Recurring (checkbox), Remind days before (number), Extra Notes |
| `Gift Ideas` | 404 | Running gift ideas per person. Fields: Person (link), Idea, Estimated Cost (single select), Occasion (free text), Status (single select), Extra Notes |
| `Gift History` | 405 | Gifts given. Fields: Person (link), Gift, Occasion (free text), Date Given, Rating (1-5), Extra Notes |

**All operations use Baserow, not Airtable.** Use `baserow_api.py` for CRUD. Mapping file: `/root/Geeves/baserow_mapping.json`.

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

## Baserow CRUD

Use `/root/Geeves/scripts/baserow_api.py`:

```bash
# List all people
python3 /root/Geeves/scripts/baserow_api.py list-rows People

# Create a person
python3 /root/Geeves/scripts/baserow_api.py create-row People \
  '{"Name": "Oran", "Tier": "Tier 2", "Relationship type": "Friend"}'

# Update a person
python3 /root/Geeves/scripts/baserow_api.py update-row People <row_id> \
  '{"Last Seen": "2026-06-07", "Hobbies & interests": "Cycling, running"}'

# Add a person note
python3 /root/Geeves/scripts/baserow_api.py create-row "Person Notes" \
  '{"Note": "Training for a marathon", "Person": [<people_row_id>], "Source": "Slack"}'

# Find a person
python3 /root/Geeves/scripts/baserow_api.py find People "Oran"
```

**Auth:** `BASEROW_API_TOKEN` from `/root/.hermes/.env`. The `baserow_api.py` helper reads it automatically.

**Field names** are resolved to `field_XXXX` IDs automatically via `baserow_mapping.json`. Pass human-readable names.

**Linked rows** use Baserow row IDs (integers), not Airtable record IDs. Pass as array: `[<row_id>]`.

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
- **relationships-agent** — manages Occasions, Gift Ideas, Gift History, Social Log tables

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
- Registry: `/root/Geeves/baserow_mapping.json`
- Get David's explicit approval before creating any Baserow table
- Thread decisions supersede reference docs
- Update this skill when conversation changes a decision
- **Never delete a person** — use Tier 4 and uncheck Active if needed
- **Baserow is the system of record** — Airtable is no longer used

## Pitfalls

1. **Tier value mismatch:** Use exact values: `"Tier 1"`, `"Tier 2"`, `"Tier 3"`, `"Tier 4"`.
2. **Relationship type mismatch:** Use exact values: `"Me"`, `"Spouse"`, `"Family"`, `"Close friend"`, `"Friend"`, `"Colleague"`, `"Acquaintance"`, `"Other"`.
3. **Dietary/Allergy select values:** Use exact values from the Key Fields table. MultipleSelects accept arrays: `["Nuts", "Dairy"]`.
4. **Person Notes is a separate table:** Don't try to write notes to the People table directly. Always create Person Notes records linked to the person.
5. **Name matching:** `find` uses text search on the Name field. Case-insensitive.
6. **Linked row format:** When linking to People, pass an array of Baserow row IDs (integers): `[<row_id>]`.
7. **Baserow API:** Use `baserow_api.py` helper — it handles field name→ID resolution and select option name→ID conversion. Never pass raw `field_XXXX` IDs unless you're sure.
8. **Google Contacts sync:** The sync script at `/root/Geeves/scripts/google_contacts_sync.py` exists but requires Google OAuth re-auth (refresh token expired June 2026). Run `python3 /root/Geeves/scripts/google_contacts_sync.py --dry-run` after re-auth.
9. **Junk fields in People table:** The `Films` (field_3318, link_row) and `Books` (field_3336, text) fields are legacy junk from the Airtable era. They need JWT auth to delete (database token can't delete fields). The proper Books link is `Books 2` (field_3337, link_row). Do not use the junk fields.
10. **Field deletion requires JWT:** Database token (`BASEROW_API_TOKEN`) can read fields but NOT delete or create them. Field/table schema changes need JWT via `POST /api/user/token-auth/` with admin email+password. The admin password is NOT stored in any file — David must provide it.

## Reference

- `geeves-airtable/SKILL.md` — Airtable CRUD patterns
- `Geeves_Schema_Reference_v2.md` — full field definitions (Module 1 — People Graph)
- `geeves-airtable/references/slack-capture.md` — classification rules, extraction patterns
