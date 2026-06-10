#!/usr/bin/env python3
"""
Rightmove Property Scanner for Geeves — Firecrawl + Fallback
Primary: HTML scraping of search results (fast, reliable, full data)
Fallback: Firecrawl for search results if HTML scraping breaks
Also uses Firecrawl to enrich individual property pages for missing data.
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────

AIRTABLE_BASE_ID = "appzvmonQXs4x2AlL"
PROPERTIES_TABLE = "tblA0jfgqxhPFJU7S"
CRITERIA_TABLE = "tbl6oeRjhK3sds99TI"

NORTH_LONDON_AREAS = [
    "REGION^87490",   # North London (broad)
]

SEARCH_PARAMS = {
    "minBedrooms": "3",
    "maxPrice": "1000000",
    "minPrice": "750000",
    "propertyTypes": "detached,semi-detached,terraced",
    "includeSSTC": "false",
    "sortBy": "NEWEST_LISTINGS",
    "radius": "0",
}

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

def get_env_key(name):
    """Read an API key from .env file."""
    env_path = Path("/root/.hermes/.env")
    with open(env_path) as f:
        for line in f:
            if line.startswith(f"{name}="):
                return line.strip().split("=", 1)[1]
    raise RuntimeError(f"{name} not found in .env")


def airtable_request(method, table, data=None, params=None, record_id=None):
    """Make an Airtable API request."""
    key = get_env_key("AIRTABLE_API_KEY")
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


def check_exclusion_criteria(address, all_text, criteria):
    """
    Check if a property should be excluded based on active criteria.
    Returns (excluded: bool, reason: str or None).
    """
    addr_lower = address.lower()

    # Hard-coded exclusion rules
    if "dudley road" in addr_lower:
        return True, "Excluded: Dudley Road (already seen)"

    if "queen elizabeth" in addr_lower and "drive" in addr_lower:
        return True, "Excluded: Queen Elizabeth Drive (needs too much refurbishment)"

    # Dynamic criteria-based exclusions
    for c in criteria:
        c_text = (c.get("Criterion") or "").lower()
        c_type = c.get("Type", "")
        if c_type == "Dealbreaker" and "exclude" in c_text:
            words = c_text.replace("exclude", "").replace("properties", "").strip()
            if words and words in addr_lower:
                return True, f"Excluded by criteria: {c['Criterion']}"

    return False, None


# ── Primary: HTML Scraping ────────────────────────────────────────────────────

def fetch_rightmove_page(area_id, page=0):
    """Fetch a Rightmove search results page."""
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
    start_marker = '"properties":'
    start_idx = html.find(start_marker)
    if start_idx < 0:
        return []

    bracket_idx = html.find("[", start_idx)
    if bracket_idx < 0:
        return []

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


# ── Fallback: Firecrawl ───────────────────────────────────────────────────────

def scrape_with_firecrawl(url):
    """
    Scrape a Rightmove search results page using Firecrawl v1 API.
    Used as fallback when HTML scraping fails.
    Returns a list of property dicts or None on failure.
    """
    try:
        from firecrawl import FirecrawlApp
    except ImportError:
        print("  Firecrawl not installed", file=sys.stderr)
        return None

    api_key = get_env_key("FIRECRAWL_API_KEY")
    app = FirecrawlApp(api_key=api_key)

    schema = {
        "type": "object",
        "properties": {
            "properties": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "displayAddress": {"type": "string"},
                        "price": {"type": "integer"},
                        "bedrooms": {"type": "integer"},
                        "bathrooms": {"type": "integer"},
                        "propertySubType": {"type": "string"},
                        "tenureType": {"type": "string"},
                        "keyFeatures": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"},
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                        "firstVisibleDate": {"type": "string"},
                        "addedOrReduced": {"type": "string"},
                        "branchDisplayName": {"type": "string"},
                    }
                }
            }
        }
    }

    prompt = (
        "Extract all property listings from this Rightmove search results page. "
        "For each property, return: id, displayAddress, price (amount as integer), "
        "bedrooms, bathrooms, propertySubType, tenureType, "
        "keyFeatures (array of feature description strings), summary, "
        "latitude, longitude, firstVisibleDate, addedOrReduced, branchDisplayName. "
        "Return as a JSON array under a 'properties' key."
    )

    try:
        result = app.v1.scrape_url(
            url,
            formats=["json"],
            json_options={"prompt": prompt, "schema": schema},
            only_main_content=True,
            timeout=120000,
        )

        data = result.json_field
        if data and isinstance(data, dict):
            props = data.get("properties", [])
            if props:
                normalised = []
                for p in props:
                    normalised.append({
                        "id": str(p.get("id", "")),
                        "displayAddress": p.get("displayAddress", ""),
                        "price": {"amount": p.get("price", 0)},
                        "bedrooms": p.get("bedrooms"),
                        "bathrooms": p.get("bathrooms"),
                        "propertySubType": p.get("propertySubType", ""),
                        "tenure": {"tenureType": p.get("tenureType", "")},
                        "keyFeatures": [{"description": f} for f in p.get("keyFeatures", [])],
                        "summary": p.get("summary", ""),
                        "location": {"latitude": p.get("latitude"), "longitude": p.get("longitude")},
                        "firstVisibleDate": p.get("firstVisibleDate", ""),
                        "addedOrReduced": p.get("addedOrReduced", ""),
                        "customer": {"branchDisplayName": p.get("branchDisplayName", "")},
                    })
                return normalised

        print(f"  Firecrawl returned no properties data", file=sys.stderr)
        return None

    except Exception as e:
        print(f"  Firecrawl error: {e}", file=sys.stderr)
        return None


# ── North-of-Thames Filter ────────────────────────────────────────────────────

def is_north_of_thames(address, lat, lon):
    """Check if a property is north of the Thames and in a London postcode."""
    import re as _re
    addr_upper = address.upper()
    postcodes = _re.findall(r'\b([A-Z]{1,2})\d', addr_upper)

    if not postcodes:
        if lat and lon:
            if lon < -0.05: return lat > 51.46
            elif lon > 0.05: return lat > 51.49
            else: return lat > 51.47
        return False

    south_prefixes = {"SE", "SW", "CR", "BR", "SM", "KT"}
    north_prefixes = {"N", "NW", "E", "EC", "W", "WC", "EN", "HA", "UB", "WD"}

    for pc in postcodes:
        if pc in south_prefixes:
            return False
        if pc == "TW":
            return lat > 51.44 if lat else True
        if pc in north_prefixes:
            return True

    return False


# ── Scoring ────────────────────────────────────────────────────────────────────

def score_property(prop):
    """Score a property against the search criteria. Returns (score, reasons)."""
    score = 0.0
    max_score = 0.0
    reasons = []

    features = " ".join(
        f.get("description", "") for f in prop.get("keyFeatures", [])
    ).lower()
    summary = (prop.get("summary") or "").lower()
    all_text = features + " " + summary

    max_score += WEIGHTS["garden"]
    if "garden" in all_text:
        score += WEIGHTS["garden"]
        reasons.append("✓ Garden")

    max_score += WEIGHTS["freehold"]
    tenure = prop.get("tenure") or {}
    tenure_type = (tenure.get("tenureType") or "").upper()
    if tenure_type == "FREEHOLD":
        score += WEIGHTS["freehold"]
        reasons.append("✓ Freehold")

    max_score += WEIGHTS["epc_c_or_above"]
    epc_match = re.search(r"EPC[:\\s]*([A-G])", all_text, re.IGNORECASE)
    if epc_match:
        epc = epc_match.group(1).upper()
        if epc in ("A", "B", "C"):
            score += WEIGHTS["epc_c_or_above"]
            reasons.append(f"✓ EPC {epc}")

    subtype = (prop.get("propertySubType") or "").lower()
    max_score += WEIGHTS["detached"]
    if "detached" in subtype:
        score += WEIGHTS["detached"]
        reasons.append("✓ Detached")
    elif "semi" in subtype:
        score += WEIGHTS["semi_detached"]
        reasons.append("✓ Semi-detached")

    max_score += WEIGHTS["garage_parking"]
    if "garage" in all_text or "parking" in all_text or "driveway" in all_text:
        score += WEIGHTS["garage_parking"]
        reasons.append("✓ Parking/garage")

    max_score += WEIGHTS["recently_added"]
    added = prop.get("addedOrReduced", "")
    if "today" in added.lower() or "yesterday" in added.lower():
        score += WEIGHTS["recently_added"]
        reasons.append("✓ Just listed")

    price = prop.get("price", {}).get("amount", 0)
    display_size = prop.get("displaySize", "")
    sqft_match = re.search(r"([\\d,]+)\\s*sq", display_size)
    if sqft_match and price:
        sqft = int(sqft_match.group(1).replace(",", ""))
        if sqft > 0:
            price_per_sqft = price / sqft
            max_score += WEIGHTS["price_per_sqft_value"]
            if price_per_sqft < 800:
                score += WEIGHTS["price_per_sqft_value"]
                reasons.append(f"✓ Good value £{price_per_sqft:.0f}/sqft")

    max_score += WEIGHTS["station_nearby"]
    if "station" in all_text or "tube" in all_text or "overground" in all_text:
        score += WEIGHTS["station_nearby"]
        reasons.append("✓ Near station")

    max_score += WEIGHTS["good_schools"]
    if "outstanding" in all_text or "good school" in all_text:
        score += WEIGHTS["good_schools"]
        reasons.append("✓ Good schools")

    normalized = (score / max_score) * 10 if max_score > 0 else 5.0
    return round(normalized, 1), reasons


def format_assessment(prop, score, reasons):
    """Format a human-readable assessment of the property."""
    parts = [f"Score: {score}/10", ""]
    for r in reasons:
        parts.append(f"  {r}")
    parts.append("")

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

    features = prop.get("keyFeatures", [])
    if features:
        parts.append("")
        parts.append("Key features:")
        for f in features[:8]:
            parts.append(f"  • {f['description']}")

    return "\n".join(parts)


def build_search_url(area_id, page=0):
    """Build a Rightmove search URL."""
    params = dict(SEARCH_PARAMS)
    params["locationIdentifier"] = area_id
    params["index"] = str(page * 24)
    return "https://www.rightmove.co.uk/property-for-sale/find.html?" + "&".join(
        f"{k}={v}" for k, v in params.items()
    )


# ── Main Scan ──────────────────────────────────────────────────────────────────

def scan_properties():
    """
    Main scan: search Rightmove (HTML primary, Firecrawl fallback),
    score, apply exclusions, and store new listings.
    """
    print(f"🏠 Property scan started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("Fetching existing listings from Airtable...")
    existing_ids = get_existing_rightmove_ids()
    print(f"  Found {len(existing_ids)} existing listings")
    print()

    print("Fetching active criteria...")
    criteria = get_active_criteria()
    print(f"  Found {len(criteria)} active criteria")
    print()

    # Search Rightmove
    all_properties = []
    html_success = False
    firecrawl_used = False

    for area_id in NORTH_LONDON_AREAS:
        print(f"Searching Rightmove (area: {area_id})...")

        for page in range(3):
            url = build_search_url(area_id, page)

            # Try HTML scraping first (fast, reliable, full data)
            html = fetch_rightmove_page(area_id, page)
            props = extract_properties_from_html(html) if html else []

            if props:
                print(f"  HTML: {len(props)} properties on page {page + 1}")
                all_properties.extend(props)
                html_success = True
            else:
                # Fallback to Firecrawl
                print(f"  HTML failed on page {page + 1}, trying Firecrawl...")
                props = scrape_with_firecrawl(url)
                if props:
                    print(f"  Firecrawl: {len(props)} properties on page {page + 1}")
                    all_properties.extend(props)
                    firecrawl_used = True
                else:
                    print(f"  No results on page {page + 1}")
                    break

            time.sleep(1)

    method = "HTML" if html_success and not firecrawl_used else ("Firecrawl" if firecrawl_used else "unknown")
    print(f"\nTotal properties ({method}): {len(all_properties)}")

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

    # Apply exclusion criteria
    filtered_props = []
    excluded_count = 0
    for p in new_props:
        address = p.get("displayAddress", "")
        features_text = " ".join(
            f.get("description", "") for f in p.get("keyFeatures", [])
        ).lower()
        summary = (p.get("summary") or "").lower()
        all_text = features_text + " " + summary

        excluded, reason = check_exclusion_criteria(address, all_text, criteria)
        if excluded:
            print(f"  ✗ {reason}: {address}")
            excluded_count += 1
            p["_excluded"] = True
            p["_exclusion_reason"] = reason
        filtered_props.append(p)

    print(f"Excluded by criteria: {excluded_count}")
    print(f"Properties to store: {len(filtered_props)}")
    print()

    if not filtered_props:
        print("No new properties found. Done.")
        return []

    # Score and store
    stored = []
    for prop in filtered_props:
        score, reasons = score_property(prop)
        assessment = format_assessment(prop, score, reasons)

        listing_date = prop.get("firstVisibleDate", "")
        if listing_date:
            try:
                listing_date = listing_date[:10]
            except:
                listing_date = datetime.now().strftime("%Y-%m-%d")

        features_text = "\n".join(
            f["description"] for f in prop.get("keyFeatures", [])
        )

        all_text = features_text.lower() + " " + (prop.get("summary") or "").lower()
        garden = "Yes" if "garden" in all_text else ("No" if "no garden" in all_text else "Unknown")

        display_size = prop.get("displaySize", "")
        sqft_match = re.search(r"([\\d,]+)\\s*sq", display_size)
        sqft = int(sqft_match.group(1).replace(",", "")) if sqft_match else None

        epc_match = re.search(r"EPC[:\\s]*([A-G])", all_text, re.IGNORECASE)
        epc = epc_match.group(1).upper() if epc_match else "Unknown"

        tenure = prop.get("tenure") or {}
        tenure_str = (tenure.get("tenureType") or "").upper()
        if tenure_str == "FREEHOLD":
            tenure_str = "Freehold"
        elif tenure_str == "LEASEHOLD":
            tenure_str = "Leasehold"
        else:
            tenure_str = "Unknown"

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

        status = "Dismissed" if prop.get("_excluded") else "New"
        notes = prop.get("_exclusion_reason", "")

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
            "Status": status,
            "First Seen": datetime.now().strftime("%Y-%m-%d"),
            "Listing Date": listing_date,
            "Rightmove ID": str(prop["id"]),
            "Agent": (prop.get("customer", {}) or {}).get("branchDisplayName", ""),
        }
        if notes:
            fields["My Notes"] = notes

        print(f"Storing: {fields['Address']} — £{fields['Price']:,} — Score: {score}/10 [{status}]")
        result = create_property_record(fields)
        if result:
            stored.append({
                "id": result["id"],
                "address": fields["Address"],
                "price": fields["Price"],
                "score": score,
                "url": fields["Rightmove URL"],
                "status": status,
            })
        time.sleep(0.5)

    print(f"\n✓ Stored {len(stored)} new properties")
    return stored


if __name__ == "__main__":
    stored = scan_properties()
    if stored:
        print(f"\n{'='*60}")
        print(f"SUMMARY: {len(stored)} new properties found")
        for s in stored:
            print(f"  • {s['address']} — £{s['price']:,} — Score: {s['score']}/10 [{s['status']}]")
            print(f"    {s['url']}")
    else:
        print("\nNo new properties today.")
