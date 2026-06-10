# uk-property-cli Reference

Installed at /root/uk-property-cli (June 2026). Agent-friendly CLI for Rightmove/Zoopla/ESPC.

## Key Commands

Search:
  uk-property search --portal rightmove --location-id 'REGION^87490' --min-beds 3 --max-price 1000000 --property-types house --max-pages 3 --jsonl

Compare snapshots:
  uk-property compare /tmp/snap_old.jsonl /tmp/snap_new.jsonl

Find location IDs:
  uk-property locations "london"

## Output Schema (property-listing.v1)

JSONL, one object per line. Key fields: id, url, address, price, beds, baths, property_type, description, features (string array), images, fetched_at.

## Gotchas

- CLI ranking is basic (~5 for everything) - use our own scoring
- "locations" lookup returns empty for some terms - use --location-id directly
- No postcode filtering - must filter north-of-Thames downstream
- No tenure field - check description text for Freehold/Leasehold
- No sq ft - parse from description if present (~30%)

## Source

github.com/abracadabra50/uk-property-cli