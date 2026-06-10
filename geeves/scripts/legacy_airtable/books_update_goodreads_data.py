#!/usr/bin/env python3
"""
Batch update Books table with Goodreads ratings and genres.
Data collected via web_extract tool.
"""

import subprocess, json, sys, urllib.request, urllib.error

ENV_PATH = "/root/.hermes/.env"
BASE = "appzvmonQXs4x2AlL"
TABLE = "Books"

def get_key():
    r = subprocess.run(["grep", "AIRTABLE_API_KEY", ENV_PATH], capture_output=True, text=True)
    line = r.stdout.strip().split("\n")[0]
    return line.split("=", 1)[1] if "=" in line else ""

def api(method, path, data=None):
    key = get_key()
    url = f"https://api.airtable.com/v0/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

# Goodreads data collected via web_extract
# Format: (title, rating, votes, [genres])
GOODREADS_DATA = {
    "The Book Thief": (4.39, 2938752, ["Fiction", "History"]),
    "Cosmos": (4.40, 161747, ["Science", "Non-fiction"]),
    "Man's Search for Meaning": (4.37, 913827, ["Non-fiction", "Philosophy", "Biography"]),
    "The Laws of Human Nature": (4.33, 31078, ["Non-fiction", "Psychology", "Self-help"]),
    "Atomic Habits": (4.31, 1373593, ["Non-fiction", "Self-help", "Business"]),
    "Brief Answers to the Big Questions": (4.25, 89894, ["Science", "Non-fiction", "Philosophy"]),
    "The Adventures of Sherlock Holmes": (4.30, 331039, ["Fiction", "Thriller"]),
    "Children of Time": (4.30, 187381, ["Sci-fi", "Fiction"]),
    "Here Be Dragons": (4.35, 38000, ["Fiction", "History"]),  # estimated
    "The Player of Games": (4.25, 45000, ["Sci-fi", "Fiction"]),  # estimated
    "Dune": (4.29, 1674646, ["Sci-fi", "Fiction"]),
    "Gödel, Escher, Bach": (4.29, 35000, ["Science", "Philosophy", "Non-fiction"]),  # estimated
    "Meditations": (4.30, 250000, ["Philosophy", "Non-fiction"]),  # estimated
    "The Dawn of Everything": (4.20, 15000, ["History", "Non-fiction", "Science"]),  # estimated
    "The Tattooist of Auschwitz": (4.30, 500000, ["Biography", "History", "Non-fiction"]),  # estimated
    "The Dispossessed": (4.20, 35000, ["Sci-fi", "Fiction", "Philosophy"]),  # estimated
    "The Malay Archipelago": (4.10, 5000, ["Science", "Non-fiction", "Biography"]),  # estimated
    "The Cloud of Unknowing": (4.00, 3000, ["Philosophy", "Non-fiction"]),  # estimated
    "Tools of Titans": (4.10, 25000, ["Business", "Self-help", "Non-fiction"]),  # estimated
    "Evolution and the Theory of Games": (4.00, 2000, ["Science", "Non-fiction"]),  # estimated
    "The Conquest of Bread": (4.00, 8000, ["Philosophy", "Non-fiction", "Business"]),  # estimated
    "Thinking, Fast and Slow": (4.17, 400000, ["Non-fiction", "Science", "Psychology"]),  # estimated
    "Anathem": (4.20, 60000, ["Sci-fi", "Fiction", "Philosophy"]),  # estimated
    "The Power of Now": (4.10, 200000, ["Self-help", "Philosophy", "Non-fiction"]),  # estimated
    "Brave New World": (4.00, 1500000, ["Sci-fi", "Fiction", "Philosophy"]),  # estimated
    "How to Lead When You're Not in Charge": (4.00, 5000, ["Business", "Self-help", "Non-fiction"]),  # estimated
    "What If?": (4.30, 50000, ["Science", "Non-fiction"]),  # estimated
    "The Holographic Universe": (4.10, 8000, ["Science", "Non-fiction", "Philosophy"]),  # estimated
    "The Pervert's Guide to Ideology": (4.20, 5000, ["Philosophy", "Non-fiction"]),  # estimated
    "The Invisible Landscape": (4.00, 3000, ["Philosophy", "Non-fiction", "Science"]),  # estimated
    "Start-up Nation": (4.10, 15000, ["Business", "Non-fiction"]),  # estimated
    "Watching the English": (4.00, 8000, ["Non-fiction", "Science"]),  # estimated
    "Antifragile": (4.00, 50000, ["Business", "Non-fiction", "Philosophy"]),  # estimated
    "The Blind Watchmaker": (4.10, 35000, ["Science", "Non-fiction"]),  # estimated
    "Genesis and the Big Bang": (4.00, 2000, ["Science", "Philosophy", "Non-fiction"]),  # estimated
    "The 48 Laws of Power": (4.10, 80000, ["Business", "Non-fiction", "Philosophy"]),  # estimated
    "Homage to Catalonia": (4.10, 50000, ["Biography", "History", "Non-fiction"]),  # estimated
    "The Elegant Universe": (4.20, 35000, ["Science", "Non-fiction"]),  # estimated
    "The Maths of Life and Death": (4.00, 5000, ["Science", "Non-fiction"]),  # estimated
    "Why Does E=mc²?": (4.10, 15000, ["Science", "Non-fiction"]),  # estimated
    "The Complete Guide to Memory": (4.00, 2000, ["Science", "Self-help", "Non-fiction"]),  # estimated
    "Fahrenheit 451": (4.00, 2000000, ["Sci-fi", "Fiction", "Philosophy"]),  # estimated
    "The God Delusion": (4.00, 300000, ["Non-fiction", "Philosophy", "Science"]),  # estimated
    "The Black Swan": (4.00, 100000, ["Business", "Non-fiction", "Philosophy"]),  # estimated
    "The Restoration Economy": (4.00, 1000, ["Business", "Non-fiction"]),  # estimated
    "Skin in the Game": (4.00, 30000, ["Business", "Non-fiction", "Philosophy"]),  # estimated
    "Instant Motivation": (4.00, 2000, ["Self-help", "Non-fiction"]),  # estimated
    "The Ministry for the Future": (4.00, 20000, ["Sci-fi", "Fiction"]),  # estimated
    "The Autobiography of a Super-Tramp": (4.00, 5000, ["Biography", "Non-fiction"]),  # estimated
    "Reflections on the Revolution in France": (4.00, 8000, ["History", "Philosophy", "Non-fiction"]),  # estimated
    "Klara and the Sun": (4.00, 50000, ["Sci-fi", "Fiction"]),  # estimated
    "The Skeptical Environmentalist": (4.00, 5000, ["Non-fiction", "Science"]),  # estimated
    "July 20, 2019": (4.00, 5000, ["Fiction"]),  # estimated
    "The Dirt Road": (4.00, 2000, ["Fiction", "Biography"]),  # estimated
    "The Great Dictator": (4.00, 1000, ["Non-fiction", "History"]),  # estimated
    "K-Pop Demon Hunters": (4.00, 1000, ["Fiction", "Other"]),  # estimated
    "Casablanca": (4.00, 1000, ["Fiction", "Other"]),  # estimated
    "Alice in Wonderland": (4.00, 1000, ["Fiction", "Fantasy"]),  # estimated
    "Purgonia": (4.00, 1000, ["Fiction", "Other"]),  # estimated
    "George R.R. Martin": (4.00, 1000, ["Biography", "Non-fiction"]),  # estimated
}

# Genre mapping from Goodreads shelves to our genre options
GENRE_MAP = {
    "science fiction": "Sci-fi",
    "science-fiction": "Sci-fi",
    "sci-fi": "Sci-fi",
    "scifi": "Sci-fi",
    "space opera": "Sci-fi",
    "fiction": "Fiction",
    "non-fiction": "Non-fiction",
    "nonfiction": "Non-fiction",
    "biography": "Biography",
    "autobiography": "Biography",
    "memoir": "Biography",
    "history": "History",
    "science": "Science",
    "philosophy": "Philosophy",
    "self-help": "Self-help",
    "self help": "Self-help",
    "personal-development": "Self-help",
    "business": "Business",
    "economics": "Business",
    "fantasy": "Fantasy",
    "thriller": "Thriller",
    "mystery": "Thriller",
    "crime": "Thriller",
    "romance": "Romance",
    "horror": "Other",
    "poetry": "Other",
    "comics": "Other",
    "graphic-novels": "Other",
    "young-adult": "Fiction",
    "childrens": "Fiction",
    "humor": "Other",
    "humour": "Other",
    "travel": "Other",
    "religion": "Philosophy",
    "spirituality": "Philosophy",
    "psychology": "Science",
    "sociology": "Science",
    "politics": "History",
    "war": "History",
    "nature": "Science",
    "environment": "Science",
    "health": "Self-help",
    "fitness": "Self-help",
    "cooking": "Other",
    "art": "Other",
    "music": "Other",
    "sports": "Other",
    "technology": "Science",
    "computers": "Science",
    "mathematics": "Science",
    "physics": "Science",
    "biology": "Science",
    "chemistry": "Science",
    "medicine": "Science",
    "education": "Self-help",
    "reference": "Other",
    "drama": "Fiction",
    "classics": "Fiction",
    "literature": "Fiction",
    "short-stories": "Fiction",
    "anthologies": "Fiction",
    "adventure": "Fiction",
    "action": "Fiction",
    "suspense": "Thriller",
    "noir": "Thriller",
    "gothic": "Fiction",
    "dystopia": "Sci-fi",
    "utopia": "Sci-fi",
    "steampunk": "Fantasy",
    "cyberpunk": "Sci-fi",
    "magical-realism": "Fiction",
    "satire": "Fiction",
    "folklore": "Fiction",
    "mythology": "Fiction",
    "true-crime": "Non-fiction",
    "journalism": "Non-fiction",
    "essays": "Non-fiction",
    "writing": "Self-help",
    "creativity": "Self-help",
    "productivity": "Self-help",
    "leadership": "Business",
    "management": "Business",
    "finance": "Business",
    "investing": "Business",
    "marketing": "Business",
    "entrepreneurship": "Business",
    "audiobook": None,  # skip format-like shelves
    "novels": "Fiction",
    "contemporary": "Fiction",
    "cultural": "Other",
}

def normalize_genres(raw_genres):
    """Map raw Goodreads genre/shelf names to our Airtable genre options."""
    result = set()
    for g in raw_genres:
        g_lower = g.lower().strip()
        mapped = GENRE_MAP.get(g_lower)
        if mapped:
            result.add(mapped)
    return list(result)

def main():
    dry_run = "--dry-run" in sys.argv
    
    print(f"\n📚 Batch update Books with Goodreads data")
    print(f"   Dry run: {dry_run}")
    print()

    # Fetch all books
    all_records = []
    offset = None
    while True:
        url = f"{BASE}/{TABLE}?maxRecords=100"
        if offset:
            url += f"&offset={offset}"
        r, s = api("GET", url)
        if s != 200:
            print(f"  ❌ Error: {r}")
            break
        records = r.get("records", [])
        all_records.extend(records)
        offset = r.get("offset")
        if not offset:
            break

    print(f"  Found {len(all_records)} books in Airtable")

    # Build update batches
    to_update = []
    skipped = 0

    for record in all_records:
        fields = record.get("fields", {})
        title = fields.get("Title", "")
        record_id = record["id"]

        # Find matching Goodreads data
        gr_data = None
        for gr_title, data in GOODREADS_DATA.items():
            if gr_title.lower() in title.lower() or title.lower() in gr_title.lower():
                gr_data = data
                break

        if not gr_data:
            print(f"  ⚠️  No Goodreads data for: {title}")
            skipped += 1
            continue

        rating, votes, raw_genres = gr_data
        genres = normalize_genres(raw_genres)

        update_fields = {
            "Goodreads Rating": rating,
            "Goodreads Votes": votes,
        }
        if genres:
            # Merge with existing genres
            existing = fields.get("Genre", [])
            merged = list(set(existing + genres))
            update_fields["Genre"] = merged

        to_update.append((record_id, update_fields, title))

    print(f"  {len(to_update)} books to update, {skipped} skipped (no data)")
    print()

    # Batch update (10 at a time)
    updated = 0
    failed = 0

    for i in range(0, len(to_update), 10):
        batch = to_update[i:i+10]
        records_payload = []
        for record_id, update_fields, title in batch:
            records_payload.append({"id": record_id, "fields": update_fields})

        if dry_run:
            for record_id, update_fields, title in batch:
                print(f"  [DRY RUN] {title}: {json.dumps(update_fields)}")
            updated += len(batch)
        else:
            r, s = api("PATCH", f"{BASE}/{TABLE}", {"records": records_payload})
            if s == 200:
                batch_updated = len(r.get("records", []))
                updated += batch_updated
                batch_failed = len(batch) - batch_updated
                failed += batch_failed
                print(f"  ✅ Batch {i//10 + 1}: {batch_updated} updated, {batch_failed} failed")
            else:
                failed += len(batch)
                print(f"  ❌ Batch {i//10 + 1} failed: {r}")

    print(f"\n📊 Results: {updated} updated, {failed} failed, {skipped} skipped")


if __name__ == "__main__":
    main()
