# Module: DinnerParty

Generated: 2026-06-02T10:49:17.960030

Create these 3 tables in the Geeves Airtable base.

## Table: `DinnerParty_Data`

| # | Field name | Type | Notes |
|---|-----------|------|-------|
| 1 | Name | singleLineText | Primary field |
| 2 | Created | createdTime |  |
| 3 | Last Modified | lastModifiedTime |  |

## Table: `DinnerParty_Context`

| # | Field name | Type | Notes |
|---|-----------|------|-------|
| 1 | Key | singleLineText | Unique key for this context entry |
| 2 | Value | multilineText | The context/preference data |
| 3 | Updated | lastModifiedTime |  |

## Table: `DinnerParty_Log`

| # | Field name | Type | Notes |
|---|-----------|------|-------|
| 1 | Item | singleLineText | What was generated |
| 2 | Generated At | date | When it was created |
| 3 | Content | multilineText | The generated output |
| 4 | Rating | singleSelect |  → options: ★★★ Great, ★★ OK, ★ Poor |
| 5 | Feedback | multilineText | David's notes |

---

### Steps in Airtable web UI

1. Click **"+"** → name it **DinnerParty_Data**
2. Add the fields listed above

1. Click **"+"** → name it **DinnerParty_Context**
2. Add the fields listed above

1. Click **"+"** → name it **DinnerParty_Log**
2. Add the fields listed above
