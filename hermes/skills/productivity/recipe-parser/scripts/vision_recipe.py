#!/usr/bin/env python3
"""
vision_recipe.py — Extract recipe text from a photo using vision API fallback chain.

Usage:
    python3 vision_recipe.py <image_path>

Environment:
    Reads API keys from ~/.hermes/.env (NVIDIA_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, GOOGLE_API_KEY)
    Tries providers in priority order; uses the first one that succeeds.

Provider priority (tested June 2026):
    1. NVIDIA NIM  — meta/llama-3.2-11b-vision-instruct  (✅ working)
    2. OpenRouter  — google/gemini-2.5-flash             (may need credits)
    3. Groq        — llama-3.2-11b-vision-instruct       (check key validity)
    4. Google AI   — gemini-2.0-flash                    (check key validity)
"""
import base64, json, subprocess, sys, urllib.error, urllib.request


def get_env_key(name):
    """Safely extract an API key from ~/.hermes/.env, handling special chars."""
    result = subprocess.run(
        ["bash", "-c", f"grep {name} /root/.hermes/.env | head -1 | sed 's/.*=//'"],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def call_openai_style(base_url, model, api_key, img_b64, prompt, timeout=120):
    """Call an OpenAI-compatible vision endpoint."""
    payload = json.dumps({
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                {"type": "text", "text": prompt}
            ]
        }],
        "max_tokens": 2048
    }).encode("utf-8")

    req = urllib.request.Request(
        base_url,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]


def call_google_gemini(api_key, img_b64, prompt, timeout=120):
    """Call Google AI Studio Gemini endpoint."""
    payload = json.dumps({
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
            ]
        }]
    }).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["candidates"][0]["content"]["parts"][0]["text"]


PROMPT = (
    "Read this recipe photo carefully. Extract: 1) Recipe name, 2) All ingredients "
    "with quantities and units (one per line), 3) All instructions/steps (numbered), "
    "4) Prep time, cook time, serving size if mentioned. Format clearly with "
    "INGREDIENTS and INSTRUCTIONS sections."
)

# Provider configs: (name, base_url_or_None, model, key_name, call_fn)
# None base_url means use Google Gemini format
PROVIDERS = [
    ("NVIDIA NIM",  "https://integrate.api.nvidia.com/v1/chat/completions",       "meta/llama-3.2-11b-vision-instruct", "NVIDIA_API_KEY",  None),
    ("OpenRouter",  "https://openrouter.ai/api/v1/chat/completions",              "google/gemini-2.5-flash",             "OPENROUTER_API_KEY", None),
    ("Groq",        "https://api.groq.com/openai/v1/chat/completions",            "llama-3.2-11b-vision-instruct",       "GROQ_API_KEY",    None),
    ("Google AI",   None,                                                         "gemini-2.0-flash",                    "GOOGLE_API_KEY",  "google"),
]


def extract_recipe_from_image(image_path):
    """Try each vision provider in order; return extracted recipe text."""
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    errors = []
    for name, base_url, model, key_name, special in PROVIDERS:
        api_key = get_env_key(key_name)
        if not api_key:
            errors.append(f"{name}: {key_name} not found in .env")
            continue
        try:
            if special == "google":
                text = call_google_gemini(api_key, img_b64, PROMPT)
            else:
                text = call_openai_style(base_url, model, api_key, img_b64, PROMPT)
            print(f"[vision_recipe] Used provider: {name}", file=sys.stderr)
            return text
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:200]
            errors.append(f"{name}: HTTP {e.code} — {body}")
        except Exception as e:
            errors.append(f"{name}: {e}")

    # All providers failed
    print("ERROR: All vision providers failed:", file=sys.stderr)
    for err in errors:
        print(f"  — {err}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    print(extract_recipe_from_image(sys.argv[1]))
