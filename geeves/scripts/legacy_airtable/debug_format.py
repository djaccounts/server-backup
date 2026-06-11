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

req2 = urllib.request.Request(
    "http://localhost:9925/api/recipes/the-best-spaghetti-bolognese-recipe",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(req2) as resp:
    r = json.loads(resp.read())

# Show the first 3 ingredients in full to understand the format
for i, ing in enumerate(r.get("recipeIngredient", [])[:3]):
    print(f"[{i}] {json.dumps(ing, indent=2)}")
    print()
