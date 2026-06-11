# Baserow Migration Pattern for Bulletin Fetchers

When migrating a legacy Airtable fetcher to Baserow (or creating a new one), follow this pattern.

## Checklist

1. **Create fetcher script** at `/root/Geeves/scripts/<name>_fetch.py`
   - Use `baserow_api.baserow_post()` for writes (NOT direct API calls)
   - Read env vars via `subprocess.run(["grep", "VAR", "/root/.hermes/.env"], ...)` — never `os.environ`
   - Support `--write` flag for Baserow writes, default to dry-run print
   - Print emoji-labeled output matching existing fetcher style

2. **Add to parallel fetch** in `bulletin_fetch_parallel.py`:
   - Add `("Label", "🪐", "<name>_fetch.py")` to `FETCHERS` list
   - All fetchers run concurrently via `ThreadPoolExecutor`

3. **Add section to digest builder** in `build_digest_baserow.py`:
   - Read from Baserow table using `baserow_get(table_id)`
   - Filter by today's date: `r.get("field_XXXX") == today_iso`
   - Append section HTML to `sections` list
   - Update footer to credit the data source

4. **Update this skill** (`bulletin-agent`):
   - Add row to Data Sources table
   - Add row to Digest Sections table
   - Add any new pitfalls discovered

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
