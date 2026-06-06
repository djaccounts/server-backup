# Airtable Setup Instructions — Geeves Base

## What you need to do in the Airtable web UI

Go to https://airtable.com → open the "Geeves" base → follow these steps.

### Step 1: Delete the generic "Table 1"
1. Open the Geeves base
2. Right-click the "Table 1" tab at the bottom → **Delete table**
3. Confirm deletion

### Step 2: Create the "People" table
1. Click the **"+"** button next to the table tabs → name it `People`
2. It auto-creates a "Name" field — rename it to **Full Name** (single line text)
3. Add these fields in order (click **"+"** in the header for each):

| # | Field name | Type | Notes |
|---|-----------|------|-------|
| 1 | Full Name | Single line text | Primary field (already exists as "Name") |
| 2 | Relationship | Single line text | e.g. "wife", "friend", "colleague", "family" |
| 3 | Birthday | Date | |
| 4 | Phone | Phone number | |
| 5 | Email | Email | |
| 6 | How Known | Single line text | e.g. "met at university", "work", "introduced by Sarah" |
| 7 | Dietary Requirements | Long text | |
| 8 | Allergies | Long text | |
| 9 | Dietary Dislikes | Long text | |
| 10 | Portion Notes | Single line text | e.g. "big appetite", "small portions" |
| 11 | Hobbies | Long text | |
| 12 | Topics They Love | Long text | |
| 13 | Topics to Avoid | Long text | |
| 14 | Gift Interests | Long text | |
| 15 | Gift Budget | Single line text | e.g. "£20-30" |
| 16 | Past Gifts | Long text | |
| 17 | What Landed | Long text | Gifts that were a hit |
| 18 | Social Style | Single line text | e.g. "big dinner parties", "intimate gatherings", "pub meetups" |
| 19 | Venue Preferences | Long text | |
| 20 | Social Notes | Long text | Anything to be aware of |
| 21 | Anniversaries | Long text | |
| 22 | Important Dates | Long text | |
| 23 | Last Seen | Date | |
| 24 | Contact Frequency | Single line text | e.g. "weekly", "monthly", "rarely" |
| 25 | Relationship Notes | Long text | *(Sensitive — Hermes routes to Ollama)* |
| 26 | Conversation Log | Long text | *(Sensitive — Hermes routes to Ollama)* |
| 27 | Tier | Single select | Options: Tier 1 (David), Tier 2 (close), Tier 3 (regular), Tier 4 (other) |
| 28 | Created | Created time | Auto-set |
| 29 | Last Modified | Last modified time | Auto-set |

### Step 3: Create the "Todos" table
1. Click the **"+"** → name it `Todos`
2. Fields:

| # | Field name | Type | Notes |
|---|-----------|------|-------|
| 1 | Task | Single line text | Primary field |
| 2 | Status | Single select | Options: Todo, In Progress, Done, Cancelled |
| 3 | Priority | Single select | Options: Low, Medium, High |
| 4 | Due Date | Date | |
| 5 | Module | Single line text | e.g. "Dinner Party", "Film Club" |
| 6 | Linked Person | Link to People | Connect to People table |
| 7 | Notes | Long text | |
| 8 | Created | Created time | Auto-set |
| 9 | Completed Date | Date | |

### Step 4: Create the "Memory_Summaries" table
1. Click the **"+"** → name it `Memory_Summaries`
2. Fields:

| # | Field name | Type | Notes |
|---|-----------|------|-------|
| 1 | Period | Single line text | e.g. "2026-W23" |
| 2 | Summary | Long text | The rolled-up summary |
| 3 | Source Entries | Long text | Raw entry IDs that were summarised |
| 4 | Created | Date | |

### Step 5: Create the "Output_Log" table
1. Click the **"+"** → name it `Output_Log`
2. Fields:

| # | Field name | Type | Notes |
|---|-----------|------|-------|
| 1 | Item | Single line text | What was generated |
| 2 | Module | Single line text | e.g. "Morning Digest", "Dinner Party" |
| 3 | Generated At | Date | |
| 4 | Content | Long text | The actual generated output |
| 5 | Rating | Single select | Options: ★★★ Great, ★★ OK, ★ Poor |
| 6 | Feedback | Long text | David's notes |
| 7 | Prompt Used | Long text | For debugging (optional) |

---

**When you're done, come back here and tell me. I'll:**
1. Verify the schema matches
2. Write the Airtable skills
3. Start seeding People (Tier 1 from a new thread)
