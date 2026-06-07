#!/usr/bin/env python3
"""
List all Mealie recipes, optionally finding duplicates by name similarity.

Usage:
  python3 list_mealie_recipes.py          # List all recipes
  python3 list_mealie_recipes.py --dupes  # Show potential duplicates
  python3 list_mealie_recipes.py --delete-slug <slug>  # Delete a specific recipe
"""
import json, subprocess, sys, urllib.request, urllib.error, urllib.parse
from collections import defaultdict
import re

MEALIE_URL = "http://localhost:9925"
MEALIE_USER = "changeme@example.com"
MEALIE_PASS = "MyPassword123"

def get_token():
    r = subprocess.run(["bash", "-c",
        f'curl -s -X POST {MEALIE_URL}/api/auth/token '
        f'-H "Content-Type: application/x-www-form-urlencoded" '
        f'-d "username={MEALIE_USER}&password={MEALIE_PASS}"'],
        capture_output=True, text=True)
    return json.loads(r.stdout).get("access_token", "")

def api_get(path, token):
    req = urllib.request.Request(
        f"{MEALIE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def api_delete(path, token):
    req = urllib.request.Request(
        f"{MEALIE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status

def list_all(token):
    data = api_get("/api/recipes?perPage=100", token)
    return data.get("items", [])

def delete_recipe(slug, token):
    status = api_delete(f"/api/recipes/{slug}", token)
    return status

def normalise_name(name):
    """Strip parenthetical suffixes like (1), (2) and trailing numbers for grouping."""
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)
    return name.strip().lower()

def main():
    token = get_token()
    if not token:
        print("ERROR: Could not get Mealie token", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "--delete-slug":
        slug = sys.argv[2]
        print(f"Deleting {slug}...")
        status = delete_recipe(slug, token)
        print(f"  Status: {status}")
        return

    recipes = list_all(token)
    print(f"Total: {len(recipes)} recipes\n")

    for r in sorted(recipes, key=lambda x: x.get("name", "").lower()):
        print(f"  {r['slug']:55s}  {r['name']}")

    if len(sys.argv) > 1 and sys.argv[1] == "--dupes":
        print("\n" + "=" * 60)
        print("Potential duplicates (grouped by normalised name):")
        print("=" * 60)
        groups = defaultdict(list)
        for r in recipes:
            key = normalise_name(r.get("name", ""))
            groups[key].append(r)

        dupes_found = False
        for key, group in sorted(groups.items()):
            if len(group) > 1:
                dupes_found = True
                print(f"\n  '{key}':")
                for r in group:
                    print(f"    {r['slug']:50s}  {r['name']}")
        if not dupes_found:
            print("\n  No duplicates found.")

if __name__ == "__main__":
    main()
