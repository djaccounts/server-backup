---
name: kanban-multi-agent
description: "Hermes Kanban for multi-agent collaboration: work queue orchestration, worker lifecycle, Codex lane pattern. Use when dispatching tasks across multiple agent profiles, implementing a task queue with Kanban, or running Codex/Claude Code as isolated implementation lanes within the Kanban system. Covers orchestrator decomposition, worker pitfalls, and the Codex lane pattern."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, worktrees, autonomous-agents, codex, collaboration, workflow]
    related_skills: [kanban-multi-agent]
---

# Kanban Multi-Agent Collaboration

Hermes Kanban: a durable SQLite board for multi-profile / multi-worker collaboration.

## When to Use

- Multiple agent profiles working on shared tasks
- Orchestrating parallel workstreams across specialists
- Long-running tasks that survive crashes/restarts
- Coding tasks where you want Codex as an isolated implementation lane

## Overview

```
Dispatcher (gateway) → Board (SQLite) → Workers (spawned profiles)
```

Users drive via `hermes kanban <verb>`; workers get a focused `kanban_*` toolset; orchestrators get the broader `kanban` toolset.

---

## Orchestrator: Decomposition Playbook

### Step 0: Discover Available Profiles

```bash
hermes profile list
```

**The dispatcher silently fails on unknown assignee names.** Always verify profiles exist before creating tasks.

### Step 1: Understand & Decompose

- Split multi-lane requests into independent cards
- Order by risk (riskiest first)
- Map each lane to an existing profile

### Step 2: Create Task Graph

```python
# Independent lanes (no parents):
t1 = kanban_create(title="research: X", assignee="researcher-profile")
t2 = kanban_create(title="discover: Y", assignee="explorer-profile")

# Synthesis depends on both:
t3 = kanban_create(title="synthesize", assignee="analyst", parents=[t1, t2])

# Pipeline stage:
t4 = kanban_create(title="draft doc", assignee="writer", parents=[t3])
```

### Step 3: Complete & Report

```python
kanban_complete(
    summary="decomposed into T1-T4",
    metadata={"task_graph": {"T1": {"parents": []}, "T3": {"parents": ["T1", "T2"]}}}
)
```

### Patterns

- **Fan-out + fan-in:** N research cards → 1 synthesis card
- **Parallel + validation:** implementer + researcher → reviewer
- **Pipeline:** planner → implementer → reviewer
- **Goal-mode:** `goal_mode=True` for persistent multi-turn workers

---

## Worker: Lifecycle & Pitfalls

### Lifecycle: 6 Steps

1. **Orient:** `kanban_show()` — read task, check prior runs
2. **Work:** Implement/test the task
3. **Heartbeat:** `kanban_heartbeat(note="progress")` for long tasks
4. **Block:** `kanban_block(reason="specific decision needed")` for human-in-the-loop
5. **Complete:** `kanban_complete(summary="...", metadata={...})`
6. **Hand off:** Comments carry context to downstream workers

### Good Handoff Shapes

```python
# Coding task:
kanban_complete(
    summary="shipped rate limiter — 14 tests pass",
    metadata={
        "changed_files": ["rate_limiter.py", "tests/test_rate_limiter.py"],
        "tests_run": 14, "tests_passed": 14,
        "decisions": ["user_id primary, IP fallback for unauthenticated"]
    }
)

# Review task (needs human eyes):
kanban_comment(body=json.dumps({"changed_files": [...], "tests_passed": 14}))
kanban_block(reason="review-required: shipped — needs eyes before merging")
```

### DO NOT

- Call `delegate_task` instead of `kanban_create` (delegate_task is intra-run; kanban is cross-agent)
- Call `clarify` (headless — use `kanban_comment` + `kanban_block`)
- Create follow-up tasks assigned to yourself — assign to the right specialist
- Complete unfinished tasks — block instead
- Claim card IDs you didn't create in `created_cards`

---

## Codex Lane Pattern

### When to Use

Use Codex lane when: task is a bounded coding task with clear acceptance criteria, repo can be isolated in a worktree, Hermes can run tests after.

### Ownership Rules

1. Hermes owns the Kanban lifecycle — Codex never calls `kanban_*`
2. Hermes owns final acceptance — treat Codex diffs as untrusted
3. Hermes owns test execution — Codex test runs are advisory
4. Hermes owns cleanup — kill stuck Codex and remove temp worktrees

### Isolation Pattern

```bash
git worktree add -b "codex/${TASK_ID}/$(date +%s)" /tmp/codex-lane BASE_BRANCH
codex exec --full-auto "$(cat /tmp/codex_prompt.md)" &
# Monitor, reconcile diff, run tests, clean up
```

### Reconciliation Checklist

- [ ] `git status --short` shows only expected files
- [ ] No secrets, credential files, or unrelated artifacts
- [ ] Codex commits are small enough to cherry-pick/squash
- [ ] Hermes ran canonical tests independently
- [ ] `kanban_complete.metadata.codex_lane` follows schema

---

## CLI Reference

All tools have CLI equivalents:

| Tool | CLI |
|------|-----|
| `kanban_show` | `hermes kanban show <id> --json` |
| `kanban_create` | `hermes kanban create "title" --assignee <p> [--parent <id>]` |
| `kanban_complete` | `hermes kanban complete <id> --summary "..." --metadata '{...}'` |
| `kanban_block` | `hermes kanban block <id> "reason"` |
| `kanban_comment` | `hermes kanban comment <id> "body"` |
| `kanban_link` | `hermes kanban link <parent> <child>` |
