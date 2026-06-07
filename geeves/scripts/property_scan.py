#!/usr/bin/env python3
"""
Rightmove Property Scanner for Geeves
Searches Rightmove for properties matching criteria, scores them,
and stores new listings in Airtable.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────

AIRTABLE_BASE_ID = "appzvmonQXs4x2AlL"
PROPERTIES_TABLE = "tblA0jfgqxhPFJU7S"
CRITERIA_TABLE = "tbl6oeRjhK3sds9TI"

# North-of-Thames London postcode areas for Rightmove location identifiers
# We search by postcode area to cover north London
NORTH_LONDON_AREAS = [
    "REGION^87490",   # North London (broad)
]

# Rightmove search parameters
SEARCH_PARAMS = {
    "minBedrooms": "3",
    "maxPrice": "1000000",
    "minPrice": "750000",
    "propertyTypes": "detached,semi-detached,terraced",
    "includeSSTC": "false",
    "sortBy": "NEWEST_LISTINGS",
    "radius": "0",
}

# Scoring weights
WEIGHTS = {
    "garden": 3.0,
    "freehold": 1.5,
    "epc_c_or_above": 1.0,
    "semi_detached": 1.0,
    "detached": 1.5,
    "garage_parking": 0.5,
    "recently_added": 1.0,
    "price_per_sqft_value": 1.5,
    "station_nearby": 0.5,
    "good_schools": 0.5,
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_airtable_key():
    """Read Airtable API key from .env file."""
    env_path = Path("/root/.hermes/.env")
    with open(env_path) as f:
        for line in f:
            if line.startswith("AIRTABLE_API_KEY="):
                return line.strip().split("=", 1)[1]
    raise RuntimeError("AIRTABLE_API_KEY not found in .env")


def airtable_request(method, table, data=None, params=None, record_id=None):
    """Make an Airtable API request."""
    import urllib.parse
    key = get_airtable_key()
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}"
    if record_id:
        url += f"/{record_id}"
    if params:
        encoded = urllib.parse.urlencode(params, doseq=True)
        url += "?" + encoded

    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")

    if data:
        req.data = json.dumps(data).encode()

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"  Airtable API error {e.code}: {body[:200]}", file=sys.stderr)
        return None


def get_existing_rightmove_ids():
    """Get all existing Rightmove IDs from Airtable to avoid duplicates."""
    ids = set()
    offset = None
    while True:
        params = {"pageSize": 100, "fields": ["Rightmove ID"]}
        if offset:
            params["offset"] = offset
        result = airtable_request("GET", PROPERTIES_TABLE, params=params)
        if not result:
            break
        for record in result.get("records", []):
            rm_id = record["fields"].get("Rightmove ID")
            if rm_id:
                ids.add(rm_id)
        offset = result.get("offset")
        if not offset:
            break
    return ids


def get_active_criteria():
    """Fetch active property criteria from Airtable."""
    result = airtable_request("GET", CRITERIA_TABLE, params={
        "filterByFormula": "{Active} = TRUE()",
        "pageSize": 100,
    })
    if not result:
        return []
    return [r["fields"] for r in result.get("records", [])]


def create_property_record(fields):
    """Create a new property record in Airtable."""
    result = airtable_request("POST", PROPERTIES_TABLE, data={
        "fields": fields,
        "typecast": True,
    })
    if result:
        print(f"  ✓ Created: {fields.get('Address', 'unknown')} (ID: {result['id']})")
    return result


# ── Rightmove Scraping ─────────────────────────────────────────────────────────

def fetch_rightmove_page(area_id, page=0):
    """Fetch a Rightmove search results page and extract property JSON data."""
    params = dict(SEARCH_PARAMS)
    params["locationIdentifier"] = area_id
    params["index"] = str(page * 24)

    url = "https://www.rightmove.co.uk/property-for-sale/find.html?" + "&".join(
        f"{k}={v}" for k, v in params.items()
    )

    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-GB,en;q=0.5",
    })

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Error fetching Rightmove page {page}: {e}", file=sys.stderr)
        return None


def extract_properties_from_html(html):
    """Extract property data from Rightmove search results HTML."""
    # Find the embedded JSON properties array
    start_marker = '"properties":'
    start_idx = html.find(start_marker)
    if start_idx < 0:
        return []

    bracket_idx = html.find("[", start_idx)
    if bracket_idx < 0:
        return []

    # Find matching closing bracket
    depth = 0
    end_idx = bracket_idx
    for i in range(bracket_idx, min(bracket_idx + 500000, len(html))):
        if html[i] == "[":
            depth += 1
        elif html[i] == "]":
            depth -= 1
            if depth == 0:
                end_idx = i
                break

    try:
        return json.loads(html[bracket_idx:end_idx + 1])
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}", file=sys.stderr)
        return []


def is_north_of_thames(address, lat, lon):
    """Check if a property is north of the Thames and in a London postcode.
    
    Only allows north London postcode areas: N, NW, E, EC, W, WC, EN, HA, UB, WD.
    Excludes all south London: SE, SW, CR, BR, SM, KT.
    TW (Twickenham) uses latitude check as it straddles the river.
    """
    import re as _re
    addr_upper = address.upper()

    # Extract all postcode-like patterns from the address
    # Match patterns like "N3", "NW7", "E14", "SE23" etc.
    postcodes = _re.findall(r'\b([A-Z]{1,2})\d', addr_upper)

    # If no postcode found, use latitude fallback
    if not postcodes:
        if lat and lon:
            if lon < -0.05: return lat > 51.46
            elif lon > 0.05: return lat > 51.49
            else: return lat > 51.47
        return False  # No postcode and no coords = exclude

    # Check each postcode found in the address
    south_prefixes = {"SE", "SW", "CR", "BR", "SM", "KT"}
    north_prefixes = {"N", "NW", "E", "EC", "W", "WC", "EN", "HA", "UB", "WD"}

    for pc in postcodes:
        if pc in south_prefixes:
            return False
        if pc == "TW":
            return lat > 51.44 if lat else True
        if pc in north_prefixes:
            return True

    # Postcode found but not in any known list (e.g. DA, RM, IG) — exclude
    return False


# ── Scoring ────────────────────────────────────────────────────────────────────

def score_property(prop):
    """Score a property against the search criteria. Returns (score, max_score, reasons)."""
    score = 0.0
    max_score = 0.0
    reasons = []

    features = " ".join(
        f.get("description", "") for f in prop.get("keyFeatures", [])
    ).lower()
    summary = (prop.get("summary") or "").lower()
    all_text = features + " " + summary

    # Garden (must have)
    max_score += WEIGHTS["garden"]
    if "garden" in all_text:
        score += WEIGHTS["garden"]
        reasons.append("✓ Garden")
    elif "no garden" in all_text or "communal garden" not in all_text:
        reasons.append("✗ No garden mentioned")

    # Freehold (preferred)
    max_score += WEIGHTS["freehold"]
    tenure = prop.get("tenure") or {}
    tenure_type = (tenure.get("tenureType") or "").upper()
    if tenure_type == "FREEHOLD":
        score += WEIGHTS["freehold"]
        reasons.append("✓ Freehold")

    # EPC rating C or above
    max_score += WEIGHTS["epc_c_or_above"]
    epc_match = re.search(r"EPC[:\s]*([A-G])", all_text, re.IGNORECASE)
    if epc_match:
        epc = epc_match.group(1).upper()
        if epc in ("A", "B", "C"):
            score += WEIGHTS["epc_c_or_above"]
            reasons.append(f"✓ EPC {epc}")
        else:
            reasons.append(f"✗ EPC {epc}")

    # Property type
    subtype = (prop.get("propertySubType") or "").lower()
    max_score += WEIGHTS["detached"]
    if "detached" in subtype:
        score += WEIGHTS["detached"]
        reasons.append("✓ Detached")
    elif "semi" in subtype:
        score += WEIGHTS["semi_detached"]
        reasons.append("✓ Semi-detached")

    # Garage/parking
    max_score += WEIGHTS["garage_parking"]
    if "garage" in all_text or "parking" in all_text or "driveway" in all_text:
        score += WEIGHTS["garage_parking"]
        reasons.append("✓ Parking/garage")

    # Recently added
    max_score += WEIGHTS["recently_added"]
    added = prop.get("addedOrReduced", "")
    if "today" in added.lower() or "yesterday" in added.lower():
        score += WEIGHTS["recently_added"]
        reasons.append("✓ Just listed")
    elif "7 days" in added.lower() or "< 7" in added.lower():
        score += WEIGHTS["recently_added"] * 0.7
        reasons.append("✓ Added < 7 days")

    # Price per sq ft value
    price = prop.get("price", {}).get("amount", 0)
    display_size = prop.get("displaySize", "")
    sqft_match = re.search(r"([\d,]+)\s*sq", display_size)
    if sqft_match and price:
        sqft = int(sqft_match.group(1).replace(",", ""))
        if sqft > 0:
            price_per_sqft = price / sqft
            max_score += WEIGHTS["price_per_sqft_value"]
            if price_per_sqft < 800:
                score += WEIGHTS["price_per_sqft_value"]
                reasons.append(f"✓ Good value £{price_per_sqft:.0f}/sqft")
            elif price_per_sqft < 1000:
                score += WEIGHTS["price_per_sqft_value"] * 0.5
                reasons.append(f"~ Fair value £{price_per_sqft:.0f}/sqft")

    # Station nearby
    max_score += WEIGHTS["station_nearby"]
    if "station" in all_text or "tube" in all_text or "overground" in all_text:
        score += WEIGHTS["station_nearby"]
        reasons.append("✓ Near station")

    # Good schools
    max_score += WEIGHTS["good_schools"]
    if "outstanding" in all_text or "good school" in all_text:
        score += WEIGHTS["good_schools"]
        reasons.append("✓ Good schools")

    # Normalize to 0-10 scale
    if max_score > 0:
        normalized = (score / max_score) * 10
    else:
        normalized = 5.0

    return round(normalized, 1), reasons


def format_assessment(prop, score, reasons):
    """Format a human-readable assessment of the property."""
    parts = []
    parts.append(f"Score: {score}/10")
    parts.append("")
    for r in reasons:
        parts.append(f"  {r}")
    parts.append("")

    # Key facts
    price = prop.get("price", {}).get("amount", 0)
    if price:
        parts.append(f"Price: £{price:,}")
    parts.append(f"Bedrooms: {prop.get('bedrooms', '?')}  Bathrooms: {prop.get('bathrooms', '?')}")
    parts.append(f"Type: {prop.get('propertySubType', '?')}")

    tenure = prop.get("tenure", {}) or {}
    if tenure.get("tenureType"):
        parts.append(f"Tenure: {tenure['tenureType']}")

    display_size = prop.get("displaySize", "")
    if display_size:
        parts.append(f"Size: {display_size}")

    added = prop.get("addedOrReduced", "")
    if added:
        parts.append(f"Listing: {added}")

    # Key features
    features = prop.get("keyFeatures", [])
    if features:
        parts.append("")
        parts.append("Key features:")
        for f in features[:8]:
            parts.append(f"  • {f['description']}")

    return "\n".join(parts)


# ── Main Scan ──────────────────────────────────────────────────────────────────

def scan_properties():
    """Main scan: search Rightmove, score, and store new listings."""
    print(f"🏠 Property scan started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get existing IDs to avoid duplicates
    print("Fetching existing listings from Airtable...")
    existing_ids = get_existing_rightmove_ids()
    print(f"  Found {len(existing_ids)} existing listings")
    print()

    # Search Rightmove
    all_properties = []
    for area_id in NORTH_LONDON_AREAS:
        print(f"Searching Rightmove (area: {area_id})...")
        for page in range(3):  # First 3 pages = up to 72 results
            html = fetch_rightmove_page(area_id, page)
            if not html:
                break

            props = extract_properties_from_html(html)
            if not props:
                print(f"  No results on page {page + 1}")
                break

            print(f"  Page {page + 1}: {len(props)} properties found")
            all_properties.extend(props)
            time.sleep(1)  # Be polite

    print(f"\nTotal properties from Rightmove: {len(all_properties)}")

    # Filter north of Thames
    north_props = []
    for p in all_properties:
        lat = p.get("location", {}).get("latitude")
        lon = p.get("location", {}).get("longitude")
        address = p.get("displayAddress", "")
        if is_north_of_thames(address, lat, lon):
            north_props.append(p)

    print(f"After north-of-Thames filter: {len(north_props)}")

    # Filter out existing
    new_props = [p for p in north_props if str(p.get("id")) not in existing_ids]
    print(f"New properties (not in Airtable): {len(new_props)}")
    print()

    if not new_props:
        print("No new properties found. Done.")
        return []

    # Score and store
    stored = []
    for prop in new_props:
        score, reasons = score_property(prop)
        assessment = format_assessment(prop, score, reasons)

        # Parse listing date
        listing_date = prop.get("firstVisibleDate", "")
        if listing_date:
            try:
                listing_date = listing_date[:10]  # Just the date part
            except:
                listing_date = datetime.now().strftime("%Y-%m-%d")

        # Extract key features as text
        features_text = "\n".join(
            f["description"] for f in prop.get("keyFeatures", [])
        )

        # Determine garden status
        all_text = features_text.lower() + " " + (prop.get("summary") or "").lower()
        garden = "Yes" if "garden" in all_text else ("No" if "no garden" in all_text else "Unknown")

        # Extract sq ft
        display_size = prop.get("displaySize", "")
        sqft_match = re.search(r"([\d,]+)\s*sq", display_size)
        sqft = int(sqft_match.group(1).replace(",", "")) if sqft_match else None

        # Extract EPC
        epc_match = re.search(r"EPC[:\s]*([A-G])", all_text, re.IGNORECASE)
        epc = epc_match.group(1).upper() if epc_match else "Unknown"

        # Tenure
        tenure = prop.get("tenure") or {}
        tenure_str = (tenure.get("tenureType") or "").upper()
        if tenure_str == "FREEHOLD":
            tenure_str = "Freehold"
        elif tenure_str == "LEASEHOLD":
            tenure_str = "Leasehold"
        else:
            tenure_str = "Unknown"

        # Property type mapping
        rm_type = prop.get("propertySubType", "Other")
        type_map = {
            "Terraced": "Terraced",
            "End of Terrace": "Terraced",
            "Semi-Detached": "Semi-Detached",
            "Detached": "Detached",
            "Flat": "Flat",
            "Maisonette": "Maisonette",
            "Bungalow": "Bungalow",
        }
        prop_type = type_map.get(rm_type, "Other")

        fields = {
            "Address": prop.get("displayAddress", ""),
            "Rightmove URL": f"https://www.rightmove.co.uk/properties/{prop['id']}",
            "Price": prop.get("price", {}).get("amount"),
            "Bedrooms": prop.get("bedrooms"),
            "Bathrooms": prop.get("bathrooms"),
            "Property Type": prop_type,
            "Sq Ft": sqft,
            "Tenure": tenure_str,
            "EPC Rating": epc,
            "Key Features": features_text,
            "Summary": prop.get("summary", "")[:500],
            "Assessment": assessment,
            "Match Score": score,
            "Status": "New",
            "First Seen": datetime.now().strftime("%Y-%m-%d"),
            "Listing Date": listing_date,
            "Rightmove ID": str(prop["id"]),
            "Agent": (prop.get("customer", {}) or {}).get("branchDisplayName", ""),
        }

        print(f"Storing: {fields['Address']} — £{fields['Price']:,} — Score: {score}/10")
        result = create_property_record(fields)
        if result:
            stored.append({
                "id": result["id"],
                "address": fields["Address"],
                "price": fields["Price"],
                "score": score,
                "url": fields["Rightmove URL"],
                "assessment": assessment,
            })
        time.sleep(0.5)  # Rate limit

    print(f"\n✓ Stored {len(stored)} new properties")
    return stored


if __name__ == "__main__":
    stored = scan_properties()
    if stored:
        print(f"\n{'='*60}")
        print(f"SUMMARY: {len(stored)} new properties found")
        for s in stored:
            print(f"  • {s['address']} — £{s['price']:,} — Score: {s['score']}/10")
            print(f"    {s['url']}")
    else:
        print("\nNo new properties today.")
