# Apple Refurbished Store Scraping — Pitfall Reference

## The Problem

Apple's refurbished product pages **always show "Add to Bag" in the static HTML**, even when the item is out of stock. Actual availability is determined by JavaScript after page load, or at checkout time.

## What We Learned (June 2026)

- Scraped 3 Apple UK refurb Mac mini M4 pages with `firecrawl_scrape`
- All 3 showed "Add to Bag" button in Firecrawl's markdown output
- All 3 showed price and specs correctly
- David loaded the same page in London and saw **"Out of stock"** under delivery
- The static HTML was a **false positive** for availability

## Why This Happens

1. **Server-side rendering**: Apple sends the same HTML regardless of stock. The buy button is always present.
2. **Client-side stock check**: JavaScript fetches availability after page load and replaces the button text.
3. **Session dependence**: Apple may show different stock based on IP location, cookies, or A/B testing.
4. **Apple has no public refurb API**: There is no documented endpoint for refurb stock.

## What Works Instead

### Option A: Firecrawl with `waitFor` + `actions`
```python
# Scrape after JS has rendered
firecrawl_scrape(
    url=url,
    formats=["markdown"],
    waitFor=5000,  # Wait 5s for JS to render
)
```
Then check for text like "Currently Unavailable" in the rendered output.

### Option B: Apple's Undocumented Fulfillment API
```
https://www.apple.com/shop/fulfillment-messages
  ?pl=true
  &mts.0=regular
  &mts.1=compact
  &cppart=UNLOCKED/WW
  &parts.0={PRODUCT_PART_NUMBER}
```
Returns JSON with real availability. The part number can be found in the product URL or page source.

### Option C: User Verification
Send the link and let the user confirm before acting. Most reliable for low-frequency scans.

## Affected Retailers (JS-Rendered Availability)

- Apple (all product pages)
- Amazon (availability via JS)
- Best Buy (US)
- Most modern React/Vue-based e-commerce

## Retailers Where Static Scraping WORKS

- Baserow (API-backed)
- eBay listing pages (availability in HTML meta tags)
- Simple HTML e-commerce sites

## Key Takeaway

For Apple refurb monitoring specifically:
1. **Recommend `refurb-tracker.com`** — they already solve this problem with email alerts and RSS feeds for Apple refurb UK
2. Use Firecrawl with `waitFor` for best scraping accuracy
3. Never trust "Add to Bag" in static HTML alone
4. Always note the limitation in alerts: "May show as available — click through to confirm"
