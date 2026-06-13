# Scripts

## Mac Mini M4 Refurb Scanner

The active scanner for David's Mac mini M4 refurb monitor lives at:
`/root/mac_mini_refurb/scanner.py` (on the VPS)

It is invoked by cron job `4baaa029632d` (daily 10am UTC).

### Known Limitation

This script uses static HTML scraping which is **unreliable for Apple refurb pages**. See `references/apple-scraping-pitfall.md`. The script reports "available" when "Add to Bag" is present in HTML, but Apple renders availability via JS after page load. David has seen "Out of stock" on pages the script reported as available.

### Recommended Improvement

Replace the static scrape with Firecrawl using `waitFor: 5000` to allow JS rendering, or use Apple's undocumented `/shop/fulfillment-messages` API endpoint.
