import json, urllib.request

data = "username=changeme@example.com&password=MyPassword123".encode()
req = urllib.request.Request(
    "http://localhost:9925/api/auth/token",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read())["access_token"]

# Delete duplicate Mealie recipes, keep only the best ones
# Keep: the-best-spaghetti-bolognese-recipe, blueberry-lemon-bread-2
# Delete: blueberry-lemon-bread (stub), blueberry-lemon-bread-1 (earlier test)
to_delete = ["blueberry-lemon-bread", "blueberry-lemon-bread-1"]

for slug in to_delete:
    req_del = urllib.request.Request(
        f"http://localhost:9925/api/recipes/{slug}",
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req_del) as resp:
            print(f"  🗑️  Deleted Mealie: {slug}")
    except Exception as e:
        print(f"  ❌ Failed to delete {slug}: {e}")

# List remaining
req2 = urllib.request.Request(
    "http://localhost:9925/api/recipes?page=1&perPage=20&orderDirection=desc",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(req2) as resp:
    data = json.loads(resp.read())
    print(f"\nRemaining Mealie recipes ({len(data.get('items',[]))}):")
    for r in data.get("items", []):
        if "blueberry" in r.get("slug","") or "bolognese" in r.get("slug",""):
            ings = len(r.get("recipeIngredient", []))
            print(f"  {r['slug']:45s} ({ings} ingredients)")
