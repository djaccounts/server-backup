# Recipe Scraping Patterns

## Extraction Priority

When scraping recipe blogs, try these in order:

### 1. JSON-LD (most reliable)
Look for `<script type="application/ld+json">` with `@type: "Recipe"`. Contains `recipeIngredient[]`, `recipeInstructions[]`, `prepTime`, `cookTime`, `recipeYield`, `description`.

**Pitfall:** The JSON-LD block sometimes exists but contains a non-Recipe schema (WebPage, Article). Always check `@type` before assuming recipe data.

### 2. WP Recipe Maker (WPRM)
Most WordPress recipe blogs use this plugin. Look for:
- Recipe container: `wprm-recipe-container-{id}`
- Ingredients: `wprm-recipe-ingredient` spans (amount + unit + name in child spans)
- Instructions: `wprm-recipe-instruction` list items
- Notes: `wprm-recipe-notes` divs
- Times: `wprm-recipe-prep_time`, `wprm-recipe-cook_time`
- Servings: `wprm-recipe-servings`

**Pitfall:** Ingredient spans have nested structure. Flatten with regex: strip all HTML tags and concatenate.

### 3. Fallback
Extract plain text around "Ingredients" / "Instructions" / "Method" headings.

## Subagent Web Access Pitfall

Subagents spawned via `delegate_task` do NOT have web search tools available. They will try to use email tools or fail. **Always scrape recipe URLs in the main session** using `terminal` + Python/curl, not in subagents.
