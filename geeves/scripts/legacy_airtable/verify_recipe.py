import json, urllib.request, os, subprocess

def get_key():
    r = subprocess.run(['grep', 'AIRTABLE_API_KEY', os.path.expanduser('~/.hermes/.env')], capture_output=True, text=True)
    return r.stdout.strip().split('\n')[0].split('=', 1)[1]

key = get_key()
base = 'appzvmonQXs4x2AlL'

# Get the recipe record
url = f'https://api.airtable.com/v0/{base}/tblehBgzRMa2Xucjd/recbJwbPquOjc3vIg'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {key}'})
with urllib.request.urlopen(req) as resp:
    recipe = json.loads(resp.read())

f = recipe['fields']
print("=== RECIPE RECORD ===")
print(f"  Name:        {f.get('Name')}")
print(f"  Mealie Slug: {f.get('Mealie Slug')}")
print(f"  Source URL:  {f.get('Source URL')}")
print(f"  Notes:       {f.get('Notes', '')[:80]}")
print(f"  Ingredients: {len(f.get('Ingredients', []))} linked")
print(f"  Created:     {recipe.get('createdTime')}")
