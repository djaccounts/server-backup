#!/usr/bin/env python3
"""Clean up Google Contacts import into Airtable People table - FULL scan with pagination."""
import subprocess, json, re, time
import urllib.request, urllib.error

ENV_PATH = "/root/.hermes/.env"
BASE = "appzvmonQXs4x2AlL"
PEOPLE_TABLE = "People"

def get_key():
    r = subprocess.run(["grep", "AIRTABLE_API_KEY", ENV_PATH], capture_output=True, text=True)
    return r.stdout.strip().split("\n")[0].split("=", 1)[1]

def api_get(path):
    key = get_key()
    url = "https://api.airtable.com/v0/" + path
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def api_patch(path, data):
    key = get_key()
    url = "https://api.airtable.com/v0/" + path
    body = json.dumps(data).encode()
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method="PATCH")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# Get ALL records with pagination
all_records = []
offset = None
page = 0
while True:
    path = BASE + "/" + PEOPLE_TABLE + "?maxRecords=100"
    if offset:
        path += "&offset=" + offset
    result = api_get(path)
    batch = result.get("records", [])
    all_records.extend(batch)
    page += 1
    offset = result.get("offset")
    if not offset:
        break

print("Scanning " + str(len(all_records)) + " records across " + str(page) + " pages...")

# Collect all fixes first
patches = {}  # rid -> {fields}

for rec in all_records:
    f = rec["fields"]
    rid = rec["id"]
    name = f.get("Name", "")
    upd = {}

    # 1. Remove name suffixes like "(btron)", "(Rob)"
    cleaned = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
    if cleaned != name:
        upd["Name"] = cleaned

    # 2. Fix lowercase names (e.g. "Sean snow" -> "Sean Snow")
    # Only fix if the name is all-lowercase or has lowercase after space
    if name and name != name.title() and " " in name:
        titled = name.title()
        # Don't title-case things like "O'Brien" or "McDonald" properly — just basic fix
        if titled != name:
            upd["Name"] = titled

    # 3. Clean non-breaking spaces in phone
    phone = f.get("Phone", "")
    if phone and "\xa0" in phone:
        upd["Phone"] = phone.replace("\xa0", " ").strip()

    # 4. Clear addresses from Venue Preferences
    venue = f.get("Venue Preferences", "")
    if venue and re.search(r"\d", venue) and "," in venue:
        upd["Venue Preferences"] = ""

    # 5. Clear Social Notes that contain job titles (single words or short phrases)
    # These were mapped from organizations.title — not really social notes
    social = f.get("Social Notes", "")
    if social and len(social) < 30 and not any(x in social.lower() for x in ["introvert", "extrovert", "quiet", "loud", "shy", "outgoing"]):
        upd["Social Notes"] = ""

    # 6. Move Topics They Love URLs to a better field if it looks like a URL
    topics = f.get("Topics They Love", "")
    if topics and topics.startswith("http"):
        upd["Topics They Love"] = ""

    if upd:
        patches[rid] = upd

print("Found " + str(len(patches)) + " records to patch")

# Apply in batches of 10
patch_list = list(patches.items())
applied = 0
for i in range(0, len(patch_list), 10):
    batch = patch_list[i:i+10]
    records = [{"id": rid, "fields": fields} for rid, fields in batch]
    result = api_patch(BASE + "/" + PEOPLE_TABLE, {"records": records})
    applied += len(result.get("records", []))
    time.sleep(0.25)

print("Applied patches to " + str(applied) + " records\n")

# Count fixes by type
name_cleaned = sum(1 for f in patches.values() if "Name" in f)
phone_cleaned = sum(1 for f in patches.values() if "Phone" in f)
venue_cleared = sum(1 for f in patches.values() if "Venue Preferences" in f)
social_cleared = sum(1 for f in patches.values() if "Social Notes" in f)
topics_cleared = sum(1 for f in patches.values() if "Topics They Love" in f)

print("=== Fix Summary ===")
print("Names fixed (suffix + casing): " + str(name_cleaned))
print("Phones cleaned (nbsp):         " + str(phone_cleaned))
print("Venue cleared (addresses):     " + str(venue_cleared))
print("Social Notes cleared (job titles): " + str(social_cleared))
print("Topics They Love cleared (URLs): " + str(topics_cleared))

# Show some examples
print("\n=== Name changes ===")
count = 0
for rid, fields in patches.items():
    if "Name" in fields:
        # Get original name
        for rec in all_records:
            if rec["id"] == rid:
                print("  " + rec["fields"].get("Name", "") + " -> " + fields["Name"])
                count += 1
                if count >= 15:
                    print("  ...")
                    break
        if count >= 15:
            break

print("\nDone!")
