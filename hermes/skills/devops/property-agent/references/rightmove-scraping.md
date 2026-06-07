# Rightmove Scraping Reference

## Technique: Embedded JSON Extraction

Rightmove search results pages are JS-rendered SPAs, but the server-side HTML contains a large embedded JSON blob with all listing data. No headless browser needed.

### How it works

1. Fetch the search results page HTML
2. In the HTML source, find the `"properties":` marker, then locate the opening `[` bracket
3. Track bracket depth to find the matching closing `]`
4. Parse the array: each element is a full property object

### Required headers

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-GB,en;q=0.5",
    }

### Key property fields

- `id` — rightmove property ID (number)
- `displayAddress` — full address string
- `price.amount` — price in GBP (number)
- `bedrooms`, `bathrooms` — room counts
- `propertySubType` — "Terraced", "End of Terrace", "Semi-Detached", "Detached", "Flat"
- `tenure.tenureType` — "FREEHOLD" or "LEASEHOLD" (CAN BE NONE)
- `keyFeatures` — array of {order, description} objects
- `summary` — description text
- `location.latitude`, `location.longitude`
- `firstVisibleDate` — ISO date
- `addedOrReduced` — "Added on DD/MM/YYYY" or "Reduced on DD/MM/YYYY"
- `displaySize` — "1,210 sq. ft." (only ~30% of listings)
- `customer.branchDisplayName` — agent name

### Pitfalls

1. **`tenure` can be None** — use `prop.get("tenure") or {}`, NOT `prop.get("tenure", {})`
2. **Property type mapping** — Rightmove "End of Terrace" → Airtable "Terraced"
3. **Rate limiting** — add 1s delays between page fetches
4. **Pagination** — 24 results per page, `index` param (0, 24, 48...)
5. **displaySize regex** — `r"([\d,]+)\s*sq"` to extract sq ft

### Rightmove listing URL
    https://www.rightmove.co.uk/properties/{id}
