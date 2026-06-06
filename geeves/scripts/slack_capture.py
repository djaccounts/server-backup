#!/usr/bin/env python3
"""
slack_capture.py — Geeves Slack → Airtable Capture Loop

Reads Slack messages (from stdin or file), classifies them, and writes
structured data directly to the correct Airtable table. No intermediate
raw-message table — one message produces one useful record.

Usage:
    echo '[{"text":"...","sender":"David","sender_id":"U0B73K4QWP5",...}]' | python3 slack_capture.py --stdin
    python3 slack_capture.py --file /tmp/slack_queue.json
    python3 slack_capture.py --stdin --dry-run
"""
import subprocess, json, sys, os, re, datetime
import urllib.request, urllib.error, urllib.parse

ENV_PATH = os.path.expanduser("~/.hermes/.env")
BASE = "appzvmonQXs4x2AlL"

# Table IDs (from Airtable metadata)
TABLES = {
    "People":           "tbl1WMPtQhWYW7bTI",
    "Todos":            "tblTcdZQ9AIltQDfu",
    "Memory_Summaries": "tblXH4eCLwM8S30cn",
    "Output_Log":       "tbldJT41dAAX1WTkC",
    # Recipe module tables (IDs filled in after table_builder.py --recipe)
    "Recipes":          "tblehBgzRMa2Xucjd",
    "Ingredients":      "tblNsgbYHNK8xWnB7",
    "Dinner_Parties":   "tblwbQrIu3nUWDz3G",
    "Dinner_Planner":   "tblnts17CCckLJoUQ",
    "Shopping_List":    "tbldvpIO91xi72a0K",
    "Recipe_Context":   "tblJRsw77kbCFyoz9",
    "Recipe_Output_Log":"tblYaJTAZDZzBkcwH",
    "Dining_Preferences":"tblzzGIF7yPf37NG5",
}


# ── Airtable helpers ────────────────────────────────────────────────────────────

def get_key():
    r = subprocess.run(["grep", "AIRTABLE_API_KEY", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def api(method, path, data=None):
    key = get_key()
    if not key:
        print("ERROR: AIRTABLE_API_KEY not found", file=sys.stderr)
        sys.exit(1)
    url = f"https://api.airtable.com/v0/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code


def q(s):
    return urllib.parse.quote(s, safe="")


def airtable_post(table, fields):
    _, status = api("POST", f"{BASE}/{q(table)}", {"fields": fields})
    return status == 200


def airtable_patch(table, record_id, fields):
    _, status = api("PATCH", f"{BASE}/{q(table)}/{record_id}", {"fields": fields})
    return status == 200


def find_person(name):
    formula = f"{{Name}}='{name}'"
    r, status = api("GET", f"{BASE}/People?filterByFormula={q(formula)}&maxRecords=5")
    if status == 200:
        records = r.get("records", [])
        return records[0] if records else None
    return None


# ── Classification ──────────────────────────────────────────────────────────────

CATEGORY_RULES = [
    ("Todo", [
        r"\btodo\b", r"\btask\b", r"\bremind\b", r"\bdon't forget\b",
        r"\bneed to\b", r"\bshould\b", r"\bhave to\b", r"\bmust\b",
        r"\baction\b", r"\bfollow up\b", r"\bfollow-up\b",
    ]),
    ("Person Note", [
        r"\bmet\b", r"\bperson\b", r"\bfriend\b", r"\bcontact\b",
        r"\bknows?\b", r"\brelationship\b", r"\bdietary\b", r"\ballerg",
        r"\bbirthday\b", r"\binterests?\b", r"\bhobbies\b",
        r"\bgift\b", r"\bsocial\b", r"\bvenue\b",
    ]),
    ("Memory", [
        r"\bremember\b", r"\bnote\b", r"\blog\b", r"\bhistory\b",
        r"\blast time\b", r"\bpreviously\b", r"\bbefore\b",
    ]),
    ("Recipe", [
        r"\brecipe\b", r"\bcook\b", r"\bcooking\b", r"\bbake\b", r"\bbaking\b",
        r"\bingredient\b", r"\bmeal\b", r"\bdinner\b", r"\blunch\b", r"\bbreakfast\b",
        r"\bsnack\b", r"\bdessert\b", r"\bside dish\b",
        r"\bwhat('s|\s+is)\s+for\s+dinner\b", r"\bwhat\s+should\s+i\s+cook\b",
        r"\badd\s+(this\s+)?recipe\b", r"\bemail\s+(me\s+)?(the\s+)?recipe\b",
        r"\bPDF\s+(the\s+)?recipe\b", r"\bshopping\s+list\b",
        r"\bdinner\s+party\b", r"\bplan\s+(a\s+)?dinner\b",
        r"\bfavourite\s+recipe\b", r"\brecipe\s+request\b",
        r"\bmealie\b",
        # Pasting raw recipe text patterns
        r"\bINGREDIENTS\b", r"\bINSTRUCTIONS\b", r"\bPREP\s*TIME\b",
        r"\bcups?\s+(of\s+)?(flour|sugar|butter|milk|oil)\b",
        r"\btablespoons?\s+(of\s+)?\w+", r"\bteaspoons?\s+(of\s+)?\w+",
    ]),
    ("Module Request", [
        r"\bmovie\b", r"\bfilm\b", r"\bwatch\b",
        r"\bparty\b", r"\btravel\b",
        r"\bholiday\b", r"\bproperty\b", r"\bhouse\b",
        r"\brecommend\b", r"\bsuggest\b",
    ]),
    ("Film Club", [
        r"\bfilm club\b", r"\bmovie club\b", r"\bmovie night\b",
        r"\bfilm night\b", r"\bjust watched\b", r"\bfinished watching\b",
        r"\brat(e|ing|ed) (the )?(movie|film)\b",
        r"\bscored (the )?(movie|film)\b", r"\badd to (the )?list\b",
        r"\blog (the )?(movie|film)\b",
    ]),
]


def classify_message(text):
    text_lower = text.lower()
    scores = {}
    for category, patterns in CATEGORY_RULES:
        score = sum(1 for p in patterns if re.search(p, text_lower))
        if score > 0:
            scores[category] = score
    if not scores:
        return "General"
    return max(scores, key=scores.get)


# ── Extraction helpers ──────────────────────────────────────────────────────────

def extract_name(text):
    """Try to extract a person's name from a message."""
    normalized = re.sub(r"\b(she|he|they|we|I)'s\b", r"\1 is", text, flags=re.IGNORECASE)
    normalized = re.sub(r"\b(she|he|they|we|I)'ve\b", r"\1 have", normalized, flags=re.IGNORECASE)

    skip = {"the", "this", "that", "what", "how", "when", "where", "who", "why",
            "but", "and", "for", "with", "from", "just", "like", "have", "been",
            "will", "should", "could", "would", "can", "don", "not", "now", "today",
            "tomorrow", "yesterday", "next", "last", "here", "there", "then", "than",
            "also", "very", "really", "quite", "pretty", "much", "many", "some", "any",
            "all", "every", "each", "both", "neither", "either",
            "she", "her", "he", "him", "his", "they", "them", "their",
            "we", "our", "us", "you", "your", "it", "its",
            "i", "me", "my", "mine", "dave", "david", "geeves"}

    patterns = [
        (r"\bmet\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", 1),
        (r"\b(about|add)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", 2),
        (r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'s\s+(birthday|dietary|allerg)", 1),
        (r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:is|loves|hates|likes|enjoys|wants|needs|has|had|can|will|would|could|should)\b", 1),
        (r"\b([A-Z][a-z]+)\s+(birthday|anniversary|party|wedding)\b", 1),
        (r"\b(new person[:]\s*|know\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", 2),
    ]

    for pat, group in patterns:
        m = re.search(pat, normalized, re.IGNORECASE)
        if m:
            name = m.group(group).strip()
            if name and name[0].isupper() and name.lower() not in skip and len(name) > 1:
                # If multi-word and second word is lowercase, take first word only
                words = name.split()
                if len(words) > 1 and words[1][0].islower():
                    name = words[0]
                if name.lower() not in skip:
                    return name
    return None


def extract_todo_task(text):
    text = re.sub(r"^(todo|task|remind me|don't forget|follow up)\s*[:\-]?\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def extract_date(text):
    today = datetime.date.today()
    text_lower = text.lower()
    if "today" in text_lower:
        return today.isoformat()
    if "tomorrow" in text_lower:
        return (today + datetime.timedelta(days=1)).isoformat()
    m = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})", text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), m.group(3)
        if len(y) == 2:
            y = "20" + y
        return f"{y}-{mo:02d}-{d:02d}"
    return None


# ── Category handlers ───────────────────────────────────────────────────────────

def handle_person_note(msg, dry_run=False):
    text = msg.get("text", "")
    name = extract_name(text)
    ts = msg.get("ts", "")

    if name:
        existing = find_person(name)
        if existing:
            current_log = existing["fields"].get("Conversation Log", "")
            new_entry = f"\n[{ts}] {text}"
            if dry_run:
                print(f"  [DRY RUN] Would append to {name}'s conversation log")
                return True
            ok = airtable_patch("People", existing["id"], {"Conversation Log": current_log + new_entry})
            if ok:
                print(f"  ✅ Updated {name}'s conversation log")
            return ok
        else:
            if dry_run:
                print(f"  [DRY RUN] Would create new person: {name}")
                return True
            ok = airtable_post("People", {
                "Name": name,
                "Tier": "Tier 4 (other)",
                "Conversation Log": f"[{ts}] {text}",
            })
            if ok:
                print(f"  ✅ Created new person: {name}")
            return ok
    else:
        # No name found — store as memory note
        print(f"  ℹ️  No name extracted — storing as memory note")
        if dry_run:
            return True
        return airtable_post("Memory_Summaries", {
            "Period": "Ad-hoc",
            "Summary": text,
            "Source Entries": f"[{ts}] {text}",
            "Created": datetime.date.today().isoformat(),
        })


def handle_todo(msg, dry_run=False):
    text = msg.get("text", "")
    task = extract_todo_task(text)
    due_date = extract_date(text)
    fields = {"Task": task, "Status": "Todo", "Priority": "Medium", "Module": "General"}
    if due_date:
        fields["Due Date"] = due_date
    if dry_run:
        print(f"  [DRY RUN] Would create todo: {json.dumps(fields)}")
        return True
    ok = airtable_post("Todos", fields)
    if ok:
        print(f"  ✅ Created todo: {task[:60]}")
    return ok


def handle_memory(msg, dry_run=False):
    text = msg.get("text", "")
    ts = msg.get("ts", "")
    if dry_run:
        print(f"  [DRY RUN] Would store memory note")
        return True
    return airtable_post("Memory_Summaries", {
        "Period": "Ad-hoc",
        "Summary": text,
        "Source Entries": f"[{ts}] {text}",
        "Created": datetime.date.today().isoformat(),
    })


def handle_module_request(msg, dry_run=False):
    text = msg.get("text", "")
    if dry_run:
        print(f"  [DRY RUN] Would log module request to Output_Log")
        return True
    return airtable_post("Output_Log", {
        "Item": text[:100],
        "Module": "General",
        "Generated At": datetime.date.today().isoformat(),
        "Content": text,
    })


def handle_recipe(msg, dry_run=False):
    """Handle recipe-related messages — log to Output_Log for Hermes to process."""
    text = msg.get("text", "")
    if dry_run:
        print(f"  [DRY RUN] Would log recipe request to Output_Log (Module=Recipe)")
        return True
    return airtable_post("Output_Log", {
        "Item": text[:100],
        "Module": "Recipe",
        "Generated At": datetime.date.today().isoformat(),
        "Content": text,
    })


# ── Film Club helpers ────────────────────────────────────────────────────────────

def get_omdb_key():
    r = subprocess.run(["grep", "OMDB_API_KEY", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""


def imdb_lookup(title):
    key = get_omdb_key()
    if not key:
        return None
    try:
        url = f"http://www.omdbapi.com/?t={urllib.parse.quote(title)}&apikey={key}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("Response") == "True":
            return {
                "Title": data.get("Title", ""),
                "Year": data.get("Year", ""),
                "Director": data.get("Director", ""),
                "Genre": data.get("Genre", ""),
                "imdbRating": data.get("imdbRating", ""),
                "imdbVotes": data.get("imdbVotes", "").replace(",", ""),
                "Metascore": data.get("Metascore", ""),
                "imdbID": data.get("imdbID", ""),
            }
    except Exception:
        pass
    return None


def extract_film_title(text):
    boundary = {"at", "on", "in", "to", "with", "for", "from", "and", "but",
                "was", "were", "had", "has", "got", "rated", "gave", "scored",
                "film", "movie", "club", "night", "it", "them", "that", "this",
                "the", "about", "like", "really", "very", "by", "as", "so",
                "if", "or", "up", "out", "off", "not", "just", "also", "list",
                "remote", "remotely", "online", "zoom"}
    m = re.search(r'["\u201c\u201d\']([A-Z][^"\']{1,60})["\u201c\u201d\']', text)
    if m:
        return m.group(1).strip()
    patterns = [
        r'\badd\s+(?:the\s+)?(?:movie\s+|film\s+)?([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,5})',
        r'\bjust watched\s+(?:the\s+)?(?:movie\s+|film\s+)?([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,5})',
        r'\bfinished watching\s+(?:the\s+)?(?:movie\s+|film\s+)?([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,5})',
        r'\bwatch(?:ed|ing)?\s+(?:the\s+)?(?:movie\s+|film\s+)?([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,5})',
        r'\b(?:movie|film)\s+(?:is|called|named)\s+([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,5})',
        r'\brat(?:e|ing|ed)\s+(?:the\s+)?(?:movie\s+|film\s+)?([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,5})',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            words = raw.split()
            title_words = []
            for w in words:
                if w.lower() in boundary:
                    break
                title_words.append(w)
            title = " ".join(title_words).strip()
            if len(title) > 1:
                return title
    return None


def extract_rating(text):
    """Extract a rating and convert to 1-10 scale."""
    # Star unicode characters (★★★★★ = 5 stars → 10/10)
    m = re.search(r'((?:★){1,5})', text)
    if m:
        star_map = {5: '10', 4: '8', 3: '6', 2: '4', 1: '2'}
        return star_map.get(m.group(1).count('★'), None)
    # X/5 format → double for 10-point scale
    m = re.search(r'(\d(?:\.\d)?)\s*/\s*5', text)
    if m:
        val = float(m.group(1))
        return str(min(int(val * 2), 10))
    # X/10 format
    m = re.search(r'(\d{1,2})(?:\.\d)?\s*/\s*10', text)
    if m:
        return str(min(int(m.group(1)), 10))
    # "rated X" or "gave it X" or "scored X" (assume out of 10)
    m = re.search(r'(?:rated?|gave|scored?)\s+(?:it\s+)?(\d(?:\.\d)?)\s*(?:out of\s+(?:5|10))?', text, re.IGNORECASE)
    if m:
        val = float(m.group(1))
        # If it's out of 5, double it
        if 'out of 5' in text.lower() or val <= 5:
            return str(min(int(val * 2), 10))
        return str(min(int(val), 10))
    return None


def extract_watched_at(text):
    tl = text.lower()
    if any(w in tl for w in ["hosted", "at mine", "at my", "at david's", "in person", "together at", "came over", "round at"]):
        return "Hosted (at someone's home)"
    if any(w in tl for w in ["remote", "streamed", "online", "zoom", "separately", "own homes", "from home"]):
        return "Remote (streamed remotely)"
    if any(w in tl for w in ["cinema", "odeon", "vue", "imax", "theatre", "theater"]):
        return "Cinema"
    return None


def extract_month(text):
    months = ["january", "february", "march", "april", "may", "june",
              "july", "august", "september", "october", "november", "december"]
    tl = text.lower()
    for i, m in enumerate(months, 1):
        if m in tl:
            return f"{datetime.date.today().year}-{i:02d}"
    today = datetime.date.today()
    return f"{today.year}-{today.month:02d}"


def handle_film_club(msg, dry_run=False):
    text = msg.get("text", "")
    film_title = extract_film_title(text)
    rating = extract_rating(text)
    month = extract_month(text)
    watched_at = extract_watched_at(text)

    print(f"   🎬 Film: {film_title or 'unknown'} | Rating: {rating or '—'} | Month: {month} | Where: {watched_at or '—'}")

    if not film_title:
        if dry_run:
            print(f"  [DRY RUN] Would log film club note to Output_Log")
            return True
        return airtable_post("Output_Log", {
            "Item": "Film Club note",
            "Module": "FilmClub",
            "Generated At": datetime.date.today().isoformat(),
            "Content": text,
        })

    print(f"   🔍 IMDb lookup: '{film_title}'...")
    imdb = imdb_lookup(film_title)
    if imdb:
        print(f"   ✅ {imdb.get('Title')} ({imdb.get('Year')}) | IMDb: {imdb.get('imdbRating')}")

    fields = {"Film Title": film_title}
    if imdb:
        if imdb.get("Year"):
            try: fields["Year"] = int(imdb["Year"].split("–")[0])
            except ValueError: pass
        if imdb.get("Director"): fields["Director"] = imdb["Director"]
        if imdb.get("Genre"): fields["Genre"] = imdb["Genre"]
        if imdb.get("imdbRating") and imdb["imdbRating"] != "N/A":
            try: fields["IMDb Rating"] = float(imdb["imdbRating"])
            except ValueError: pass
        if imdb.get("imdbVotes"):
            try: fields["IMDb Votes"] = int(imdb["imdbVotes"])
            except ValueError: pass
        if imdb.get("Metascore") and imdb["Metascore"] != "N/A":
            try: fields["Metascore"] = int(imdb["Metascore"])
            except ValueError: pass
        if imdb.get("imdbID"):
            fields["IMDb URL"] = f"https://www.imdb.com/title/{imdb['imdbID']}/"

    if month: fields["Month Picked"] = month
    if rating: fields["My Rating"] = rating
    if watched_at: fields["Watched At"] = watched_at
    fields["Film Club"] = "Yes"
    fields["Club Discussion Notes"] = text

    if dry_run:
        print(f"  [DRY RUN] Would create Films: {json.dumps(fields, indent=2)[:300]}")
        return True

    ok = airtable_post("Films", fields)
    if ok:
        print(f"  ✅ Films record created")
    return ok


HANDLERS = {
    "Person Note": handle_person_note,
    "Todo": handle_todo,
    "Memory": handle_memory,
    "Recipe": handle_recipe,
    "Module Request": handle_module_request,
    "Film Club": handle_film_club,
}


# ── Main ────────────────────────────────────────────────────────────────────────

def process_messages(messages, dry_run=False):
    results = {"processed": 0, "skipped": 0, "failed": 0, "categories": {}}

    for msg in messages:
        text = msg.get("text", "").strip()
        if not text or msg.get("sender_id") == "GEVES_BOT":
            continue

        category = classify_message(text)
        results["categories"][category] = results["categories"].get(category, 0) + 1

        print(f"\n📨 [{msg.get('sender', '?')}] {text[:100]}...")
        print(f"   Category: {category}")

        if category == "General":
            print(f"   ℹ️  General — no action taken")
            results["skipped"] += 1
            continue

        handler = HANDLERS.get(category)
        if handler:
            try:
                success = handler(msg, dry_run=dry_run)
                if success:
                    results["processed"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                print(f"  ❌ Error: {e}")
                results["failed"] += 1
        else:
            results["skipped"] += 1

    return results


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args

    if "--stdin" in args:
        messages = json.loads(sys.stdin.read())
    elif "--file" in args:
        idx = args.index("--file")
        with open(args[idx + 1]) as f:
            messages = json.load(f)
    else:
        print(__doc__)
        sys.exit(1)

    if not isinstance(messages, list):
        messages = [messages]

    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"🔄 Slack Capture Loop [{mode}] — {len(messages)} messages")
    print("=" * 60)

    results = process_messages(messages, dry_run=dry_run)

    print("\n" + "=" * 60)
    print(f"📊 Results: {results['processed']} processed, {results['skipped']} skipped, {results['failed']} failed")
    print(f"   Categories: {results['categories']}")


if __name__ == "__main__":
    main()
