---
name: books-agent
description: "Geeves Books Agent — manage reading list, track books, log reading progress, handle book recommendations from people. Use when adding books, updating reading status, logging finished books, looking up book info, or handling book-related Slack messages."
version: 1.0.0
author: Geeves
---

# Books Agent

Geeves Books module — track what you're reading, what you want to read, and what you've finished. Links to People for recommendations.

## Table(s)

| Table | ID | Purpose |
|-------|----|---------|
| `Books` | `tblUfRTBkCMLUe2pY` | Master book list — reading tracker, want-to-read, finished books, recommendations |

## Key Fields

| Field | Type | Purpose |
|-------|------|---------|
| `Title` | singleLineText | Book title (primary field) |
| `Author` | singleLineText | Author name |
| `Status` | singleSelect | Want to read / Reading / Read / Abandoned |
| `Genre` | multipleSelects | Fiction / Non-fiction / Biography / History / Science / Philosophy / Self-help / Business / Fantasy / Sci-fi / Thriller / Romance / Other |
| `My rating` | rating (1-5) | Your star rating |
| `Date started` | date | When you began reading |
| `Date finished` | date | When you completed it |
| `Recommended by` | multipleRecordLinks → People | Who suggested this book |
| `Goodreads ID` | singleLineText | Goodreads reference ID |
| `ISBN` | singleLineText | ISBN for lookups |
| `Page count` | number | Total pages |
| `Format` | singleSelect | Hardcover / Paperback / eBook / Audiobook |
| `Cover image` | multipleAttachments | Book cover |
| `Notes` | multilineText | Thoughts, summary, quotes |
| `Source` | singleSelect | Manual / Slack / Goodreads import |

## Airtable CRUD

Use `/root/Geeves/scripts/airtable_api.py`:

```bash
# Create record
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "Books" \
  '{"Title": "Project Hail Mary", "Author": "Andy Weir", "Status": "Read", "My rating": 5, "Date finished": "2026-06-10", "Format": "Audiobook", "Genre": ["Sci-fi", "Fiction"]}'

# Update record
python3 /root/Geeves/scripts/airtable_api.py update-record appzvmonQXs4x2AlL "Books" "<record_id>" \
  '{"Status": "Reading", "Date started": "2026-06-15"}'

# List records
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "Books"

# Filter by status
python3 /root/Geeves/scripts/airtable_api.py list-records appzvmonQXs4x2AlL "Books" "Status='Reading'"
```

**Auth:** Read `AIRTABLE_API_KEY` from `/root/.hermes/.env` via grep (never from `os.environ`).

## Workflows

### Adding a Book

1. Extract title and author from the message (or ask if unclear)
2. Set Status to "Want to read" (default) or "Reading" if user says they're currently reading
3. If someone recommended it, look up the person in People table and link via "Recommended by"
4. Create the record
5. Confirm back to the user with the title and status

### Logging a Finished Book

1. Find the book in the Books table (search by title)
2. Update Status to "Read"
3. Set Date finished to today (or extract from message)
4. If user gave a rating, set My rating (1-5 stars)
5. If user mentioned who recommended it, link to People
6. Confirm back with title and rating

### Updating Reading Progress

1. Find the book in the Books table
2. Update Status (e.g., "Want to read" → "Reading")
3. Set Date started if transitioning to "Reading"
4. Confirm the update

### Looking Up Book Info

When user asks about a book they should read or wants info:
1. Search the web for the book title + author
2. Return: title, author, genre, page count, Goodreads rating, brief description
3. Offer to add it to their list

### Goodreads Integration

The Goodreads API was deprecated in 2020. Workarounds:
- **CSV Import:** User exports Goodreads library → import script processes CSV → batch create records
- **Web scraping:** Search Goodreads by title/ISBN → extract metadata (rating, description, cover URL)
- **Manual link:** Store Goodreads ID or URL for reference

For CSV import, create a script at `/root/Geeves/scripts/books_goodreads_import.py` that:
1. Reads the Goodreads export CSV
2. Maps columns → Books table fields
3. Uses `typecast=true` for select fields
4. Batch creates records (10 per API call)

## Slack Capture

**Script:** `/root/Geeves/scripts/slack_capture.py`

**Trigger keywords:** "book", "reading", "read", "finished", "novel", "author", "recommend", "book list", "reading list", "goodreads", "audiobook", "ebook", "paperback"

**Classification priority:** After Film Club, before Module Request. Book-related messages should NOT be caught by the general Module Request classifier.

### Extraction Patterns

- **Title:** Usually in quotes or after "book" / "reading" / "finished"
- **Author:** After "by" or "author"
- **Rating:** "rated it X", "X/5", "X/5 stars", "X out of 5"
- **Status inference:**
  - "finished" / "just read" / "completed" → Read
  - "reading" / "started" / "currently on" → Reading
  - "want to read" / "add to list" / "recommend" → Want to read
  - "gave up" / "stopped" / "didn't finish" → Abandoned
- **Recommended by:** Look for person names after "recommended by", "suggested by", "X said"

## Cron Jobs

None currently. Future: monthly "reading summary" digest showing books finished, currently reading, and recommendations.

## Dependencies

- **People** → `Books.Recommended by` (for tracking who recommended what)

## Integration Points

- **People graph:** Link recommendations to people → see all books recommended by a person
- **Goodreads:** Import via CSV export; store Goodreads ID for reference
- **Future digest:** Books finished this month could appear in Weekly Digest

## Standing Rules

- All schema changes go through steward (`geeves-steward` skill)
- Registry: `/root/Geeves/schema_registry.json`
- Get David's explicit approval before creating any Airtable table
- Thread decisions supersede reference docs
- Update this skill when conversation changes a decision

## Pitfalls

1. **Select field values must match exactly:** Status must be "Want to read", "Reading", "Read", or "Abandoned" — not "Finished", "Started", etc. Always use the exact select option names.
2. **Rating is 1-5 stars:** Not 1-10. Convert if user gives a 10-point scale (divide by 2).
3. **Goodreads API deprecated:** Cannot fetch live data from Goodreads API. Use CSV import or web scraping instead.
4. **Book titles can be ambiguous:** Always confirm author if multiple books share a title.
5. **Link fields need record IDs:** When setting "Recommended by", you must first look up the person's record ID in the People table — you can't just write a name.
6. **"Reading list" triggers Reading status:** The word "reading" in "reading list" matches the Reading status regex. The Slack capture handler checks for "add to list" patterns BEFORE "reading" to avoid this false positive. When adding books manually, always set Status explicitly.

## Reference

- `geeves-airtable/SKILL.md` — Airtable CRUD patterns and API quirks
- `Geeves_Schema_Reference_v2.md` — full field definitions (Module 18 — Movies, TV + Books)
- `public-apis` skill — for book metadata APIs (Open Library, Google Books)
