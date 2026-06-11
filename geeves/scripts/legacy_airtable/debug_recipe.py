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
    "http://localhost:9925/api/recipes/blueberry-lemon-loaf-1",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(req2) as resp:
    recipe = json.loads(resp.read())

print("=== INGREDIENTS RAW ===")
for i, ing in enumerate(recipe.get("recipeIngredient", [])):
    print(f"  [{i}] {json.dumps(ing)}")

print()
print("=== INSTRUCTIONS RAW ===")
for i, inst in enumerate(recipe.get("recipeInstructions", [])):
    print(f"  [{i}] title={inst.get('title','')} text={inst.get('text','')[:60]}")
