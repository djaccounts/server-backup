# Property Scan v2 — Architecture Reference

## Overview

`property_scan_v2.py` replaces `property_scan_firecrawl.py` (660 lines → ~300 lines) by delegating fetching to `uk-property-cli` and keeping our custom scoring/Airtable logic.

## Architecture

```
uk-property-cli (fetch) → raw JSON enrichment → north-of-Thames filter → scoring → Airtable store
```

## Field Mapping (CLI → Airtable)

| Airtable Field | Source | Notes |
|----------------|--------|-------|
| Address | `cli.address` | |
| Rightmove URL | `cli.url` | Strip `#/?channel=RES_BUY` suffix |
| Price | `cli.price` | Integer |
| Bedrooms | `cli.beds` | |
| Bathrooms | `cli.baths` | |
| Property Type | `cli.property_type` | Mapped: "end of terrace"→"Terraced", etc. |
| Garden | features/description | "Yes" if "garden" in text |
| Sq Ft | `raw.displaySize` | Parsed from "1,200 sq ft" text |
| Tenure | `raw.tenure.tenureType` | From raw JSON, not CLI |
| EPC Rating | features/description | Regex: EPC[:\s]*([A-G]) |
| Key Features | `cli.features[].description` | Joined with newlines |
| Summary | `cli.description` | Truncated to 500 chars |
| Match Score | computed | 0-10 float |
| Listing Date | `raw.firstVisibleDate` | From raw JSON, not CLI |
| Rightmove ID | `cli.id` | String, used for dedup |
| Agent | `raw.customer.branchDisplayName` | From raw JSON, not CLI |

## What the CLI Drops (Must Enrich)

The `property-listing.v1` schema does NOT include:
- tenure (FREEHOLD/LEASEHOLD)
- location (latitude, longitude)
- firstVisibleDate
- addedOrReduced
- customer.branchDisplayName (agent)
- displaySize

These are re-fetched from the raw Rightmove JSON `<script>` tags.

## Cron Job

- Job ID: cea50fc34ab0
- Schedule: Daily 5am UTC
- Prompt: Runs `python3 /root/Geeves/scripts/property_scan_v2.py`

## Dependencies

- uk-property-cli at `/root/uk-property-cli/` (pip install -e)
- Python stdlib only — no Selenium, Playwright, or Firecrawl SDK needed
