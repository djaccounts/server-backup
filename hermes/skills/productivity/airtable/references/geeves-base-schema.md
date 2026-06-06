# Geeves Project — Airtable Base Reference

## Base: Geeves
- **Base ID:** `appzvmonQXs4x2AlL`
- **Permission:** `create` (full read/write/schema)
- **Do NOT touch:** `appk0DXJthirMxTZV` ("Practice Management") — absolute restriction

## Schema caveat
The Airtable REST API **cannot create or delete tables**. Tables must be created
manually in the Airtable web UI.

## Python auth pattern — CRITICAL
`AIRTABLE_API_KEY` is stored in `~/.hermes/.env` (Hermes credential store).

`os.environ.get("AIRTABLE_API_KEY")` in `execute_code` Python scripts returns
`None`. The `.env` is NOT injected into the Python subprocess environment.

The key IS available in `terminal()` shell subprocesses and via shell commands
inside Python (`subprocess`).

### Recommended: Use the Geeves helper script
`/root/Geeves/scripts/airtable_api.py` reads the key via shell subprocess:
```bash
python3 /root/Geeves/scripts/airtable_api.py list-tables appzvmonQXs4x2AlL
python3 /root/Geeves/scripts/airtable_api.py create-record appzvmonQXs4x2AlL "People" '{"Full Name": "David"}'
```

### Alternative: terminal() with curl
```bash
ATKEY=$(grep AIRTABLE_API_KEY /root/.hermes/.env | head -1 | cut -d= -f2-)
curl -s "https://api.airtable.com/v0/meta/bases" -H "Authorization: Bearer $ATKEY" | python3 -m json.tool
```

## Core table names (after restructure)
- `People` — the people graph
- `Todos` — tasks
- `Memory_Summaries` — periodic memory roll-ups
- `Output_Log` — generated output log
