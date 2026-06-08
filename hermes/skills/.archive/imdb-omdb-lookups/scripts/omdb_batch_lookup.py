# OMDb Batch Rating Lookup

Write to `/tmp/omdb_ratings.py` via terminal heredoc, then run with `python3 /tmp/omdb_ratings.py`.

Set ODB_KEY to your OMDb API key. Films is a list of (title, year) tuples.

```python
import subprocess, json, os

OMDB_KEY = os.environ.get("OMDB_KEY", "YOUR_KEY_HERE")

films = [
    ("Film Title", "Year"),
]

results = []
for title, year in films:
    url = f"http://www.omdbapi.com/?t={title.replace(' ', '+')}&y={year}&apikey={OMDB_KEY}"
    r = subprocess.run(["curl", "-s", url], capture_output=True, text=True, timeout=10)
    d = json.loads(r.stdout)
    if d.get("Response") == "True":
        t = d.get("Title", title)
        y = d.get("Year", year)
        rt = d.get("imdbRating", "N/A")
        v = d.get("imdbVotes", "N/A")
        g = d.get("Genre", "")
        results.append((t, y, rt, v, g))

def sort_key(r):
    try:
        return -float(r[2])
    except:
        return 1

results.sort(key=sort_key)

print(f"{'Film':<45} {'Year':<6} {'IMDb':<8} {'Votes':<15} Genres")
print("-" * 100)
for t, y, rt, v, g in results:
    try:
        ok = " 8+ YES!" if float(rt) >= 8.0 else ""
    except:
        ok = ""
    print(f"{t:<45} {y:<6} {rt:<8} {v:<15} {g}{ok}")
```
