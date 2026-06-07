import json, os, urllib.request

env_path = os.path.expanduser("~/.hermes/.env")
or_key = None
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("OPENROUTER_API_KEY=***            or_key = line.split("=", 1)[1]
            break

# List available vision models
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": "Bearer " + or_key},
)
with urllib.request.urlopen(req) as resp:
    models = json.loads(resp.read())

# Filter for vision models
vision_models = []
for m in models.get("data", []):
    if "vision" in m.get("id", "").lower() or "gemini" in m.get("id", "").lower():
        vision_models.append(m["id"])

print("Vision-capable models on OpenRouter:")
for v in sorted(vision_models)[:20]:
    print(f"  {v}")
