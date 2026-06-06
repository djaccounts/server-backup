# Geeves Reference — User Preferences & Design Principles

## Schema Design

- **Consolidated over normalized**: One wide table beats many linked tables. The Films table (personal diary + club + member ratings) is the canonical example.
- **User approval required**: Always show the full field list and get explicit "yes" before creating any table or field. No exceptions.
- **Thread > reference docs**: When a conversation changes a schema decision, update both `schema_registry.json` and the relevant `references/<module>.md` immediately.

## Airtable Gotchas

- API key: read via `subprocess grep` from `/root/.hermes/.env`, never `os.environ`
- Auth: Bearer token in header, base ID `appzvmonQXs4x2AlL`
- NEVER touch base `appk0DXJthirMxTZV` (Practice Management)
- API can't: delete tables/fields, change field types, remove select options → needs web UI
- Use `typecast=true` on batch PATCH to auto-create select options
- Date fields need `{"dateFormat": {"name": "local"}}`, number fields need `{"precision": N}`

## Key Files

- Registry: `/root/Geeves/schema_registry.json` — single source of truth for what exists
- Schema Reference: `/root/Geeves/Geeves_Schema_Reference_v2.md` — proposed fields per module
- Table builder: `/root/Geeves/scripts/table_builder.py`
- CRUD helper: `/root/Geeves/scripts/airtable_api.py`
- Slack capture: `/root/Geeves/scripts/slack_capture.py`

## Module Table IDs

| Module | Table | ID |
|--------|-------|----|
| People | People | tbl1WMPtQhWYW7bTI |
| Todos | Todos | tblTcdZQ9AIltQDfu |
| Memory | Memory_Summaries | tblXH4eCLwM8S30cn |
| Output | Output_Log | tbldJT41dAAX1WTkC |
| Person Notes | Person Notes | tbl6hnxzXXmWFkVfh |
| Conversation Log | Conversation Log | tbl2dbgksA9XveLcx |
| Weather | Weather_Data | tblFd4kAahIUozJsf |
| Stocks | Stock_Prices | tblI1oXlNIFXrVm7f |
| Facts | Fact_of_the_Day | tblUTCWleQD61Ti2v |
| Token Usage | Token_Usage | tbl3EjtE3YW1ZUqEv |
| Films | Films | tblqCpp3EB7wU2ZZ3 |
