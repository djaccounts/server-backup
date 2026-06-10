#!/usr/bin/env python3
"""
Geeves Airtable Module Scaffold

Generates field definitions for a new module's tables so you can create them
in the Airtable web UI. Usage:

    python3 module_scaffold.py <module_name> [--output md|json]

Examples:
    python3 module_scaffold.py DinnerParty
    python3 module_scaffold.py FilmClub --output json

Airtable CANNOT create tables or fields via API — this outputs instructions
for manual creation in the Airtable web UI.
"""
import json, sys, os
from datetime import datetime

# ── Universal fields that every module table gets ───────────────────────────
UNIVERSAL_FIELDS = {
    "Data": [
        {"name": "Created", "type": "createdTime", "auto": True},
        {"name": "Last Modified", "type": "lastModifiedTime", "auto": True},
    ],
    "Context": [
        {"name": "Key", "type": "singleLineText", "note": "Unique key for this context entry"},
        {"name": "Value", "type": "multilineText", "note": "The context/preference data"},
        {"name": "Updated", "type": "lastModifiedTime", "auto": True},
    ],
    "Log": [
        {"name": "Item", "type": "singleLineText", "note": "What was generated"},
        {"name": "Generated At", "type": "date", "note": "When it was created"},
        {"name": "Content", "type": "multilineText", "note": "The generated output"},
        {"name": "Rating", "type": "singleSelect", "options": ["★★★ Great", "★★ OK", "★ Poor"]},
        {"name": "Feedback", "type": "multilineText", "note": "David's notes"},
    ],
}

# ── Type mapping: human name → Airtable type ───────────────────────────────
TYPE_MAP = {
    "text": "Single line text",
    "longText": "Long text",
    "date": "Date",
    "dateTime": "Date and time",
    "number": "Number",
    "checkbox": "Checkbox",
    "select": "Single select",
    "multiSelect": "Multiple select",
    "link": "Link to another record",
    "email": "Email",
    "phone": "Phone number",
    "url": "URL",
    "createdTime": "Created time (auto)",
    "lastModifiedTime": "Last modified time (auto)",
}


def generate_module(module_name: str) -> dict:
    """Generate the 3-table schema for a module."""
    prefix = module_name.replace(" ", "")

    tables = {}

    # 1. Data table
    data_name = f"{prefix}_Data"
    data_fields = [
        {"name": "Name", "type": "singleLineText", "note": "Primary field"},
    ]
    data_fields.extend(UNIVERSAL_FIELDS["Data"])
    tables[data_name] = data_fields

    # 2. Context table
    context_name = f"{prefix}_Context"
    context_fields = list(UNIVERSAL_FIELDS["Context"])
    tables[context_name] = context_fields

    # 3. Log table
    log_name = f"{prefix}_Log"
    log_fields = list(UNIVERSAL_FIELDS["Log"])
    tables[log_name] = log_fields

    return {
        "module": module_name,
        "tables": tables,
        "created": datetime.now().isoformat(),
    }


def format_markdown(schema: dict) -> str:
    """Format schema as markdown instructions for Airtable web UI."""
    lines = [
        f"# Module: {schema['module']}",
        "",
        f"Generated: {schema['created']}",
        "",
        "Create these 3 tables in the Geeves Airtable base.",
        "",
    ]

    for table_name, fields in schema["tables"].items():
        lines.append(f"## Table: `{table_name}`")
        lines.append("")
        lines.append("| # | Field name | Type | Notes |")
        lines.append("|---|-----------|------|-------|")

        for i, f in enumerate(fields, 1):
            note = f.get("note", "")
            options = ""
            if "options" in f:
                options = f" → options: {', '.join(f['options'])}"
            lines.append(f"| {i} | {f['name']} | {f['type']} | {note}{options} |")

        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("### Steps in Airtable web UI")
    lines.append("")
    for table_name in schema["tables"]:
        lines.append(f"1. Click **\"+\"** → name it **{table_name}**")
        lines.append(f"2. Add the fields listed above")
        lines.append("")

    return "\n".join(lines)


def format_json(schema: dict) -> str:
    return json.dumps(schema, indent=2)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    module_name = args[0]
    output_format = "md"
    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output_format = args[idx + 1]

    schema = generate_module(module_name)

    if output_format == "json":
        print(format_json(schema))
    else:
        print(format_markdown(schema))

    # Also save to file
    out_dir = "/root/Geeves/module_schemas"
    os.makedirs(out_dir, exist_ok=True)
    safe_name = module_name.replace(" ", "_")
    out_path = os.path.join(out_dir, f"{safe_name}.md")
    with open(out_path, "w") as f:
        f.write(format_markdown(schema))
    print(f"\nSaved to: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
