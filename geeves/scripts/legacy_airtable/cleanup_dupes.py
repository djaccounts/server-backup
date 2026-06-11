import json, urllib.request, os, subprocess

def get_key():
    r = subprocess.run(['grep', 'AIRTABLE_API_KEY', os.path.expanduser('~/.hermes/.env')], capture_output=True, text=True)
    return r.stdout.strip().split('\n')[0].split('=', 1)[1]

key = get_key()
base = 'appzvmonQXs4x2AlL'
table = 'tblNsgbYHNK8xWnB7'

# Get ALL ingredients for this recipe
url = f'https://api.airtable.com/v0/{base}/{table}?maxRecords=100'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

target = 'recbJwbPquOjc3vIg'
to_delete = []
for r in data.get('records', []):
    f = r['fields']
    recipe_links = f.get('Recipe', [])
    if target in recipe_links:
        to_delete.append(r['id'])

print(f"Found {len(to_delete)} ingredient records to delete")

# Delete in batches of 10
for rid in to_delete:
    req = urllib.request.Request(
        f'https://api.airtable.com/v0/{base}/{table}/{rid}',
        headers={'Authorization': f'Bearer {key}'},
        method='DELETE',
    )
    try:
        urllib.request.urlopen(req)
        print(f"  🗑️  Deleted {rid}")
    except Exception as e:
        print(f"  ❌ Failed to delete {rid}: {e}")

print("Done")
