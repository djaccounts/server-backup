import base64, json, os, urllib.request

env = {}
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v

or_key = env.get("OPENROUTER_API_KEY", "")

with open("/tmp/recipe_photo.jpg", "rb") as f:
    image_data = f.read()

b64 = base64.b64encode(image_data).decode()
print(f"Image: {len(image_data)} bytes, sending to Gemini 2.5 Flash...")

payload = json.dumps({
    "model": "google/gemini-2.5-flash",
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
                    "text": "Read this recipe photo carefully. Extract: 1) Recipe name, 2) All ingredients with quantities and units (one per line), 3) All instructions/steps (numbered), 4) Prep time, cook time, serving size if mentioned. Format clearly with INGREDIENTS and INSTRUCTIONS sections."
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
        "Authorization": "Bearer " + or_key,
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"]
        print("\n=== RECIPE EXTRACTED FROM PHOTO ===")
        print(content)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:500]}")
except Exception as e:
    print(f"Error: {e}")
