# Word of the Day — Pitfalls & Fixes

## Script: `/root/Geeves/scripts/word_of_the_day_fetch.py`

### ASCII Encoding Crash (2026-06-12)

**Symptom:** `UnicodeEncodeError: 'ascii' codec can't encode character '\xed' in position 27: ordinal not in range(128)`

**Cause:** Cron environment has `PYTHONIOENCODING` unset or set to ASCII. When `print()` outputs a word definition containing non-ASCII characters (e.g. "anchínoia" with í), it crashes.

**Fix:** Add at the top of the script (after imports):
```python
import io
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

### Dictionary API 404 for Non-English Words (2026-06-12)

**Symptom:** `HTTP Error 404: Not Found` for words like "anchínoia", "eudaimonia", "deipnosophist", "eunoia"

**Cause:** The Free Dictionary API (dictionaryapi.dev) only has English words. Greek-derived and rare academic words return 404.

**Fix:** Two-part:
1. URL-encode the word: `urllib.parse.quote(word)` in the API URL
2. Catch 404 and fallback to next word in `WORD_LIST`:
```python
try:
    data = fetch_json(url)
except urllib.error.HTTPError as e:
    if e.code == 404:
        raise Exception(f"No dictionary entry for '{word}' (404)")
    raise
```

Then in `main()`, wrap the fetch in a try/except that tries `WORD_LIST[(idx+1) % len(WORD_LIST)]` as fallback.

### Curated Word List Maintenance

When adding words to `WORD_LIST`, verify they exist in the dictionary API:
```bash
python3 -c "import urllib.request, json; r = urllib.request.urlopen('https://api.dictionaryapi.dev/api/v2/entries/en/WORD'); print(json.loads(r.read())[0]['word'])"
```

Words confirmed missing (as of 2026-06-12): `anchínoia`, `eudaimonia`, `deipnosophist`, `eunoia`
