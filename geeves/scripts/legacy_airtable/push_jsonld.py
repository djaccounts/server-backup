import json, urllib.request, urllib.error

# Get token
data = "username=changeme@example.com&password=MyPassword123".encode()
req = urllib.request.Request(
    "http://localhost:9925/api/auth/token",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read())["access_token"]

# The exact recipe text David sent, parsed into JSON-LD
recipe = {
    "@context": "https://schema.org",
    "@type": "Recipe",
    "name": "Blueberry Lemon Bread",
    "description": "Super moist and delicious blueberry lemon bread with lemon icing. Perfect for breakfast. Something good to make this Memorial Day weekend.",
    "recipeIngredient": [
        "2 1/2 cups cake flour, sifted and then measured (NOTE: if using all-purpose flour, reduce to 2 1/4 cups)",
        "2 teaspoons baking powder",
        "1 teaspoon salt",
        "2 eggs, well beaten",
        "1 1/2 cups white granulated sugar",
        "1/2 cup vegetable oil",
        "1/2 cup whole milk",
        "juice and zest of 1 large lemon",
        "1/2 teaspoon pure vanilla extract",
        "1 1/4 cups fresh or frozen blueberries tossed with 1 Tablespoon flour (thaw and measure if frozen)",
        "1 Tablespoon butter (for icing)",
        "2 Tablespoons milk (for icing)",
        "1 3/4 cups confectioners sugar, sifted (for icing)",
        "4 Tablespoons fresh lemon juice (for icing)",
        "1/4 teaspoon pure vanilla extract (for icing)",
    ],
    "recipeInstructions": [
        {"@type": "HowToStep", "text": "Preheat oven to 350 degrees. Grease and flour a 9x5 loaf pan. In a large mixing bowl combine the flour, baking powder and salt and set aside."},
        {"@type": "HowToStep", "text": "In a separate mixing bowl, using an electric mixer or whisk, beat the eggs until light and fluffy. Add sugar and oil and stir using a wooden spoon or whisk. NOTE: Don't use an electric mixer for the rest of the mixing. Over mixing will cause the bread to be tough."},
        {"@type": "HowToStep", "text": "Slowly add the dry ingredients to the egg mixture, alternating with the milk. Add lemon zest, lemon juice and vanilla extract. Gently stir."},
        {"@type": "HowToStep", "text": "Gently fold blueberries into the batter. Pour batter into the prepared loaf pan."},
        {"@type": "HowToStep", "text": "Bake for 50 minutes to 1 hour or until a toothpick inserted in the center comes out clean. Be careful not to over bake. Check after about 40 minutes. If it's getting too brown, reduce the heat to 325 degrees and continue baking."},
        {"@type": "HowToStep", "text": "Allow bread to cool completely in the pan on a wire rack before glazing with the lemon icing and slicing."},
        {"@type": "HowToStep", "text": "Make the icing: Melt butter and milk together in a small saucepan. Pour the hot melted butter and milk over the confectioners sugar in a small mixing bowl. Add lemon juice and vanilla extract and whisk well or beat until smooth and creamy."},
        {"@type": "HowToStep", "text": "When bread is cooled, take out of pan and place on a wire rack and drizzle icing over bread. Let icing set for about 15 to 20 minutes before slicing. Garnish with fresh blueberries and lemon zest, if desired. Wrap bread in plastic wrap and store in an airtight container. Bread will stay fresh for up to 5 or 6 days."},
    ],
    "prepTime": "PT20M",
    "cookTime": "PT1H",
    "recipeYield": "10 slices",
}

payload = json.dumps({"data": json.dumps(recipe)}).encode()
req2 = urllib.request.Request(
    "http://localhost:9925/api/recipes/create/html-or-json",
    data=payload,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(req2, timeout=30) as resp:
        slug = resp.read().decode().strip().strip('"')
        print(f"✅ Mealie slug: {slug}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body[:300]}")
