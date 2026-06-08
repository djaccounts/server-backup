---
name: autonomous-coding-agents
description: "Delegate coding to external AI coding agents: Claude Code, OpenAI Codex, OpenCode. Use when you want an external agent to implement features, refactor code, review PRs, or run autonomous coding sessions. Covers setup, one-shot tasks, interactive PRY sessions, and parallel work patterns for all three agents."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude-Code, Codex, OpenCode, Autonomous, Refactoring, Code-Review, PTY, Automation, Delegation]
    related_skills: [autonomous-coding-agents]
---

# Autonomous Coding Agents

Orchestrate external AI coding agents (Claude Code, Codex, OpenCode) via Hermes terminal/process tools.

## When to Use

- User asks to use a specific coding agent (Claude Code, Codex, OpenCode)
- You want an external agent to implement/refactor/review code
- Long-running coding sessions with progress checks
- Parallel task execution in isolated workdirs/worktrees

## Agent Selection Guide

| Agent | Best For | Auth | Install |
|-------|---------|------|---------|
| **Claude Code** | Complex multi-step work, reasoning | OAuth or `ANTHROPIC_API_KEY` | `npm i -g @anthropic-ai/claude-code` |
| **Codex** | Quick one-shot tasks, PR reviews | `OPENAI_API_KEY` or Codex OAuth | `npm i -g @openai/codex` |
| **OpenCode** | Provider-agnostic, long-running sessions | OAuth or env vars | `npm i -g opencode-ai` |

---

## Common Patterns (All Agents)

### One-Shot Mode (Preferred for Automation)

All agents support non-interactive one-shot mode:

```
claude -p "Fix the auth bug" --max-turns 10
codex exec "Add dark mode toggle"
opencode run "Add retry logic to API calls"
```

### Interactive Mode (Multi-Turn)

All agents use tmux for interactive orchestration:

```bash
# Start
tmux new-session -d -s agent -x 140 -y 40
tmux send-keys -t agent 'cd /project && <agent> <mode>' Enter
# Send task
tmux send-keys -t agent 'Your task here' Enter
# Monitor
tmux capture-pane -t agent -p -S -50
# Exit
tmux send-keys -t agent '/exit' Enter && tmux kill-session -t agent
```

### Background Mode

```bash
terminal(command="<agent> <mode> 'task'", workdir="/project",
         background=true, pty=true, notify_on_complete=True)
# Monitor with: process(action='poll'|'log', session_id='<id>')
# Kill with:   process(action='kill', session_id='<id>')
```

---

## Claude Code

**Install:** `npm install -g @anthropic-ai/claude-code`
**Auth:** `claude` (browser OAuth) or `claude auth login --console` (API key)

### Key Flags

| Flag | Effect |
|------|--------|
| `-p "query"` | Print mode (non-interactive, exits when done) |
| `--max-turns N` | Limit agentic loops (prevents runaway) |
| `--allowedTools Read,Edit` | Restrict to specific tools |
| `--dangerously-skip-permissions` | Auto-approve all tool use |
| `-c` / `--continue` | Resume most recent session |
| `-r "id"` / `--resume` | Resume specific session |

### PR Review

```bash
# Pipe diff to claude:
git diff main...HEAD | claude -p "Review for bugs and security issues" --max-turns 1

# From PR number:
claude -p "Review this PR thoroughly" --from-pr 42 --max-turns 10
```

### Parallel Claude Instances

```bash
tmux new-session -d -s backend && tmux send-keys -t backend 'claude -p "Fix auth bug" --max-turns 10' Enter
tmux new-session -d -s frontend && tmux send-keys -t frontend 'claude -p "Add tests" --max-turns 15' Enter
```

> **Dialog handling:** First launch shows workspace trust dialog (Enter to accept). With `--dangerously-skip-permissions`, also send Down+Enter for the permissions dialog.

---

## Codex

**Install:** `npm install -g @openai/codex`
**Auth:** `OPENAI_API_KEY` or Codex CLI OAuth
**Requires:** git repository

### Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed, auto-approves changes |
| `--yolo` | No sandbox, no approvals |
| `review` | PR review mode |

### Rules

1. **Always use `pty=true`** — Codex hangs without PTY
2. **Git repo required** — use `mktemp -d && git init` for scratch work
3. **Use `exec` for one-shots** — `codex exec "prompt"` exits cleanly
4. **Background for long tasks** — `background=true` + `process` tool

### Parallel Issue Fixing

```bash
git worktree add -b fix/issue-78 /tmp/issue-78 main
codex exec --full-auto 'Fix issue #78. Commit when done.' &
cd /tmp/issue-78 && git push -u origin fix/issue-78
```

---

## OpenCode

**Install:** `npm i -g opencode-ai@latest`
**Auth:** `opencode auth login` or env vars

### Key Flags

| Flag | Effect |
|------|--------|
| `run 'prompt'` | One-shot execution, exits when done |
| `--continue` / `-c` | Continue last session |
| `--model provider/model` | Force specific model |
| `--file path` / `-f` | Attach file(s) |
| `--thinking` | Show model thinking |

### Important Notes

- **Do NOT use `/exit`** — it opens an agent selector. Use Ctrl+C (`\x03`) or `process(action="kill")`
- **Interactive sessions need `pty=true`**
- **`opencode run` does NOT need pty**

### Smoke Test

```bash
opencode run 'Respond with exactly: OPENCODE_SMOKE_OK'
```

---

## Comparison

| | Claude Code | Codex | OpenCode |
|--|------------|-------|----------|
| One-shot | `-p "query"` | `exec "query"` | `run 'query'` |
| Interactive | tmux + PTY | tmux + PTY | tmux + PTY |
| Parallel | Yes | Yes (worktrees) | Yes (workdirs) |
| Resume | `-c` or `-r id` | N/A | `-c` or `-s id` |
| Exit | `/exit` | Auto-exits | Ctrl+C or kill |
