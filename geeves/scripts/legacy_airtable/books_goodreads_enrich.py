#!/usr/bin/env python3
"""
books_goodreads_enrich.py — Fetch Goodreads rating, votes, and genre for books in the Geeves Airtable base.

Uses Goodreads search + page scraping (API deprecated 2020).
Updates each book record with:
  - Goodreads Rating (avg rating, e.g. 4.23)
  - Goodreads Votes (number of ratings)
  - Genre (maps Goodreads shelves to our genre list)

Usage:
    python3 books_goodreads_enrich.py              # enrich all Want-to-Read books
    python3 books_goodreads_enrich.py --status Read # enrich books with Status=Read
    python3 books_goodreads_enrich.py --dry-run    # preview without writing
    python3 books_goodreads_enrich.py --limit 5    # only process 5 books
"""

import subprocess, json, sys, time, re, urllib.request, urllib.error, urllib.parse, html
from html.parser import HTMLParser

ENV_PATH = "/root/.hermes/.env"
BASE = "appzvmonQXs4x2AlL"
TABLE = "Books"
# Genre mapping: Goodreads shelf name → our Genre select options
GENRE_MAP = {
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
    "business": "Business",
    "economics": "Business",
    "fantasy": "Fantasy",
    "science-fiction": "Sci-fi",
    "sci-fi": "Sci-fi",
    "scifi": "Sci-fi",
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
    "lgbt": "Fiction",
    "erotica": "Romance",
    "paranormal": "Fantasy",
    "urban-fantasy": "Fantasy",
    "epic-fantasy": "Fantasy",
    "historical-fiction": "Fiction",
    "historical": "History",
    "cultural": "Other",
    "media-tie-in": "Other",
    "novels": "Fiction",
    "contemporary": "Fiction",
    "realistic-fiction": "Fiction",
    "suspense": "Thriller",
    "conspiracy": "Thriller",
    "espionage": "Thriller",
    "detective": "Thriller",
    "noir": "Thriller",
    "gothic": "Fiction",
    "dystopia": "Sci-fi",
    "utopia": "Sci-fi",
    "apocalyptic": "Sci-fi",
    "space-opera": "Sci-fi",
    "hard-science-fiction": "Sci-fi",
    "cyberpunk": "Sci-fi",
    "steampunk": "Fantasy",
    "alternate-history": "History",
    "time-travel": "Sci-fi",
    "magical-realism": "Fiction",
    "satire": "Fiction",
    "folklore": "Fiction",
    "mythology": "Fiction",
    "fairy-tales": "Fiction",
    "legends": "Fiction",
    "true-crime": "Non-fiction",
    "journalism": "Non-fiction",
    "essays": "Non-fiction",
    "letters": "Non-fiction",
    "speeches": "Non-fiction",
    "criticism": "Non-fiction",
    "literary-criticism": "Non-fiction",
    "writing": "Self-help",
    "creativity": "Self-help",
    "productivity": "Self-help",
    "leadership": "Business",
    "management": "Business",
    "finance": "Business",
    "investing": "Business",
    "marketing": "Business",
    "entrepreneurship": "Business",
    "biographical": "Biography",
    "autobiographical": "Biography",
}


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


def fetch_books(status_filter=None):
    """Fetch all book records from Airtable."""
    all_records = []
    offset = None
    while True:
        url = f"{BASE}/{TABLE}?maxRecords=100"
        if status_filter:
            url += f"&filterByFormula={{Status}}='{status_filter}'"
        if offset:
            url += f"&offset={offset}"
        r, s = api("GET", url)
        if s != 200:
            print(f"  ❌ Error fetching books: {r}")
            break
        records = r.get("records", [])
        all_records.extend(records)
        offset = r.get("offset")
        if not offset:
            break
    return all_records


def search_goodreads(title, author):
    """Search Goodreads for a book by title + author. Returns book URL or None."""
    query = urllib.parse.quote(f"{title} {author}")
    url = f"https://www.goodreads.com/search?q={query}&search_type=books"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            page = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None, None, None

    # Find first book result link
    m = re.search(r'href="(/book/show/\d+[^"]*)"', page)
    if not m:
        return None, None, None

    book_path = m.group(1).split("?")[0]
    book_url = f"https://www.goodreads.com{book_path}"
    return scrape_goodreads_page(book_url)


def scrape_goodreads_page(url):
    """Scrape a Goodreads book page for rating, votes, and genres."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            page = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None, None, None

    # Extract rating
    rating = None
    m = re.search(r'"ratingValue":\s*"?([0-9.]+)"?', page)
    if not m:
        m = re.search(r'aria-label="Rating details">.*?([0-9.]+)\s*out of\s*5', page, re.DOTALL)
    if not m:
        m = re.search(r'class="RatingStatistics__rating".*?>([0-9.]+)<', page, re.DOTALL)
    if m:
        try:
            rating = float(m.group(1))
        except ValueError:
            pass

    # Extract number of ratings (votes)
    votes = None
    m = re.search(r'"ratingCount":\s*"?(\d+)"?', page)
    if not m:
        m = re.search(r'([0-9,]+)\s*ratings?', page)
    if m:
        try:
            votes = int(m.group(1).replace(",", ""))
        except ValueError:
            pass

    # Extract genres/shelves
    genres = set()
    # Look for genre links in the page
    shelf_matches = re.findall(r'/genres/([a-z-]+)', page)
    for shelf in shelf_matches:
        shelf_clean = shelf.replace("-", " ").strip()
        mapped = GENRE_MAP.get(shelf, GENRE_MAP.get(shelf_clean))
        if mapped:
            genres.add(mapped)

    # Also look for "shelf" patterns
    shelf_matches2 = re.findall(r'"shelfName":\s*"([^"]+)"', page)
    for shelf in shelf_matches2:
        shelf_lower = shelf.lower().strip()
        mapped = GENRE_MAP.get(shelf_lower)
        if mapped:
            genres.add(mapped)

    return rating, votes, list(genres) if genres else []


def update_book(record_id, fields, dry_run=False):
    """Update a book record in Airtable."""
    if dry_run:
        print(f"    [DRY RUN] Would update: {json.dumps(fields)}")
        return True
    r, s = api("PATCH", f"{BASE}/{TABLE}/{record_id}", {"fields": fields})
    return s == 200


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    status_filter = None
    limit = None

    for i, arg in enumerate(args):
        if arg == "--status" and i + 1 < len(args):
            status_filter = args[i + 1]
        if arg == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])

    print(f"\n📚 Goodreads Enrichment Script")
    print(f"   Status filter: {status_filter or 'All'}")
    print(f"   Dry run: {dry_run}")
    print(f"   Limit: {limit or 'All'}")
    print()

    # Fetch books
    books = fetch_books(status_filter)
    if limit:
        books = books[:limit]

    print(f"Found {len(books)} books to process\n")

    updated = 0
    skipped = 0
    failed = 0

    for i, book in enumerate(books):
        fields = book.get("fields", {})
        title = fields.get("Title", "")
        author = fields.get("Author", "")
        record_id = book["id"]

        # Skip if already has Goodreads data
        if fields.get("Goodreads Rating") and fields.get("Genre"):
            print(f"  [{i+1}/{len(books)}] SKIP (already enriched): {title}")
            skipped += 1
            continue

        print(f"  [{i+1}/{len(books)}] Looking up: {title} by {author}...")

        gr_rating, gr_votes, genres = search_goodreads(title, author)

        update_fields = {}
        if gr_rating:
            update_fields["Goodreads Rating"] = gr_rating
        if gr_votes:
            update_fields["Goodreads Votes"] = gr_votes
        if genres:
            # Merge with existing genres
            existing = fields.get("Genre", [])
            merged = list(set(existing + genres))
            update_fields["Genre"] = merged

        if update_fields:
            success = update_book(record_id, update_fields, dry_run=dry_run)
            if success:
                parts = []
                if gr_rating:
                    parts.append(f"rating={gr_rating}")
                if gr_votes:
                    parts.append(f"votes={gr_votes:,}")
                if genres:
                    parts.append(f"genres={genres}")
                print(f"    ✅ {', '.join(parts)}")
                updated += 1
            else:
                print(f"    ❌ Update failed")
                failed += 1
        else:
            print(f"    ⚠️  No data found on Goodreads")
            skipped += 1

        # Rate limit: be nice to Goodreads
        time.sleep(1.5)

    print(f"\n📊 Results: {updated} updated, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
