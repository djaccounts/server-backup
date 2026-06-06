#!/usr/bin/env python3
"""
starwars_fetch.py — Fetch a random Star Wars character fact from SWAPI.

Usage:
    python3 starwars_fetch.py         # fetch and print
    python3 starwars_fetch.py --write # fetch and write to Airtable Star_Wars_Fact table
"""

import json, urllib.request, random, sys
from datetime import datetime, timezone
import subprocess

ENV_PATH = "/root/.hermes/.env"
BASE = "appzvmonQXs4x2AlL"
TABLE = "Star_Wars_Fact"

def get_key():
    r = subprocess.run(["grep", "AIRTABLE_API_KEY", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def swapi_get(path):
    url = f"https://www.swapi.tech/api/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Geeves/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

def fetch_character(char_id):
    """Fetch a character and build a fun fact string."""
    data = swapi_get(f"people/{char_id}/")
    char = data["result"]["properties"]
    name = char["name"]
    height = char["height"]
    mass = char["mass"]
    hair = char["hair_color"]
    eyes = char["eye_color"]
    gender = char["gender"]
    birth = char["birth_year"]
    skin = char["skin_color"]

    # Get homeworld
    homeworld = "Unknown"
    try:
        hw_data = swapi_get(char["homeworld"].split("/")[-2] + "/" + char["homeworld"].split("/")[-1] + "/")
        homeworld = hw_data["result"]["properties"]["name"]
    except Exception:
        pass

    # Get films count
    films = char.get("films", [])
    film_count = len(films)

    # Build a varied fact
    facts = [
        f"{name} is a {gender} from {homeworld}, born {birth}. Height: {height}cm, mass: {mass}kg. Appears in {film_count} film(s).",
        f"Star Wars character {name} hails from {homeworld}. {name} has {hair} hair, {eyes} eyes, and {skin} skin. Born {birth}.",
        f"Did you know? {name} appears in {film_count} Star Wars film(s). This {gender} character from {homeworld} stands {height}cm tall.",
        f"{name} — a {height}cm tall, {mass}kg {gender} from {homeworld}. {name} has {eyes} eyes and was born {birth}.",
    ]
    fact = random.choice(facts)

    return {
        "Name": name,
        "Height": height,
        "Mass": mass,
        "Hair Color": hair,
        "Eye Color": eyes,
        "Gender": gender,
        "Birth Year": birth,
        "Homeworld": homeworld,
        "Films Count": film_count,
        "Fact": fact,
        "Source URL": "https://www.swapi.tech",
    }

def write_to_airtable(record):
    key = get_key()
    url = f"https://api.airtable.com/v0/{BASE}/{TABLE}"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    payload = json.dumps({
        "records": [{
            "fields": {
                "Date": today,
                **record
            }
        }]
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    return result["records"][0]["id"]

def main():
    write_mode = "--write" in sys.argv

    # Get a random character (1-83, some IDs are missing so retry if needed)
    char_id = random.randint(1, 83)
    try:
        record = fetch_character(char_id)
    except Exception as e:
        # Try another ID
        char_id = random.randint(1, 83)
        record = fetch_character(char_id)

    print(f"⚔️  Star Wars Fact")
    print(f"    Character: {record['Name']}")
    print(f"    From: {record['Homeworld']}")
    print(f"    Fact: {record['Fact']}")

    if write_mode:
        rec_id = write_to_airtable(record)
        print(f"    ✅ Written to Airtable ({rec_id})")
    else:
        print(f"    (dry run — add --write to save)")

if __name__ == "__main__":
    main()
