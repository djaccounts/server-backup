# Rightmove Scraping Technique

## How to extract property listings from Rightmove search results

Rightmove's search results page embeds full property JSON data in the HTML. This is NOT loaded via AJAX — it's in the initial server response.

### Method

1. Fetch the Rightmove search URL with proper headers:
```python
import urllib.request, json, re

url = "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E87490&minBedrooms=3&maxPrice=1000000&minPrice=750000&propertyTypes=detached%2Csemi-detached%2Cterraced&includeSSTC=false&sortBy=NEWEST_LISTINGS&radius=0"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = resp.read().decode("utf-8", errors="replace")
```

2. Find and extract the JSON array:
```python
start_idx = data.find('"properties":')
bracket_idx = data.find('[', start_idx)
depth = 0
end_idx = bracket_idx
for i in range(bracket_idx, len(data)):
    if data[i] == '[': depth += 1
    elif data[i] == ']':
        depth -= 1
        if depth == 0:
            end_idx = i
            break
properties = json.loads(data[bracket_idx:end_idx+1])
```

3. Each property object contains:
   - `id` — Rightmove property ID (URL: `https://www.rightmove.co.uk/properties/{id}`)
   - `displayAddress` — Full address string
   - `price.amount` — Price in GBP (integer)
   - `price.displayPrices[0].displayPrice` — Formatted price string
   - `bedrooms`, `bathrooms` — Integer counts
   - `propertySubType` — e.g. "Terraced", "Semi-Detached"
   - `tenure.tenureType` — "FREEHOLD" or "LEASEHOLD" (can be None)
   - `keyFeatures` — List of dicts with `description` (mentions garden, EPC, stations)
   - `summary` — 1-2 paragraph description
   - `firstVisibleDate` — ISO date when first listed
   - `addedOrReduced` — Human-readable status
   - `listingUpdate.listingUpdateReason` — "new" or "price_reduced"
   - `displaySize` — Sq ft (only sometimes present)
   - `location.latitude`, `location.longitude`
   - `images`, `numberOfFloorplans`, `numberOfVirtualTours`
   - `customer.brandTradingName` — Agent name

### Search URL Parameters

- `locationIdentifier` — `REGION%5E87490` for Greater London
- `sortBy=NEWEST_LISTINGS` — Essential for daily scan
- `propertyTypes=detached,semi-detached,terraced` — Houses only (no flats)
- `radius=0` — Exact area match

### Rate Limiting

- Max 1 request/second to Rightmove
- Use realistic User-Agent
- If blocked, wait 60s and retry
- Cache results for 12-24h to avoid re-fetching
