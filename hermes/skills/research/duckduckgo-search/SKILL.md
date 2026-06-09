---
name: duckduckgo-search
description: "Search the web using DuckDuckGo. Free, no API key required. Supports text, image, and news search. Use when you need web search without API key restrictions, or as a privacy-respecting alternative to other search tools."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [search, web, duckduckgo, privacy, free]
---

# DuckDuckGo Search

Search the web using DuckDuckGo's unofficial Python client (`ddgs`). No API key needed. Free. Privacy-respecting.

## Prerequisites

```bash
pip install ddgs
```

Already installed on this machine.

## Usage

### Text Search

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.text("your search query", max_results=10):
        print(r['title'])
        print(r['href'])
        print(r.get('body', '')[:200])
        print('---')
```

### News Search

```python
with DDGS() as ddgs:
    for r in ddgs.news("topic", max_results=5):
        print(r['title'])
        print(r['url'])
        print(r.get('body', '')[:200])
        print(r.get('date', ''))
        print('---')
```

### Image Search

```python
with DDGS() as ddgs:
    for r in ddgs.images("query", max_results=5):
        print(r['title'])
        print(r['image'])  # direct image URL
        print('---')
```

## Parameters

### `ddgs.text()`
| Param | Default | Description |
|-------|---------|-------------|
| `keywords` | — | Search query |
| `max_results` | 10 | Number of results |
| `region` | `wt-wt` | Region (e.g., `uk-en`, `us-en`) |
| `safesearch` | `moderate` | `on`, `moderate`, `off` |
| `timelimit` | None | `d` (day), `w` (week), `m` (month), `y` (year) |

### `ddgs.news()`
| Param | Default | Description |
|-------|---------|-------------|
| `keywords` | — | Search query |
| `max_results` | 10 | Number of results |
| `region` | `wt-wt` | Region |
| `safesearch` | `moderate` | `on`, `moderate`, `off` |
| `timelimit` | None | `d`, `w`, `m` |

## Instant Answer API (no package needed)

For quick factual answers, you can also use the official DDG Instant Answer API directly:

```bash
curl -sL "https://api.duckduckgo.com/?q=your+query&format=json&no_html=1" | python3 -m json.tool
```

This returns abstracts, definitions, and related topics — but NOT full search results.

## When to Use

- **DuckDuckGo text search** — general web search, no API key needed
- **DuckDuckGo news** — current events, complements your Bulletin
- **DuckDuckGo images** — finding images without API keys
- **Instant Answer API** — quick factual lookups (like a lightweight Wikipedia search)

## Integration Notes

- Works alongside Firecrawl (which provides full page scraping)
- Good fallback when other search APIs hit rate limits
- Privacy-respecting: DDG doesn't track searches
