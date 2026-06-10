# Garmin Connect Integration

## Overview

Geeves imports cycling activities from Garmin Connect using the unofficial `garminconnect` Python package. The script fetches rides, creates both a Workout record and a detailed Cycling record in Airtable.

## Setup

### 1. Install the package

```bash
pip3 install garminconnect
```

### 2. Add credentials to `/root/.hermes/.env`

```
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=yourpassword
```

### 3. First-run authentication

The first login may trigger 2FA. Run interactively:

```bash
python3 /root/Geeves/scripts/garmin_fetch.py --days 1
```

## Script: `garmin_fetch.py`

**Location:** `/root/Geeves/scripts/garmin_fetch.py`

**Usage:**
```bash
# Dry run (fetch only, don't write)
python3 garmin_fetch.py --days 7

# Write to Airtable
python3 garmin_fetch.py --days 7 --write

# Fetch all history
python3 garmin_fetch.py --all --write
```

**What it does:**
1. Logs in to Garmin Connect
2. Fetches cycling activities (filters by activity type)
3. For each ride creates a Workout record + a detailed Cycling record
4. Links Cycling → Workout

## Cron Job

- **Job ID:** `0d2ddb20ece8`
- **Schedule:** Daily at 7am UTC
- **Fetches:** Last 2 days of activities

## Known Issues

- **Misclassified activities:** Garmin may auto-classify long rides as "Walking". Manual correction may be needed.
- **2FA:** First login may require interactive 2FA input.
- **Units:** Garmin returns meters/mps; script converts to miles/mph.
- **Adding People:** Import doesn't auto-tag ride partners. Edit in Airtable to add People links.
