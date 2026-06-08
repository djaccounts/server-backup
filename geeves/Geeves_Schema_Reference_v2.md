# Geeves — Schema Reference

*The complete Airtable data model for every module. Companion to the Master Plan: the plan describes what Geeves is and how it behaves; this document defines how its data is structured. This is the source of truth for tables, fields, and the links between them.*

> **About this document.** Like the Master Plan, this is written to be read by both the user and Hermes. Airtable is Geeves's system of record — its permanent, structured memory — and Hermes reads and writes it through an MCP connection. The structure below is what Hermes works against, so the tables, field names, and especially the links matter: they are what let information in one module inform another. Build phase by phase, keep the naming consistent, and the modules connect themselves.

---

## How to read this document

Each module lists its tables. Each table lists its fields in this format:

> **Field name** · `field type` — description

**Airtable field types used throughout:**

- `single line text` — short text
- `long text` — multi-line / notes
- `number` — numeric value
- `currency` — money (£)
- `single select` — pick one from a fixed list
- `multiple select` — pick several from a fixed list
- `checkbox` — true/false
- `date` — date (optionally with time)
- `rating` — 1–5 stars
- `attachment` — files/images
- `link` — links to a record in another table (the heart of the people graph)
- `lookup` — pulls a field from a linked record (read-only)
- `rollup` — aggregates values from linked records (count, sum, average)
- `formula` — computed from other fields
- `created time` / `last modified time` — automatic timestamps
- `autonumber` — unique sequential ID

**A note on linking:** wherever you see `link → [Table]`, that field connects this record to one or more records in another table. This is what makes Geeves intelligent — a meal links to a recipe, a recipe links to the people at a dinner, a person links to their gift history. These links are the mechanism by which the system compounds; build them as specified.

**Naming convention:** field names are kept consistent across the system. A link to a person is always `Person` or `People`. A rating is always `Rating`. A date logged is always `Date`. This consistency lets Hermes reason over the data without ambiguity and keeps the tables linking cleanly as the system grows.

**A note on capture and delivery:** Geeves takes input through Slack and sends briefings by email through AgentMail; Hermes interprets messages and routes them to the right table, and runs the digests on its own schedule. Several tables below carry a `Source` field recording how a record was created (Slack, voice, manual, an import, or a feed). These are written to support whichever input channels are connected now or later — the data model does not depend on any one channel.

---

# PHASE 1 — FOUNDATION

---

## Module 1 — People Graph

The spine of the entire system. Every person the user knows has one record here. Modules across all phases link back to this table.

### Table: `People`

> **Name** · `single line text` — full name (primary field)
> **Relationship type** · `single select` — Me / Spouse / Family / Close friend / Friend / Colleague / Acquaintance / Other
> **Tier** · `single select` — Tier 1 / Tier 2 / Tier 3 / Tier 4 (data richness level)
> **Birthday** · `date` — no year required if unknown
> **Phone** · `single line text` — used to match the person to an incoming message where a channel provides a number
> **Email** · `single line text`
> **How I know them** · `long text` — origin of the relationship
> **Photo** · `attachment` — optional; used in guest briefings
> **Dietary requirements** · `multiple select` — Vegetarian / Vegan / Pescatarian / Halal / Kosher / Gluten-free / Dairy-free / None
> **Allergies** · `multiple select` — Nuts / Shellfish / Eggs / Dairy / Gluten / Soy / Other
> **Food dislikes** · `long text` — e.g. "doesn't like coriander or blue cheese"
> **Food preferences** · `long text` — e.g. "prefers chicken to beef, loves spicy food"
> **Portion notes** · `single line text` — e.g. "small eater" / "big appetite"
> **Hobbies & interests** · `long text` — what they're into
> **Topics they love** · `long text` — good conversation territory
> **Topics to avoid** · `long text` — sensitive subjects
> **Gift interests** · `long text` — what to consider for presents
> **Gift budget range** · `single select` — Under £20 / £20–50 / £50–100 / £100+
> **Social style** · `long text` — how they like to socialise
> **Venue preferences** · `long text` — e.g. "hates loud places, loves a quiet pub"
> **Anniversaries** · `long text` — wedding, other important recurring dates
> **Last seen** · `date` — updated after each interaction
> **Typical contact frequency** · `single select` — Weekly / Monthly / Quarterly / Yearly / Rarely
> **Relationship notes** · `link → Person Notes` — timestamped freeform entries
> **Conversation log** · `link → Conversation Log` — debrief notes after seeing them
> **Gifts given** · `link → Gift History` — past presents
> **Gift ideas** · `link → Gift Ideas` — captured ideas for them
> **Occasions** · `link → Occasions` — birthdays/events tracked for them
> **Events invited to** · `link → Events` — events considered for them
> **Created** · `created time`

### Table: `Person Notes`

Timestamped freeform notes about a person, so a running record builds up rather than overwriting one field.

> **Note** · `long text` — the note itself (primary field)
> **Person** · `link → People`
> **Date added** · `created time`
> **Source** · `single select` — Manual / Slack / Voice
> **Active** · `checkbox` — uncheck to retire without deleting

### Table: `Conversation Log`

The conversation-memory record: a short debrief after seeing someone.

> **Summary** · `long text` — what was discussed, their news (primary field)
> **Person** · `link → People` — can link several people for a group occasion
> **Date** · `date`
> **Key things to remember** · `long text` — promotions, moves, life events
> **Follow-ups created** · `link → Follow-ups` — any commitments extracted
> **Source** · `single select` — Manual / Slack / Voice
> **Logged** · `created time`

---

## Module 2 — Capture

Capture is how a passing message becomes a filed fact. It is mostly Hermes's work — interpreting an incoming message and writing it to the right table — but a log table records what came in and where it was routed, which is useful for auditing and for catching anything that didn't route cleanly.

### Table: `Input Log`

> **Raw message** · `long text` — exactly what was sent (primary field)
> **Channel** · `single select` — Slack / Voice / WhatsApp / Telegram / Email / Other
> **Message type** · `single select` — Text / Voice note
> **Transcription** · `long text` — transcription if voice
> **Interpreted intent** · `single select` — Log meal / Log workout / Add person note / Add todo / Add gift idea / Journal / Other
> **Routed to** · `single line text` — which table the data was written to
> **Status** · `single select` — Success / Failed / Needs review
> **Detail** · `long text` — note if routing failed or needed review
> **Received** · `created time`

---

# PHASE 2 — DAILY BULLETIN

---

## Module 3 — Morning Digest

Pulls from many tables; writes a record of each briefing sent.

### Table: `Digest Log`

> **Date** · `date` (primary field, with time)
> **Type** · `single select` — Morning / Evening / Weekly / Monthly
> **Content** · `long text` — full text of the briefing sent
> **Sections included** · `multiple select` — Weather / Calendar / Todos / Dinner / Reminders / News / Stocks / Words / Fitness / Meals
> **Delivered via** · `single select` — Email / Slack
> **Delivery status** · `single select` — Sent / Failed
> **Sent** · `created time`

### Table: `Stocks Watchlist`

> **Ticker** · `single line text` (primary field) — e.g. AAPL
> **Name** · `single line text` — e.g. Apple Inc.
> **Type** · `single select` — Stock / ETF / Crypto / Index
> **Show in digest** · `checkbox`

### Table: `Word List` (Russian)

> **Word** · `single line text` (primary field)
> **Pronunciation** · `single line text` — transliteration
> **Meaning** · `single line text`
> **Example sentence** · `long text`
> **Part of speech** · `single select` — Noun / Verb / Adjective / Adverb / Phrase
> **Used** · `checkbox` — marked once featured
> **Date used** · `date`
> **Difficulty** · `single select` — Beginner / Intermediate / Advanced

*(The English word of the day is generated live, so it needs no table — though an `English Word Log` with the same shape can be added if a record is wanted.)*

### Table: `News Sources`

> **Source name** · `single line text` (primary field)
> **Feed URL** · `single line text` — RSS feed
> **Category** · `single select` — Science / Tech / Culture / London / World / Other
> **Active** · `checkbox`

---

## Module 4 — To-Do List

### Table: `Todos`

> **Task** · `single line text` (primary field)
> **Timeframe** · `single select` — Short term / Mid term / Long term
> **Status** · `single select` — Not started / In progress / Done
> **Due date** · `date` — optional
> **Priority** · `single select` — Low / Medium / High
> **Category** · `single select` — Personal / Work / Household / Health / Errand / Other
> **Linked goal** · `link → Goals` — if this task supports a goal
> **Source** · `single select` — Manual / Slack / Voice / Goal auto-gen
> **Completed date** · `date`
> **Created** · `created time`

---

## Module 5 — Sleep + Habit Tracker

### Table: `Sleep Log`

> **Date** · `date` (primary field)
> **Bedtime** · `single line text` — e.g. 23:15
> **Wake time** · `single line text` — e.g. 06:45
> **Hours slept** · `number` — entered or computed
> **Quality** · `rating` — 1–5
> **Notes** · `long text` — woke in night, etc.
> **Logged** · `created time`

### Table: `Habits`

The habits the user wants to build (the definitions).

> **Habit** · `single line text` (primary field) — e.g. "Russian practice"
> **Frequency target** · `single select` — Daily / Weekdays / 3x week / Weekly
> **Category** · `single select` — Health / Learning / Mindfulness / Household / Other
> **Active** · `checkbox`
> **Streak** · `rollup` — count of consecutive completions from Habit Log

### Table: `Habit Log`

Each daily completion.

> **Date** · `date` (primary field)
> **Habit** · `link → Habits`
> **Completed** · `checkbox`
> **Logged** · `created time`

---

## Module 6 — Fitness Tracker

### Table: `Workouts`

> **Date** · `date` (primary field, with time)
> **Type** · `single select` — Gym / Run / Cycle / Walk / Swim / Yoga / Class / Other
> **Duration (mins)** · `number`
> **Distance (km)** · `number` — for cardio
> **Energy level** · `rating` — 1–5, how it felt
> **Perceived difficulty** · `rating` — 1–5
> **Notes** · `long text`
> **Exercises** · `link → Exercise Log` — for gym sessions
> **Source** · `single select` — Manual / Slack / Voice / Strava / Google Fit
> **Logged** · `created time`

### Table: `Exercise Log`

Optional detail for gym sessions.

> **Exercise** · `single line text` (primary field) — e.g. Bench press
> **Workout** · `link → Workouts`
> **Sets** · `number`
> **Reps** · `single line text` — e.g. "8, 8, 6"
> **Weight (kg)** · `single line text` — e.g. "60, 60, 65"

### Table: `Fitness Goals` *(shared with Meal Tracker)*

> **Goal type** · `single select` (primary) — Cut / Bulk / Maintain / Endurance / Strength
> **Daily calorie target** · `number`
> **Daily protein target (g)** · `number`
> **Weekly workout target** · `number`
> **Start date** · `date`
> **Active** · `checkbox`
> **Notes** · `long text` — e.g. "training for a 10k in September"

---

## Module 7 — Meal Tracker

### Table: `Meals`

> **Description** · `single line text` (primary field) — what was eaten
> **Date** · `date` (with time)
> **Meal type** · `single select` — Breakfast / Lunch / Dinner / Snack
> **Calories (est)** · `number` — estimate
> **Protein (g)** · `number`
> **Carbs (g)** · `number`
> **Fat (g)** · `number`
> **From recipe** · `link → Recipes` — if cooked from a saved recipe (carries its macros)
> **Accuracy** · `single select` — Estimated / Barcode / From recipe
> **Source** · `single select` — Manual / Slack / Voice
> **Logged** · `created time`

### Table: `Daily Nutrition Summary`

A daily roll-up for digests and trends (can be a view or a generated table).

> **Date** · `date` (primary field)
> **Total calories** · `rollup` — sum from Meals
> **Total protein** · `rollup`
> **Total carbs** · `rollup`
> **Total fat** · `rollup`
> **Vs target** · `formula` — calories vs Fitness Goals target

---

# PHASE 3 — WEEKLY RHYTHM

---

## Module 8 — Weekly Digest + Intentions

Uses the shared `Digest Log` (Type = Weekly) plus an intentions table.

### Table: `Intentions`

> **Intention** · `single line text` (primary field)
> **Week starting** · `date`
> **Type** · `single select` — Accomplish / Let go of / Focus
> **Status** · `single select` — Set / Achieved / Missed / Carried over
> **Source** · `single select` — Suggested / Manual
> **Reflection** · `long text` — end of week note
> **Created** · `created time`

---

## Module 9 — Recipe App

One of the richest modules. Links to people (for dinner parties) and to meals (for logging what was eaten).

**Architecture:** Mealie (self-hosted, port 9925) is the recipe engine — URL scraping, ingredient parsing, method, nutrition, scaling, images. Airtable holds metadata and cross-module links. Sync direction: Mealie → Airtable (one-way, on-demand). Full recipe detail lives in Mealie; Airtable connects recipes to people, meals, dinner parties, and shopping lists.

### Table: `Recipes`

Slim metadata table — the connective layer. Full recipe content (method, nutrition, images) lives in Mealie and is accessed via `Mealie Slug`.

> **Name** · `single line text` (primary field)
> **Mealie Slug** · `single line text` — e.g. "horiatiki-greek-village-salad-1", links to full recipe in Mealie
> **Source URL** · `single line text` — original recipe URL
> **Cuisine** · `single select` — Italian / Indian / Thai / British / Mexican / Chinese / French / Japanese / Korean / Other
> **Meal type** · `multiple select` — Breakfast / Lunch / Dinner / Side / Dessert / Snack
> **Quality rating** · `number` — 1–5, how good it was (user-rated)
> **Will do again** · `single select` — Never / Rarely / Sometimes / Often / Staple
> **Favourite** · `checkbox` — quick filter for "what's for dinner?" queries
> **Ingredients** · `link → Ingredients` — one recipe links to many ingredients
> **Photo** · `attachment` — Mealie image
> **Notes** · `long text` — freeform
> **Times cooked** · `rollup` — count from linked Meals (added when Meals table exists)
> **Last cooked** · `date` — from Meals
> **Created** · `created time`

*Fields stored in Mealie (not duplicated in Airtable):* Difficulty, Prep/Cook time, Servings, Method, Hints & tips, Calories/Protein per serving, Dietary tags. These are fetched from Mealie's API on demand.

### Table: `Ingredients`

Normalised ingredient list synced from Mealie. Enables shopping lists, dietary cross-checks, and seasonality filtering. LLM categorises each ingredient at sync time.

> **Ingredient** · `single line text` (primary field) — e.g. "Chicken thighs"
> **Recipe** · `link → Recipes` — back-link to parent recipe
> **Quantity** · `single line text` — e.g. "500g", "2 tbsp"
> **Category** · `single select` — Meat / Fish / Veg / Fruit / Dairy / Grain / Spice / Pantry / Other
> **Seasonal** · `multiple select` — Jan / Feb / Mar / Apr / May / Jun / Jul / Aug / Sep / Oct / Nov / Dec
> **Created** · `created time`

### Table: `Dinner Parties`

The standout feature — cross-references guests against recipes, auto-compiles dietary constraints.

> **Event name** · `single line text` (primary field)
> **Date** · `date`
> **Guests** · `link → People` — carries everyone's dietary data
> **Chosen recipes** · `link → Recipes`
> **Dietary constraints (auto)** · `long text` — compiled from guests' allergy/dietary records
> **Menu notes** · `long text`
> **Shopping list generated** · `checkbox`
> **Status** · `single select` — Planning / Confirmed / Done
> **Created** · `created time`

### Table: `Dinner Planner`

Forward-looking "what's for dinner tonight" table. Distinct from Meals (which is backward-looking nutrition log).

> **Date** · `date` (primary field)
> **Meal** · `single line text` — free text description
> **Recipe** · `link → Recipes` — optional
> **Prep notes** · `long text` — e.g. "defrost chicken by noon"
> **Status** · `single select` — Planned / Shopping / Cooking / Done
> **Created** · `created time`

### Table: `Shopping List`

Ad-hoc and dinner-party shopping lists. Items auto-generated from recipes or added manually.

> **Item** · `single line text` (primary field)
> **Category** · `single select` — Meat / Fish / Veg / Fruit / Dairy / Grain / Spice / Pantry / Household / Other
> **Quantity** · `single line text` — e.g. "500g", "2 bottles"
> **Source** · `single select` — Recipe / Dinner Party / Manual
> **Recipe** · `link → Recipes` — optional
> **Purchased** · `checkbox` — ticked off in shop
> **Created** · `created time`

### Table: `Recipe Context`

Module context table — permanent knowledge/preferences fed into prompts before any recipe task.

> **Preference** · `single line text` (primary field) — e.g. "prefers quick weeknight meals"
> **Detail** · `long text` — the actual context
> **Source** · `single select` — Inferred / Manual
> **Updated** · `last modified time`

### Table: `Recipe Output Log`

What Hermes generated, when, how it was rated. Prevents repetition, enables learning.

> **Output** · `long text` (primary field) — what was generated
> **Type** · `single select` — Suggestion / Shopping List / Meal Plan / Dinner Party Plan / Email / PDF
> **Recipe(s)** · `link → Recipes`
> **Rating** · `number` — 1–5
> **Feedback** · `long text`
> **Created** · `created time`

---

## Module 9b — Dining Preferences *(shared cross-module bridge)*

Populated automatically by Hermes from recipe ratings, meal frequency, and ingredient patterns. Read by the future Restaurant Finder module to personalise recommendations.

> **Preference** · `single line text` (primary field) — e.g. "Loves pizza", "Dislikes coriander"
> **Category** · `single select` — Cuisine / Dish / Style / Avoid / Dietary
> **Confidence** · `single select` — Strong / Moderate / Emerging
> **Evidence** · `long text` — what data supports this preference
> **Source modules** · `multiple select` — Recipes / Meals / People Graph
> **Last updated** · `date`

---

## Module 10 — Travel + Commute Assistant

Mostly Hermes reading the calendar and live transit data. A small reference table helps.

### Table: `Routes`

> **From** · `single line text` (primary field) — usually home
> **To** · `single line text` — common destinations
> **Default mode** · `single select` — Tube / Bus / Walk / Cycle / Train / Drive
> **Typical duration (mins)** · `number`
> **Notes** · `long text` — e.g. "Northern line, avoid Bank"

---

## Module 11 — Relationship + Occasion Tracker

Reads heavily from the People Graph. Adds occasion tracking.

### Table: `Occasions`

> **Occasion** · `single line text` (primary field) — e.g. "Mum's birthday"
> **Person** · `link → People`
> **Type** · `single select` — Birthday / Anniversary / Other
> **Date** · `date`
> **Recurring** · `checkbox`
> **Days before to remind** · `number` — e.g. 30 for gift planning
> **Send card** · `checkbox`
> **Send flowers** · `checkbox`
> **Message drafted** · `checkbox`
> **Status this year** · `single select` — Upcoming / Gift sorted / Card sent / Done
> **Notes** · `long text`

---

## Module 12 — Gift Ideas Running List

### Table: `Gift Ideas`

> **Idea** · `single line text` (primary field) — e.g. "Pottery class voucher"
> **Person** · `link → People`
> **Occasion** · `link → Occasions` — optional
> **Estimated cost** · `currency`
> **Status** · `single select` — Idea / Shortlisted / Purchased / Rejected
> **Link** · `single line text` — URL if relevant
> **Notes** · `long text`
> **Captured** · `created time`
> **Source** · `single select` — Manual / Slack / Voice

### Table: `Gift History`

What has actually been given, so nothing repeats and the system learns what landed.

> **Gift** · `single line text` (primary field)
> **Person** · `link → People`
> **Occasion** · `single line text` — e.g. "Birthday 2024"
> **Date given** · `date`
> **Cost** · `currency`
> **How it landed** · `single select` — Loved it / Liked it / Neutral / Missed
> **Notes** · `long text`

---

## Module 13 — Skills + Goals Tracker

### Table: `Goals`

> **Goal** · `single line text` (primary field) — e.g. "Learn to drive"
> **Timeframe** · `single select` — Short term / Mid term / Long term
> **Category** · `single select` — Health / Learning / Career / Personal / Creative / Other
> **Target date** · `date`
> **Status** · `single select` — Not started / In progress / On hold / Achieved / Abandoned
> **Progress notes** · `long text`
> **Milestones** · `link → Milestones`
> **Linked todos** · `link → Todos`
> **Last activity** · `last modified time` — used to flag stale goals
> **Created** · `created time`

### Table: `Milestones`

> **Milestone** · `single line text` (primary field)
> **Goal** · `link → Goals`
> **Target date** · `date`
> **Achieved** · `checkbox`
> **Achieved date** · `date`

---

## Module 14 — Document + Subscription Organiser

### Table: `Documents`

> **Document** · `single line text` (primary field) — e.g. "Passport"
> **Type** · `single select` — ID / Vehicle / Insurance / Home / Health / Financial / Other
> **Expiry / renewal date** · `date`
> **Reminder days before** · `multiple select` — 60 / 30 / 7
> **Reference number** · `single line text` — not for passwords or sensitive numbers
> **Notes** · `long text`
> **Status** · `single select` — Valid / Expiring soon / Expired / Renewed

### Table: `Subscriptions`

> **Service** · `single line text` (primary field) — e.g. Spotify
> **Cost** · `currency`
> **Billing cycle** · `single select` — Monthly / Annual / Quarterly
> **Renewal date** · `date`
> **Category** · `single select` — Entertainment / Software / News / Fitness / Other
> **Worth it?** · `rating` — 1–5
> **Status** · `single select` — Active / Reviewing / Cancelled
> **Notes** · `long text`

---

# PHASE 4 — LIFESTYLE MODULES

---

## Module 15 — Wardrobe App

### Table: `Wardrobe Items`

> **Item** · `single line text` (primary field) — e.g. "Navy wool overcoat"
> **Type** · `single select` — Top / Bottom / Outerwear / Footwear / Accessory / Suit
> **Colour** · `multiple select` — Black / White / Navy / Grey / Brown / Beige / Green / Blue / Other
> **Season** · `multiple select` — Spring / Summer / Autumn / Winter / All
> **Occasions** · `multiple select` — Casual / Smart casual / Formal / Work / Sport / Loungewear
> **Photo** · `attachment`
> **Last worn** · `date`
> **Wear count** · `number`
> **Condition** · `single select` — New / Good / Worn / Replace soon
> **Added** · `created time`

### Table: `Outfit Log`

> **Date** · `date` (primary field)
> **Items** · `link → Wardrobe Items`
> **Occasion** · `single line text`
> **Rating** · `rating` — how it felt
> **Suggested by Geeves** · `checkbox`
> **Feedback** · `single select` — Loved it / Fine / Wouldn't repeat

### Table: `Style Context`

The preference table for wardrobe.

> **Note** · `long text` (primary field) — e.g. "into quiet luxury, avoid dry-clean only"
> **Type** · `single select` — Preference / Avoid / Aspiration / Body note
> **Active** · `checkbox`

---

## Module 16 — Restaurant Tracker + Recommendations

### Table: `Restaurants`

> **Name** · `single line text` (primary field)
> **Cuisine** · `single select` — same options as Recipes
> **Area** · `single line text` — e.g. "Shoreditch"
> **Price range** · `single select` — £ / ££ / £££ / ££££
> **Visited** · `checkbox`
> **My rating** · `rating` — 1–5
> **Notes** · `long text`
> **Good for** · `multiple select` — Date night / Casual / Business / Group / Special occasion
> **Noise level** · `single select` — Quiet / Moderate / Loud
> **Would return** · `checkbox`
> **Visits** · `link → Restaurant Visits`
> **Added** · `created time`

### Table: `Restaurant Visits`

> **Date** · `date` (primary field)
> **Restaurant** · `link → Restaurants`
> **Companions** · `link → People` — who came along
> **Occasion** · `single line text`
> **Rating** · `rating`
> **Notes** · `long text`

---

## Module 17 — Events, Gigs + Places (Discovery)

### Table: `Event Sources`

> **Source** · `single line text` (primary field) — e.g. a listings feed
> **Feed URL** · `single line text`
> **Type** · `single select` — Music / Theatre / Art / Food / General
> **Active** · `checkbox`

### Table: `Events`

> **Event** · `single line text` (primary field)
> **Date** · `date`
> **Venue** · `single line text`
> **Type** · `single select` — Gig / Theatre / Exhibition / Festival / Talk / Other
> **Source** · `single line text` — where it was discovered
> **URL** · `single line text`
> **Taste match score** · `number` — a 1–10 relevance score
> **Status** · `single select` — Suggested / Interested / Booked / Dismissed / Attended
> **Potential companions** · `link → People` — who might enjoy it
> **Added to calendar** · `checkbox`
> **Notes** · `long text`

### Table: `Taste Profile`

What events are filtered against.

> **Preference** · `long text` (primary field) — e.g. "loves electronic music, indie cinema, modern art"
> **Type** · `single select` — Like / Dislike / Genre / Artist / Venue
> **Active** · `checkbox`

---

## Module 18 — Movies, TV + Books

### Table: `Watchlist`

> **Title** · `single line text` (primary field)
> **Type** · `single select` — Film / TV series / Documentary
> **Status** · `single select` — Want to watch / Watching / Watched
> **External rating** · `number` — pulled from a ratings source
> **My rating** · `rating` — 1–5
> **Genre** · `multiple select` — Drama / Comedy / Thriller / Sci-fi / Documentary / Horror / Other
> **Where to watch** · `single line text` — Netflix, etc.
> **Recommended by** · `link → People` — optional
> **Notes** · `long text`
> **Watched date** · `date`

### Table: `Reading List`

> **Title** · `single line text` (primary field)
> **Author** · `single line text`
> **Status** · `single select` — Want to read / Reading / Read
> **My rating** · `rating` — 1–5
> **Genre** · `multiple select` — Fiction / Non-fiction / Biography / History / Science / Other
> **Recommended by** · `link → People` — optional
> **Notes / summary** · `long text` — summary on completion
> **Finished date** · `date`

---

## Module 19 — Property Search

### Table: `Properties`

> **Address** · `single line text` (primary field)
> **URL** · `single line text` — listing link
> **Price** · `currency`
> **Bedrooms** · `number`
> **Area** · `single line text`
> **Property type** · `single select` — Flat / Terraced / Semi / Detached / Maisonette
> **Garden** · `single select` — None / Yard / Small / Medium / Large
> **Square footage** · `number`
> **Assessment** · `long text` — appraisal against criteria
> **Match score** · `number` — 1–10 against criteria
> **Status** · `single select` — New / Interested / Viewing booked / Viewed / Dismissed
> **My notes** · `long text`
> **First seen** · `created time`

### Table: `Property Criteria`

The deal-breakers and preferences (the context table).

> **Criterion** · `long text` (primary field) — e.g. "real lawn essential, concrete is a dealbreaker"
> **Type** · `single select` — Must have / Nice to have / Dealbreaker / Budget
> **Active** · `checkbox`

---

## Module 20 — London To-Do + Holiday Planner

### Table: `London To-Do`

> **Activity** · `single line text` (primary field)
> **Category** · `single select` — Restaurant / Bar / Walk / Museum / Show / Market / Day trip / Other
> **Area** · `single line text`
> **Best season** · `multiple select` — Spring / Summer / Autumn / Winter / Any
> **Status** · `single select` — Want to do / Planned / Done
> **Companions** · `link → People` — who to do it with
> **Notes** · `long text`
> **Added** · `created time`

### Table: `Holiday Ideas`

> **Destination** · `single line text` (primary field)
> **Type** · `single select` — City break / Beach / Adventure / Cultural / Relaxation
> **Estimated budget** · `currency`
> **Best time to go** · `multiple select` — months
> **Duration** · `single line text` — e.g. "long weekend" / "2 weeks"
> **Status** · `single select` — Idea / Researching / Planning / Booked / Been
> **Companions** · `link → People`
> **Notes** · `long text`

---

# PHASE 4 — LIFESTYLE & DISCOVERY

---

## Module 21 — Restaurants

Restaurant tracking and review module. Logs visits, captures detailed feedback (including separate ratings and notes for David and wife), and builds a taste profile over time via the shared `Dining Preferences` table. Recommendations are powered by comparing restaurant attributes against your dining preferences and visit history.

### Table: `Restaurants`

Master record for every restaurant visited or want to try.

> **Name** · `single line text` — restaurant name (primary field)
> **Cuisine** · `multiple select` — Italian / Indian / Thai / Chinese / Japanese / French / British / Mexican / Mediterranean / Korean / Vietnamese / Spanish / Turkish / Other
> **Address** · `long text` — full address
> **Postcode** · `single line text` — for map lookups
> **Phone** · `single line text` — contact number
> **Website** · `url` — restaurant website
> **Maps URL** · `url` — Google search link for the restaurant
> **Price Range** · `single select` — £ / ££ / £££ / ££££
> **Food Type** · `multiple select` — Fine dining / Casual / Pub / Cafe / Street food / Takeaway / Brunch / Roast / Bistro / Gastropub
> **Dietary Friendly** · `multiple select` — Vegetarian-friendly / Vegan-friendly / Gluten-free options / Halal / Kosher
> **Ambience** · `multiple select` — Romantic / Family-friendly / Quiet / Lively / Outdoor seating / BYOB / Dog-friendly / Date night
> **Google Rating** · `number` — rating from Google (1 decimal, e.g. 4.5)
> **Google Review Count** · `number` — number of Google reviews
> **Google Price Level** · `number` — 1–4 from Google
> **Google Types** · `long text` — e.g. "fine_dining, restaurant, food"
> **Review Summary** · `long text` — Hermes's summary of what reviewers say
> **Alignment Score** · `single select` — Strong match / Moderate / Weak / Unknown
> **Alignment Notes** · `long text` — why this does/doesn't match your preferences
> **Source** · `single select` — We went / Recommended / Found online / Want to try
> **Recommended By** · `link → People` — who recommended it
> **Status** · `single select` — Want to go / Been — loved it / Been — liked it / Been — meh / Been — avoid
> **Overall Rating** · `single select` — 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10
> **Times Visited** · `number` — how many times you've been
> **Last Visited** · `date` — most recent visit
> **Photo** · `attachment` — photo of the place or a dish
> **Notes** · `long text` — freeform notes

### Table: `Restaurant Visits`

Each visit to a restaurant. Detailed feedback lives here.

> **Restaurant** · `link → Restaurants` — which restaurant
> **Date** · `date` — when you went
> **People** · `link → People` — who was there (you, wife, friends)
> **Dishes Ordered** · `long text` — what was ordered
> **Dish Ratings** · `long text` — "Pizza: 9/10, Garlic bread: 7/10"
> **Service Rating** · `single select` — 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10
> **Ambience Rating** · `single select` — 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10
> **Value Rating** · `single select` — 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10
> **Overall Rating** · `single select` — 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10
> **Wife's Rating** · `single select` — 1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10
> **Wife's Notes** · `long text` — her separate detailed feedback
> **Would Return** · `single select` — Definitely / Maybe / No
> **Best Dish** · `single line text` — standout dish
> **Worst Dish** · `single line text` — letdown dish
> **Cost Total** · `currency` — total bill (£)
> **Cost Per Head** · `currency` — per person
> **Occasion** · `single select` — Date night / Family meal / Friends / Birthday / Casual / Business / Anniversary
> **Photo** · `attachment` — photo of the meal
> **Notes** · `long text` — detailed feedback
> **Source** · `single select` — Slack / Manual

---

# PHASE 5 — INTELLIGENCE LAYER

---

## Module 22 — Cross-Module Intelligence

No new data tables — this module's power comes from Hermes reading across all existing tables at once. It writes its observations to a log.

### Table: `Insights`

> **Insight** · `long text` (primary field) — the observation surfaced
> **Date** · `date`
> **Modules drawn from** · `multiple select` — Sleep / Fitness / Meals / Mood / Calendar / People / Other
> **Type** · `single select` — Pattern / Anomaly / Suggestion / Forward plan
> **Acted on** · `checkbox`
> **Generated** · `created time`

---

## Module 23 — Shopping Super-Connector

The payoff for consistent linking. One list, fed automatically from many modules.

### Table: `Shopping List`

> **Item** · `single line text` (primary field)
> **Category** · `single select` — Groceries / Household / Gift / Clothing / Other
> **Source module** · `single select` — Recipe / Dinner party / Gift / Wardrobe / Todo / Manual
> **Linked recipe** · `link → Recipes` — if from a recipe
> **Linked gift** · `link → Gift Ideas` — if a gift
> **Quantity** · `single line text`
> **Status** · `single select` — To buy / Bought
> **Added** · `created time`

---

## Module 24 — Language Learning Progression

Extends the daily word into a full system.

### Table: `Vocabulary`

> **Word** · `single line text` (primary field)
> **Pronunciation** · `single line text`
> **Meaning** · `single line text`
> **Example** · `long text`
> **Status** · `single select` — New / Learning / Known / Struggling
> **Times reviewed** · `number`
> **Last reviewed** · `date`
> **Next review** · `date` — for spaced repetition
> **Added** · `created time`

### Table: `Grammar Concepts`

> **Concept** · `single line text` (primary field) — e.g. "Genitive case"
> **Explanation** · `long text`
> **Status** · `single select` — Learning / Understood / Needs work
> **Examples** · `long text`

### Table: `Practice Log`

> **Date** · `date` (primary field)
> **Type** · `single select` — Vocabulary / Grammar / Listening / Speaking / Reading
> **Duration (mins)** · `number`
> **Notes** · `long text`

---

## Module 25 — Communication Automation

The most complex module. Mostly Hermes's work, but it uses tables to track what it manages.

### Table: `Clients` *(if doing work automation)*

> **Client name** · `single line text` (primary field)
> **Email** · `single line text`
> **Status** · `single select` — Lead / Active / Completed / Dormant
> **Linked person** · `link → People`
> **Job notes** · `long text`
> **Last contact** · `date`
> **Created** · `created time`

### Table: `Jobs`

> **Job** · `single line text` (primary field)
> **Client** · `link → Clients`
> **Status** · `single select` — Enquiry / Quoted / Confirmed / In progress / Complete / Invoiced / Paid
> **Value** · `currency`
> **Due date** · `date`
> **Notes** · `long text`

### Table: `Follow-ups` *(worth standing up early — see Phase 3)*

Commitments extracted from conversations and mail.

> **Commitment** · `single line text` (primary field) — e.g. "Send James the proposal"
> **Who** · `link → People`
> **Direction** · `single select` — I owe them / They owe me
> **Due date** · `date`
> **Status** · `single select` — Open / Done
> **Source** · `single select` — Conversation log / Email / Manual
> **Created** · `created time`

---

# Cross-module link map

How the tables connect. These links are the mechanism by which Geeves compounds; build them as specified.

```
People (the spine)
 ├── Person Notes
 ├── Conversation Log ──→ Follow-ups
 ├── Gift History
 ├── Gift Ideas ──────────→ Shopping List
 ├── Occasions
 ├── Dinner Parties ──────→ Recipes ──→ Ingredients ──→ Shopping List
 ├── Restaurant Visits ───→ Restaurants
 ├── Events
 ├── Watchlist / Reading List (recommended by)
 ├── London To-Do
 └── Holiday Ideas

Recipes ──→ Meals ──→ Daily Nutrition Summary ──→ Fitness Goals
Goals ──→ Milestones
Goals ──→ Todos
Workouts ──→ Exercise Log
Workouts + Sleep + Meals ──→ Insights (cross-module)
```

---

# Build principles for the schema

**Build tables in phase order.** There's no need to create Phase 4 tables during Phase 1 — but the People Graph comes first, because nearly everything links to it.

**Keep field names identical across tables.** A person link is always `Person` or `People`. A date is always `Date`. A rating is always `Rating`. This keeps the data unambiguous and the links clean.

**Add links as you go.** When a later module links to an earlier table, add the link field then. Airtable allows new link fields on existing tables at any time without disruption.

**Prefer fixed lists over free text where a list works.** Single and multiple selects keep the data clean, which makes reasoning over it reliable and filtering dependable.

**Every module has a context element and, where it generates output, a log.** The context informs what Hermes produces; the log records what was produced and how it landed, which is what prevents repetition and lets the system learn. The pattern matters more than the exact table count.

---

*Companion documents:*
- *The Master Plan describes what Geeves is, how it's built, and where it's going.*
- *The [Module Build Playbook](Module_Build_Playbook.md) describes how to build a new module — the standard process for creating tables, skills, scripts, and cron jobs.*
- *[modules_status.json](modules_status.json) tracks what's built, what's in-progress, and what's planned.*
- *This document holds the structure beneath it — the exact table and field definitions.*
