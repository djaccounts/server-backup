---
name: github-workflow
description: "Complete GitHub workflow: auth setup, repo management, issues, PRs, code review, and CI/CD. Use when working with GitHub in any capacity — authentication, repositories, issues, pull requests, code review, releases, Actions, or API access."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Git, Workflow, Authentication, Pull-Requests, Issues, Code-Review, CI/CD, Repositories]
    related_skills: [github-workflow]
---

# GitHub Workflow

Complete guide for working with GitHub: authentication, repository management, issues, pull requests, code review, releases, and CI/CD.

## When to Use

- Any GitHub operation: auth, repos, issues, PRs, code review, releases, Actions
- Setting up `gh` CLI or git-only authentication
- Managing the full PR lifecycle (branch → commit → open → CI → merge)
- Triaging and managing GitHub issues
- Reviewing code (local changes or open PRs)

## Table of Contents

1. [Authentication](#1-authentication)
2. [Repository Management](#2-repository-management)
3. [Issues](#3-issues)
4. [Pull Request Workflow](#4-pull-request-workflow)
5. [Code Review](#5-code-review)
6. [Releases & GitHub Actions](#6-releases--github-actions)

---

## 1. Authentication

### Detection Flow

```bash
git --version
gh --version 2>/dev/null || echo "gh not installed"
gh auth status 2>/dev/null || echo "gh not authenticated"
```

**Decision tree:**
1. `gh auth status` shows authenticated → use `gh` for everything
2. `gh` installed but not authenticated → prefer SSH key auth for servers; use `gh auth login --with-token` if PAT available
3. `gh` not installed → use git-only method

### Git-Only Auth (No gh, No sudo)

**HTTPS with PAT (recommended):**
```bash
git config --global credential.helper store
# Then do a test operation — username = GitHub username, password = PAT
git ls-remote https://github.com/<user>/<any-repo>.git
```

**SSH Key Auth:**
```bash
ssh-keygen -t ed25519 -C "email@example.com" -f ~/.ssh/id_ed25519 -N ""
# Add public key at https://github.com/settings/keys
ssh -T git@github.com
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

### gh CLI Auth

```bash
# Headless / SSH servers:
echo "<TOKEN>" | gh auth login --with-token
gh auth setup-git
```

> **⚠️ Slack/messaging latency warning:** `gh auth login --web` generates a one-time code that expires in ~90 seconds. Do not use via Slack. Use SSH or token-based login.

### API Access Without gh

```bash
export GITHUB_TOKEN="<token>"
curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Auth Helper Detection Script

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
elif [ -n "$GITHUB_TOKEN" ]; then
  AUTH="curl"
elif [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
  export GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
  AUTH="curl"
else
  AUTH="none"
fi
```

---

## 2. Repository Management

### Clone

```bash
git clone https://github.com/owner/repo.git
gh repo clone owner/repo
```

### Create

```bash
# With gh:
gh repo create my-project --public --clone

# With API:
curl -s -X POST -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos \
  -d '{"name":"my-project","private":false,"auto_init":true}'
```

### Fork

```bash
gh repo fork owner/repo --clone
```

### Repository Settings

```bash
gh repo edit --description "Updated" --visibility public
gh repo edit --enable-auto-merge
```

### Branch Protection

```bash
curl -s -X PUT -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/branches/main/protection \
  -d '{
    "required_status_checks": {"strict":true,"contexts":["ci/test"]},
    "required_pull_request_reviews": {"required_approving_review_count":1}
  }'
```

### Secrets (GitHub Actions)

```bash
gh secret set API_KEY --body "value"
gh secret list
```

---

## 3. Issues

### View

```bash
gh issue list
gh issue list --state open --label "bug"
gh issue view 42
```

### Create

```bash
gh issue create \
  --title "Bug: login redirect ignores ?next=" \
  --body "## Description\n..." \
  --label "bug,backend" \
  --assignee "username"
```

### Manage

```bash
gh issue edit 42 --add-label "priority:high"
gh issue edit 42 --add-assignee username
gh issue comment 42 --body "Investigated — working on fix."
gh issue close 42
gh issue reopen 42
```

### Triage Workflow

1. List untriaged: `gh issue list --label "needs-triage" --state open`
2. Read and categorize each issue
3. Apply labels and priority
4. Assign if owner is clear
5. Comment with triage notes

---

## 4. Pull Request Workflow

### Branch & Commit

```bash
git fetch origin
git checkout main && git pull origin main
git checkout -b feat/add-feature
# Make changes, then:
git add src/feature.py tests/test_feature.py
git commit -m "feat: add feature

- Detailed description
- Closes #42"
```

Branch naming: `feat/`, `fix/`, `refactor/`, `docs/`, `ci/`

### Push & Create PR

```bash
git push -u origin HEAD

gh pr create \
  --title "feat: add feature" \
  --body "## Summary\n...\n\nCloses #42"
```

### Monitor CI

```bash
gh pr checks
gh pr checks --watch
```

### Auto-Fix CI Failures

1. Check CI status → identify failures
2. Read failure logs: `gh run view <RUN_ID> --log-failed`
3. Fix code, commit, push
4. Re-check CI
5. Repeat (up to 3 attempts)

### Merge

```bash
gh pr merge --squash --delete-branch
gh pr merge --auto --squash --delete-branch
```

---

## 5. Code Review

### Review Local Changes (Pre-Push)

```bash
git diff main...HEAD --stat
git diff main...HEAD
```

Check for:
- Debug statements, TODOs, secrets
- Merge conflict markers
- Large files accidentally staged

### Review a PR

```bash
gh pr view 123
gh pr diff 123
# Or check out locally:
git fetch origin pull/123/head:pr-123
git checkout pr-123
```

### Leave Comments

```bash
gh pr comment 123 --body "Looks good overall."

# Inline comment:
gh pr review 123 --request-changes --body "See inline comments."
```

### Submit Formal Review

```bash
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "See inline comments."
```

### Review Checklist

- **Correctness:** Does code do what it claims? Edge cases handled?
- **Security:** No hardcoded secrets, input validation, no injection
- **Code Quality:** Clear naming, DRY, focused functions
- **Testing:** New code paths tested, happy + error cases
- **Performance:** No N+1 queries, appropriate caching
- **Documentation:** Public APIs documented, "why" comments

---

## 6. Releases & GitHub Actions

### Releases

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release list
```

### GitHub Actions

```bash
gh workflow list
gh run list --limit 10
gh run view <RUN_ID> --log-failed
gh run rerun <RUN_ID> --failed
gh workflow run ci.yml --ref main
```

---

## Quick Reference Table

| Action | gh | git + curl |
|--------|-----|-----------|
| Auth setup | `gh auth login` | SSH key or PAT in credential helper |
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create repo | `gh repo create name --public` | `curl POST /user/repos` |
| Fork | `gh repo fork o/r --clone` | `curl POST /repos/o/r/forks` |
| List issues | `gh issue list` | `curl GET /repos/o/r/issues` |
| Create PR | `gh pr create ...` | `curl POST /repos/o/r/pulls` |
| Merge | `gh pr merge --squash` | `curl PUT /repos/o/r/pulls/N/merge` |
| CI status | `gh pr checks` | `curl GET /repos/o/r/commits/SHA/status` |
| Release | `gh release create v1.0` | `curl POST /repos/o/r/releases` |
