---
name: relationships-agent
description: "Geeves Relationships & Occasions Agent — track birthdays, anniversaries, gift ideas, gift history, and social interactions. Links to People graph for dietary preferences, social style, and gift interests. Use when David mentions occasions, gifts, social plans, or past interactions with people."
version: 1.0.0
author: OWL
---

# Relationships & Occasions Agent

Tracks the social side of David's life — who he's seen, when, what he gave them, and what's coming up.

## Tables

| Table | ID | Purpose |
|-------|-----|---------|
| Occasions | 403 | Birthdays, anniversaries, recurring events per person |
| Gift Ideas | 404 | Running gift ideas per person |
| Gift History | 405 | Record of gifts given, with ratings |
| Social Log | 406 | Social interactions — dinners, meetups, calls |

**System of record:** Baserow (database ID 132). All CRUD via `baserow_api.py`.

## Table Schemas

### Occasions (403)

| Field | ID | Type | Notes |
|-------|-----|------|-------|
| Person | field_3749 | link_row → People (359) | Who it's for |
| Occasion Type | field_3751 | single_select | Birthday / Anniversary / Wedding / Other |
| Date | field_3752 | date | Month-day, year optional |
| Recurring | field_3753 | boolean | Annual recurring |
| Remind Days Before | field_3754 | number | Custom per person |
| Extra Notes | field_3741 | long_text | |
| Created | field_3755 | created_on | |

### Gift Ideas (404)

| Field | ID | Type | Notes |
|-------|-----|------|-------|
| Person | field_3756 | link_row → People (359) | Who it's for |
| Idea | field_3758 | long_text | The gift idea |
| Estimated Cost | field_3759 | single_select | Under £20 / £20-50 / £50-100 / £100+ |
| Occasion | field_3760 | text | Free text — when to give it |
| Status | field_3761 | single_select | Idea / Purchased / Given |
| Extra Notes | field_3744 | long_text | |
| Created | field_3762 | created_on | |

### Gift History (405)

| Field | ID | Type | Notes |
|-------|-----|------|-------|
| Person | field_3763 | link_row → People (359) | Who received it |
| Gift | field_3765 | long_text | What was given |
| Occasion | field_3766 | text | Free text — what occasion |
| Date Given | field_3767 | date | |
| Rating | field_3768 | single_select | 1-5 (how well it landed) |
| Extra Notes | field_3747 | long_text | |
| Created | field_3769 | created_on | |

### Social Log (406)

| Field | ID | Type | Notes |
|-------|-----|------|-------|
| Date | field_3773 | date | |
| Type | field_3774 | single_select | Dinner / Meetup / Call / Event / Other |
| Person | field_3775 | link_row → People (359) | Who was involved |
| Summary | field_3777 | long_text | What was discussed |
| Key Things to Remember | field_3778 | long_text | Promotions, moves, life events |
| Follow-up | field_3779 | long_text | Things to follow up on |
| Source | field_3780 | single_select | Slack / Calendar / Manual / Voice |
| Created | field_3781 | created_on | |

## Slack Capture

When David messages about:
- **Occasions:** "It's Sam's birthday on the 15th", "Jane's anniversary is next week" → Occasions
- **Gift ideas:** "Sam would love a new cookbook", "I should get Jane something for Christmas" → Gift Ideas
- **Gifts given:** "Gave Sam the cookbook, she loved it" → Gift History (from Gift Idea if exists)
- **Social interactions:** "Had dinner with Sam and Jane", "Called Mum, she's doing well" → Social Log

## Morning Digest Integration

The morning digest should check Occasions for:
- Today's birthdays/anniversaries
- Upcoming occasions within the next 14 days (using Remind Days Before)
- Format: "🎂 Sam's birthday is in 3 days — gift idea: new cookbook (£20-50)"

## Cross-Module Links

- **People** → Occasions: Birthday/anniversary data enriches person records
- **People** → Gift Ideas: Gift interests from People feed gift suggestions
- **Recipes** → Social Log: Dinner parties link to recipes cooked
- **Restaurants** → Social Log: Restaurant meals link to social occasions
- **Dinner Parties** → Social Log: Party records become social log entries

## Model Routing

- **Ordinary** (occasions, gift ideas, social log) → hosted OpenRouter model
- **Sensitive** (relationship notes, personal details) → local Ollama only

## Scripts

All at `/root/Geeves/scripts/`:
- `baserow_api.py` — CRUD on Baserow records (with field name→ID resolution)

## User Context

- **David** — primary user. Slack U0B73K4QWP5.
- **Wife** — Tier 2 in People graph, owns opinions on social occasions.
- **Style:** Build one piece at a time. Confirm before schema changes.
