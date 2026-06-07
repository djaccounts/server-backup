import json, os, urllib.request, subprocess

# Read all env vars at once
env = {}
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v

or_key = env.get("OPENROUTER_API_KEY", "")
print(f"Key: {or_key[:10]}...")

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": "Bearer " + or_key},
)
with urllib.request.urlopen(req) as resp:
    models = json.loads(resp.read())

vision_models = []
for m in models.get("data", []):
    mid = m.get("id", "")
    if "vision" in mid.lower() or "gemini" in mid.lower() or "gpt-4" in mid.lower():
        vision_models.append(mid)

print("Vision-capable models:")
for v in sorted(vision_models)[:20]:
    print(f"  {v}")
