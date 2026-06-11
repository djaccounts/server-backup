#!/usr/bin/env python3
"""
Rightmove Property Scanner for Geeves v2
Uses uk-property-cli for fetching, enriches from raw Rightmove JSON,
scores with Geeves weights, and stores in Airtable.

Replaces property_scan_firecrawl.py (660 lines -> ~300 lines).
"""

import json
import os
import re
import subprocess
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

SEARCH_LOCATION_ID = "REGION^87490"  # North London (broad)
SEARCH_MIN_BEDS = "3"
SEARCH_MAX_PRICE = "1000000"
SEARCH_PROPERTY_TYPES = "house"
SEARCH_MAX_PAGES = "3"

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
    env_path = Path("/root/.hermes/.env")
    with open(env_path) as f:
        for line in f:
            if line.startswith(f"{name}="):
                return line.strip().split("=", 1)[1]
    raise RuntimeError(f"{name} not found in .env")


def airtable_request(method, table, data=None, params=None, record_id=None):
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
    result = airtable_request("GET", CRITERIA_TABLE, params={
        "filterByFormula": "{Active} = TRUE()",
        "pageSize": 100,
    })
    if not result:
        return []
    return [r["fields"] for r in result.get("records", [])]


def create_property_record(fields):
    result = airtable_request("POST", PROPERTIES_TABLE, data={
        "fields": fields,
        "typecast": True,
    })
    if result:
        print(f"  ✓ Created: {fields.get('Address', 'unknown')} (ID: {result['id']})")
    return result


# ── Fetch via uk-property-cli ─────────────────────────────────────────────────

def fetch_listings():
    """Fetch listings using uk-property-cli. Returns list of normalized dicts."""
    cmd = [
        "uk-property", "search",
        "--portal", "rightmove",
        "--location-id", SEARCH_LOCATION_ID,
        "--min-beds", SEARCH_MIN_BEDS,
        "--max-price", SEARCH_MAX_PRICE,
        "--property-types", SEARCH_PROPERTY_TYPES,
        "--max-pages", SEARCH_MAX_PAGES,
        "--jsonl",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"  uk-property-cli error: {result.stderr[:300]}", file=sys.stderr)
        return []

    listings = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if line:
            try:
                listings.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return listings


# ── Enrich from raw Rightmove JSON ────────────────────────────────────────────

def fetch_raw_listings():
    """
    Fetch raw Rightmove JSON to get fields the CLI normalizes away:
    tenure, location (lat/lon), firstVisibleDate, addedOrReduced, branchDisplayName.
    Returns dict keyed by property ID.
    """
    raw_by_id = {}
    params = {
        "locationIdentifier": SEARCH_LOCATION_ID,
        "minBedrooms": SEARCH_MIN_BEDS,
        "maxPrice": SEARCH_MAX_PRICE,
        "propertyTypes": SEARCH_PROPERTY_TYPES,
        "sortType": "6",
        "radius": "0",
    }

    for page in range(int(SEARCH_MAX_PAGES)):
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
                html = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"  Error fetching page {page}: {e}", file=sys.stderr)
            break

        # Extract searchResults JSON from page
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
        found = False
        for script in scripts:
            if "searchResults" not in script:
                continue
            try:
                data = json.loads(script)
                search_results = data["props"]["pageProps"]["searchResults"]
                for prop in search_results.get("properties", []):
                    pid = str(prop.get("id", ""))
                    if pid:
                        raw_by_id[pid] = prop
                found = True
                break
            except Exception:
                continue

        if not found:
            break
        time.sleep(1)

    return raw_by_id


def enrich_listing(cli_listing, raw_props):
    """Merge CLI listing with raw Rightmove data for fields the CLI drops."""
    pid = cli_listing["id"]
    raw = raw_props.get(pid, {})

    # Tenure
    tenure = raw.get("tenure") or {}
    tenure_type = (tenure.get("tenureType") or "").upper()

    # Location
    location = raw.get("location") or {}
    lat = location.get("latitude")
    lon = location.get("longitude")

    # Dates
    first_visible = raw.get("firstVisibleDate", "")
    added_or_reduced = raw.get("addedOrReduced", "")

    # Agent
    customer = raw.get("customer") or {}
    agent = customer.get("branchDisplayName", "")

    # Build enriched listing
    enriched = dict(cli_listing)
    enriched["tenure"] = {"tenureType": tenure_type}
    enriched["location"] = {"latitude": lat, "longitude": lon}
    enriched["firstVisibleDate"] = first_visible
    enriched["addedOrReduced"] = added_or_reduced
    enriched["customer"] = {"branchDisplayName": agent}

    # Also grab displaySize from raw if present (CLI doesn't include it)
    display_size = raw.get("displaySize", "")
    if display_size:
        enriched["displaySize"] = display_size

    return enriched


# ── North-of-Thames Filter ────────────────────────────────────────────────────

def is_north_of_thames(address, lat, lon):
    addr_upper = address.upper()
    postcodes = re.findall(r'\b([A-Z]{1,2})\d', addr_upper)

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


# ── Exclusion Criteria ────────────────────────────────────────────────────────

def check_exclusion_criteria(address, all_text, criteria):
    addr_lower = address.lower()

    if "dudley road" in addr_lower:
        return True, "Excluded: Dudley Road (already seen)"
    if "queen elizabeth" in addr_lower and "drive" in addr_lower:
        return True, "Excluded: Queen Elizabeth Drive (needs too much refurbishment)"

    for c in criteria:
        c_text = (c.get("Criterion") or "").lower()
        c_type = c.get("Type", "")
        if c_type == "Dealbreaker" and "exclude" in c_text:
            words = c_text.replace("exclude", "").replace("properties", "").strip()
            if words and words in addr_lower:
                return True, f"Excluded by criteria: {c['Criterion']}"

    return False, None


# ── Scoring ────────────────────────────────────────────────────────────────────

def score_property(prop):
    score = 0.0
    max_score = 0.0
    reasons = []

    features = " ".join(
        f.get("description", "") if isinstance(f, dict) else str(f)
        for f in prop.get("features", [])
    ).lower()
    summary = (prop.get("description") or prop.get("summary") or "").lower()
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
    epc_match = re.search(r"EPC[:\s]*([A-G])", all_text, re.IGNORECASE)
    if epc_match:
        epc = epc_match.group(1).upper()
        if epc in ("A", "B", "C"):
            score += WEIGHTS["epc_c_or_above"]
            reasons.append(f"✓ EPC {epc}")

    subtype = (prop.get("property_type") or prop.get("propertySubType") or "").lower()
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

    price = prop.get("price", 0)
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
    parts = [f"Score: {score}/10", ""]
    for r in reasons:
        parts.append(f"  {r}")
    parts.append("")

    price = prop.get("price", 0)
    if price:
        parts.append(f"Price: £{price:,}")
    parts.append(f"Bedrooms: {prop.get('beds', '?')}  Bathrooms: {prop.get('baths', '?')}")
    parts.append(f"Type: {prop.get('property_type', prop.get('propertySubType', '?'))}")

    tenure = prop.get("tenure", {}) or {}
    if tenure.get("tenureType"):
        parts.append(f"Tenure: {tenure['tenureType']}")

    display_size = prop.get("displaySize", "")
    if display_size:
        parts.append(f"Size: {display_size}")

    added = prop.get("addedOrReduced", "")
    if added:
        parts.append(f"Listing: {added}")

    features = prop.get("features", [])
    if features:
        parts.append("")
        parts.append("Key features:")
        for f in features[:8]:
            desc = f.get("description", str(f)) if isinstance(f, dict) else str(f)
            parts.append(f"  • {desc}")

    return "\n".join(parts)


# ── Type mapping ───────────────────────────────────────────────────────────────

TYPE_MAP = {
    "Terraced": "Terraced",
    "End of Terrace": "Terraced",
    "end of terrace": "Terraced",
    "Semi-Detached": "Semi-Detached",
    "semi-detached": "Semi-Detached",
    "Detached": "Detached",
    "detached": "Detached",
    "Flat": "Flat",
    "flat": "Flat",
    "Maisonette": "Maisonette",
    "maisonette": "Maisonette",
    "Bungalow": "Bungalow",
    "bungalow": "Bungalow",
    "Town House": "Terraced",
    "town house": "Terraced",
}


# ── Main Scan ──────────────────────────────────────────────────────────────────

def scan_properties():
    print(f"🏠 Property scan v2 started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Fetch existing IDs
    print("Fetching existing listings from Airtable...")
    existing_ids = get_existing_rightmove_ids()
    print(f"  Found {len(existing_ids)} existing listings")
    print()

    # Fetch criteria
    print("Fetching active criteria...")
    criteria = get_active_criteria()
    print(f"  Found {len(criteria)} active criteria")
    print()

    # Step 1: Fetch listings via uk-property-cli
    print("Fetching listings via uk-property-cli...")
    cli_listings = fetch_listings()
    print(f"  CLI returned {len(cli_listings)} listings")
    print()

    # Step 2: Enrich from raw Rightmove JSON
    print("Enriching from raw Rightmove JSON (tenure, location, dates, agent)...")
    raw_props = fetch_raw_listings()
    print(f"  Raw data for {len(raw_props)} properties")
    print()

    # Merge
    all_properties = []
    for cli in cli_listings:
        enriched = enrich_listing(cli, raw_props)
        all_properties.append(enriched)

    print(f"Total enriched: {len(all_properties)}")

    # Filter north of Thames
    north_props = []
    for p in all_properties:
        lat = p.get("location", {}).get("latitude")
        lon = p.get("location", {}).get("longitude")
        address = p.get("address", "")
        if is_north_of_thames(address, lat, lon):
            north_props.append(p)

    print(f"After north-of-Thames filter: {len(north_props)}")

    # Deduplicate
    new_props = [p for p in north_props if str(p.get("id")) not in existing_ids]
    print(f"New properties (not in Airtable): {len(new_props)}")

    # Apply exclusion criteria
    filtered_props = []
    excluded_count = 0
    for p in new_props:
        address = p.get("address", "")
        features_text = " ".join(
            f.get("description", "") if isinstance(f, dict) else str(f)
            for f in p.get("features", [])
        ).lower()
        summary = (p.get("description") or p.get("summary") or "").lower()
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
            except Exception:
                listing_date = datetime.now().strftime("%Y-%m-%d")

        features_text = "\n".join(
            f.get("description", str(f)) if isinstance(f, dict) else str(f)
            for f in prop.get("features", [])
        )

        all_text = features_text.lower() + " " + (prop.get("description") or prop.get("summary") or "").lower()
        garden = "Yes" if "garden" in all_text else ("No" if "no garden" in all_text else "Unknown")

        display_size = prop.get("displaySize", "")
        sqft_match = re.search(r"([\d,]+)\s*sq", display_size)
        sqft = int(sqft_match.group(1).replace(",", "")) if sqft_match else None

        epc_match = re.search(r"EPC[:\s]*([A-G])", all_text, re.IGNORECASE)
        epc = epc_match.group(1).upper() if epc_match else "Unknown"

        tenure = prop.get("tenure") or {}
        tenure_str = (tenure.get("tenureType") or "").upper()
        if tenure_str == "FREEHOLD":
            tenure_str = "Freehold"
        elif tenure_str == "LEASEHOLD":
            tenure_str = "Leasehold"
        else:
            tenure_str = "Unknown"

        rm_type = prop.get("property_type", "Other")
        prop_type = TYPE_MAP.get(rm_type, "Other")

        status = "Dismissed" if prop.get("_excluded") else "New"
        notes = prop.get("_exclusion_reason", "")

        fields = {
            "Address": prop.get("address", ""),
            "Rightmove URL": prop.get("url", "").split("#")[0],  # Clean URL
            "Price": prop.get("price"),
            "Bedrooms": prop.get("beds"),
            "Bathrooms": prop.get("baths"),
            "Property Type": prop_type,
            "Garden": garden,
            "Sq Ft": sqft,
            "Tenure": tenure_str,
            "EPC Rating": epc,
            "Key Features": features_text,
            "Summary": (prop.get("description") or prop.get("summary", ""))[:500],
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
