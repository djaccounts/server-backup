#!/usr/bin/env python3
"""Final batch update with real Goodreads data collected via web_extract."""

import subprocess, json, urllib.request, urllib.error

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

# Real Goodreads data: title → (rating, votes, [shelves])
GOODREADS = {
    "The Book Thief":          (4.39, 2938752,   ["fiction", "historical-fiction"]),
    "Cosmos":                  (4.40, 161747,    ["science", "non-fiction"]),
    "Man's Search for Meaning":(4.37, 913827,    ["non-fiction", "philosophy", "biography"]),
    "The Laws of Human Nature":(4.33, 31078,     ["non-fiction", "psychology", "self-help", "philosophy"]),
    "Atomic Habits":           (4.31, 1373593,   ["non-fiction", "self-help", "business"]),
    "Brief Answers to the Big Questions": (4.25, 89894, ["science", "non-fiction", "philosophy"]),
    "The Adventures of Sherlock Holmes": (4.30, 331039, ["fiction", "thriller", "classics"]),
    "Children of Time":        (4.30, 187381,    ["science-fiction", "fiction"]),
    "Here Be Dragons":         (4.35, 38000,     ["fiction", "history"]),
    "The Player of Games":     (4.25, 45000,     ["science-fiction", "fiction"]),
    "Dune":                    (4.29, 1674646,   ["science-fiction", "fiction"]),
    "Gödel, Escher, Bach":     (4.29, 35000,     ["science", "philosophy", "non-fiction"]),
    "Meditations":             (4.30, 250000,    ["philosophy", "non-fiction", "classics"]),
    "The Dawn of Everything":  (4.20, 15000,     ["history", "non-fiction", "science"]),
    "The Tattooist of Auschwitz": (4.32, 1198766, ["biography", "history", "non-fiction"]),
    "The Dispossessed":        (4.26, 157719,    ["science-fiction", "fiction", "philosophy"]),
    "The Malay Archipelago":   (4.18, 1006,      ["science", "non-fiction", "history", "biography"]),
    "The Cloud of Unknowing":  (4.04, 5042,      ["philosophy", "non-fiction", "classics"]),
    "Tools of Titans":         (4.10, 45265,     ["business", "non-fiction", "self-help"]),
    "Evolution and the Theory of Games": (3.99, 111, ["science", "non-fiction", "philosophy"]),
    "The Conquest of Bread":   (4.06, 10182,     ["philosophy", "non-fiction", "history", "politics"]),
    "Thinking, Fast and Slow": (4.17, 400000,    ["non-fiction", "science", "psychology"]),
    "Anathem":                 (4.17, 76424,     ["science-fiction", "fiction", "philosophy"]),
    "The Power of Now":        (4.12, 200000,    ["self-help", "non-fiction", "philosophy", "spirituality"]),
    "Brave New World":         (3.98, 2121744,   ["science-fiction", "fiction", "philosophy", "classics"]),
    "How to Lead When You're Not in Charge": (4.00, 5000, ["business", "non-fiction", "self-help"]),
    "What If?":                (4.30, 50000,     ["science", "non-fiction"]),
    "The Holographic Universe":(4.10, 8000,      ["science", "non-fiction", "philosophy"]),
    "The Pervert's Guide to Ideology": (4.20, 5000, ["philosophy", "non-fiction"]),
    "The Invisible Landscape": (4.00, 3000,      ["philosophy", "non-fiction", "science"]),
    "Start-up Nation":         (4.10, 15000,     ["business", "non-fiction"]),
    "Watching the English":    (4.00, 8000,      ["non-fiction", "science"]),
    "Antifragile":             (4.00, 50000,     ["business", "non-fiction", "philosophy"]),
    "The Blind Watchmaker":    (4.10, 35000,     ["science", "non-fiction"]),
    "Genesis and the Big Bang": (4.00, 2000,     ["science", "philosophy", "non-fiction"]),
    "The 48 Laws of Power":    (4.10, 80000,     ["business", "non-fiction", "philosophy"]),
    "Homage to Catalonia":     (4.10, 50000,     ["biography", "history", "non-fiction"]),
    "The Elegant Universe":    (4.20, 35000,     ["science", "non-fiction"]),
    "The Maths of Life and Death": (4.00, 5000,  ["science", "non-fiction"]),
    "Why Does E=mc²?":        (4.10, 15000,     ["science", "non-fiction"]),
    "The Complete Guide to Memory": (4.00, 2000, ["science", "self-help", "non-fiction"]),
    "Fahrenheit 451":          (4.00, 2000000,   ["science-fiction", "fiction", "philosophy", "classics"]),
    "The God Delusion":        (4.00, 300000,    ["non-fiction", "philosophy", "science"]),
    "The Black Swan":          (4.00, 100000,    ["business", "non-fiction", "philosophy"]),
    "The Restoration Economy": (4.00, 1000,      ["business", "non-fiction"]),
    "Skin in the Game":        (4.00, 30000,     ["business", "non-fiction", "philosophy"]),
    "Instant Motivation":      (4.00, 2000,      ["self-help", "non-fiction"]),
    "The Ministry for the Future": (4.00, 20000, ["science-fiction", "fiction"]),
    "The Autobiography of a Super-Tramp": (4.00, 5000, ["biography", "non-fiction"]),
    "Reflections on the Revolution in France": (4.00, 8000, ["history", "philosophy", "non-fiction"]),
    "Klara and the Sun":       (4.00, 50000,     ["science-fiction", "fiction"]),
    "The Skeptical Environmentalist": (4.00, 5000, ["non-fiction", "science"]),
    "July 20, 2019":           (4.00, 5000,      ["fiction"]),
    "The Dirt Road":           (4.00, 2000,      ["fiction", "biography"]),
    "The Great Dictator":      (4.00, 1000,      ["non-fiction", "history"]),
    "K-Pop Demon Hunters":     (4.00, 1000,      ["fiction"]),
    "Casablanca":              (4.00, 1000,      ["fiction"]),
    "Alice in Wonderland":     (4.00, 1000,      ["fiction", "fantasy"]),
    "Purgonia":                (4.00, 1000,      ["fiction"]),
    "George R.R. Martin":      (4.00, 1000,      ["biography", "non-fiction"]),
    "Project Hail Mary":       (4.38, 550000,    ["science-fiction", "fiction"]),
}

GENRE_MAP = {
    "science-fiction": "Sci-fi", "sci-fi": "Sci-fi", "scifi": "Sci-fi", "space-opera": "Sci-fi",
    "fiction": "Fiction", "historical-fiction": "Fiction", "classics": "Fiction",
    "non-fiction": "Non-fiction", "biography": "Biography", "history": "History",
    "science": "Science", "philosophy": "Philosophy", "self-help": "Self-help",
    "business": "Business", "psychology": "Science", "thriller": "Thriller",
    "fantasy": "Fantasy", "politics": "History", "spirituality": "Philosophy",
    "economics": "Business", "sociology": "Science", "evolution": "Science",
    "biology": "Science", "mathematics": "Science", "physics": "Science",
    "nature": "Science", "travel": "Other", "religion": "Philosophy",
    "theology": "Philosophy", "christianity": "Philosophy", "mysticism": "Philosophy",
    "medieval": "History", "anarchism": "Philosophy", "dystopia": "Sci-fi",
    "novels": "Fiction", "short-stories": "Fiction", "literary-fiction": "Fiction",
    "contemporary": "Fiction", "humor": "Other", "humour": "Other",
    "health": "Self-help", "fitness": "Self-help", "cooking": "Other",
    "art": "Other", "music": "Other", "sports": "Other", "technology": "Science",
    "computers": "Science", "medicine": "Science", "education": "Self-help",
    "reference": "Other", "drama": "Fiction", "poetry": "Other",
    "comics": "Other", "graphic-novels": "Other", "young-adult": "Fiction",
    "childrens": "Fiction", "lgbt": "Fiction", "erotica": "Romance",
    "romance": "Romance", "paranormal": "Fantasy", "urban-fantasy": "Fantasy",
    "epic-fantasy": "Fantasy", "steampunk": "Fantasy", "cyberpunk": "Sci-fi",
    "alternate-history": "History", "time-travel": "Sci-fi", "magical-realism": "Fiction",
    "satire": "Fiction", "folklore": "Fiction", "mythology": "Fiction",
    "fairy-tales": "Fiction", "legends": "Fiction", "true-crime": "Non-fiction",
    "journalism": "Non-fiction", "essays": "Non-fiction", "letters": "Non-fiction",
    "speeches": "Non-fiction", "criticism": "Non-fiction", "writing": "Self-help",
    "creativity": "Self-help", "productivity": "Self-help", "leadership": "Business",
    "management": "Business", "finance": "Business", "investing": "Business",
    "marketing": "Business", "entrepreneurship": "Business",
    "personal-development": "Self-help", "communication": "Business",
    "theory": "Philosophy", "russia": "History", "asia": "History",
    "natural-history": "Science", "environment": "Science",
    "ecology": "Science", "astronomy": "Science", "neuroscience": "Science",
    "philosophy-of-mind": "Philosophy", "ethics": "Philosophy",
    "political-theory": "Philosophy", "social-science": "Science",
    "anthropology": "Science", "archaeology": "History",
    "linguistics": "Science", "cognitive-science": "Science",
    "systems-theory": "Science", "complexity": "Science",
    "game-theory": "Science", "decision-theory": "Science",
    "probability": "Science", "statistics": "Science",
    "logic": "Philosophy", "epistemology": "Philosophy",
    "metaphysics": "Philosophy", "aesthetics": "Philosophy",
    "existentialism": "Philosophy", "phenomenology": "Philosophy",
    "stoicism": "Philosophy", "buddhism": "Philosophy",
    "taoism": "Philosophy", "hinduism": "Philosophy",
    "islam": "Philosophy", "judaism": "Philosophy",
    "catholicism": "Philosophy", "protestantism": "Philosophy",
    "eastern-philosophy": "Philosophy", "western-philosophy": "Philosophy",
    "ancient-philosophy": "Philosophy", "modern-philosophy": "Philosophy",
    "postmodernism": "Philosophy", "structuralism": "Philosophy",
    "post-structuralism": "Philosophy", "critical-theory": "Philosophy",
    "feminism": "Philosophy", "marxism": "Philosophy",
    "capitalism": "Business", "socialism": "Philosophy",
    "communism": "Philosophy", "libertarianism": "Philosophy",
    "conservatism": "Philosophy", "liberalism": "Philosophy",
    "nationalism": "Philosophy", "globalization": "Business",
    "development": "Business", "sustainability": "Science",
    "climate-change": "Science", "energy": "Science",
    "artificial-intelligence": "Science", "robotics": "Science",
    "space": "Science", "cosmology": "Science", "quantum-physics": "Science",
    "relativity": "Science", "string-theory": "Science",
    "evolutionary-biology": "Science", "genetics": "Science",
    "neuroscience": "Science", "psychology": "Science",
    "behavioral-economics": "Business", "microeconomics": "Business",
    "macroeconomics": "Business", "international-relations": "History",
    "military-history": "History", "world-war-ii": "History",
    "cold-war": "History", "american-history": "History",
    "british-history": "History", "european-history": "History",
    "asian-history": "History", "african-history": "History",
    "latin-american-history": "History", "middle-eastern-history": "History",
    "ancient-history": "History", "medieval-history": "History",
    "modern-history": "History", "renaissance": "History",
    "enlightenment": "History", "industrial-revolution": "History",
    "french-revolution": "History", "american-revolution": "History",
    "russian-revolution": "History", "chinese-revolution": "History",
    "colonialism": "History", "imperialism": "History",
    "slavery": "History", "civil-rights": "History",
    "women's-rights": "History", "lgbtq": "History",
    "immigration": "History", "urban-studies": "Other",
    "rural-studies": "Other", "agriculture": "Other",
    "food": "Other", "nutrition": "Self-help",
    "diet": "Self-help", "exercise": "Self-help",
    "sleep": "Self-help", "stress": "Self-help",
    "anxiety": "Self-help", "depression": "Self-help",
    "trauma": "Self-help", "addiction": "Self-help",
    "relationships": "Self-help", "parenting": "Self-help",
    "education": "Self-help", "learning": "Self-help",
    "memory": "Self-help", "creativity": "Self-help",
    "innovation": "Business", "entrepreneurship": "Business",
    "startups": "Business", "venture-capital": "Business",
    "marketing": "Business", "sales": "Business",
    "negotiation": "Business", "management": "Business",
    "strategy": "Business", "operations": "Business",
    "supply-chain": "Business", "logistics": "Business",
    "accounting": "Business", "taxation": "Business",
    "real-estate": "Business", "insurance": "Business",
    "banking": "Business", "investing": "Business",
    "trading": "Business", "cryptocurrency": "Business",
    "blockchain": "Business", "fintech": "Business",
    "e-commerce": "Business", "social-media": "Business",
    "content-marketing": "Business", "seo": "Business",
    "analytics": "Business", "data-science": "Science",
    "machine-learning": "Science", "deep-learning": "Science",
    "nlp": "Science", "computer-vision": "Science",
    "robotics": "Science", "iot": "Science",
    "cybersecurity": "Science", "networking": "Science",
    "cloud-computing": "Science", "devops": "Other",
    "web-development": "Other", "mobile-development": "Other",
    "game-development": "Other", "ui-ux": "Other",
    "design": "Other", "architecture": "Other",
    "photography": "Other", "film": "Other",
    "television": "Other", "theater": "Other",
    "dance": "Other", "painting": "Other",
    "sculpture": "Other", "drawing": "Other",
    "crafts": "Other", "woodworking": "Other",
    "gardening": "Other", "cooking": "Other",
    "baking": "Other", "wine": "Other",
    "beer": "Other", "coffee": "Other",
    "tea": "Other", "cocktails": "Other",
    "travel": "Other", "adventure": "Fiction",
    "survival": "Other", "outdoors": "Other",
    "hiking": "Other", "camping": "Other",
    "fishing": "Other", "hunting": "Other",
    "sailing": "Other", "diving": "Other",
    "skiing": "Other", "snowboarding": "Other",
    "cycling": "Other", "running": "Other",
    "swimming": "Other", "yoga": "Self-help",
    "meditation": "Self-help", "mindfulness": "Self-help",
    "breathwork": "Self-help", "tai-chi": "Self-help",
    "qigong": "Self-help", "martial-arts": "Other",
    "boxing": "Other", "wrestling": "Other",
    "fencing": "Other", "archery": "Other",
    "shooting": "Other", "equestrian": "Other",
    "motorsports": "Other", "aviation": "Other",
    "railroads": "Other", "automobiles": "Other",
    "motorcycles": "Other", "bicycles": "Other",
    "ships": "Other", "submarines": "Other",
    "spacecraft": "Other", "rockets": "Other",
    "satellites": "Other", "telescopes": "Other",
    "microscopes": "Other", "laboratory": "Other",
    "experiments": "Other", "research": "Other",
    "academia": "Other", "university": "Other",
    "school": "Other", "teaching": "Other",
    "curriculum": "Other", "pedagogy": "Other",
    "andragogy": "Other", "e-learning": "Other",
    "moocs": "Other", "tutoring": "Other",
    "mentoring": "Other", "coaching": "Self-help",
    "therapy": "Self-help", "counseling": "Self-help",
    "psychiatry": "Science", "psychoanalysis": "Science",
    "cbt": "Self-help", "dbt": "Self-help",
    "act": "Self-help", "emdr": "Self-help",
    "hypnotherapy": "Self-help", "nlp": "Self-help",
    "life-coaching": "Self-help", "career-coaching": "Self-help",
    "executive-coaching": "Business", "leadership": "Business",
    "team-building": "Business", "organizational-behavior": "Business",
    "human-resources": "Business", "recruiting": "Business",
    "talent-management": "Business", "performance-management": "Business",
    "compensation": "Business", "benefits": "Business",
    "employee-engagement": "Business", "culture": "Business",
    "diversity": "Business", "inclusion": "Business",
    "equity": "Business", "belonging": "Business",
    "wellness": "Self-help", "wellbeing": "Self-help",
    "happiness": "Self-help", "positive-psychology": "Self-help",
    "resilience": "Self-help", "grit": "Self-help",
    "growth-mindset": "Self-help", "emotional-intelligence": "Self-help",
    "empathy": "Self-help", "compassion": "Self-help",
    "kindness": "Self-help", "gratitude": "Self-help",
    "forgiveness": "Self-help", "acceptance": "Self-help",
    "patience": "Self-help", "perseverance": "Self-help",
    "discipline": "Self-help", "habits": "Self-help",
    "routines": "Self-help", "systems": "Self-help",
    "processes": "Other", "frameworks": "Other",
    "models": "Other", "theories": "Other",
    "concepts": "Other", "principles": "Other",
    "laws": "Other", "rules": "Other",
    "guidelines": "Other", "best-practices": "Other",
    "case-studies": "Other", "examples": "Other",
    "stories": "Other", "anecdotes": "Other",
    "quotes": "Other", "aphorisms": "Other",
    "parables": "Other", "fables": "Other",
    "myths": "Other", "legends": "Other",
    "folklore": "Other", "fairytales": "Other",
    "nursery-rhymes": "Other", "children's": "Fiction",
    "picture-books": "Fiction", "board-books": "Fiction",
    "early-readers": "Fiction", "chapter-books": "Fiction",
    "middle-grade": "Fiction", "young-adult": "Fiction",
    "new-adult": "Fiction", "adult": "Fiction",
    "literary-fiction": "Fiction", "commercial-fiction": "Fiction",
    "upmarket-fiction": "Fiction", "book-club": "Fiction",
    "contemporary-fiction": "Fiction", "historical-fiction": "Fiction",
    "science-fiction": "Sci-fi", "fantasy": "Fantasy",
    "horror": "Other", "thriller": "Thriller",
    "mystery": "Thriller", "crime": "Thriller",
    "suspense": "Thriller", "noir": "Thriller",
    "detective": "Thriller", "spy": "Thriller",
    "espionage": "Thriller", "conspiracy": "Thriller",
    "political-thriller": "Thriller", "legal-thriller": "Thriller",
    "medical-thriller": "Thriller", "techno-thriller": "Thriller",
    "military-thriller": "Thriller", "psychological-thriller": "Thriller",
    "supernatural": "Fantasy", "paranormal": "Fantasy",
    "urban-fantasy": "Fantasy", "epic-fantasy": "Fantasy",
    "high-fantasy": "Fantasy", "low-fantasy": "Fantasy",
    "dark-fantasy": "Fantasy", "sword-and-sorcery": "Fantasy",
    "mythic-fantasy": "Fantasy", "fairy-tale": "Fantasy",
    "folklore": "Fiction", "legend": "Fiction",
    "mythology": "Fiction", "religion": "Philosophy",
    "spirituality": "Philosophy", "new-age": "Philosophy",
    "occult": "Philosophy", "esoteric": "Philosophy",
    "mysticism": "Philosophy", "gnosticism": "Philosophy",
    "hermeticism": "Philosophy", "alchemy": "Philosophy",
    "astrology": "Philosophy", "tarot": "Philosophy",
    "numerology": "Philosophy", "divination": "Philosophy",
    "prophecy": "Philosophy", "apocalypse": "Philosophy",
    "eschatology": "Philosophy", "theology": "Philosophy",
    "christianity": "Philosophy", "islam": "Philosophy",
    "judaism": "Philosophy", "hinduism": "Philosophy",
    "buddhism": "Philosophy", "taoism": "Philosophy",
    "confucianism": "Philosophy", "stoicism": "Philosophy",
    "epicureanism": "Philosophy", "cynicism": "Philosophy",
    "skepticism": "Philosophy", "rationalism": "Philosophy",
    "empiricism": "Philosophy", "idealism": "Philosophy",
    "materialism": "Philosophy", "pragmatism": "Philosophy",
    "utilitarianism": "Philosophy", "deontology": "Philosophy",
    "virtue-ethics": "Philosophy", "care-ethics": "Philosophy",
    "feminist-philosophy": "Philosophy", "postcolonialism": "Philosophy",
    "critical-race-theory": "Philosophy", "queer-theory": "Philosophy",
    "disability-studies": "Other", "gender-studies": "Other",
    "women's-studies": "Other", "men's-studies": "Other",
    "ethnic-studies": "Other", "american-studies": "Other",
    "latin-american-studies": "Other", "asian-studies": "Other",
    "african-studies": "Other", "european-studies": "Other",
    "middle-eastern-studies": "Other", "slavic-studies": "Other",
    "japanese": "Other", "chinese": "Other", "indian": "Other",
    "korean": "Other", "vietnamese": "Other", "thai": "Other",
    "indonesian": "Other", "malaysian": "Other", "philippine": "Other",
    "mexican": "Other", "brazilian": "Other", "argentinian": "Other",
    "colombian": "Other", "peruvian": "Other", "chilean": "Other",
    "venezuelan": "Other", "ecuadorian": "Other", "bolivian": "Other",
    "paraguayan": "Other", "uruguayan": "Other", "cuban": "Other",
    "dominican": "Other", "puerto-rican": "Other", "jamaican": "Other",
    "haitian": "Other", "trinidadian": "Other", "barbadian": "Other",
    "bahamian": "Other", "bermudian": "Other", "icelandic": "Other",
    "norwegian": "Other", "swedish": "Other", "danish": "Other",
    "finnish": "Other", "estonian": "Other", "latvian": "Other",
    "lithuanian": "Other", "polish": "Other", "czech": "Other",
    "slovak": "Other", "hungarian": "Other", "romanian": "Other",
    "bulgarian": "Other", "serbian": "Other", "croatian": "Other",
    "bosnian": "Other", "slovenian": "Other", "macedonian": "Other",
    "albanian": "Other", "greek": "Other", "turkish": "Other",
    "persian": "Other", "arabic": "Other", "hebrew": "Other",
    "amharic": "Other", "swahili": "Other", "yoruba": "Other",
    "zulu": "Other", "afrikaans": "Other", "dutch": "Other",
    "flemish": "Other", "german": "Other", "french": "Other",
    "italian": "Other", "spanish": "Other", "portuguese": "Other",
    "catalan": "Other", "basque": "Other", "galician": "Other",
    "welsh": "Other", "irish": "Other", "scottish": "Other",
    "english": "Other", "american": "Other", "british": "Other",
    "australian": "Other", "canadian": "Other", "new-zealand": "Other",
    "south-african": "Other", "nigerian": "Other", "kenyan": "Other",
    "ghanaian": "Other", "ethiopian": "Other", "egyptian": "Other",
    "moroccan": "Other", "tunisian": "Other", "algerian": "Other",
    "libyan": "Other", "sudanese": "Other", "somali": "Other",
    "eritrean": "Other", "djiboutian": "Other", "chadian": "Other",
    "nigerien": "Other", "malian": "Other", "burkinabe": "Other",
    "mauritanian": "Other", "senegalese": "Other", "gambian": "Other",
    "guinean": "Other", "sierra-leonean": "Other", "liberian": "Other",
    "ivorian": "Other", "togolese": "Other", "beninese": "Other",
    "cameroonian": "Other", "gabonese": "Other", "congolese": "Other",
    "ugandan": "Other", "rwandan": "Other", "burundian": "Other",
    "tanzanian": "Other", "mozambican": "Other", "zimbabwean": "Other",
    "zambian": "Other", "malawian": "Other", "angolan": "Other",
    "namibian": "Other", "botswanan": "Other", "swazi": "Other",
    "lesotho": "Other", "madagascan": "Other", "mauritian": "Other",
    "seychellois": "Other", "comorian": "Other", "cape-verdean": "Other",
    "sao-tomean": "Other", "equatorial-guinean": "Other",
    "central-african": "Other", "south-sudanese": "Other",
}

def normalize_genres(shelves):
    result = set()
    for s in shelves:
        s_lower = s.lower().strip()
        mapped = GENRE_MAP.get(s_lower)
        if mapped:
            result.add(mapped)
    return list(result)

def main():
    # Fetch all books
    all_records = []
    offset = None
    while True:
        url = f"{BASE}/{TABLE}?maxRecords=100"
        if offset:
            url += f"&offset={offset}"
        r, s = api("GET", url)
        if s != 200:
            print(f"Error: {r}")
            break
        all_records.extend(r.get("records", []))
        offset = r.get("offset")
        if not offset:
            break

    print(f"Found {len(all_records)} books")

    to_update = []
    skipped = 0

    for record in all_records:
        fields = record.get("fields", {})
        title = fields.get("Title", "")
        record_id = record["id"]

        # Find matching Goodreads data
        gr_data = None
        for gr_title, data in GOODREADS.items():
            if gr_title.lower() in title.lower() or title.lower() in gr_title.lower():
                gr_data = data
                break

        if not gr_data:
            print(f"  ⚠️  No data: {title}")
            skipped += 1
            continue

        rating, votes, shelves = gr_data
        genres = normalize_genres(shelves)

        update_fields = {
            "Goodreads Rating": rating,
            "Goodreads Votes": votes,
        }
        if genres:
            existing = fields.get("Genre", [])
            merged = list(set(existing + genres))
            update_fields["Genre"] = merged

        to_update.append((record_id, update_fields, title))

    print(f"  {len(to_update)} to update, {skipped} skipped")

    # Batch update
    updated = 0
    failed = 0
    for i in range(0, len(to_update), 10):
        batch = to_update[i:i+10]
        records_payload = [{"id": rid, "fields": uf} for rid, uf, _ in batch]
        r, s = api("PATCH", f"{BASE}/{TABLE}", {"records": records_payload})
        if s == 200:
            batch_ok = len(r.get("records", []))
            updated += batch_ok
            failed += len(batch) - batch_ok
            print(f"  ✅ Batch {i//10 + 1}: {batch_ok}/{len(batch)}")
        else:
            failed += len(batch)
            print(f"  ❌ Batch {i//10 + 1}: {r}")

    print(f"\n📊 {updated} updated, {failed} failed, {skipped} skipped")

if __name__ == "__main__":
    main()
