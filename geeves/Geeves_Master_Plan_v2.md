# Geeves — Master Plan

*A personal AI system. One user. Built on Hermes Agent, with Airtable as the system of record.*

> **About this document.** This is the reference plan for Geeves — what it is, how it's built, and where it's going. It's written to be read by two audiences: the user, as a thinking and planning document; and Hermes, as a description of the system it operates. It describes intent and structure rather than implementation steps — the foundations are already in place, and Hermes handles the doing. Exact table and field definitions live in the companion *Schema Reference*; this document names tables where useful but does not restate their fields.

---

## 1. What Geeves is

Geeves is a personal assistant that runs continuously, learns over time, and handles the recurring thinking and admin of one person's life. It is not a single app but a growing collection of modules — recipes, fitness, people, property, and more — that share one datastore and one agent, so that information gathered in one place makes every other place smarter.

The defining bet is that **data compounds**. A dinner party planned a year from now should be far better than one planned today, because by then Geeves knows the user's recipes, their guests, those guests' preferences, what's been cooked before, and what worked. Every design choice serves that compounding. The value is not in any single module but in the connections between them accumulating over time.

Geeves is for one user. Other people exist in the system as records — rich for those close to the user, sparse for acquaintances — but they are subjects the system knows about, not users of it.

---

## 2. How Geeves is built

The architecture is deliberately lean. Four components, each with a clear job.

**Hermes Agent** is the core. It runs on a VPS, reasons over requests, decides what to do, calls its tools, and remembers recent context across sessions. It also schedules its own recurring work through its built-in natural-language scheduler — the digests and periodic reviews are instructions Hermes holds and runs unattended, not external workflows. Hermes drives a model hosted on Nous Portal.

**Airtable** is the system of record — the permanent, structured, long-term memory. Everything that must persist, link to something else, or be queried months later lives here: the people graph, recipes, workouts, meals, goals, and the rest of the schema. Hermes reaches Airtable through an MCP connection, so reading and writing records is a native capability rather than a separate integration.

**Slack** is the primary input channel. The user talks to Geeves in Slack — to log something, ask something, add context, or capture a passing thought. Hermes listens there and acts. Further channels (WhatsApp, Telegram) can be added later through the same gateway without changing anything else.

**AgentMail** is the outbound channel for digests. Geeves has its own email identity and sends the daily, weekly, and monthly briefings to the user's inbox, where they are easy to read and keep. This is distinct from the user's personal email; it is Geeves's own voice.

### The division of memory

The split between Hermes and Airtable is the most important architectural idea, so it is worth stating plainly:

- **Hermes remembers the conversation.** Recent context, the thread of a discussion, what was just said — short- and medium-term, and conversational in nature.
- **Airtable remembers the facts.** Anything durable, structured, or relational — the things that need to be true and retrievable long after the conversation that produced them has ended.

When something said in passing matters beyond the moment — a new dietary note about a friend, a gift idea, a completed workout — it belongs in Airtable. The conversation is ephemeral; the record is permanent.

### What this replaced

An earlier version of this plan used n8n for orchestration, Gemini as the model, Glide as a front-end app, and a third-party service for WhatsApp. That stack has been retired in favour of the Hermes-centred design above, which is simpler, cheaper to run, and more capable: orchestration, scheduling, reasoning, and memory now live in one place, and interaction happens through channels the user already uses rather than a separate app.

---

## 3. The operating pattern

Every module, regardless of what it does, works the same way. Understanding the pattern once explains all of them.

**Capture is frictionless.** The user should be able to record something in a sentence, by message, without opening anything or filling in a form. Friction is the enemy of consistent data, and inconsistent data is weak data. A passing message in Slack is enough; Hermes interprets it and files it correctly.

**Context is read before acting.** Nothing is generated in a vacuum. Before Geeves suggests, plans, or drafts anything, it draws on what it already knows — the relevant people, the stored preferences, the history of what's been suggested before and how it landed. This is what makes output feel personal rather than generic, and it is why the datastore matters as much as the agent.

**Output is delivered where it's wanted.** Briefings arrive by email. Conversational answers come back in Slack. The channel suits the content: things to read and keep go to the inbox; things that are part of a back-and-forth stay in chat.

**Feedback closes the loop.** When the user rates, corrects, dismisses, or adds to something, that response is captured and shapes what comes next. Over time this is how Geeves learns not just what the user likes, but what they will actually do — which is a more useful thing to know.

The result is a system that gets better the more it is used, because every interaction either adds a fact, refines a preference, or teaches the system something about the person it serves.

---

## 4. The people graph

At the centre of Geeves sits a database of everyone the user knows. It is the spine of the system: modules across every phase link back to it, and its richness is what allows Geeves to be genuinely personal about the people in the user's life.

Each person has a single record that accumulates over time — who they are, how they relate to the user, what they like and dislike, what they're allergic to, what they're into, what they've been given before, when they were last seen, and a running set of notes and conversation memories. The relevant tables include the central `People` table and its linked companions for notes, conversations, occasions, and gift history.

Data richness is uneven by design, organised in tiers:

- **The user** holds the most complete picture, across every module.
- **The closest few** (partner, family, close friends) carry full profiles — dietary detail, gift history, occasions, interests, relationship notes.
- **Regular contacts** carry the essentials — dietary basics, birthday, a few interests, anything notable.
- **Everyone else** carries whatever has been captured, even if that is just a name and a single detail.

The principle is that even one data point is worth holding. "Sam prefers chicken to beef" is a small fact, but on the evening Sam comes to dinner it is exactly the fact that makes Geeves useful. The graph is built opportunistically, a detail at a time, and grows more valuable the longer it runs.

---

## 5. The modules

Geeves is built in phases. Earlier phases lay foundations and deliver daily value; later phases add reach and, finally, intelligence that spans the whole system. The order is deliberate — each phase makes the next easier, and the final phase only becomes meaningful once months of data exist beneath it.

### Phase 1 — Foundation
The groundwork everything else stands on.

- **People graph** — the central record of everyone the user knows; built early so every later module can link to it from the start.
- **Capture** — the means by which a passing message becomes a filed fact; the input habit that feeds every module that follows.

### Phase 2 — Daily bulletin
The first daily-value layer, and the things the user touches every day.

- **Morning digest** — a single readable briefing to start the day: weather, the day's calendar, today's tasks, what's for dinner, due reminders, curated news worth knowing, markets, and the word of the day. Delivered to the inbox each morning.
- **Evening digest** — a short close to the day: what got done, what rolls over to tomorrow, tomorrow's shape.
- **To-do list** — tasks across short, medium, and long horizons, surfaced at the right cadence rather than all at once.
- **Sleep and habit tracking** — quick to log, quietly building a picture over time; the morning briefing can soften on a bad night.
- **Fitness tracking** — workouts logged in a sentence or imported from a wearable; summarised weekly, with the next session suggested from recent history.
- **Meal tracking** — meals logged conversationally, with calories and macros estimated; daily totals against the user's targets.

### Phase 3 — Weekly rhythm
Where the system starts to feel less like a tracker and more like an assistant.

- **Weekly digest and intentions** — a reflective look back over the week and a short, considered look forward; a few intentions set for the week ahead and revisited at its end.
- **Recipes** — a living library powered by Mealie as the recipe engine and Airtable as the connective metadata layer. Recipes are imported from URLs, rated, and linked to ingredients (with LLM-assigned categories). The standout feature is planning a dinner party around who's coming and what they can and can't eat — guests' dietary data from the People graph is auto-compiled and cross-referenced against recipe ingredients. Restaurant meals can be logged by description or photo, with macros estimated by the LLM. A shared **Dining Preferences** table accumulates taste signals (frequent/high-rated cuisines, favourite dishes, avoidances) and feeds the future Restaurant Finder module.
- **Travel and commute** — on days with somewhere to be, the morning briefing already knows the route and any disruption.
- **Relationships and occasions** — birthdays, anniversaries, and the gentle nudge that it's been too long since the user saw someone, with the context to make the reach-out meaningful.
- **Gift ideas** — a running place to capture ideas the moment they occur, tagged to the person, ready when the occasion comes.
- **Skills and goals** — ambitions tracked across horizons, broken into steps that feed the to-do list, with goals that have gone quiet surfaced for a decision.
- **Documents and subscriptions** — the admin that otherwise slips: renewals, expiries, and recurring costs flagged before they bite.

### Phase 4 — Lifestyle
Self-contained modules that broaden what Geeves covers; built in whatever order appeals.

- **Wardrobe** — a catalogue of what the user owns, with outfit suggestions shaped by weather and occasion.
- **Restaurants** — places logged and rated, with recommendations that account for who the user is dining with.
- **Events and discovery** — Geeves watching for things the user would want to know about, and surfacing them in time to act, with a tap to put them in the calendar.
- **Watching and reading** — watchlists and reading lists, with suggestions drawn from what the user has enjoyed before.
- **Property** — a standing search that reviews new listings against the user's criteria and shows only what's genuinely worth a look.
- **London and travel** — a wishlist of things to do and places to go, surfaced by season and occasion, with trips planned out over time.

### Phase 5 — Intelligence
The payoff layer, meaningful only once the data beneath it has accumulated.

- **Cross-module intelligence** — Geeves drawing on everything at once: noticing that poor sleep, skipped training, and a dip in mood have arrived together, and saying so.
- **Unified shopping** — a single list fed automatically from recipes, gifts, wardrobe, and tasks, organised and ready.
- **Language progression** — the daily word grown into a proper learning system, with review timed to how well things are remembered.
- **Communication automation** — incoming mail and messages that trigger the right action, and routine replies handled on the user's behalf.

---

## 6. Capabilities that deepen over time

Beyond the modules themselves, a set of capabilities make Geeves feel less like software and more like a chief of staff. They are not separate features so much as ways the system grows into its role as data accumulates. They are noted here as direction, to be grown into rather than built all at once.

**Anticipation.** Looking weeks ahead and raising what's coming while there's still time to act — an unplanned dinner, an expiring passport, an unbought gift. Noticing when something is off the usual pattern and saying so. Reading the week's weather and surfacing what it makes possible.

**Depth about people.** A short debrief after seeing someone, captured into their record, so the relationship has a memory. A quiet sense of which relationships are drifting. A briefing on who's coming before a social occasion — recent news, things to raise, things to avoid.

**A longer memory.** Periodic summaries of how the user has been living — what they ate, how they trained and slept, who they saw, what they accomplished — stored and drawn on later, so Geeves has genuine continuity rather than only the recent past. A sense of the user's own voice, learned from how they edit what Geeves drafts, so that over time it writes more like them.

**The admin of life, handled.** Commitments made in passing — "I'll send that over Friday" — caught and surfaced until done. Appointments nudged when overdue. A quiet record of what the user is learning.

**The long view.** A reflection drawn from a voice note whenever the user wants to think out loud. A proper review each quarter and each year — a real account of how the time was actually spent, the kind of thing almost no one keeps and most would value enormously.

The ones worth growing into early are the ones that compound: capturing conversations and commitments, and keeping the longer memory. These are architectural in spirit — the sooner they begin, the more they are worth later.

---

## 7. Principles to hold to

As Geeves grows, a few principles keep it coherent.

**Build simple, connect later.** A module that works in isolation is worth more than an ambitious web of half-built connections. Get each thing working and useful on its own, then let the links between modules accumulate. The connections are where the long-term value lives, but they are added onto working foundations, not designed in from the first day.

**Keep the data clean and consistent.** The same kind of thing should be named and structured the same way everywhere. Consistency is what lets modules link cleanly and lets Hermes reason over the data without ambiguity. This discipline is dull and entirely worth it.

**Capture beats recall.** It is always better to write a fact down the moment it appears than to hope to reconstruct it later. The system is only as good as the data in it, and the data only arrives if capturing it is effortless.

**Let the agent infer.** Geeves does not need rigid rules for every situation. Given good information — clear modules, clean data, stored context — Hermes can work out what to do. This document provides the information; it deliberately leaves the doing to the agent.

**Serve the person, gently.** The point of Geeves is to make one person's life run a little better and freer, not to nag or to demand attention. Briefings inform; they don't hector. Nudges are gentle. The system earns its place by being quietly useful over a long time.

---

## 8. Where things stand

The foundations are in place: Hermes runs on the VPS, with Airtable and AgentMail connected and Slack as the input channel. Parts of the data model exist already, including the beginnings of the people graph. The path forward is to complete the foundation, stand up the daily bulletin so Geeves delivers visible value every morning, and then build outward phase by phase — adding modules, accumulating data, and, in time, switching on the intelligence that spans them all.

The plan is not fixed. It is a direction held loosely, revised as the system grows and as it becomes clearer what is genuinely useful in daily life. This document should evolve with it.

---
---

# Appendix — System architecture at a glance

A layered view of how Geeves fits together. Data sources feed the agent; the agent reasons and acts; modules give it structure; everything persists in the datastore; briefings flow out to the user.

```
┌─────────────────────────────────────────────────────────────────────┐
│  DATA SOURCES                                                         │
│                                                                       │
│   Calendar    Weather    Markets    News    Property    Maps/TfL      │
│   Watching/reading data    Wearable (fitness)    Event feeds          │
│                                                                       │
│   — external information Geeves draws on, fetched as needed —         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  INPUT                                                                │
│                                                                       │
│        Slack  (primary)        · later ·   WhatsApp    Telegram       │
│                                                                       │
│   — where the user talks to Geeves: log, ask, add context, capture —  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  THE AGENT  —  Hermes  (on VPS, driving Nous Portal model)            │
│                                                                       │
│   Reasoning   ·   Tool use   ·   Self-scheduled recurring work        │
│   Short / medium-term conversational memory                           │
│                                                                       │
│   — the brain: decides, acts, schedules, remembers the conversation — │
└─────────────────────────────────────────────────────────────────────┘
              │                                       │
              ▼                                       ▼
┌──────────────────────────────────┐   ┌──────────────────────────────┐
│  MODULES  (what Hermes operates)  │   │  DATASTORE  —  Airtable       │
│                                   │   │                              │
│  Phase 2 · Daily bulletin         │   │  System of record:          │
│    digests · to-dos · sleep ·     │◄─►│  long-term, structured,      │
│    habits · fitness · meals       │   │  relational memory           │
│                                   │   │                              │
│  Phase 3 · Weekly rhythm          │   │  People graph (the spine) ·  │
│    weekly digest · recipes ·      │   │  recipes · workouts ·        │
│    travel · relationships ·       │   │  meals · goals · occasions · │
│    gifts · goals · documents      │   │  gifts · and the rest        │
│                                   │   │                              │
│  Phase 4 · Lifestyle              │   │  — the facts: durable,       │
│    wardrobe · restaurants ·       │   │    linked, retrievable       │
│    events · watching/reading ·    │   │    long after the           │
│    property · London/travel       │   │    conversation ends —       │
│                                   │   │                              │
│  Phase 5 · Intelligence           │   │  (connected to Hermes        │
│    cross-module insight ·         │   │   via MCP)                   │
│    unified shopping ·             │   │                              │
│    language · comms automation    │   │                              │
│                                   │   │                              │
│  — all built on the people graph  │   │                              │
│    and the operating pattern —    │   │                              │
└──────────────────────────────────┘   └──────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OUTPUT                                                               │
│                                                                       │
│   Email via AgentMail  →  daily · weekly · monthly briefings          │
│   Slack                →  conversational answers, in the moment       │
│                                                                       │
│   — read-and-keep goes to the inbox; back-and-forth stays in chat —   │
└─────────────────────────────────────────────────────────────────────┘


        The loop:  capture (in)  →  reason + read context (Hermes)
                   →  persist (Airtable)  →  deliver (out)
                   →  feedback  →  the system knows a little more
```

**Reading the diagram.** Information flows down: external sources and the user's own messages feed Hermes; Hermes reasons over them, drawing on the modules for structure and Airtable for memory; results flow out as briefings by email or answers in Slack. The two-way arrow between the agent and the datastore is the heart of it — Hermes both reads what it knows and records what it learns, and that exchange, repeated daily, is what makes Geeves compound.

---

*Companion document: the Schema Reference holds the exact table and field definitions for every module named above.*
