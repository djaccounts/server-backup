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
    # Restaurant module tables
    "Restaurants":         "tblvpSxjeoCQvjotM",
    "Restaurant_Visits":   "tblf2k6uAHLW7mA4b",
    # Meals module
    "Meals":               "tblzEBw7Whoomb63E",
    # Fitness module
    "Workouts":            "tblMDYF8Lkl5A15CW",
    "Exercise Log":        "tbl8MXDYZ2hajsdIk",
    "Cycling":             "tblZ7hkoE68IRnQwV",
    "Fitness Goals":       "tblAM0Grin01IQmdd",
    # Sleep/Habits module
    "Sleep Log":           "tblTZchsmcXXernI0",
    "Habits":              "tblS6SryrC3RnRl1L",
    "Habit Log":           "tbl3YRZ1yoQ7kRPIT",
    # People module
    "Person Notes":        "tbl6hnxzXXmWFkVfh",
    "Conversation Log":    "tbl2dbgksA9XveLcx",
    # Books module
    "Books":               "tblUfRTBkCMLUe2pY",
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
    r, status = api("POST", f"{BASE}/{q(table)}", {"fields": fields})
    if status == 200:
        return True, r.get("id", "")
    return False, ""


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
        r"\bingredient\b", r"\bdinner\b", r"\blunch\b", r"\bbreakfast\b",
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
        r"\btablespoons?\s+(of\s+)?\w+\b", r"\bteaspoons?\s+(of\s+)?\w+\b",
    ]),
    ("Meal", [
        r"\bate\b", r"\bhad\b", r"\bfor lunch\b", r"\bfor dinner\b", r"\bfor breakfast\b",
        r"\bfor snack\b", r"\bsnack\b", r"\bcalories\b", r"\bmacros\b", r"\bprotein\b",
        r"\bcarbs?\b", r"\bfat\b", r"\blog(ged)? (my )?(food|meal|lunch|dinner|breakfast|snack)\b",
        r"\bfood log\b", r"\bnutrition\b", r"\bcalorie\b",
    ]),
    ("Restaurant", [
        r"\brestaurant\b", r"\bfor dinner\b", r"\bfor lunch\b", r"\bwent to\b", r"\bate at\b",
        r"\bdinner at\b", r"\blunch at\b", r"\bfind me a restaurant\b", r"\brecommend a restaurant\b",
        r"\brat(e|ing|ed) (the )?restaurant\b", r"\bscored (the )?restaurant\b",
        r"\bbooking\b", r"\bbooked\b.*\b(restaurant|place|cafe|pub)\b",
        r"\bmenu\b", r"\bfine dining\b",
        r"\bwent out (for|to)\b.*\b(eat|dinner|lunch|food)\b",
        r"\bwe ate\b", r"\bwe went\b.*\b(restaurant|place|cafe|pub)\b",
        r"\btried\b.*\b(place|restaurant|cafe|pub)\b",
        r"\b(place|restaurant|cafe|pub)\b.*\b(was|were)\b.*\b(great|good|amazing|terrible|bad|ok|nice)\b",
    ]),
    ("Module Request", [
        r"\bmovie\b", r"\bfilm\b", r"\bwatch\b",
        r"\bparty\b", r"\btravel\b",
        r"\bholiday\b", r"\bproperty\b", r"\bhouse\b",
        r"\brecommend\b", r"\bsuggest\b",
    ]),
    ("Sleep/Habit", [
        r"\bslept\b", r"\bsleep\b", r"\bbed\b", r"\bwake\b", r"\bwoke\b",
        r"\btired\b", r"\brest\b", r"\bhabit\b", r"\broutine\b", r"\bstreak\b",
        r"\bcompleted\b", r"\bdid my\b", r"\blogged\b",
    ]),
    ("Fitness", [
        r"\bworkout\b", r"\bgym\b", r"\bran\b", r"\brun\b",
        r"\bcycl(ing|ed|e)\b", r"\bbike\b", r"\bride\b",
        r"\bswim\b", r"\bswam\b", r"\bpool\b",
        r"\byoga\b", r"\bstretch\b",
        r"\bwalk(ed|s|ing)?\b", r"\bhike\b",
        r"\btrained\b", r"\btraining\b", r"\blift(ed|ing|s)?\b",
        r"\bexercise\b", r"\bcardio\b", r"\bstrength\b",
        r"\bweights?\b", r"\bbench\b", r"\bsquat\b", r"\bdeadlift\b",
        r"\bpress\b", r"\btreadmill\b", r"\brow(ed|ing|s)?\b",
        r"\bsets?\b", r"\breps?\b", r"\bHIIT\b",
        r"\bpeloton\b", r"\bstrava\b", r"\bfitness\b",
        r"\bPB\b", r"\bpersonal best\b", r"\bgymnastics\b",
    ]),
    ("Film Club", [
        r"\bfilm club\b", r"\bmovie club\b", r"\bmovie night\b",
        r"\bfilm night\b", r"\bjust watched\b", r"\bfinished watching\b",
        r"\brat(e|ing|ed) (the )?(movie|film)\b",
        r"\bscored (the )?(movie|film)\b", r"\badd to (the )?list\b",
        r"\blog (the )?(movie|film)\b",
    ]),
    ("Books", [
        r"\bbook\b", r"\breading\b", r"\bread\b",
        r"\bnovel\b", r"\bauthor\b", r"\bisbn\b",
        r"\baudiobook\b", r"\bebook\b", r"\be-book\b",
        r"\bhardcover\b", r"\bpaperback\b",
        r"\bgoodreads\b",
        r"\bfinished (the )?(book|novel|it)\b",
        r"\bjust (read|finished)\b",
        r"\bwant to read\b", r"\badd to (my )?(reading )?list\b",
        r"\bcurrently reading\b", r"\bstarted reading\b",
        r"\bgave up on\b", r"\bstopped reading\b",
        r"\brecommend(s|ed|ation)?\b.*\b(book|novel|read)\b",
        r"\b(book|novel|read)\b.*\brecommend(s|ed|ation)?\b",
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
    today = datetime.date.today().isoformat()

    if name:
        existing = find_person(name)
        if existing:
            # Create a Person Notes record linked to this person
            if dry_run:
                print(f"  [DRY RUN] Would create person note for {name}: {text[:60]}")
                return True
            ok, _ = airtable_post("Person Notes", {
                "Note": text,
                "Person": [existing["id"]],
                "Source": "Slack",
            })
            if ok:
                print(f"  ✅ Created person note for {name}")
            return ok
        else:
            # Person doesn't exist — create them with Tier 4
            if dry_run:
                print(f"  [DRY RUN] Would create new person: {name}")
                return True
            ok, pid = airtable_post("People", {
                "Name": name,
                "Tier": "Tier 4",
            })
            if ok:
                # Also create a Person Note with the context
                airtable_post("Person Notes", {
                    "Note": f"Added via Slack: {text}",
                    "Person": [pid],
                    "Source": "Slack",
                })
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
            "Created": today,
        })


def handle_todo(msg, dry_run=False):
    text = msg.get("text", "")
    task = extract_todo_task(text)
    due_date = extract_date(text)
    fields = {"Task": task, "Status": "Not started", "Priority": "Medium", "Module": "General", "Source": "Slack"}
    if due_date:
        fields["Due Date"] = due_date
    if dry_run:
        print(f"  [DRY RUN] Would create todo: {json.dumps(fields)}")
        return True
    ok, _ = airtable_post("Todos", fields)
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
        "Created": datetime.date.today()[0].isoformat(),
    })


def handle_module_request(msg, dry_run=False):
    text = msg.get("text", "")
    if dry_run:
        print(f"  [DRY RUN] Would log module request to Output_Log")
        return True
    return airtable_post("Output_Log", {
        "Item": text[:100],
        "Module": "General",
        "Generated At": datetime.date.today()[0].isoformat(),
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
        "Generated At": datetime.date.today()[0].isoformat(),
        "Content": text,
    })


def handle_meal(msg, dry_run=False):
    """Handle meal logging messages — log to Meals table."""
    text = msg.get("text", "")
    ts = msg.get("ts", "")
    today = datetime.date.today().isoformat()

    # Extract what was eaten — remove common prefixes
    description = text
    prefixes = [
        r"(?i)^i ate\s+", r"(?i)^i had\s+", r"(?i)^i've had\s+",
        r"(?i)^had\s+", r"(?i)^ate\s+", r"(?i)^lunch:\s+", r"(?i)^dinner:\s+",
        r"(?i)^breakfast:\s+", r"(?i)^snack:\s+", r"(?i)^logged\s+",
        r"(?i)^log\s+(my\s+)?(food|meal|lunch|dinner|breakfast|snack):\s*",
        r"(?i)^food:\s+",
    ]
    for prefix in prefixes:
        description = re.sub(prefix, "", description).strip()

    # Detect meal type from context
    text_lower = text.lower()
    meal_type = "Snack"  # default
    if re.search(r"\b(breakfast|morning)\b", text_lower):
        meal_type = "Breakfast"
    elif re.search(r"\b(lunch|midday)\b", text_lower):
        meal_type = "Lunch"
    elif re.search(r"\b(dinner|evening|supper)\b", text_lower):
        meal_type = "Dinner"
    elif re.search(r"\b(snack|afternoon)\b", text_lower):
        meal_type = "Snack"

    # Time-based fallback for meal type
    if meal_type == "Snack":
        hour = datetime.datetime.now().hour
        if hour < 11:
            meal_type = "Breakfast"
        elif hour < 14:
            meal_type = "Lunch"
        elif hour >= 17:
            meal_type = "Dinner"

    if dry_run:
        print(f"  [DRY RUN] Would log meal: {description[:60]} (type={meal_type})")
        return True

    return airtable_post("Meals", {
        "Description": description[:200],
        "Date": today,
        "Meal type": meal_type,
        "Accuracy": "Estimated",
        "Source": "Slack",
    })


# ── Sleep/Habit helpers ──────────────────────────────────────────────────────────

def handle_sleep_habit(msg, dry_run=False):
    """Handle sleep logging and habit tracking messages."""
    text = msg.get("text", "")
    today = datetime.date.today().isoformat()
    text_lower = text.lower()

    # Check if this is a sleep log message
    if re.search(r"\b(slept|sleep|bed|woke|wake)\b", text_lower):
        # Extract bedtime
        bedtime = None
        m = re.search(r"(?:went to bed|bed at|slept at)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", text_lower)
        if m:
            bedtime = m.group(1).strip()
        else:
            m = re.search(r"(?:from|at)\s+(\d{1,2}(?::\d{2})?\s*(?:pm|am)?)\s+(?:to|-)\s+\d{1,2}", text_lower)
            if m:
                bedtime = m.group(1).strip()

        # Extract wake time
        wake_time = None
        m = re.search(r"(?:woke|wake)\s+(?:at\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", text_lower)
        if m:
            wake_time = m.group(1).strip()
        else:
            m = re.search(r"(?:to|-)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", text_lower)
            if m:
                wake_time = m.group(1).strip()

        # Extract hours slept
        hours = None
        m = re.search(r"(\d+(?:\.\d+)?)\s*hours?\s*(?:of\s+)?(?:sleep|slept)", text_lower)
        if m:
            hours = float(m.group(1))

        # Extract quality
        quality = None
        m = re.search(r"(?:quality|rated?|rating)\s+(\d)\s*/?\s*5?", text_lower)
        if m:
            quality = int(m.group(1))

        if dry_run:
            print(f"  [DRY RUN] Would log sleep: bed={bedtime}, wake={wake_time}, hours={hours}, quality={quality}")
            return True

        fields = {"Date": today}
        if bedtime:
            fields["Bedtime"] = bedtime
        if wake_time:
            fields["Wake time"] = wake_time
        if hours:
            fields["Hours slept"] = hours
        if quality:
            fields["Quality"] = quality
        if len(fields) > 1:  # More than just Date
            return airtable_post("Sleep Log", fields)
        return False

    # Check if this is a habit message
    if re.search(r"\b(habit|completed|did my|logged|routine|streak)\b", text_lower):
        # Extract habit name
        habit_name = None
        m = re.search(r"(?:did my|completed|logged)\s+(.+?)(?:\s*$|\s+(?:habit|today|streak))", text_lower)
        if m:
            habit_name = m.group(1).strip().title()

        if dry_run:
            print(f"  [DRY RUN] Would log habit: {habit_name}")
            return True

        if habit_name:
            # Find or create the habit
            formula = f"{{Habit}}='{habit_name}'"
            r, status = api("GET", f"{BASE}/Habits?filterByFormula={q(formula)}&maxRecords=1")
            habit_id = None
            if status == 200 and r.get("records"):
                habit_id = r["records"][0]["id"]
            else:
                # Create the habit
                hr, hs = api("POST", f"{BASE}/Habits", {"fields": {"Habit": habit_name, "Active": True}})
                if hs == 200:
                    habit_id = hr.get("id")

            if habit_id:
                return airtable_post("Habit Log", {
                    "Date": today,
                    "Habit": [habit_id],
                    "Completed": True,
                })
        return False

    return False


# ── Fitness helpers ─────────────────────────────────────────────────────────────

def handle_fitness(msg, dry_run=False):
    """Handle workout logging, gym sessions, cycling, and fitness goals."""
    text = msg.get("text", "")
    today = datetime.date.today().isoformat()
    text_lower = text.lower()

    # Detect workout type
    workout_type = "Other"
    if re.search(r"\b(gym|lift|weights|bench|squat|deadlift|press|hiit)\b", text_lower):
        workout_type = "Gym"
    elif re.search(r"\b(run|ran|jog|treadmill)\b", text_lower):
        workout_type = "Run"
    elif re.search(r"\b(cycl|bike|ride|strava)\b", text_lower):
        workout_type = "Cycle"
    elif re.search(r"\b(swim|swam|pool)\b", text_lower):
        workout_type = "Swim"
    elif re.search(r"\b(yoga|stretch)\b", text_lower):
        workout_type = "Yoga"
    elif re.search(r"\b(walk|hike)\b", text_lower):
        workout_type = "Walk"
    elif re.search(r"\b(class|session|peloton)\b", text_lower):
        workout_type = "Class"

    # Extract duration
    duration = None
    m = re.search(r"(\d+)\s*(?:min|mins|minutes)\b", text_lower)
    if m:
        duration = int(m.group(1))
    else:
        m = re.search(r"(\d+)\s*(?:hr|hrs|hours?)\b", text_lower)
        if m:
            duration = int(m.group(1)) * 60

    # Extract distance
    distance = None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kilomet)", text_lower)
    if m:
        distance = float(m.group(1))
    else:
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:mi|miles?)\b", text_lower)
        if m:
            distance = round(float(m.group(1)) * 1.609, 1)

    # Extract energy level
    energy = None
    m = re.search(r"(?:energy|felt|feeling)\s+(\d)\s*/?5", text_lower)
    if m:
        energy = int(m.group(1))

    # Extract difficulty
    difficulty = None
    m = re.search(r"(?:difficulty|hard|tough)\s+(\d)\s*/?5", text_lower)
    if m:
        difficulty = int(m.group(1))

    if dry_run:
        print(f"  [DRY RUN] Would log workout: type={workout_type}, dur={distance}, dist={distance}, energy={energy}, diff={difficulty}")
        return True

    fields = {"Date": today, "Type": workout_type, "Source": "Slack"}
    if duration:
        fields["Duration (mins)"] = duration
    if distance:
        fields["Distance (km)"] = distance
    if energy:
        fields["Energy level"] = energy
    if difficulty:
        fields["Perceived difficulty"] = difficulty

    # Cycle rides get a linked Cycling record
    if workout_type == "Cycle":
        ride_type = "Road"
        for rt, label in [("gravel", "Gravel"), ("mtb", "MTB"), ("turbo", "Turbo"), ("commute", "Commute")]:
            if rt in text_lower:
                ride_type = label
                break
        avg_speed = None
        m = re.search(r"(?:avg|average)\s+(\d+(?:\.\d+)?)\s*mph", text_lower)
        if m:
            avg_speed = float(m.group(1))
        max_speed = None
        m = re.search(r"(?:max|top)\s+speed\s+(\d+(?:\.\d+)?)\s*mph", text_lower)
        if m:
            max_speed = float(m.group(1))
        elevation = None
        m = re.search(r"(?:elevation|climbed|ascended)\s+(\d+)\s*m", text_lower)
        if m:
            elevation = int(m.group(1))
        bike = None
        m = re.search(r"(?:on my|rode the|using the)\s+(.+?)(?:\.|\s+and|\s+for|\s+at|$)", text_lower)
        if m:
            bike = m.group(1).strip()

        ok, workout_id = airtable_post("Workouts", {**fields, "Notes": text[:500]})
        if ok:
            cycling_fields = {"Date": today, "Workout": [workout_id], "Ride type": ride_type}
            if distance:
                cycling_fields["Distance (miles)"] = round(distance * 0.621, 1)
            if duration:
                cycling_fields["Duration (mins)"] = duration
            if elevation:
                cycling_fields["Elevation gain (m)"] = elevation
            if avg_speed:
                cycling_fields["Avg speed (mph)"] = avg_speed
            if max_speed:
                cycling_fields["Max speed (mph)"] = max_speed
            if bike:
                cycling_fields["Bike used"] = bike.capitalize()
            airtable_post("Cycling", cycling_fields)
            dist_str = f"{distance}km " if distance else ""
            print(f"  ✅ Logged cycle ride: {dist_str}{ride_type}")
            return True
        return False

    # Gym sessions: extract exercises
    if workout_type == "Gym":
        exercises = _extract_exercises(text)
        if exercises:
            ok, workout_id = airtable_post("Workouts", {**fields, "Notes": text[:500]})
            if ok:
                for ex in exercises:
                    airtable_post("Exercise Log", {
                        "Exercise": ex["name"],
                        "Workout": [workout_id],
                        "Sets": ex.get("sets"),
                        "Reps": ex.get("reps"),
                        "Weight (kg)": ex.get("weight"),
                    })
                print(f"  ✅ Logged gym session with {len(exercises)} exercises")
                return True
            return False

    # Default: just log the workout
    ok, _ = airtable_post("Workouts", {**fields, "Notes": text[:500]})
    if ok:
        type_str = workout_type if workout_type != "Other" else "workout"
        dur_str = f", {duration}min" if duration else ""
        dist_str = f", {distance}km" if distance else ""
        print(f"  ✅ Logged {type_str}: {dur_str}{dist_str}")
    return ok


def _extract_exercises(text):
    """Extract exercise names, sets, reps, weight from gym session text."""
    exercises = []
    text_lower = text.lower()

    # Pattern: "sets x reps exercise" or "exercise: sets x reps at weight kg"
    patterns = [
        # "3x8 bench press at 60kg"
        r'(\d+)\s*x\s*(\d+)\s+(?:at\s+\d+(?:\.\d+)?\s*kg\s+)?([\w\s]+?)(?:\s+at\s+(\d+(?:\.\d+)?)\s*kg)?(?:\s*[,\.;]|$)',
        # "bench press: 3x8 at 60kg"
        r'([\w\s]+?):\s*(\d+)\s*x\s*(?:\d+\s*,\s*)*(?:\d+)\s*(?:at\s+(\d+(?:\.\d+)?)\s*kg)?',
        # "3 sets of 8 bench press at 60kg"
        r'(\d+)\s+sets?\s+(?:of\s+)?(\d+)\s+(?:reps?\s+)?([\w\s]+?)(?:\s+at\s+(\d+(?:\.\d+)?)\s*kg)?(?:\s*[,\.;]|$)',
    ]

    known_exercises = [
        "bench press", "squat", "deadlift", "overhead press", "ohp",
        "barbell row", "pull ups", "pullups", "lat pulldown", "leg press",
        "bicep curl", "tricep extension", "lateral raise", "front raise",
        "chest press", "leg extension", "leg curl", "calf raise",
        "incline bench", "decline bench", "dumbbell press", "cable row",
        "face pull", "shrugs", "dips", "crunches", "plank",
    ]

    found_names = set()
    for pattern in patterns:
        for m in re.finditer(pattern, text_lower):
            groups = m.groups()
            if len(groups) < 3:
                continue
            if "set" in groups[0] or groups[0].isdigit() and int(groups[0]) > 30:
                # Pattern 1 or 3: sets, reps, name, weight
                sets = int(groups[0])
                reps = groups[1]
                name = groups[2].strip().title()[:50]
                weight = f"{groups[3]}kg" if len(groups) > 3 and groups[3] else None
            else:
                # Pattern 2: name, sets, weight
                name = groups[0].strip().title()[:50]
                sets = int(groups[1]) if groups[1] else None
                reps = None
                weight = f"{groups[2]}kg" if len(groups) > 2 and groups[2] else None

            if name and len(name) > 2 and name not in found_names:
                found_names.add(name)
                exercises.append({"name": name, "sets": sets, "reps": reps, "weight": weight})

    if exercises:
        return exercises

    # Fallback: just match known exercise names
    for ex in known_exercises:
        if ex in text_lower:
            if ex not in found_names:
                found_names.add(ex)
                exercises.append({"name": ex.title(), "sets": None, "reps": None, "weight": None})
    return exercises

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
            "Generated At": datetime.date.today()[0].isoformat(),
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

    ok, _ = airtable_post("Films", fields)
    if ok:
        print(f"  ✅ Films record created")
    return ok


def handle_restaurant(msg, dry_run=False):
    """Handle restaurant-related messages — create Restaurants and Restaurant Visits records."""
    text = msg.get("text", "")
    ts = msg.get("ts", "")
    today = datetime.date.today().isoformat()

    # Extract restaurant name
    restaurant_name = extract_restaurant_name(text)
    rating = extract_rating(text)
    wife_rating = extract_wife_rating(text)
    would_return = extract_would_return(text)
    cost = extract_cost(text)
    dishes = extract_dishes(text)

    print(f"   🍽️ Restaurant: {restaurant_name or 'unknown'} | Rating: {rating or '—'} | Wife: {wife_rating or '—'} | Return: {would_return or '—'}")

    if not restaurant_name:
        # Can't identify restaurant — log for Hermes to handle
        if dry_run:
            print(f"  [DRY RUN] Would log restaurant note to Output_Log")
            return True
        return airtable_post("Output_Log", {
            "Item": text[:100],
            "Module": "Restaurant",
            "Generated At": today,
            "Content": text,
        })[0]

    # Build Google search URL for the restaurant
    maps_url = f"https://www.google.com/search?q={urllib.parse.quote(restaurant_name + ' restaurant London')}"

    # Find or create restaurant record
    existing = find_restaurant(restaurant_name)
    if existing:
        restaurant_id = existing["id"]
        print(f"   ℹ️  Found existing restaurant: {restaurant_name}")
    else:
        fields = {"Name": restaurant_name, "Maps URL": maps_url, "Source": "We went"}
        if rating:
            fields["Overall Rating"] = rating
        if dry_run:
            print(f"  [DRY RUN] Would create restaurant: {json.dumps(fields)}")
            restaurant_id = "dry_run_id"
        else:
            ok, rid = airtable_post("Restaurants", fields)
            if ok:
                restaurant_id = rid
                print(f"  ✅ Created restaurant: {restaurant_name}")
            else:
                print(f"  ❌ Failed to create restaurant")
                return True  # still try to log visit

    # Create visit record
    visit_fields = {"Date": today, "Source": "Slack"}
    if restaurant_id and restaurant_id != "dry_run_id":
        visit_fields["Restaurant"] = [restaurant_id]
    if rating:
        visit_fields["Overall Rating"] = rating
    if wife_rating:
        visit_fields["Wife's Rating"] = wife_rating
    if would_return:
        visit_fields["Would Return"] = would_return
    if cost:
        visit_fields["Cost Total"] = cost
    if dishes:
        visit_fields["Dishes Ordered"] = dishes

    if dry_run:
        print(f"  [DRY RUN] Would create visit: {json.dumps(visit_fields)}")
        return True

    ok, _ = airtable_post("Restaurant_Visits", visit_fields)
    if ok:
        print(f"  ✅ Created restaurant visit for: {restaurant_name}")
    return ok


def extract_restaurant_name(text):
    """Extract restaurant name from a message."""
    # Quoted names
    m = re.search(r'["\u201c\u201d\']([A-Z][^"\']{2,60})["\u201c\u201d\']', text)
    if m:
        return m.group(1).strip()

    boundary = {"at", "in", "to", "with", "for", "from", "and", "but", "was",
                "were", "had", "has", "got", "rated", "gave", "scored", "the",
                "about", "like", "really", "very", "by", "as", "so", "if", "or",
                "up", "out", "off", "not", "just", "also", "list", "place",
                "restaurant", "cafe", "pub", "bar", "went", "ate", "tried",
                "had", "dinner", "lunch", "breakfast", "food", "meal", "park",
                "last", "night", "this", "that", "it", "there", "here"}

    patterns = [
        r'\bwent to\s+(?:the\s+)?(?:restaurant\s+|cafe\s+|pub\s+|bar\s+)?([A-Z][a-z]+(?:\'[a-z]+)?(?:\s+[A-Z]?[a-z]+(?:\'[a-z]+)?){0,4})',
        r'\bate at\s+(?:the\s+)?(?:restaurant\s+|cafe\s+|pub\s+|bar\s+)?([A-Z][a-z]+(?:\'[a-z]+)?(?:\s+[A-Z]?[a-z]+(?:\'[a-z]+)?){0,4})',
        r'\bdinner at\s+(?:the\s+)?(?:restaurant\s+|cafe\s+|pub\s+|bar\s+)?([A-Z][a-z]+(?:\'[a-z]+)?(?:\s+[A-Z]?[a-z]+(?:\'[a-z]+)?){0,4})',
        r'\blunch at\s+(?:the\s+)?(?:restaurant\s+|cafe\s+|pub\s+|bar\s+)?([A-Z][a-z]+(?:\'[a-z]+)?(?:\s+[A-Z]?[a-z]+(?:\'[a-z]+)?){0,4})',
        r'\bbooked\s+(?:the\s+)?(?:restaurant\s+|cafe\s+|pub\s+|bar\s+)?([A-Z][a-z]+(?:\'[a-z]+)?(?:\s+[A-Z]?[a-z]+(?:\'[a-z]+)?){0,4})',
        r'\btried\s+(?:the\s+)?(?:restaurant\s+|cafe\s+|pub\s+|bar\s+)?([A-Z][a-z]+(?:\'[a-z]+)?(?:\s+[A-Z]?[a-z]+(?:\'[a-z]+)?){0,4})',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            words = raw.split()
            name_words = []
            for w in words:
                if w.lower() in boundary:
                    break
                name_words.append(w)
            name = " ".join(name_words).strip()
            if len(name) > 1:
                return name
    return None


def extract_wife_rating(text):
    """Extract wife's rating from message."""
    m = re.search(r"(?:wife|she)\s+(?:rated|gave|scored)\s+(?:it\s+)?(\d(?:\.\d)?)\s*(?:/|out of)\s*(?:5|10)", text, re.IGNORECASE)
    if m:
        val = float(m.group(1))
        if val <= 5:
            return str(min(int(val * 2), 10))
        return str(min(int(val), 10))
    m = re.search(r"(?:wife|she)\s+(?:rated|gave|scored)\s+(?:it\s+)?(\d{1,2})", text, re.IGNORECASE)
    if m:
        return str(min(int(m.group(1)), 10))
    return None


def extract_would_return(text):
    tl = text.lower()
    if any(w in tl for w in ["definitely going back", "will return", "going back", "back again", "can't wait to go back"]):
        return "Definitely"
    if any(w in tl for w in ["maybe go back", "might return", "could go back", "not sure about going back"]):
        return "Maybe"
    if any(w in tl for w in ["never going back", "won't return", "not going back", "avoid"]):
        return "No"
    return None


def handle_books(msg, dry_run=False):
    """Handle book-related messages — add to reading list, log finished books, track reading."""
    import re as _re
    text = msg.get("text", "")
    today = datetime.date.today().isoformat()
    text_lower = text.lower()

    # Extract title — look for quoted text or text after "book" / "add" / "reading"
    title = None
    # Try quoted title first
    m = _re.search(r'"([^"]+)"', text)
    if m:
        title = m.group(1).strip()
    else:
        # Try patterns like "add X to my list" or "finished X" or "reading X"
        for pattern in [
            _re.compile(r'(?:add|finished|reading|started|just read|want to read|recommend(?:ed)?)\s+(?:the\s+)?(?:book\s+)?["\u201c]?([^"\u201d]+?)["\u201d]?\s+(?:to my|to the|from|by|today|this year|$)', _re.IGNORECASE),
            _re.compile(r'(?:book|novel)\s+(?:called|named|titled)\s+["\u201c]?([^"\u201d]+)["\u201d]?', _re.IGNORECASE),
            _re.compile(r'(?:by|author)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', _re.IGNORECASE),
        ]:
            m = pattern.search(text)
            if m:
                candidate = m.group(1).strip()
                if len(candidate) > 2 and len(candidate) < 100:
                    title = candidate
                    break

    # Extract author
    author = None
    m = _re.search(r'(?:by|author)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
    if m:
        author = m.group(1).strip()

    # Determine status — order matters! More specific patterns first.
    status = "Want to read"  # default
    if _re.search(r'\b(finished|just read|completed)\b', text_lower):
        status = "Read"
    elif _re.search(r'\b(gave up|stopped|abandoned|quit)\b', text_lower):
        status = "Abandoned"
    elif _re.search(r'\bwant to read\b', text_lower):
        status = "Want to read"
    elif _re.search(r'\badd(ed|s)?\s+.*to\s+(my\s+)?(reading\s+)?list\b', text_lower):
        status = "Want to read"
    elif _re.search(r'\b(started|currently on|partway through)\b', text_lower):
        status = "Reading"
    elif _re.search(r'\breading\b', text_lower):
        status = "Reading"

    # Extract rating
    rating = None
    m = _re.search(r'(?:rated?|rating|gave)\s+(?:it\s+)?(\d+(?:\.\d+)?)\s*/?\s*(?:5|10)?', text_lower)
    if m:
        val = float(m.group(1))
        if val > 5:  # Assume 10-point scale
            val = val / 2
        rating = min(5, max(1, round(val)))
    else:
        # Look for star emojis or X/5 patterns
        m = _re.search(r'(\d+)\s*/\s*5', text)
        if m:
            rating = min(5, max(1, int(m.group(1))))

    # Build fields
    fields = {}
    if title:
        fields["Title"] = title[:200]
    if author:
        fields["Author"] = author[:100]
    fields["Status"] = status
    fields["Source"] = "Slack"
    if status == "Read":
        fields["Date finished"] = today
        if rating:
            fields["My rating"] = rating
    elif status == "Reading":
        fields["Date started"] = today

    if not title:
        print(f"  ℹ️  Could not extract book title — skipping")
        return False

    if dry_run:
        print(f"  [DRY RUN] Would create book record: {json.dumps(fields)}")
        return True

    ok, _ = airtable_post("Books", fields)
    if ok:
        print(f"  ✅ Book: '{title}' → {status}" + (f" ({rating}★)" if rating else ""))
    return ok


def extract_cost(text):
    """Extract total cost from message."""
    m = re.search(r'(?:bill|cost|total|spent|was)\s+(?:£|GBP\s+)(\d{2,4})(?:\.\d{2})?', text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r'£(\d{2,4})(?:\.\d{2})?\s+(?:total|bill|for the meal)', text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None


def extract_dishes(text):
    """Extract dishes ordered from message."""
    m = re.search(r'(?:had|ordered|ate|tried)\s+(?:the\s+)?(.+?)(?:\.|,|;|\band\b)', text, re.IGNORECASE)
    if m:
        dishes = m.group(1).strip()
        if len(dishes) > 5 and len(dishes) < 200:
            return dishes
    return None


def find_restaurant(name):
    """Find a restaurant by name (fuzzy match)."""
    if not name:
        return None
    # Try exact match first
    formula = f"{{Name}}='{name}'"
    r, status = api("GET", f"{BASE}/Restaurants?filterByFormula={q(formula)}&maxRecords=5")
    if status == 200:
        records = r.get("records", [])
        if records:
            return records[0]
    # Try contains match
    formula = f"FIND('{name}', {{Name}})>0"
    r, status = api("GET", f"{BASE}/Restaurants?filterByFormula={q(formula)}&maxRecords=5")
    if status == 200:
        records = r.get("records", [])
        if records:
            return records[0]
    return None


HANDLERS = {
    "Person Note": handle_person_note,
    "Todo": handle_todo,
    "Memory": handle_memory,
    "Recipe": handle_recipe,
    "Meal": handle_meal,
    "Restaurant": handle_restaurant,
    "Sleep/Habit": handle_sleep_habit,
    "Fitness": handle_fitness,
    "Module Request": handle_module_request,
    "Film Club": handle_film_club,
    "Books": handle_books,
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
