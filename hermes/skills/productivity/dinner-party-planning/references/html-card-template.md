# Dinner Party HTML Card — Design Notes

## Two Files, Two Audiences

Always produce **two separate HTML files**:

1. **Cooking version** (`<event-name>.html`): Full interactive card with tabs (Invite → Summary → Shopping List → Timeline → Recipes). For the cook.
2. **Guest version** (`<event-name>-guest.html`): Standalone invite/cover page only. Clean, elegant, no cooking details. For the guests.

## Style Guidelines (from user feedback)

### Cooking Version
- **Background**: White/light (`#fff` or `#fafafa`) — NOT dark
- **Spacing**: Compact — small padding (0.5–0.8rem), tight gaps, efficient use of page space
- **Cards**: Subtle borders (`#e5e5e5`), light backgrounds (`#f9f9f9`), small border-radius (8–10px)
- **Typography**: System fonts, 0.8–0.9rem body, 0.75rem metadata
- **Colors**: Accent `#e94560`, green `#2d9e6a`, orange `#e8941a`

### Guest Version
- **Background**: Clean white
- **Layout**: Centered card, max ~520px wide
- **Guests**: Listed **vertically** (block display, one per line) — NOT horizontal chips
- **Address**: Prominently displayed on the card
- **Spacing**: Minimal padding, elegant but compact
- **Closing**: "Come hungry. Leave happy."

## Tab Order (Cooking Version)
1. Invite (cover)
2. Summary
3. Shopping List
4. Timeline
5. Recipes

## PDF Generation
```bash
weasyprint /root/<event-name>.html /root/<event-name>-cooking.pdf
weasyprint /root/<event-name>-guest.html /root/<event-name>-guest.pdf
```

## Hosting
```bash
cp /root/<event-name>.html /var/www/html/<event-name>.html
cp /root/<event-name>-guest.html /var/www/html/<event-name>-guest.html
cp /root/<event-name>-cooking.pdf /var/www/html/<event-name>-cooking.pdf
cp /root/<event-name>-guest.pdf /var/www/html/<event-name>-guest.pdf
chmod 644 /var/www/html/<event-name>.*
```

## Email Delivery
Use AgentMail REST API with base64-encoded attachments (NOT `mcp_agentmail_send_message` with URLs — VPS may not be publicly accessible).

Email body text = simple invitation (date, time, address) — NOT a feature list.
