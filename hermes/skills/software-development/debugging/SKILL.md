---
name: debugging
description: "Debugging toolkit: systematic root-cause analysis, Python (pdb/debugpy), and Node.js (CDP/inspect). Use when investigating any technical issue — test failures, bugs, unexpected behavior, performance problems. Covers: 4-phase root-cause process, Python pdb/debugpy remote debugging, Node.js Chrome DevTools Protocol debugging."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, troubleshooting, root-cause, pdb, debugpy, nodejs, cdp, breakpoints, dap]
    related_skills: [debugging]
---

# Debugging Toolkit

Systematic debugging for Python, Node.js, and multi-component systems.

## When to Use

- Test failures, bugs in production, unexpected behavior
- Performance problems, build failures, integration issues
- Debugging long-lived processes (gateway, daemons, workers)

---

## 1. Systematic Debugging (4-Phase)

**Iron Law:** NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.

### Phase 1: Root Cause Investigation

1. **Read error messages carefully** — stack traces, line numbers, error codes
2. **Reproduce consistently** — exact steps, every time?
3. **Check recent changes** — `git log --oneline -10`, `git diff`
4. **Gather evidence** — add diagnostic instrumentation at component boundaries
5. **Trace data flow** — where does the bad value originate?

**Completion:** Error reproduced, recent changes identified, root cause hypothesis formed.

### Phase 2: Pattern Analysis

1. Find working examples in the codebase
2. Compare against reference implementations
3. Identify differences (working vs broken)

### Phase 3: Hypothesis & Testing

1. Form single hypothesis: "I think X is root cause because Y"
2. Test minimally — one variable at a time
3. Verify before continuing

### Phase 4: Implementation

1. Create failing test case first
2. Implement single fix (root cause, not symptom)
3. Verify fix — all tests pass
4. **Rule of Three:** If 3+ fixes failed, question the architecture, not the bug

---

## 2. Python Debugging (pdb + debugpy)

### pdb Quick Reference

| Command | Action |
|---------|--------|
| `n` / `s` / `r` | next / step into / return |
| `c` | continue |
| `b file:line` | set breakpoint |
| `p expr` / `pp expr` | print expression |
| `w` | where (stack trace) |
| `interact` | full Python REPL in current scope |

### Local breakpoint

```python
def compute(x, y):
    breakpoint()  # drops into pdb here
    return x + y
```

### pytest Debug

```bash
# Drop to pdb on failure:
pytest tests/test.py::test_name --pdb -p no:xdist

# Show locals in tracebacks:
pytest tests/test.py --showlocals --tb=long
```

### Remote Debug with debugpy

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
```

Attach via IDE or use `remote-pdb` for terminal debugging:

```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
# Then: nc 127.0.0.1 4444
```

### Attach to Running Process

```bash
# Send SIGUSR1 to enable inspector:
kill -SIGUSR1 <pid>
# Then attach debugpy:
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
```

### Pitfalls

1. **pdb under pytest-xdist does nothing** — use `-p no:xdist`
2. **`PYTHONBREAKPOINT=0`** disables all `breakpoint()` calls
3. **Forking** — pdb doesn't follow forks; each child needs its own breakpoint
4. **Threads** — pdb only debugs current thread; use `debugpy` for multithreaded code

---

## 3. Node.js Debugging (CDP + node inspect)

### Quick Reference

```bash
# Start paused on first line:
node inspect path/to/script.js

# Start with inspector:
node --inspect-brk script.js

# Attach to running process:
kill -SIGUSR1 <pid>
node inspect -p <pid>
```

### REPL Commands

| Command | Action |
|---------|--------|
| `c` / `n` / `s` / `o` | continue / next / step / out |
| `sb('file.js', 42)` | set breakpoint |
| `bt` | backtrace |
| `repl` | drop into JS REPL in current scope |
| `exec expr` | evaluate expression |
| `.exit` | quit |

### Programmatic CDP Scripting

```bash
node --inspect-brk=9229 target.js &
node /tmp/cdp-debug.js  # script using chrome-remote-interface
```

### Debugging Hermes TUI (Ink/Node)

```bash
node --inspect-brk dist/entry.js
# In another terminal:
node inspect -p <pid>
```

### Pitfalls

1. **Wrong line numbers** — breakpoints hit emitted JS, not `.ts`. Use sourcemaps or break in `dist/*.js`
2. **`--inspect` vs `--inspect-brk`** — use `--inspect-brk` when you need breakpoints before code runs
3. **Port collisions** — default is `9229`, use `--inspect=0` for random port
4. **Security** — always bind to `127.0.0.1` (default)

---

## 4. Debugging Hermes-Specific Processes

### Tests

```bash
scripts/run_tests.sh tests/path/test.py --pdb -p no:xdist
```

### Gateway (long-lived)

```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)  # in the handler you want to trap
```

### TUI Gateway Subprocess

```python
# tui_gateway/server.py
import remote_pdb; remote_pdb.set_trace(host="127.0.0.1", port=4444)
# Trigger the matching slash command from TUI, then: nc 127.0.0.1 4444
```

### `_SlashWorker` Subprocess

Same pattern — `remote-pdb` with `set_trace()` inside the worker's `exec` path.
