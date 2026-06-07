#!/usr/bin/env python3
"""
Extract recipe text from a photo using NVIDIA NIM vision API.

Usage: python3 vision_extract.py <image_path>

Requires: NVIDIA_API_KEY in ~/.hermes/.env
API: https://integrate.api.nvidia.com/v1/chat/completions
Model: meta/llama-3.2-11b-vision-instruct
"""
import base64, json, subprocess, sys, urllib.request, urllib.error

def get_env_key(key_name):
    result = subprocess.run(
        ["bash", "-c", f"grep {key_name} ~/.hermes/.env | head -1 | sed 's/.*=//'"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def extract_recipe_from_image(image_path):
    api_key = get_env_key("NVIDIA_API_KEY")
    if not api_key:
        print("ERROR: NVIDIA_API_KEY not found in ~/.hermes/.env", file=sys.stderr)
        sys.exit(1)

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    print(f"Image: {image_path} ({len(img_b64)} base64 chars)", file=sys.stderr)

    payload = json.dumps({
        "model": "meta/llama-3.2-11b-vision-instruct",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                {"type": "text", "text": "What recipe is shown in this image? Extract the full recipe including title, all ingredients with quantities, and all step-by-step instructions. Also note prep time, cook time, temperature, and yield if visible."}
            ]
        }],
        "max_tokens": 2048
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            else:
                print(f"ERROR: No choices in response: {json.dumps(result)[:500]}", file=sys.stderr)
                sys.exit(1)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body[:500]}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <image_path>", file=sys.stderr)
        sys.exit(1)
    print(extract_recipe_from_image(sys.argv[1]))
