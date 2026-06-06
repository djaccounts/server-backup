# Recipe Module Plan — June 2026

## Architecture
- **Mealie** = recipe engine (URL scrape, ingredients, method, nutrition, scaling, images)
- **Airtable** = metadata + cross-module connective layer
- Sync direction: Mealie → Airtable (one-way, on-demand)

## Airtable Tables

### Recipes (slimmed — metadata + links only)
- Name, Mealie Slug, Source URL, Cuisine, Meal type, Quality rating (1-5), Will do again, Times cooked (rollup), Last cooked (date), Ingredients (link), Photo, Notes, **Favourite (checkbox)**

### Ingredients (linked to Recipes)
- Ingredient, Recipe (link), Quantity, Category (Meat/Fish/Veg/Fruit/Dairy/Grain/Spice/Pantry/Other), Seasonal (months)
- Populated from Mealie ingredients via LLM categorisation at sync time

### Dinner Planner (unchanged)
- Date, Meal, Recipe (link), Prep notes

### Meals (add: Cuisine field)
- Description, Date, Meal type, Calories, Protein, Carbs, Fat, **Cuisine (single select)**, From recipe (link, optional), Accuracy, Source, Logged
- Restaurant meals: no Recipe link, Accuracy=Estimated, Cuisine tagged

### Recipe Context
- Preference, Detail, Source (Inferred/Manual)

### Recipe Output Log
- Output, Type (Suggestion/Shopping list/Meal plan/Dinner party), Recipes link, Date, Rating, Feedback

### Shopping List (new)
- Item, Category (aisle), Quantity, Source (recipe/manual), Purchased (checkbox), Dinner Party link (optional)

### Dining Preferences (new — shared cross-module bridge)
- Preference, Category (Cuisine/Dish/Dietary/Style/Avoid), Confidence (Strong/Moderate/Emerging), Evidence, Source modules, Last updated
- Auto-populated by Hermes from recipe ratings, meal frequency, ingredient patterns
- Future Restaurant Finder reads this table

## Key Flows
1. Add recipe: Slack → Mealie URL import → Airtable Recipes + Ingredients records
2. Log meal (with recipe): Find recipe → create Meals record → sync lastMade back to Mealie
3. Log meal (restaurant): description/photo → LLM identifies dish + estimates macros → Meals record (no recipe link)
4. Dinner Party: Link guests → compile dietary constraints → suggest recipes → generate shopping list
5. "What's for dinner?": Filter Favourites + high rating + Often/Staple
6. Email/PDF: Fetch from Mealie API → format → AgentMail or PDFBolt
7. Preference signals: Periodic cron scans Recipes + Meals → updates Dining Preferences

## Fields removed from old plan (now in Mealie)
Difficulty, Prep/Cook time, Servings, Seasonal tags (on recipe), Dietary tags (on recipe), Calories/Protein per serving (from Mealie nutrition), Method, Hints
