# Baserow Digest Field Mappings

Reference for `build_digest_baserow.py` — table/field IDs and access patterns.

## Table IDs

| Table | ID | Key Fields |
|-------|----|-----------|
| Weather_Data | 364 | field_3364 (Date), field_3366 (Temp), field_3370 (Condition), field_3372 (High), field_3373 (Low), field_3375 (Rain Expected), field_3376 (Rain Times) |
| Fact_of_the_Day | 363 | field_3360 (Date), field_3361 (Category), field_3362 (Fact), field_3363 (Source URL) |
| Stock_Prices | 365 | field_3387 (Date), field_3388 (Ticker), field_3389 (Price), field_3390 (Currency), field_3391 (Change Pct) |
| Token_Usage | 367 | field_3418 (Date), field_3419 (Sessions), field_3423 (Total), field_3425 (Top Model) |
| Todos | 362 | field_3349 (Task), field_3350 (Status), field_3352 (Due Date), field_3351 (Priority), field_3357 (Timeframe), field_3358 (Category) |
| Properties | 380 | field_3508 (Address), field_3509 (URL), field_3510 (Price), field_3511 (Beds), field_3521 (Score), field_3522 (Status), field_3524 (First Seen), field_3518 (Features) |

## Select Option Values

### Todos Status (field_3350)
Filter: `status != "Done"` — values: "Not started", "In progress", "Done"

### Properties Status (field_3522)
Filter: `status == "New"` — values: "New", "Interested", "Viewing Booked", "Viewed", "Dismissed", "Bought"

## Critical Gotchas

1. **single_select returns dicts**: `{"id": N, "value": "New", "color": "..."}` — use `get_select_value()` helper
2. **Dates are naive**: Add `.replace(tzinfo=timezone.utc)` before comparing with aware datetimes
3. **Numbers may be strings**: Cast to `int()` before `f"{val:,}"` formatting
4. **No order_by**: Fetch all pages and sort client-side
5. **Use `--json` flag**: `baserow_api.py list-rows <id> --json` for machine-readable output
6. **Price formatting**: `price_val = int(price) if price else 0; f"£{price_val:,}"`

## Client-Side Date Filtering

```python
from datetime import datetime, timezone, timedelta

today = datetime.now(timezone.utc)
week_ahead = (today + timedelta(days=7)).strftime("%Y-%m-%d")

# Filter todos due within 7 days
short_term = [
    r for r in rows
    if get_select_value(r.get("field_3350")) != "Done"
    and r.get("field_3352", "") <= week_ahead
]
```
