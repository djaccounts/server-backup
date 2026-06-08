"""
Direct API key test script for Hermes provider stack.
Tests each provider's API key by making a real inference call (not just model listing).

Usage:
  1. Write this file to /tmp/test_keys.py:
     write_file(path="/tmp/test_keys.py", content=<this file>)
  2. Run: python3 /tmp/test_keys.py

Expected keys in /root/.hermes/.env:
  GOOGLE_API_KEY, OPENROUTER_API_KEY, NVIDIA_API_KEY, GROQ_API_KEY,
  AIRTABLE_API_KEY, GITHUB_TOKEN

Each test sends a minimal "Reply with exactly: XXX_OK" prompt and checks the response.
"""

import urllib.request, json, datetime, re

def get_env_key(name):
    with open('/root/.hermes/.env') as f:
        for line in f:
            line = line.strip()
            if line.startswith(name + '='):
                return line.split('=', 1)[1]
    return None

results = []

# ── Google Gemini ──────────────────────────────────────────────────────────
key = get_env_key('GOOGLE_API_KEY')
if key:
    url = f'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions?key={key}'
    body = json.dumps({
        'model': 'gemini-2.0-flash',
        'messages': [{'role': 'user', 'content': 'Reply with exactly: GOOGLE_OK'}],
        'max_tokens': 20
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            reply = data['choices'][0]['message']['content'].strip()
            results.append(f'GOOGLE ✓ → "{reply}"')
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        if 'limit: 0' in err:
            results.append(f'GOOGLE ✗ → 429 quota=0 (billing not enabled on Google Cloud)')
        elif 'quota' in err.lower():
            m = re.search(r'Retry in ([\d.]+)s', err)
            retry = m.group(1)+'s' if m else '?'
            results.append(f'GOOGLE ✗ → 429 quota exceeded (retry in {retry})')
        else:
            results.append(f'GOOGLE ✗ → {e.code}: {err[:100]}')
    except Exception as e:
        results.append(f'GOOGLE ✗ → {e}')

# ── OpenRouter ─────────────────────────────────────────────────────────────
key = get_env_key('OPENROUTER_API_KEY')
if key:
    url = 'https://openrouter.ai/api/v1/chat/completions'
    body = json.dumps({
        'model': 'openrouter/owl-alpha',
        'messages': [{'role': 'user', 'content': 'Reply with exactly: OPENROUTER_OK'}],
        'max_tokens': 20
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            reply = data['choices'][0]['message']['content'].strip()
            results.append(f'OPENROUTER ✓ → "{reply}"')
    except urllib.error.HTTPError as e:
        results.append(f'OPENROUTER ✗ → {e.code}: {e.read().decode()[:100]}')
    except Exception as e:
        results.append(f'OPENROUTER ✗ → {e}')

# ── NVIDIA NIM ─────────────────────────────────────────────────────────────
key = get_env_key('NVIDIA_API_KEY')
if key:
    url = 'https://integrate.api.nvidia.com/v1/chat/completions'
    body = json.dumps({
        'model': 'meta/llama-3.1-70b-instruct',
        'messages': [{'role': 'user', 'content': 'Reply with exactly: NVIDIA_OK'}],
        'max_tokens': 20
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            reply = data['choices'][0]['message']['content'].strip()
            results.append(f'NVIDIA ✓ → "{reply}"')
    except urllib.error.HTTPError as e:
        results.append(f'NVIDIA ✗ → {e.code}: {e.read().decode()[:100]}')
    except Exception as e:
        results.append(f'NVIDIA ✗ → {e}')

# ── Groq ───────────────────────────────────────────────────────────────────
key = get_env_key('GROQ_API_KEY')
if key:
    url = 'https://api.groq.com/openai/v1/chat/completions'
    body = json.dumps({
        'model': 'llama-3.3-70b-versatile',
        'messages': [{'role': 'user', 'content': 'Reply with exactly: GROQ_OK'}],
        'max_tokens': 20
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {key}'
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            reply = data['choices'][0]['message']['content'].strip()
            results.append(f'GROQ ✓ → "{reply}"')
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        if '1010' in err:
            results.append(f'GROQ ✗ → 403 error 1010 (invalid/expired key)')
        else:
            results.append(f'GROQ ✗ → {e.code}: {err[:100]}')
    except Exception as e:
        results.append(f'GROQ ✗ → {e}')

# ── Airtable ───────────────────────────────────────────────────────────────
key = get_env_key('AIRTABLE_API_KEY')
if key:
    url = 'https://api.airtable.com/v0/meta/bases'
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            bases = data.get('bases', [])
            names = [b.get('name', '?') for b in bases]
            results.append(f'AIRTABLE ✓ → {len(bases)} base(s): {names}')
    except urllib.error.HTTPError as e:
        results.append(f'AIRTABLE ✗ → {e.code}: {e.read().decode()[:100]}')
    except Exception as e:
        results.append(f'AIRTABLE ✗ → {e}')

# ── GitHub ─────────────────────────────────────────────────────────────────
key = get_env_key('GITHUB_TOKEN')
if key:
    url = 'https://api.github.com/rate_limit'
    req = urllib.request.Request(url, headers={'Authorization': f'token {key}'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            core = data.get('resources', {}).get('core', {})
            remaining = core.get('remaining', '?')
            limit = core.get('limit', '?')
            reset = core.get('reset', 0)
            reset_time = datetime.datetime.fromtimestamp(reset).strftime('%H:%M:%S') if reset else '?'
            results.append(f'GITHUB ✓ → rate limit: {remaining}/{limit} (resets {reset_time})')
    except urllib.error.HTTPError as e:
        results.append(f'GITHUB ✗ → {e.code}: {e.read().decode()[:100]}')
    except Exception as e:
        results.append(f'GITHUB ✗ → {e}')

# ── Results ────────────────────────────────────────────────────────────────
print('=' * 60)
print('  API KEY TEST RESULTS (direct provider calls)')
print('=' * 60)
for r in results:
    print('  %s' % r)
print('=' * 60)

# ── Local Token Usage ──────────────────────────────────────────────────────
try:
    import sqlite3
    from datetime import datetime, timezone
    conn = sqlite3.connect('/root/.hermes/state.db')
    today = int(datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    agg = conn.execute("""
        SELECT SUM(input_tokens) as ti, SUM(output_tokens) as to2,
               SUM(cache_read_tokens) as tc,
               SUM(COALESCE(actual_cost_usd, estimated_cost_usd)) as cost,
               SUM(message_count) as msgs, COUNT(*) as sessions
        FROM sessions WHERE started_at >= ?
    """, (today,)).fetchone()
    total = (agg['ti'] or 0) + (agg['to2'] or 0)
    print('\n  LOCAL USAGE TODAY: {:,} tokens | cache_r: {:,} | ${:.6f} | {} msgs | {} sessions'.format(
        total, agg['tc'] or 0, agg['cost'] or 0, agg['msgs'], agg['sessions']))
    conn.close()
except Exception as e:
    print('\n  LOCAL USAGE: could not read (%s)' % e)
print('=' * 60)
