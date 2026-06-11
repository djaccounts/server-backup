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

# List recent recipes to find what was actually created
req2 = urllib.request.Request(
    "http://localhost:9925/api/recipes?page=1&perPage=10&orderDirection=desc",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(req2) as resp:
    data = json.loads(resp.read())
    for r in data.get("items", []):
        print(f"  {r['name']:50s} | {r['slug']:40s} | {r.get('orgURL','')}")
