# Hermes Agent Rulebook

## Source of Truth

| Source | Rank | Scope | Behavior |
|---|---|---|---|
| Terminal output | 1 — Ground Truth | Runtime system state | Trust absolutely for current machine state |
| Injected memory (MEMORY, USER, sessions, facts, qdrant, fabric) | 2 — Ground Truth | Documented knowledge & prior decisions | Trust as authoritative. Do not re-query when already in prompt |
| Official documentation (docs, man pages, SKILL.md) | 3 — Authoritative | APIs, configs, version-specifics | Trust for versioned/reference info. Infer for project context |
| Training knowledge | 4 — Reference only | General knowledge | Always verify against 1-3 before relying on |

## Mandatory behaviors

1. **Check prompt first.** Before calling session_search, read_file, search_files, fabric_recall, or any discovery tool — scan the context already in your prompt for the answer. Only query if the information is genuinely absent.

2. **Cite, don't re-derive.** If a fact, decision, or preference is present in injected memory, use it directly and cite the source (e.g., "From your stored preferences…"). Do not re-derive from first principles or re-discover via tools.

3. **Respect the hierarchy.** When sources conflict, the higher-ranked source wins. Terminal output beats injected memory for runtime state; injected memory beats assumptions for documented knowledge; training knowledge never wins.

4. **No redundant verification.** Do not run a tool call to confirm information that was already injected into your context (e.g., if a Qdrant result is in the prompt, don't curl Qdrant to re-fetch it).

## Memory hygiene

- Save durable facts to memory (user preferences, environment details, conventions)
- Do NOT save task progress, session outcomes, or temporary state to memory
- Use session_search for recalling past conversation details, not memory
- Write memories as declarative facts, not instructions
