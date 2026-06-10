#!/bin/bash
# airtable.sh — Airtable API helper for Geeves
# Usage: ./airtable.sh METHOD [PATH] [DATA]
#
# Examples:
#   ./airtable.sh GET meta/bases
#   ./airtable.sh GET "meta/bases/appzvmonQXs4x2AlL/tables"
#   ./airtable.sh PATCH "appzvmonQXs4x2AlL/Table%201" '{"fields":{"Name":"test"}}'

ATKEY=$(grep AIRTABLE_API_KEY /root/.hermes/.env 2>/dev/null | head -1 | cut -d= -f2-)
BASE="https://api.airtable.com/v0"

METHOD="${1:-GET}"
PATH_VAL="${2:-}"
DATA="${3:-}"

if [ -z "$ATKEY" ]; then
  echo "ERROR: AIRTABLE_API_KEY not found" >&2
  exit 1
fi

URL="${BASE}/${PATH_VAL}"

CMD=(curl -s -X "$METHOD" "$URL" -H "Authorization: Bearer $ATKEY")

if [ -n "$DATA" ]; then
  CMD+=(-H "Content-Type: application/json" -d "$DATA")
fi

exec "${CMD[@]}"
