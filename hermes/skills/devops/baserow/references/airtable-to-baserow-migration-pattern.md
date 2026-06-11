# Airtable → Baserow Script Migration Pattern

## When to Use

When a script still uses `AIRTABLE_API_KEY` / `airtable_request()` / `api.airtable.com` and needs to write to Baserow instead.

## Migration Steps

### 1. Replace the API layer

**Before (Airtable):**
```python
def airtable_request(method, table, data=None, params=None):
    key = get_env_key("AIRTABLE_API_KEY")
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table}"
    ...
```

**After (Baserow via helper):**
```python
# Use baserow_api.py for all CRUD — it handles field name→ID resolution
# and select option name→ID conversion automatically.

# CREATE:
result = subprocess.run(
    ["python3", "/root/Geeves/scripts/baserow_api.py", "create-row",
     str(TABLE_ID), json.dumps(fields)],
    capture_output=True, text=True, timeout=30
)
# Parse output: "Created: row 123"
if "Created: row" in result.stdout:
    row_id = int(result.stdout.split("Created: row")[1].strip())

# READ (all rows with pagination):
result = subprocess.run(
    ["python3", "/root/Geeves/scripts/baserow_api.py", "list-rows",
     str(TABLE_ID), "--limit", "200", "--json"],
    capture_output=True, text=True, timeout=30
)
data = json.loads(result.stdout)
rows = data.get("results", [])
```

### 2. Key Differences

| Aspect | Airtable | Baserow |
|--------|----------|---------|
| Auth | `Bearer <key>` | `Token <key>` |
| Base URL | `https://api.airtable.com/v0/{base}` | `http://77.68.33.121/api/database/rows/table/{id}/` |
| Field names in API | Human-readable (`"Status"`) | Internal IDs (`"field_3522"`) |
| Select values | String (`"New"`) | Dict (`{"id": 1677, "value": "New"}`) |
| Pagination | Offset-based (`?offset=...`) | Page-based (`?page=N&size=100`) |
| Row count | `count` param (unreliable) | Paginate and count manually |
| `order_by` param | Supported | Returns HTTP 400 — sort client-side |

### 3. Select Option Handling

Baserow `single_select` fields return dicts, not strings:
```python
def get_select_value(field_val):
    if field_val is None:
        return ""
    if isinstance(field_val, dict):
        return field_val.get("value", "")
    return str(field_val)
```

### 4. Date Comparison

Baserow dates are naive strings. When comparing with timezone-aware datetimes:
```python
# WRONG — raises TypeError
seen_date = datetime.strptime(first_seen[:10], "%Y-%m-%d")
if (today_dt - seen_date).days <= 7:  # TypeError!

# RIGHT — make both timezone-aware
seen_date = datetime.strptime(first_seen[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
if (today_dt - seen_date).days <= 7:  # Works
```

### 5. Number Formatting

Baserow number fields may return strings. Cast before formatting:
```python
# WRONG — ValueError if price is a string
price_str = f"£{price:,}"

# RIGHT — cast first
price_val = int(price) if price else 0
price_str = f"£{price_val:,}" if price_val else "Price TBC"
```

### 6. Mealie Ingredient Dict Format

When syncing recipes from Mealie's `?loadFood=true` endpoint, ingredients are **dicts**, not strings:

```python
# Mealie returns:
# {"quantity": 1.0, "unit": None, "food": None, "note": "1/4 cup flour",
#  "display": "1/4 cup flour", "referenceId": "..."}

# Extract the text:
for ing in ingredients:
    if isinstance(ing, dict):
        raw_text = ing.get("display", "") or ing.get("note", "") or ing.get("food", {}).get("name", "")
    else:
        raw_text = str(ing)
    if not raw_text:
        continue
    # Now clean and categorise raw_text...
```

### 7. `baserow_api.py create-row` Output Parsing

The `create-row` command outputs human-readable text, not JSON:

```python
result = subprocess.run(
    ["python3", "/root/Geeves/scripts/baserow_api.py", "create-row",
     str(TABLE_ID), json.dumps(fields)],
    capture_output=True, text=True, timeout=30
)
if result.returncode == 0 and result.stdout.strip():
    stdout = result.stdout.strip()
    if "Created: row" in stdout:
        row_id = int(stdout.split("Created: row")[1].strip())
        return {"id": row_id}
return None
```

| Script | Status | Notes |
|--------|--------|-------|
| `property_scan_firecrawl.py` | ✅ Migrated | Uses `baserow_api.py create-row` |
| `garmin_fetch.py` | ✅ Already Baserow | Cron uses this, not `garmin_sync.py` |
| `bulletin_fetch.py` | ✅ Already Baserow | All fetchers write to Baserow |
| `build_digest_baserow.py` | ✅ Already Baserow | Reads from Baserow tables |
| `recipe_sync.py` (scripts/) | ✅ Migrated June 10 | Mealie → Baserow Recipes (379) + Ingredients (375) |
| `skills/recipe-parser/scripts/recipe_sync.py` | ✅ Migrated June 10 | Same, with `--slug` and bulk sync |
| `skills/recipe-parser/scripts/push_recipe.py` | ✅ Migrated June 10 | Photo/text/URL → Mealie → Baserow |

## Archived (No Longer Active)

| Script | Notes |
|--------|-------|
| `garmin_sync.py` | Old Garmin → Airtable version, moved to `legacy_airtable/` |
| `news_fetch.py` | News fetch, not called, moved to `legacy_airtable/` |
| `property_scan_v2.py` | Old property scan, moved to `legacy_airtable/` |
| `property_scan.py` | Oldest property scan, moved to `legacy_airtable/` |
| `tmp/*.py` | All one-off cleanup/verify scripts, moved to `legacy_airtable/` |

## Still on Airtable (Pending)

_None remaining. All active scripts now write to Baserow._
