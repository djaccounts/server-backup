import json, urllib.request, os, subprocess

def get_key():
    r = subprocess.run(['grep', 'AIRTABLE_API_KEY', os.path.expanduser('~/.hermes/.env')], capture_output=True, text=True)
    return r.stdout.strip().split('\n')[0].split('=', 1)[1]

key = get_key()
base = 'appzvmonQXs4x2AlL'
table = 'tblNsgbYHNK8xWnB7'
url = f'https://api.airtable.com/v0/{base}/{table}?maxRecords=100'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

target = 'recbJwbPquOjc3vIg'
ingredients = []
for r in data.get('records', []):
    f = r['fields']
    if target in f.get('Recipe', []):
        ingredients.append(f)

print(f"Ingredients for Bolognese recipe: {len(ingredients)}")
print("-" * 75)
for i, f in enumerate(ingredients, 1):
    seasonal = f.get('seasonal', [])
    sea = ', '.join(seasonal[:3]) + '...' if len(seasonal) > 3 else ', '.join(seasonal)
    print(f"  {i:2d}. {f.get('Ingredient','?'):35s} │ {f.get('Category','?'):10s} │ {sea}")
