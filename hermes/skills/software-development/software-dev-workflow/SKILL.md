---
name: software-dev-workflow
description: "Software development workflow toolkit: writing plans, spikes, TDD, subagent-driven development, pre-commit review. Use when implementing features with structured methodology. Covers: writing implementation plans, throwaway spikes/prototypes, test-driven development (RED-GREEN-REFACTOR), subagent-driven execution with two-stage review, and pre-commit code verification."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, testing, tdd, subagent, code-review, spikes, workflow, implementation, quality]
    related_skills: [software-dev-workflow]
---

# Software Development Workflow

Structured methodology for implementing software features: planning → spikes → TDD → subagent execution → review.

---

## 1. Writing Implementation Plans

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

### Bite-Sized Task Granularity

Each task = 2-5 minutes of focused work.

**Too big:** "Implement user authentication system"
**Right size:** "Create User model with email field" → "Add password hashing function" → "Create login endpoint"

### Plan Structure

```markdown
# Feature Implementation Plan

**Goal:** One sentence
**Architecture:** 2-3 sentences
**Tech Stack:** Key technologies

### Task N: Descriptive Name

**Objective:** One sentence
**Files:**
- Create: `exact/path/to/file.py`
- Test: `tests/path/to/test.py`

**Step 1: Write failing test**
```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**
Run: `pytest tests/path/test.py::test_specific -v`
Expected: FAIL

**Step 3: Write minimal implementation**
**Step 4: Run test to verify pass**
**Step 5: Commit**
```

### Principles: DRY, YAGNI, TDD, Frequent Commits

- Save plans to `docs/plans/YYYY-MM-DD-feature-name.md`
- Each task includes full code examples (copy-pasteable), exact commands, expected output

---

## 2. Spikes (Throwaway Experiments)

**Use when:** Faking out an idea before committing to a build — validating feasibility, comparing approaches, surfacing unknowns.

**Not for:** Questions answerable from docs, production-path work, already-validated ideas.

### Method: Decompose → Research → Build → Verdict

1. **Decompose:** Break into 2-5 feasibility questions (Given/When/Then framing)
2. **Research:** Brief per approach (tool/library, pros, cons, status)
3. **Build:** One directory per spike (`spikes/NNN-name/`). Bias toward interactive output (CLI, HTML page)
4. **Verdict:** VALIDATED | PARTIAL | INVALIDATED + recommendation

### Comparison Spikes

For `002a` vs `002b`, build back-to-back, then head-to-head comparison table (quality, setup, perf).

---

## 3. Test-Driven Development (TDD)

**Iron Law:** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.

### RED-GREEN-REFACTOR

1. **RED:** Write one failing test for one behavior
2. **Verify RED:** Run test — confirm it fails for expected reason
3. **GREEN:** Write minimal code to pass (hardcode is OK)
4. **Verify GREEN:** Run test — confirm pass, no regressions
5. **REFACTOR:** Clean up (keep tests green)
6. **Repeat:** Next failing test for next behavior

### Key Rules

- Tests passing immediately prove nothing (might test wrong thing)
- "I'll test after" — disqualified, start over
- "Skip TDD just this once" — that's rationalization
- Used everywhere: new features, bug fixes, refactoring

### pytest One-Liners

```bash
# Fail on first, with locals:
pytest tests/ -x --tb=long --showlocals

# Specific test, fail → pdb:
pytest tests/test.py::test_name --pdb -p no:xdist

# Full suite, no regressions:
pytest tests/ -q
```

---

## 4. Subagent-Driven Development

**Core principle:** Fresh subagent per task + two-stage review = high quality, fast iteration.

### Per-Task Workflow

1. **Dispatch Implementer** — `delegate_task` with complete context (TDD required)
2. **Spec Compliance Review** — fresh subagent: does implementation match spec?
3. **Code Quality Review** — fresh subagent: follows conventions, proper handling?
4. **Mark Complete** — only when both reviews pass

### If Issues Found

- Fix → re-review → repeat
- Don't skip re-review
- Never proceed with open critical/important issues

### Why Fresh Subagent Per Task

- Prevents context pollution from accumulated state
- No confusion from prior tasks' code
- Each subagent gets clean, focused context

### Two-Stage Review Order

1. **Spec compliance first** — catches under/over-building early
2. **Code quality second** — ensures well-built implementation

---

## 5. Pre-Commit Code Verification

**Use when:** Before `git commit` or `git push`, after implementing a feature/fix.

### Pipeline

1. **Get diff:** `git diff --cached` (or `git diff`)
2. **Static security scan** — hardcoded secrets, shell injection, eval/exec, pickle, SQL injection
3. **Baseline tests & linting** — detect regressions vs baseline
4. **Self-review checklist** — input validation, error handling, no debug prints
5. **Independent reviewer subagent** — `delegate_task` with diff + scan results → JSON verdict
6. **Evaluate** — all pass → commit; failures → auto-fix loop (max 2 cycles)
7. **Commit** — `git commit -m "[verified] description"`

### Common Patterns to Flag

```python
# SQL injection (BAD):
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
# Parameterized (GOOD):
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# Shell injection (BAD):
os.system(f"ls {user_input}")
# Safe subprocess (GOOD):
subprocess.run(["ls", user_input], check=True)
```
