# Baserow Migration Pattern for Bulletin Fetchers

When migrating a legacy Airtable fetcher to Baserow (or creating a new one), follow this pattern.

## Checklist

0. **Create Baserow table** (if new table needed):
   - Database API token (`BASEROW_API_TOKEN`) CANNOT create tables or list tables — it can only do row CRUD
   - Use JWT auth via `table_builder.py`: `from table_builder import create_table, add_field`
   - `create_table('Table_Name')` → returns table ID
   - `add_field(table_id, {"name": "Field Name", "type": "text"})` for each field
   - Field types: text, long_text, date, single_select (with "options"), number, boolean, url
   - After creating table, regenerate mapping manually via JWT — `baserow_api.py get-mapping` uses database token and won't see new tables

1. **Create fetcher script** at `/root/Geeves/scripts/<name>_fetch.py`
   - Use `baserow_api.baserow_post()` for writes (NOT direct API calls)
   - Read env vars via `subprocess.run(["grep", "VAR", "/root/.hermes/.env"], ...)` — never `os.environ`
   - Support `--write` flag for Baserow writes, default to dry-run print
   - Print emoji-labeled output matching existing fetcher style
   - For external API data: use `urllib.request` with `User-Agent: GeevesBot/1.0` header
   - Wrap external API calls in try/except with fallback chain

2. **Add to parallel fetch** in `bulletin_fetch_parallel.py`:
   - Add `("Label", "🪐", "<name>_fetch.py")` to `FETCHERS` list
   - All fetchers run concurrently via `ThreadPoolExecutor`

3. **Add section to digest builder** in `build_digest_baserow.py`:
   - Read from Baserow table using `baserow_get(table_id)`
   - Filter by today's date: `r.get("field_XXXX") == today_iso`
   - Append section HTML to `sections` list
   - Wrap in `try/except Exception: pass` so failure doesn't break the whole digest
   - Update footer to credit the data source

4. **Update this skill** (`bulletin-agent`):
   - Add row to Data Sources table
   - Add row to Digest Sections table
   - Add any new pitfalls discovered

## Baserow Auth: JWT vs Database Token

| Operation | Auth | Tool |
|-----------|------|------|
| Create/delete tables | JWT | `table_builder.py` |
| Add/delete fields | JWT | `table_builder.py` |
| List tables | JWT | `table_builder.py api()` |
| Row CRUD (create/read/update/delete) | Database token | `baserow_api.py` |
| Regenerate mapping file | JWT (list tables + fields) | manual script |

## Baserow Field Access Patterns

- **single_select**: returns `{"id": N, "value": "..."}` — use `get_select_value()` helper
- **date fields**: naive strings `"2026-06-10"` — add `.replace(tzinfo=timezone.utc)` before comparison
- **number fields**: may return strings — cast to `int()` before `f"{val:,}"`
- **long_text**: use `field_XXXX` IDs, values may contain `\n` — replace with `<br>\n` for HTML

## Common Pitfalls

- **Deduplication**: `--write` twice creates duplicates. Only run once per day.
- **Date filtering**: Baserow API `filter__field_XXXX__equal` fails for date fields. Fetch with `size=N` and filter client-side.
- **Select options**: writing undefined choice to `singleSelect` fails with 422. Use exact option names.
- **Number negative**: if `number_negative=False`, negative values fail. Fix via JWT PATCH.
- **Mapping staleness**: After creating tables/fields via JWT, the mapping file won't update automatically. Regenerate manually.

## Example: Word of the Day Fetcher (June 2026)

Created `Word_of_the_Day` table (ID 407) with JWT auth:
```python
from table_builder import create_table, add_field
result = create_table('Word_of_the_Day')
# → table ID 407
add_field(407, {"name": "Word", "type": "text"})
add_field(407, {"name": "Russian", "type": "text"})
add_field(407, {"name": "Hebrew", "type": "text"})
# etc.
```

Fetcher uses Free Dictionary API + MyMemory Translation API (both free, no keys):
```python
# English definition + pronunciation
url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
# Russian translation
url = f"https://api.mymemory.translated.net/get?q={word}&langpair=en|ru"
# Hebrew translation
url = f"https://api.mymemory.translated.net/get?q={word}&langpair=en|he"
```

Curated 40-word list rotated by `day_of_year % 40`. Words range from common (serendipity) to advanced (defenestration, eudaimonia).

## Example: Star Wars Fetcher Migration (June 2026)

Before (Airtable):
```python
key = get_key()  # AIRTABLE_API_KEY
url = f"https://api.airtable.com/v0/{BASE}/{TABLE}"
```

After (Baserow):
```python
import baserow_api
TABLE = "Star_Wars_Fact"
ok, row_id = baserow_api.baserow_post(baserow_api.load_mapping(), TABLE, record)
```

The `baserow_post()` helper auto-resolves field names to `field_XXXX` IDs and select option names to IDs.
