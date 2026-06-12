#!/usr/bin/env python3
"""
word_of_the_day_fetch.py — Fetch a daily word with EN/RU/HE translations.

Sources:
  - Free Dictionary API (dictionaryapi.dev) — English definition, pronunciation, part of speech, example
  - MyMemory Translation API (mymemory.translated.net) — Russian and Hebrew translations

Word selection: Uses a curated list of interesting English words, rotated by day-of-year.
All free, no API keys required.

Usage:
    python3 word_of_the_day_fetch.py              # fetch and print
    python3 word_of_the_day_fetch.py --write      # fetch and write to Baserow
    python3 word_of_the_day_fetch.py --word serendipity  # force a specific word
"""

import subprocess, sys, json, urllib.request, urllib.error
from datetime import datetime, timezone

sys.path.insert(0, "/root/Geeves/scripts")
import baserow_api

TABLE = "Word_of_the_Day"

# Curated word list — interesting, useful words across difficulties
WORD_LIST = [
    # Easy / Common
    "serendipity", "ephemeral", "ubiquitous", "eloquent", "resilient",
    "nostalgia", "paradox", "catalyst", "dichotomy", "empathy",
    # Intermediate
    "quintessential", "juxtaposition", "mellifluous", "labyrinth", "surreptitious",
    "perspicacious", "ineffable", "sonder", "petrichor", "limerence",
    "defenestration", "gobbledygook", "sesquipedalian", "onomatopoeia", "oxymoron",
    # Advanced
    "perspicuous", "pulchritude", "sagacious", "vicissitude", "zeitgeist",
    "schadenfreude", "wanderlust", "hiraeth", "komorebi", "mamihlapinatapai",
    "tartle", "kenopsia", "ellipsism", "liberosis", "altschmerz",
    "occhiolism", "nodus tollens", "anagnorisis", "catharsis", "hubris",
    "nemesis", "metanoia", "phronesis", "arete", "eudaimonia",
    "ataraxia", "aporia", "kairos", "anchínoia", "deipnosophist",
]


def fetch_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "GeevesBot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def fetch_english(word):
    """Fetch English definition, pronunciation, part of speech, example from Free Dictionary API."""
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    data = fetch_json(url)

    if not isinstance(data, list) or len(data) == 0:
        raise Exception(f"No dictionary entry for '{word}'")

    entry = data[0]
    result = {
        "word": entry.get("word", word),
        "pronunciation": "",
        "part_of_speech": "",
        "definition": "",
        "example": "",
        "source_url": f"https://dictionaryapi.dev/",
    }

    # Get pronunciation (prefer text, fallback to first phonetic with audio)
    phonetics = entry.get("phonetics", [])
    for p in phonetics:
        if p.get("text"):
            result["pronunciation"] = p["text"]
            break
    if not result["pronunciation"]:
        for p in phonetics:
            if p.get("audio"):
                result["pronunciation"] = p.get("text", "")
                break

    # Get first meaning with definition and example
    meanings = entry.get("meanings", [])
    for m in meanings:
        pos = m.get("partOfSpeech", "")
        defs = m.get("definitions", [])
        if defs:
            result["part_of_speech"] = pos
            result["definition"] = defs[0].get("definition", "")
            if defs[0].get("example"):
                result["example"] = defs[0]["example"]
            break

    return result


def translate_mymemory(word, target_lang):
    """Translate a word using MyMemory free API."""
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(word)}&langpair=en|{target_lang}"
    data = fetch_json(url)

    response = data.get("responseData", {})
    translated = response.get("translatedText", "")

    if not translated or translated.lower() == word.lower():
        # Try with a short phrase for better context
        url2 = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote('the word ' + word)}&langpair=en|{target_lang}"
        data2 = fetch_json(url2)
        response2 = data2.get("responseData", {})
        translated2 = response2.get("translatedText", "")
        if translated2:
            # Extract just the translated word (rough heuristic)
            translated = translated2.replace("слово ", "").replace("המילה ", "").strip()

    return translated


def fetch_translation(word, lang_code, lang_name):
    """Fetch translation and example sentence for a word in target language."""
    import urllib.parse

    # Translate the word itself
    translated_word = translate_mymemory(word, lang_code)

    # Translate an example sentence for context
    en_example = f"The word '{word}' is very useful."
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(en_example)}&langpair=en|{lang_code}"
    try:
        data = fetch_json(url)
        translated_example = data.get("responseData", {}).get("translatedText", "")
    except Exception:
        translated_example = ""

    # Get definition in target language (translate the English definition)
    return {
        "word": translated_word,
        "example": translated_example,
    }


def fetch_word_of_the_day(word=None):
    """Fetch complete word of the day data: EN + RU + HE."""
    today = datetime.now(timezone.utc)

    # Select word
    if not word:
        day_of_year = today.timetuple().tm_yday
        word = WORD_LIST[day_of_year % len(WORD_LIST)]

    print(f"  Word: {word}")

    # Fetch English data
    print("  Fetching English definition...")
    en_data = fetch_english(word)
    print(f"    Pronunciation: {en_data['pronunciation']}")
    print(f"    Part of speech: {en_data['part_of_speech']}")
    print(f"    Definition: {en_data['definition'][:80]}...")

    # Fetch Russian translation
    print("  Fetching Russian translation...")
    ru_data = fetch_translation(word, "ru", "Russian")
    print(f"    Russian: {ru_data['word']}")

    # Fetch Hebrew translation
    print("  Fetching Hebrew translation...")
    he_data = fetch_translation(word, "he", "Hebrew")
    print(f"    Hebrew: {he_data['word']}")

    # Build record for Baserow
    record = {
        "Date": today.strftime("%Y-%m-%d"),
        "Word": en_data["word"],
        "Pronunciation": en_data["pronunciation"],
        "Part of Speech": en_data["part_of_speech"],
        "Definition EN": en_data["definition"],
        "Example EN": en_data["example"],
        "Russian": ru_data["word"],
        "Russian Definition": f"Перевод слова '{en_data['word']}'",
        "Russian Example": ru_data["example"],
        "Hebrew": he_data["word"],
        "Hebrew Definition": f"תרגום המילה '{en_data['word']}'",
        "Hebrew Example": he_data["example"],
        "Source URL": en_data["source_url"],
    }

    return record


def write_to_baserow(record):
    """Write word of the day record to Baserow."""
    mapping = baserow_api.load_mapping()
    ok, row_id = baserow_api.baserow_post(mapping, TABLE, record)
    if ok:
        print(f"  ✅ Written to Baserow (record {row_id})")
    else:
        print(f"  ❌ Baserow error: {row_id}")
    return ok


def main():
    write_mode = "--write" in sys.argv
    word = None
    if "--word" in sys.argv:
        idx = sys.argv.index("--word")
        if idx + 1 < len(sys.argv):
            word = sys.argv[idx + 1]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"📖 Word of the Day — {today}")

    try:
        record = fetch_word_of_the_day(word)
    except Exception as e:
        print(f"  ❌ Fetch failed: {e}")
        sys.exit(1)

    print(f"\n  Summary:")
    print(f"    EN: {record['Word']} ({record['Part of Speech']}) — {record['Definition EN'][:60]}...")
    print(f"    RU: {record['Russian']}")
    print(f"    HE: {record['Hebrew']}")

    if write_mode:
        write_to_baserow(record)
    else:
        print("\n  (dry run — add --write to save to Baserow)")


if __name__ == "__main__":
    main()
