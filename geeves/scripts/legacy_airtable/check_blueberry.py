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
    "http://localhost:9925/api/recipes/blueberry-lemon-bread",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(req2) as resp:
    r = json.loads(resp.read())

print(f"Name: {r.get('name')}")
print(f"Slug: {r.get('slug')}")
print(f"orgURL: {r.get('orgURL')}")
print(f"Description: {r.get('description', '')[:100]}")
print()
print("Ingredients:")
for i, ing in enumerate(r.get("recipeIngredient", [])):
    print(f"  [{i}] qty={ing.get('quantity')} unit={ing.get('unit')} food={ing.get('food')} note={ing.get('note','')[:40]} display={ing.get('display','')[:50]}")
