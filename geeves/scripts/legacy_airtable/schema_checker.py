#!/usr/bin/env python3
"""
Geeves Airtable Schema Checker

Reads the current Geeves base schema from the Airtable API and checks it
against expected definitions. Usage:

    python3 schema_checker.py                    # check all tables
    python3 schema_checker.py --table People     # check one table
    python3 schema_checker.py --json             # output raw schema as JSON
"""
import subprocess, json, sys, urllib.request, urllib.error

def get_key():
    r = subprocess.run(
        ["grep", "AIRTABLE_API_KEY", "/root/.hermes/.env"],
        capture_output=True, text=True
    )
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def api(path, method="GET"):
    key = get_key()
    url = f"https://api.airtable.com/v0/{path}"
    headers = {"Authorization": f"Bearer {key}"}
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {json.loads(e.read())}")

def main():
    args = sys.argv[1:]
    show_json = "--json" in args
    table_filter = None
    if "--table" in args:
        idx = args.index("--table")
        if idx + 1 < len(args):
            table_filter = args[idx + 1]

    BASE = "appzvmonQXs4x2AlL"
    r = api(f"meta/bases/{BASE}/tables")
    tables = r.get("tables", [])

    if show_json:
        print(json.dumps(r, indent=2))
        return

    # ── Expected schemas ─────────────────────────────────────────────────────
    EXPECTED = {
        "People": {
            "fields": [
                "Full Name", "Relationship", "Birthday", "Phone", "Email",
                "How Known", "Dietary Requirements", "Allergies",
                "Dietary Dislikes", "Portion Notes", "Hobbies",
                "Topics They Love", "Topics to Avoid", "Gift Interests",
                "Gift Budget", "Past Gifts", "What Landed", "Social Style",
                "Venue Preferences", "Social Notes", "Anniversaries",
                "Important Dates", "Last Seen", "Contact Frequency",
                "Relationship Notes", "Conversation Log", "Tier",
            ],
            "note": "People graph — the spine of Geeves",
        },
        "Todos": {
            "fields": ["Task", "Status", "Priority", "Due Date", "Module",
                        "Linked Person", "Notes", "Created", "Completed Date"],
            "note": "Tasks and to-dos",
        },
        "Memory_Summaries": {
            "fields": ["Period", "Summary", "Source Entries", "Created"],
            "note": "Periodic long-term memory roll-ups",
        },
        "Output_Log": {
            "fields": ["Item", "Module", "Generated At", "Content",
                        "Rating", "Feedback", "Prompt Used"],
            "note": "What Geeves generated, when, and how it was rated",
        },
    }

    issues = []

    for t in tables:
        name = t["name"]
        if table_filter and name != table_filter:
            continue

        field_names = {f["name"] for f in t.get("fields", [])}
        field_map = {f["name"]: f for f in t.get("fields", [])}

        print(f"\n{'='*60}")
        print(f"TABLE: {name}  (id: {t['id']})")
        print(f"{'='*60}")

        if name in EXPECTED:
            expected_fields = set(EXPECTED[name]["fields"])
            missing = expected_fields - field_names
            extra = field_names - expected_fields

            print(f"  Note: {EXPECTED[name]['note']}")

            if missing:
                print(f"  ⚠️  MISSING fields: {', '.join(sorted(missing))}")
                issues.append((name, "missing", missing))

            if extra:
                print(f"  ℹ️  Extra fields (not in spec): {', '.join(sorted(extra))}")

            if not missing and not extra:
                print(f"  ✅ Schema matches specification")
            elif not missing:
                print(f"  ✅ All required fields present (has extras)")

            # List all fields with types
            print(f"\n  Fields ({len(field_names)}):")
            for f in sorted(field_map.values(), key=lambda x: x["name"]):
                opts = ""
                if "options" in f and "choices" in f.get("options", {}):
                    choices = [c["name"] for c in f["options"]["choices"]]
                    opts = f" → {choices}"
                print(f"    {f['id']:22s}  {f['name']:28s}  {f['type']}{opts}")
        else:
            print(f"  ℹ️  No expected schema defined for this table")
            print(f"  Fields: {', '.join(sorted(field_names))}")

    # ── Summary ─────────────────────────────────────────────────────────────
    missing_tables = set(EXPECTED.keys()) - {t["name"] for t in tables}
    if missing_tables:
        print(f"\n⚠️  MISSING TABLES: {', '.join(sorted(missing_tables))}")
        for mt in sorted(missing_tables):
            issues.append((mt, "missing_table", set()))

    if issues:
        print(f"\n{'='*60}")
        print(f"ISSUES FOUND: {len(issues)}")
        print(f"{'='*60}")
        for table, kind, items in issues:
            if kind == "missing_table":
                print(f"  ❌ Table '{table}' does not exist")
            else:
                print(f"  ⚠️  Table '{table}': missing {len(items)} fields")
        sys.exit(1)
    else:
        print(f"\n✅ All tables match their expected schemas")
        sys.exit(0)


if __name__ == "__main__":
    main()
