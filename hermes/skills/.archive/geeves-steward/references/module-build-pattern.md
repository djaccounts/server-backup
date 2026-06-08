# Module Build Pattern — Session Notes

## Pattern: Adding a New Phase 2 Module (June 2026)

This documents the consistent pattern used to build the Meals, Sleep/Habits, and People Graph modules. Follow this for future Phase 2 modules (Fitness, etc.).

### Prerequisites
- Tables already exist in Airtable (created in a previous session)
- Schema registry has table IDs
- Schema reference has field definitions

### Steps

1. **Create the skill** at `/root/.hermes/skills/devops/<module>-agent/SKILL.md`
   - Use todos-agent or meals-agent as the template
   - Include: table IDs, key fields, CRUD examples, workflows, Slack capture patterns, pitfalls
   - Version starts at 1.0.0

2. **Add Slack capture** in `/root/Geeves/scripts/slack_capture.py`:
   - Add table IDs to `TABLES` dict
   - Add category to `CATEGORY_RULES` (check for keyword overlap with existing categories!)
   - Add handler function
   - Add to `HANDLERS` dict

3. **Test with dry run**:
   ```bash
   echo '[{"text":"test message","sender":"David","sender_id":"U0B73K4QWP5","ts":"1"}]' | python3 slack_capture.py --stdin --dry-run
   ```

4. **Update modules_status.json**:
   - Set status to "built"
   - Set skill name
   - Update notes

5. **Update schema_registry.json**:
   - Add any missing fields
   - Update `last_synced` timestamp

6. **Update skills_list** in modules_status.json:
   - Add to "built" array

### Classification Priority Lessons

When adding a new category to `CATEGORY_RULES`:
1. Check ALL existing categories for shared keywords
2. If overlap exists, the more specific category must come FIRST
3. Consider removing the overlapping keyword from the less specific category
4. Test with messages that could match both categories

Example: "for dinner" matched both Recipe and Restaurant. Fix: added "for dinner" to Restaurant patterns, removed from Recipe.

### Handler Return Values

All handlers in slack_capture.py should return `True` (success) or `False` (failure). For dry-run mode, always return `True`.

### Common Pitfalls

- **Person Notes**: Must create records in the Person Notes table, NOT write to a text field on People
- **Linked records**: Pass array of record IDs: `["recXXXX"]`
- **Select values**: Must match exactly (case-sensitive)
- **Date format**: Always `YYYY-MM-DD`
- **Tier values**: `"Tier 1"`, `"Tier 2"`, `"Tier 3"`, `"Tier 4"` — NOT `"Tier 4 (other)"`
