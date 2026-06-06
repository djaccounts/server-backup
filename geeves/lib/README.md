# Geeves — Core Utilities

This directory holds shared infrastructure for the Geeves project:
- `api_usage_tracker.py` — logs every API call by service, date, and estimated tokens
- `messaging.py` — messaging abstraction layer (Slack today, Telegram tomorrow)

## Usage
- Import from `/root/Geeves/lib/` in any script or cron job
- Keep this directory clean — shared libraries only, no module-specific code
