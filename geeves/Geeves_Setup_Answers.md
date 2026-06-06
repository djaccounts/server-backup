# Geeves — Setup Answers for Hermes (§13)

*Paste this to Hermes alongside the Operating Brief. Recommended defaults are filled in; replace anything marked «FILL IN» or adjust to taste, then tell Hermes to proceed.*

---

## 1. Airtable & Slack names

**Airtable base + tables** — recommended naming (consistent so modules link cleanly):

- Base: **`Geeves`**
- Core tables to create now:
  - `People` — the people graph (one record per person)
  - `Todos`
  - `Memory_Summaries` — periodic long-term summaries
  - `Output_Log` — what you generated, when, rating
- Per-module tables come later, each named `<Module>_Data`, `<Module>_Context`, `<Module>_Log` (e.g. `FilmClub_Data`).

**Slack** — talk to Geeves via:

- Workspace: «FILL IN — your Slack workspace name»
- Channel: a dedicated **`#geeves`** channel, or just **DM the bot directly** (recommended — keeps it private and simple).
- Bot identifies sender by Slack user ID: **David = primary**; wife = secondary (one shared bot for now).

## 2. Default hosted model (Ordinary tasks)

- Default to the **agentic model Nous Portal recommends** (one OAuth also gives you web/browser/TTS tools, and it's already in your Hermes setup). Requirement: ≥64k context, good tool-calling, **non-training tier**.
- Alternative: route via **OpenRouter** to an equivalent agentic model if you want provider flexibility.
- **Do not** use the Hermes 4 reasoning series (405B/70B) for the agent loop — only for occasional heavy one-shot reasoning, if ever.
- **Sensitive tasks always use the local Ollama model — never this one.**
- ☐ Confirm the chosen hosted tier does not train on inputs before any data flows.

## 3. Digest email & timing

- Send daily digest to: **dj@djaccounts.com** (confirm or change)
- Send time: **07:00** local, every day
- Weekly digest: **Monday 07:00**, covering the week ahead + last week's roll-up
- Also CC wife? **No for now** «change if wanted»

## 4. Sensitivity classification — confirm before data flows

Confirm this matches your comfort (adjust the lists if not):

- **Sensitive → local Ollama only, never leaves the VPS:** health/medical, intimate or relationship notes, anything about the marriage, private details about third parties. *When in doubt, treat as Sensitive.*
- **Ordinary → hosted model OK (with names pseudonymised):** recipes, films, shopping, todos, travel, general logistics.
- ☐ I confirm the above. Anything to move between the two lists: «FILL IN or "none"»

---

## What Hermes should do once these are confirmed

1. Verify it can read/write Airtable, send/receive on Slack, send email, and reach both Ollama and the hosted model — report status.
2. Create the `Geeves` base and the four core tables above.
3. Seed `People`: Tier 1 (David) and Tier 2 (wife + 3–4 closest) — ask David for these details conversationally, a few fields at a time, not as a form.
4. Wire Slack capture → classified, structured Airtable write.
5. Ship the 07:00 morning email digest via cron.
6. Turn on nightly Airtable→Drive backup, log retention, and Slack failure alerts.
7. Then stop and wait for the first real module need.
