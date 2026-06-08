# External Data Sources — Quick Reference

## Rightmove Property Search

**Location:** `devops/property-agent/references/rightmove-scraping.md`

The Rightmove scraping technique extracts embedded JSON from search result pages. Key points:
- Find `"properties":` in HTML source, extract JSON array by tracking bracket depth
- Gets: id, address, price, beds, baths, type, tenure, keyFeatures, summary, images, floorplans, agent, dates
- Rate limit: 1s between page fetches
- Deduplicate by Rightmove ID

For full details, field reference, and pitfalls, see the property-agent reference file.
