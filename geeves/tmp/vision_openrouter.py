import base64, json, os, urllib.request, urllib.error

# Get OpenRouter API key
env_path = os.path.expanduser("~/.hermes/.env")
or_key = None
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("OPENROUTER_API_KEY=***            or_key = line.split("=", 1)[1]
            break

print(f"Key: {or_key[:10]}...")

# Read and encode image
with open("/tmp/recipe_photo.jpg", "rb") as f:
    image_data = f.read()

b64 = base64.b64encode(image_data).decode()

# Try OpenRouter with a vision model
payload = json.dumps({
    "model": "google/gemini-2.0-flash-vision",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}"
                    }
                },
                {
                    "type": "text",
                    "text": "Read this recipe photo carefully. Extract: 1) Recipe name, 2) All ingredients with quantities and units, 3) All instructions/steps, 4) Prep time, cook time, serving size if mentioned. Format clearly with sections."
                }
            ]
        }
    ],
    "max_tokens": 2000,
}).encode()

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=payload,
    headers={
        "Authorization": f"Bearer {or_key}",
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"]
        print("\n=== RECIPE EXTRACTED ===")
        print(content)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:500]}")
except Exception as e:
    print(f"Error: {e}")
