---
name: product-stock-monitor
description: "Monitor product availability and pricing across e-commerce sites via scheduled scrapers. Use when building cron-based stock alerts, price trackers, or deal scanners for any online retailer. Covers Apple, Amazon, eBay, and general e-commerce scraping patterns."
---

# Product Stock Monitor

Build scheduled scrapers that check e-commerce product pages and alert when items become available or hit target prices.

## When to Use

- User wants to track availability of a specific product (e.g., refurbished electronics, limited-stock items)
- User wants price-drop alerts
- User wants to scan multiple retailers for the best deal

## Core Architecture

### 1. Scraper Script (Python)

Write a Python script per retailer that:
- Fetches product pages (using `urllib` or `requests`)
- Parses availability from the HTML
- Compares against previous state (JSON state file)
- Outputs a structured report

```python
# Pattern: state-based change detection
STATE_FILE = os.path.expanduser("~/.hermes/{product}_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
```

### 2. Cron Job

Schedule the scanner with `cronjob(action='create')`:
- Daily is typical for refurb/deal scanning
- Timezone-aware: use UTC and convert for the user
- Deliver to `origin` (current Slack thread)

### 3. Alert Logic

**Only alert when something changed.** Silent scans = no message.
- Newly available → send alert with product details + direct link
- Price dropped below target → send alert
- No change from last scan → silent (log only)

## CRITICAL: JavaScript-Rendered Sites

**This is the #1 pitfall.** Many e-commerce sites (Apple, Amazon, Best Buy) render availability via JavaScript *after* the initial HTML loads.

### Signs a site needs JS rendering:
- "Add to Bag" / "Buy" button is always present in static HTML even when out of stock
- Availability appears only after page交互 (clicking, scrolling)
- The page is a SPA (React, Vue, etc.)

### What DOESN'T work:
- Static HTML scraping with `urllib` or `requests` for these sites
- Looking for "Currently Unavailable" text — it may never appear in the HTML

### What DOES work:
- **Firecrawl with `waitFor`** — allows JS to render before extracting
- **Firecrawl `actions`** — click "Add to Bag" and observe what happens
- **Undocumented retailer APIs** — e.g., Apple's `/shop/fulfillment-messages` endpoint
- **Headless browser** (if Firecrawl is insufficient)

### Apple-Specific Notes

See `references/apple-scraping-pitfall.md` for detailed findings.

## UK Geo Considerations

- Apple and Amazon show **different stock by country/IP**
- Always use `firecrawl_scrape` with `location: { country: "GB" }` for UK-specific results
- A US-based server scraping Apple.com will see US stock, not UK

## Output Format for Slack Alerts

Keep it compact. David's preference: no raw log tables, simple consolidated design.

```
🍎 Product Alert — X available:
• [Config] — [Price] → [Direct Link]
```

When nothing available: **do not send a message.** Log silently.

## Cron Schedule Guidelines

| Scan Frequency | Cron | Use Case |
|---|---|---|
| Daily | `0 10 * * *` | Refurbished stock (Apple, Amazon) |
| Twice daily | `0 8,16 * * *` | Fast-moving deals |
| Hourly | `0 * * * *` | Flash sales, limited drops |

Always set `schedule` in UTC. For UK users, 10am UTC = 11am BST (summer) / 10am GMT (winter).

## Files to Create

```
~/.hermes/{product}_state.json          # Scraper state (auto-created)
~/.hermes/{product}_log.jsonl           # History log (auto-created)
/root/{product}_monitor/scanner.py     # Scraper script
```
