---
name: vision-food-analysis
description: "Analyze food photos using OpenRouter vision API (Claude Sonnet 4 or Gemini). Use when the user uploads a food photo and the vision_analyze Hermes tool is NOT available, or when you need a reliable fallback for food identification from images."
version: 1.0.0
author: Geeves
---

# Vision Food Analysis

When `vision_analyze` Hermes tool is unavailable, use this script-based approach to analyze food photos through OpenRouter's API.

## Prerequisites

- `OPENROUTER_API_KEY` in `~/.hermes/.env`
- Python 3 with `urllib`, `base64`, `json` (all stdlib — no pip installs needed)
- Image file accessible at a local path

## Quick Analysis (copy-paste ready)

```python
import os, subprocess, base64, json, urllib.request, urllib.error

# 1. Get API key
r = subprocess.run(['grep', 'OPENROUTER_API_KEY', os.path.expanduser('~/.hermes/.env')], capture_output=True, text=True)
or_key = r.stdout.strip().split('\n')[0].split('=', 1)[1]

# 2. Encode image (replace path)
with open('/tmp/food_photo.jpg', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

# 3. Call OpenRouter vision API
data = json.dumps({
    'model': 'anthropic/claude-sonnet-4',
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': 'Identify all food and drink items in this photo. For each item, estimate the portion size and provide approximate calories, protein (g), carbs (g), and fat (g) per serving. Return as a structured list with totals.'},
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}}
        ]
    }],
    'max_tokens': 1000
}).encode()

headers = {'Authorization': f'Bearer {or_key}', 'Content-Type': 'application/json'}
req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=data, headers=headers)

with urllib.request.urlopen(req, timeout=120) as resp:
    result = json.loads(resp.read().decode())
    print(result['choices'][0]['message']['content'])
```

## Full Pipeline (photo → Baserow)

Use `/root/Geeves/scripts/meal_photo_pipeline.py`:

```bash
# Step 1: Download photo from Slack (if URL)
python3 /root/Geeves/scripts/meal_photo_pipeline.py "<image_url>" --output /tmp/food_photo.jpg

# Step 2: Analyze with vision (run the Python snippet above)

# Step 3: Log to Baserow
python3 /root/Geeves/scripts/baserow_api.py create-row Meals \
  '{"Description": "<food from analysis>", "Date": "<YYYY-MM-DD>", "Meal type": "<type>", "Calories (est)": <int>, "Protein (g)": <int>, "Carbs (g)": <int>, "Fat (g)": <int>, "Accuracy": "Estimated", "Source": "Photo"}'
```

## Image Location

When Slack sends a photo, it's cached at:
```
/root/.hermes/image_cache/img_<hash>.jpeg
```

The exact filename changes per message. Use the path provided in the user's message or list the cache:
```bash
ls -lt /root/.hermes/image_cache/ | head -5
```

## Model Options

| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| `anthropic/claude-sonnet-4` | Medium | ⭐⭐⭐⭐⭐ | Medium |
| `google/gemini-2.5-flash` | Fast | ⭐⭐⭐⭐ | Low |
| `google/gemini-3.5-flash` | Fast | ⭐⭐⭐⭐⭐ | Low |

**Default: `anthropic/claude-sonnet-4`** — best food recognition accuracy.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `vision_analyze` tool not in tool list | Use this script approach instead — it always works |
| HTTP 400 from OpenRouter | Wrong model name — check available models at openrouter.ai/models |
| HTTP 403 from Groq | Key doesn't have vision access — use OpenRouter |
| Image too large (>5MB) | Resize first: `python3 -c "from PIL import Image; img=Image.open('/tmp/big.jpg'); img.thumbnail((1920,1920)); img.save('/tmp/small.jpg', quality=85)"` |
| Baserow 400 `max_decimal_places` | All macro fields must be integers — use `int(round(value))` |
| Photo shows no food (e.g., cycling selfie) | Ask user to confirm what they ate — don't guess |

## Notes

- Always tell the user what you identified and ask for confirmation
- Be transparent: "From your photo, I estimate..."
- If the photo is unclear, ask the user to describe the meal
- Date format for Baserow: `YYYY-MM-DD`
- Meal type inference: before 11am → Breakfast, 11am-2pm → Lunch, 5pm+ → Dinner, else → Snack
