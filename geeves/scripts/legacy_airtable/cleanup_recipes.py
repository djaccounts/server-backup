import json, urllib.request, os, subprocess

def get_key():
    r = subprocess.run(['grep', 'AIRTABLE_API_KEY', os.path.expanduser('~/.hermes/.env')], capture_output=True, text=True)
    return r.stdout.strip().split('\n')[0].split('=', 1)[1]

key = get_key()
base = 'appzvmonQXs4x2AlL'
recipes_table = 'tblehBgzRMa2Xucjd'
ingredients_table = 'tblNsgbYHNK8xWnB7'

# Find all recipe records
url = f'https://api.airtable.com/v0/{base}/{recipes_table}?maxRecords=100'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

print("All recipe records:")
for r in data.get('records', []):
    f = r['fields']
    print(f"  {r['id']:20s} {f.get('Name','?'):40s} {f.get('Mealie Slug','')}")

# Delete the duplicate test recipes (keep only the bolognese and the latest blueberry)
# Delete: recpAJgCrt1rIkqtg (blueberry v1, stub), recwc6IWUWpeUP1j1 (blueberry v2, manual), recaArhKb0LSwaRg2 (blueberry v3, jsonld)
# Keep: recbJwbPquOjc3vIg (bolognese), recaArhKb0LSwaRg2 (blueberry v3 — the proper one)
to_delete_recipes = ['recpAJgCrt1rIkqtg', 'recwc6IWUWpeUP1j1']

for rid in to_delete_recipes:
    # First delete linked ingredients
    url2 = f'https://api.airtable.com/v0/{base}/{ingredients_table}?maxRecords=100'
    req2 = urllib.request.Request(url2, headers={'Authorization': f'Bearer {key}'})
    with urllib.request.urlopen(req2) as resp:
        ing_data = json.loads(resp.read())
    for ing in ing_data.get('records', []):
        if rid in ing.get('fields', {}).get('Recipe', []):
            req_del = urllib.request.Request(
                f'https://api.airtable.com/v0/{base}/{ingredients_table}/{ing["id"]}',
                headers={'Authorization': f'Bearer {key}'},
                method='DELETE',
            )
            try:
                urllib.request.urlopen(req_del)
                print(f"  🗑️  Deleted ingredient {ing['id']}")
            except:
                pass

    # Delete recipe
    req_del = urllib.request.Request(
        f'https://api.airtable.com/v0/{base}/{recipes_table}/{rid}',
        headers={'Authorization': f'Bearer {key}'},
        method='DELETE',
    )
    try:
        urllib.request.urlopen(req_del)
        print(f"  🗑️  Deleted recipe {rid}")
    except Exception as e:
        print(f"  ❌ Failed to delete {rid}: {e}")

print("\nDone. Remaining recipes:")
url = f'https://api.airtable.com/v0/{base}/{recipes_table}?maxRecords=100'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
for r in data.get('records', []):
    f = r['fields']
    ings = len(f.get('Ingredients', []))
    print(f"  {r['id']:20s} {f.get('Name','?'):40s} ({ings} ingredients)")
