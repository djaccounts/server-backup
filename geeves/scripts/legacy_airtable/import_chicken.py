import json, urllib.request, urllib.error

data = "username=changeme@example.com&password=MyPassword123".encode()
req = urllib.request.Request(
    "http://localhost:9925/api/auth/token",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read())["access_token"]

# Try jamieoliver.com — excellent structured data
url = "https://www.jamieoliver.com/recipes/chicken-recipes/the-best-chicken-tikka-masala/"
recipe_data = json.dumps({"url": url}).encode()
req2 = urllib.request.Request(
    "http://localhost:9925/api/recipes/create/url",
    data=recipe_data,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(req2) as resp:
        result = resp.read().decode().strip().strip('"')
        print(f"Recipe slug: {result}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body}")
