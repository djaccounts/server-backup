#!/usr/bin/env python3
"""
google_contacts_sync.py — Two-way sync between Google Contacts and Baserow People table.

Matching strategy (no Baserow schema changes needed):
  - Google Contacts resource names are stored in a local mapping file
  - Matching priority: google_contacts_id (mapping file) → email → phone → name
  - The mapping file is the source of truth for which Google Contact maps to which Person

Direction 1: Google → Baserow
  - Fetches all Google Contacts
  - Matches to existing People records
  - Creates new People records for unmatched Google contacts
  - Updates changed contact fields (name, phone, email, birthday)

Direction 2: Baserow → Google
  - Finds People records modified since last sync that have a mapping entry
  - Pushes name/email/phone/birthday updates back to Google

Usage:
    python3 google_contacts_sync.py [--dry-run] [--direction google-to-baserow|baserow-to-google|both]
    python3 google_contacts_sync.py --status

Files:
    /root/Geeves/google_contacts_mapping.json   — Google resource_name → Baserow row_id
    /root/Geeves/google_contacts_sync_state.json — last sync timestamp
    /root/Geeves/google_contacts_sync.log        — sync log
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

# ── Paths ──────────────────────────────────────────────────────────────────
ENV_PATH = os.path.expanduser("~/.hermes/.env")
GOOGLE_TOKEN_PATH = os.path.expanduser("~/.hermes/google_token.json")
MAPPING_PATH = "/root/Geeves/baserow_mapping.json"
CONTACTS_MAPPING_PATH = "/root/Geeves/google_contacts_mapping.json"
STATE_PATH = "/root/Geeves/google_contacts_sync_state.json"
LOG_PATH = "/root/Geeves/google_contacts_sync.log"

# ── Baserow config ────────────────────────────────────────────────────────
GEVES_DB_ID = 132
PEOPLE_TABLE_ID = 359
BASE_URL = "http://77.68.33.121"

# ── Google People API ─────────────────────────────────────────────────────
GOOGLE_PEOPLE_API = "https://people.googleapis.com/v1"
CONTACT_FIELDS = "names,emailAddresses,phoneNumbers,birthdays,photos,biographies,organizations"
PAGE_SIZE = 1000


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def get_baserow_token():
    import subprocess
    r = subprocess.run(["grep", "BASEROW_API_TOKEN", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def get_google_token():
    """Read and refresh the Google OAuth token."""
    import subprocess

    if not os.path.exists(GOOGLE_TOKEN_PATH):
        log("ERROR: Google token not found at ~/.hermes/google_token.json")
        sys.exit(1)

    with open(GOOGLE_TOKEN_PATH) as f:
        creds = json.load(f)

    expiry_str = creds.get("expiry", "")
    if expiry_str:
        try:
            expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if now >= expiry:
                log("Google token expired, refreshing...")
                creds = refresh_google_token(creds)
        except Exception:
            pass

    return creds


def refresh_google_token(creds):
    import urllib.request, urllib.error
    payload = json.dumps({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request(
        creds.get("token_uri", "https://oauth2.googleapis.com/token"),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        new_creds = json.loads(resp.read())
    creds["token"] = new_creds["access_token"]
    # Calculate expiry
    expires_in = new_creds.get("expires_in", 3600)
    from datetime import timedelta
    creds["expiry"] = (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
    with open(GOOGLE_TOKEN_PATH, "w") as f:
        json.dump(creds, f, indent=2)
    log("Google token refreshed.")
    return creds


def baserow_api(method, path, data=None):
    import urllib.request, urllib.error
    token = get_baserow_token()
    url = BASE_URL + path
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read()
            if resp.status == 204 or not resp_body:
                return {}
            return json.loads(resp_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        raise Exception(f"Baserow API error {e.code}: {err_body}")


def google_api(method, path, data=None, token=None):
    import urllib.request, urllib.error
    tok = token or get_google_token()["token"]
    url = GOOGLE_PEOPLE_API + path
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read()
            if resp.status == 204 or not resp_body:
                return {}
            return json.loads(resp_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        raise Exception(f"Google API error {e.code}: {err_body}")


def load_contacts_mapping():
    """Load the Google resource_name → Baserow row_id mapping."""
    if os.path.exists(CONTACTS_MAPPING_PATH):
        with open(CONTACTS_MAPPING_PATH) as f:
            return json.load(f)
    return {"contacts": {}, "people": {}}


def save_contacts_mapping(mapping):
    with open(CONTACTS_MAPPING_PATH, "w") as f:
        json.dump(mapping, f, indent=2)


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"last_sync": None}


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def load_baserow_mapping():
    with open(MAPPING_PATH) as f:
        return json.load(f)


def resolve_field_id(field_name, mapping):
    table = mapping.get("tables", {}).get("People", {})
    fields = table.get("fields", {})
    finfo = fields.get(field_name)
    if finfo:
        return f"field_{finfo['id']}"
    return None


# ═══════════════════════════════════════════════════════════════════════════
# GOOGLE CONTACTS → DATA
# ═══════════════════════════════════════════════════════════════════════════

def fetch_google_contacts(creds):
    token = creds["token"]
    contacts = []
    page_token = None
    while True:
        params = f"?personFields={CONTACT_FIELDS}&pageSize={PAGE_SIZE}&sortOrder=LAST_MODIFIED_DESCENDING"
        if page_token:
            params += f"&pageToken={page_token}"
        result = google_api("GET", f"/people/me/connections{params}", token=token)
        connections = result.get("connections", [])
        contacts.extend(connections)
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    log(f"Fetched {len(contacts)} Google Contacts")
    return contacts


def parse_google_contact(gc):
    names = gc.get("names", [])
    name = names[0].get("displayName", "") if names else ""

    emails = gc.get("emailAddresses", [])
    email = emails[0].get("value", "") if emails else ""

    phones = gc.get("phoneNumbers", [])
    phone = phones[0].get("value", "") if phones else ""

    birthdays = gc.get("birthdays", [])
    birthday = ""
    if birthdays:
        bday = birthdays[0].get("date", {})
        if bday:
            year = bday.get("year", "")
            month = bday.get("month", 0)
            day = bday.get("day", 0)
            if year:
                birthday = f"{year}-{month:02d}-{day:02d}"
            elif month and day:
                birthday = f"{month:02d}-{day:02d}"

    return {
        "resource_name": gc.get("resourceName", ""),
        "name": name,
        "email": email.strip().lower() if email else "",
        "phone": phone.strip() if phone else "",
        "birthday": birthday,
    }


# ═══════════════════════════════════════════════════════════════════════════
# BASEROW PEOPLE → DATA
# ═══════════════════════════════════════════════════════════════════════════

def build_field_name_to_id_mapping(baserow_mapping):
    """Build a reverse mapping: field_name -> field_XXXX for People table."""
    table = baserow_mapping.get("tables", {}).get("People", {})
    fields = table.get("fields", {})
    return {name: f"field_{info['id']}" for name, info in fields.items()}


def resolve_person_field(person, field_name, name_to_id):
    """Get a field value from a person record using the field name."""
    fid = name_to_id.get(field_name)
    if fid and fid in person:
        val = person[fid]
        # Handle single_select objects
        if isinstance(val, dict):
            return val.get("value", "")
        return val or ""
    return ""


def fetch_all_people():
    all_people = []
    page = 1
    while True:
        result = baserow_api("GET", f"/api/database/rows/table/{PEOPLE_TABLE_ID}/?size=100&page={page}")
        batch = result.get("results", [])
        all_people.extend(batch)
        if not result.get("next"):
            break
        page += 1
    log(f"Fetched {len(all_people)} People records from Baserow")
    return all_people


def build_people_index(people, name_to_id):
    by_email = {}
    by_phone = {}
    by_name = {}
    for p in people:
        pid = p.get("id")
        email = resolve_person_field(p, "Email", name_to_id).strip().lower()
        phone = resolve_person_field(p, "Phone", name_to_id).strip()
        name = resolve_person_field(p, "Name", name_to_id).strip().lower()
        if email:
            by_email[email] = p
        if phone:
            by_phone[phone] = p
        if name:
            by_name[name] = p
    return by_email, by_phone, by_name


# ═══════════════════════════════════════════════════════════════════════════
# GOOGLE → BASEROW SYNC
# ═══════════════════════════════════════════════════════════════════════════

def sync_google_to_baserow(dry_run=False):
    log("=" * 60)
    log("GOOGLE → BASEROW SYNC")
    log("=" * 60)

    creds = get_google_token()
    baserow_mapping = load_baserow_mapping()
    contacts_mapping = load_contacts_mapping()

    google_contacts = fetch_google_contacts(creds)
    people = fetch_all_people()
    name_to_id = build_field_name_to_id_mapping(baserow_mapping)
    by_email, by_phone, by_name = build_people_index(people, name_to_id)

    created = 0
    updated = 0
    unchanged = 0
    errors = 0

    for gc in google_contacts:
        try:
            gc_data = parse_google_contact(gc)
            if not gc_data["name"] and not gc_data["email"] and not gc_data["phone"]:
                continue

            resource_name = gc_data["resource_name"]

            # Check if already mapped
            person = None
            match_method = None

            if resource_name in contacts_mapping["contacts"]:
                row_id = contacts_mapping["contacts"][resource_name]
                # Find the person by ID
                for p in people:
                    if p.get("id") == row_id:
                        person = p
                        match_method = "mapping"
                        break

            if not person:
                # Match by email
                if gc_data["email"] and gc_data["email"] in by_email:
                    person = by_email[gc_data["email"]]
                    match_method = "email"
                # Match by phone
                elif gc_data["phone"]:
                    phone_digits = "".join(c for c in gc_data["phone"] if c.isdigit())
                    for phone, p in by_phone.items():
                        p_digits = "".join(c for c in phone if c.isdigit())
                        if phone_digits and p_digits and phone_digits == p_digits:
                            person = p
                            match_method = "phone"
                            break
                # Match by name
                if not person and gc_data["name"]:
                    name_lower = gc_data["name"].strip().lower()
                    if name_lower in by_name:
                        person = by_name[name_lower]
                        match_method = "name"

            if person:
                pid = person.get("id")
                changes = {}

                person_name = resolve_person_field(person, "Name", name_to_id)
                person_email = resolve_person_field(person, "Email", name_to_id).lower()
                person_phone = resolve_person_field(person, "Phone", name_to_id)
                person_birthday = resolve_person_field(person, "Birthday", name_to_id)

                if gc_data["name"] and gc_data["name"] != person_name:
                    changes["Name"] = gc_data["name"]
                if gc_data["email"] and gc_data["email"] != person_email:
                    changes["Email"] = gc_data["email"]
                if gc_data["phone"] and gc_data["phone"] != person_phone:
                    changes["Phone"] = gc_data["phone"]
                if gc_data["birthday"] and gc_data["birthday"] != person_birthday:
                    changes["Birthday"] = gc_data["birthday"]

                # Update mapping
                if resource_name not in contacts_mapping["contacts"]:
                    contacts_mapping["contacts"][resource_name] = pid
                    contacts_mapping["people"][str(pid)] = resource_name

                if changes:
                    updated += 1
                    log(f"  UPDATE: {gc_data['name']} (matched by {match_method}) — {list(changes.keys())}")
                    if not dry_run:
                        row_data = {}
                        for k, v in changes.items():
                            fid = resolve_field_id(k, baserow_mapping)
                            if fid:
                                row_data[fid] = v
                        if row_data:
                            baserow_api("PATCH", f"/api/database/rows/table/{PEOPLE_TABLE_ID}/{pid}/", row_data)
                            time.sleep(0.1)
                else:
                    unchanged += 1
            else:
                # Create new Person
                created += 1
                log(f"  CREATE: {gc_data['name']} ({gc_data['email']})")
                if not dry_run:
                    row_data = {}
                    for field in ["Name", "Email", "Phone", "Birthday"]:
                        val = gc_data.get(field.lower())
                        if val:
                            fid = resolve_field_id(field, baserow_mapping)
                            if fid:
                                row_data[fid] = val
                    if row_data:
                        result = baserow_api("POST", f"/api/database/rows/table/{PEOPLE_TABLE_ID}/", row_data)
                        new_id = result.get("id")
                        if new_id:
                            contacts_mapping["contacts"][resource_name] = new_id
                            contacts_mapping["people"][str(new_id)] = resource_name
                        time.sleep(0.1)

        except Exception as e:
            errors += 1
            log(f"  ERROR: {e}")

    if not dry_run:
        save_contacts_mapping(contacts_mapping)

    log(f"\nGoogle → Baserow: created={created}, updated={updated}, unchanged={unchanged}, errors={errors}")
    return {"created": created, "updated": updated, "unchanged": unchanged, "errors": errors}


# ═══════════════════════════════════════════════════════════════════════════
# BASEROW → GOOGLE SYNC
# ═══════════════════════════════════════════════════════════════════════════

def sync_baserow_to_google(dry_run=False):
    log("=" * 60)
    log("BASEROW → GOOGLE SYNC")
    log("=" * 60)

    creds = get_google_token()
    state = load_state()
    last_sync = state.get("last_sync")
    contacts_mapping = load_contacts_mapping()

    people = fetch_all_people()

    pushed = 0
    skipped = 0
    errors = 0

    for person in people:
        try:
            pid = person.get("id")
            resource_name = contacts_mapping["people"].get(str(pid))
            if not resource_name:
                skipped += 1
                continue

            # Check if modified since last sync
            last_modified = person.get("Last Modified", "") or person.get("last_modified", "")
            if last_sync and last_modified:
                try:
                    mod_time = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
                    sync_time = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
                    if mod_time <= sync_time:
                        skipped += 1
                        continue
                except Exception:
                    pass

            # Build update
            update_fields = {}
            update_mask = []

            name = person.get("Name", "")
            if name:
                update_fields["names"] = [{"givenName": name}]
                update_mask.append("names")

            email = person.get("Email", "")
            if email:
                update_fields["emailAddresses"] = [{"value": email}]
                update_mask.append("emailAddresses")

            phone = person.get("Phone", "")
            if phone:
                update_fields["phoneNumbers"] = [{"value": phone}]
                update_mask.append("phoneNumbers")

            birthday = person.get("Birthday", "")
            if birthday:
                parts = birthday.split("-")
                if len(parts) == 3:
                    update_fields["birthdays"] = [{"date": {"year": int(parts[0]), "month": int(parts[1]), "day": int(parts[2])}}]
                    update_mask.append("birthdays")
                elif len(parts) == 2:
                    update_fields["birthdays"] = [{"date": {"month": int(parts[0]), "day": int(parts[1])}}]
                    update_mask.append("birthdays")

            if not update_mask:
                skipped += 1
                continue

            log(f"  PUSH: {name} → Google ({', '.join(update_mask)})")
            if not dry_run:
                google_api("PATCH", f"/{resource_name}", {
                    **update_fields,
                    "updatePersonFields": ",".join(update_mask)
                }, token=creds["token"])
                time.sleep(0.1)

            pushed += 1

        except Exception as e:
            errors += 1
            log(f"  ERROR pushing {person.get('Name', '?')}: {e}")

    log(f"\nBaserow → Google: pushed={pushed}, skipped={skipped}, errors={errors}")
    return {"pushed": pushed, "skipped": skipped, "errors": errors}


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Google Contacts ↔ Baserow People two-way sync")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--direction", choices=["google-to-baserow", "baserow-to-google", "both"], default="both")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if args.status:
        state = load_state()
        mapping = load_contacts_mapping()
        print(f"Last sync: {state.get('last_sync', 'never')}")
        print(f"Mapped contacts: {len(mapping['contacts'])}")
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH) as f:
                lines = f.readlines()
            print(f"\nLast 10 log lines:")
            for line in lines[-10:]:
                print(f"  {line.rstrip()}")
        return

    log("=" * 60)
    log(f"SYNC START — direction={args.direction}, dry_run={args.dry_run}")
    log("=" * 60)

    results = {}

    if args.direction in ("google-to-baserow", "both"):
        results["google_to_baserow"] = sync_google_to_baserow(dry_run=args.dry_run)

    if args.direction in ("baserow-to-google", "both"):
        results["baserow_to_google"] = sync_baserow_to_google(dry_run=args.dry_run)

    if not args.dry_run:
        state = load_state()
        state["last_sync"] = datetime.now(timezone.utc).isoformat()
        state["direction"] = args.direction
        save_state(state)
        log("Sync state saved.")

    log("SYNC COMPLETE")


if __name__ == "__main__":
    main()
