#!/usr/bin/env python3
"""
meal_photo_pipeline.py — Download a food photo, analyze it, and log the meal to Baserow.

Usage:
    python3 meal_photo_pipeline.py <image_url> [--meal-type Breakfast|Lunch|Dinner|Snack] [--date YYYY-MM-DD]

Steps:
    1. Download image from URL (with Slack auth if needed)
    2. Analyze with vision model (via hermes_tools vision_analyze)
    3. Estimate macros
    4. Log to Baserow Meals table

This script handles steps 1 and 4. Steps 2-3 are done by the agent (vision analysis + macro estimation).
"""

import argparse
import subprocess
import sys
import os
import json
import datetime
import urllib.request
import urllib.error

ENV_PATH = os.path.expanduser("~/.hermes/.env")
MAPPING_PATH = "/root/Geeves/baserow_mapping.json"
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_env_var(name):
    """Read a variable from .env file."""
    r = subprocess.run(["grep", f"^{name}=", ENV_PATH], capture_output=True, text=True)
    if r.returncode == 0:
        line = r.stdout.strip().split("\n")[0]
        return line.split("=", 1)[1]
    return ""


def download_image(url, output_path):
    """Download image from URL. Handles Slack auth if URL is from Slack, and local file paths."""
    # Handle local file paths
    if url.startswith("file://"):
        import shutil
        src = url[7:]
        shutil.copy2(src, output_path)
        return True, os.path.getsize(output_path)
    
    slack_token = get_env_var("SLACK_BOT_TOKEN")
    
    headers = {}
    if "slack.com" in url or "slack-files.com" in url:
        if slack_token:
            headers["Authorization"] = f"Bearer {slack_token}"
    
    # Add user-agent for non-Slack URLs
    if not headers:
        headers["User-Agent"] = "Mozilla/5.0 (compatible; Geeves/1.0)"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            with open(output_path, "wb") as f:
                f.write(data)
            return True, len(data)
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        return False, str(e)


def log_meal_to_baserow(description, date, meal_type, calories, protein, carbs, fat, accuracy="Estimated", source=None):
    """Log a meal record to Baserow using baserow_api.py."""
    sys.path.insert(0, SCRIPTS_DIR)
    import baserow_api
    
    # Default source: use "Photo" if available in Baserow, otherwise "Slack"
    if source is None:
        source = "Slack"  # TODO: change to "Photo" once added to Baserow select options
    
    with open(MAPPING_PATH) as f:
        mapping = json.load(f)
    
    fields = {
        "Description": description[:200],
        "Date": date,
        "Meal type": meal_type,
        "Calories (est)": int(round(calories)),
        "Protein (g)": int(round(protein)),
        "Carbs (g)": int(round(carbs)),
        "Fat (g)": int(round(fat)),
        "Accuracy": accuracy,
        "Source": source,
    }
    
    ok, result = baserow_api.baserow_post(mapping, "Meals", fields)
    if ok:
        return True, result
    return False, result


def main():
    parser = argparse.ArgumentParser(description="Download food photo and prepare for meal logging")
    parser.add_argument("image_url", help="URL of the food photo")
    parser.add_argument("--meal-type", default=None, choices=["Breakfast", "Lunch", "Dinner", "Snack"],
                        help="Meal type (auto-detected from time if not specified)")
    parser.add_argument("--date", default=None, help="Date YYYY-MM-DD (default: today)")
    parser.add_argument("--output", default="/tmp/meal_photo.jpg", help="Output path for downloaded image")
    parser.add_argument("--log", action="store_true", help="Also log to Baserow (requires --description and macro args)")
    parser.add_argument("--description", default=None, help="Meal description (for --log mode)")
    parser.add_argument("--calories", type=float, default=None, help="Estimated calories")
    parser.add_argument("--protein", type=float, default=None, help="Estimated protein (g)")
    parser.add_argument("--carbs", type=float, default=None, help="Estimated carbs (g)")
    parser.add_argument("--fat", type=float, default=None, help="Estimated fat (g)")
    
    args = parser.parse_args()
    
    # Step 1: Download the image
    print(f"📥 Downloading image from {args.image_url[:60]}...")
    ok, result = download_image(args.image_url, args.output)
    if not ok:
        print(f"❌ Download failed: {result}")
        sys.exit(1)
    print(f"✅ Downloaded {result} bytes to {args.output}")
    
    # Determine meal type from time if not specified
    meal_type = args.meal_type
    if not meal_type:
        hour = datetime.datetime.now().hour
        if hour < 11:
            meal_type = "Breakfast"
        elif hour < 14:
            meal_type = "Lunch"
        elif hour >= 17:
            meal_type = "Dinner"
        else:
            meal_type = "Snack"
    
    date = args.date or datetime.date.today().isoformat()
    
    print(f"\n📋 Photo ready for analysis: {args.output}")
    print(f"   Meal type: {meal_type}")
    print(f"   Date: {date}")
    print(f"\n🔍 Next: Run vision analysis on the image to identify food and estimate macros.")
    
    # Optional: log directly if all fields provided
    if args.log:
        if not args.description:
            print("❌ --description required for --log mode")
            sys.exit(1)
        
        calories = args.calories or 0
        protein = args.protein or 0
        carbs = args.carbs or 0
        fat = args.fat or 0
        
        print(f"\n📝 Logging to Baserow...")
        ok, result = log_meal_to_baserow(
            description=args.description,
            date=date,
            meal_type=meal_type,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
        )
        if ok:
            print(f"✅ Meal logged! Row ID: {result}")
        else:
            print(f"❌ Failed to log: {result}")
            sys.exit(1)


if __name__ == "__main__":
    main()
