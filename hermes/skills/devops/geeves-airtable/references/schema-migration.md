# Geeves Schema Migration Pattern

How to change Airtable field types when the Metadata API doesn't support it.

## The Problem

Airtable's Metadata API can:
- Create new tables and fields ✅
- Rename fields ✅ (PATCH with `{"name": "new name"}`)
- Add select choices ✅

Airtable's Metadata API CANNOT:
- Change field types ❌ (PATCH with `{"type": "newType"}` → 422 INVALID_REQUEST_UNKNOWN)
- Delete fields ❌ (DELETE → 404)
- Create `createdTime`/`lastModifiedTime` fields ❌ (422 UNSUPPORTED_FIELD_TYPE_FOR_CREATE)

## Migration Pattern (what works)

### For EMPTY fields changing type

1. Create a new field with the desired type and name adjacent to the old one
2. Hide the old field in the Airtable web UI (right-click → Hide)
3. Optionally delete the old field in the web UI (permanent)

**Example:** `Dietary Requirements` (multilineText, empty) → created `Dietary reqs` (multipleSelects) alongside it, hid the old field.

### For POPULATED fields changing type

1. Read all existing data from the old field
2. Create the new field with desired type
3. Write migrated data to the new field
4. Hide the old field in UI

**Example:** `Relationship` (singleLineText, "Self" on 1 record) → created `Relationship type` (singleSelect), set David to "Me", hid old field.

### For select option renames (same type, different option names)

Use `typecast=true` on batch PATCH — this auto-creates new select options:

```python
updates = [{"id": rec_id, "fields": {"Tier": "Tier 1"}} for ...]
api("PATCH", f"{BASE}/People", {"records": updates, "typecast": True})
```

Then remove old options in the Airtable web UI (Customize field → delete unused options).

### For field renames (same type)

Simple PATCH: `api("PATCH", f".../fields/{field_id}", {"name": "New Name"})` ✅

## V2 Migration (2026-06-03) — What Was Done

| Action | Method |
|--------|--------|
| Created Person Notes table | API (POST meta/bases/{id}/tables) |
| Created Conversation Log table | API (POST meta/bases/{id}/tables) |
| Added Photo, Food preferences fields | API (POST fields) |
| Added v2 replacement fields (Relationship type, Dietary reqs, Allergy list, Gift budget range, Typical contact frequency) | API (POST fields with select types) |
| Renamed How Known → How I know them | API (PATCH field name) |
| Renamed Dietary Dislikes → Food dislikes | API (PATCH field name) |
| Renamed Hobbies → Hobbies & interests | API (PATCH field name) |
| Renamed Gift Interests → Gift interests | API (PATCH field name) |
| Remapped 261 Tier records via typecast | API (PATCH records with typecast=true) |
| Remapped Todos Status "Todo" → "Not started" | API (PATCH records with typecast=true) |
| Added Timeframe, Category, Source to Todos | API (POST fields) |
| Set David's Relationship type = "Me" | API (PATCH record) |

### Manual UI steps still needed

These cannot be done via API:
- Hide old fields (Relationship, Dietary Requirements, Allergies, Contact Frequency, Gift Budget, junk fields)
- Remove old Tier select options (Tier 1 (David), Tier 2 (close), etc.)
- Remove old Todos Status option ("Todo")
- Add createdTime fields to Person Notes and Conversation Log
- Delete junk fields (FilmClub_Data, FilmClub_Log, Films 2, Films 3, Films 4)

### Key lesson

User pushed back on "you need to do this in the Airtable UI." Always try harder to automate — create replacement fields via API, migrate data, and minimise UI work to just hiding/deleting old fields. Don't hand off more than necessary.
