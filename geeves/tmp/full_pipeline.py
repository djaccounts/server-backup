import json, os, urllib.request

env = {}
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v

# Step 1: Create recipe in Mealie via html-or-json
mealie_data = "username=changeme@example.com&password=MyPassword123".encode()
req = urllib.request.Request(
    "http://localhost:9925/api/auth/token",
    data=mealie_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read())["access_token"]

recipe = {
    "@context": "https://schema.org",
    "@type": "Recipe",
    "name": "Lemon Blueberry Loaf Cake",
    "description": "A moist, tender loaf cake studded with fresh blueberries and topped with a tangy lemon glaze. Perfect for breakfast or afternoon tea.",
    "recipeIngredient": [
        "1 1/2 cups all-purpose flour",
        "1 teaspoon baking powder",
        "1/4 teaspoon salt",
        "1/2 cup unsalted butter, softened",
        "1 cup granulated sugar",
        "2 large eggs",
        "1 teaspoon vanilla extract",
        "1/2 cup milk (or buttermilk)",
        "1 cup fresh blueberries",
        "Zest of 1-2 lemons",
        "2 tablespoons fresh lemon juice",
        "1 1/2 cups powdered sugar (for glaze)",
        "3-4 tablespoons fresh lemon juice (for glaze)",
    ],
    "recipeInstructions": [
        {"@type": "HowToStep", "text": "Preheat oven to 350F (175C). Grease and flour a 9x5 inch loaf pan, or line with parchment paper."},
        {"@type": "HowToStep", "text": "In a medium bowl, whisk together the flour, baking powder, and salt."},
        {"@type": "HowToStep", "text": "In a large bowl, cream together the softened butter and granulated sugar until light and fluffy."},
        {"@type": "HowToStep", "text": "Beat in the eggs one at a time, mixing well after each addition. Stir in the vanilla extract, lemon zest, and lemon juice."},
        {"@type": "HowToStep", "text": "Gradually add the dry ingredients to the wet ingredients, alternating with the milk, beginning and ending with the dry ingredients. Mix until just combined."},
        {"@type": "HowToStep", "text": "Gently fold in the fresh blueberries."},
        {"@type": "HowToStep", "text": "Pour the batter into the prepared loaf pan and spread evenly. Bake for 50-60 minutes, or until a wooden skewer inserted into the center comes out clean."},
        {"@type": "HowToStep", "text": "Let the loaf cool in the pan for 10-15 minutes before transferring to a wire rack to cool completely."},
        {"@type": "HowToStep", "text": "Whisk together the powdered sugar and lemon juice for the glaze until smooth. Drizzle over the cooled cake. Garnish with extra blueberries and lemon zest."},
    ],
    "prepTime": "PT20M",
    "cookTime": "PT1H",
    "recipeYield": "8-10 slices",
}

payload = json.dumps({"data": json.dumps(recipe)}).encode()
req2 = urllib.request.Request(
    "http://localhost:9925/api/recipes/create/html-or-json",
    data=payload,
    headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req2) as resp:
    slug = resp.read().decode().strip().strip('"')
    print(f"✅ Mealie: {slug}")

# Step 2: Sync to Airtable
import subprocess
result = subprocess.run(
    ["python3", "/root/Geeves/scripts/recipe_sync.py", slug],
    capture_output=True, text=True
)
print(result.stdout)
if result.returncode != 0:
    print(f"Error: {result.stderr}")
