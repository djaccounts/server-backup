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
print(f"Ingredients linked to Bolognese recipe ({target}):")
print("-" * 70)
count = 0
for r in data.get('records', []):
    f = r['fields']
    recipe_links = f.get('Recipe', [])
    if target in recipe_links:
        count += 1
        seasonal = f.get('Seasonal', [])
        seasonal_str = ', '.join(seasonal[:3]) + '...' if len(seasonal) > 3 else ', '.join(seasonal)
        print(f"  {count:2d}. {f.get('Ingredient','?'):30s} │ {f.get('Category','?'):10s} │ {f.get('Quantity',''):12s} │ {seasonal_str}")
print("-" * 70)
print(f"Total: {count} ingredients")
