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

# Try with loadFood parameter
req2 = urllib.request.Request(
    "http://localhost:9925/api/recipes/blueberry-lemon-loaf-1?loadFood=true",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(req2) as resp:
    recipe = json.loads(resp.read())

print("=== INGREDIENTS (loadFood=true) ===")
for i, ing in enumerate(recipe.get("recipeIngredient", [])):
    print(f"  [{i}] {json.dumps(ing)}")

print()
print("=== TOP-LEVEL FIELDS ===")
for k in ["name", "description", "prepTime", "cookTime", "recipeYield", "orgURL", "recipeCategory", "tags"]:
    print(f"  {k}: {recipe.get(k)}")
