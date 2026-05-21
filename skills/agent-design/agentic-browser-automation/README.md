# Agentic Browser Automation

Build AI-powered browser agents that use LLMs to reason about web pages — navigating, clicking, filling forms, extracting data, and recovering from failures — without hardcoded selectors. Replaces brittle CSS/XPath scraping with intent-driven, self-healing automation.

## Quick Start

```typescript
// Describe what you want in natural language
const data = await extractWithIntent(
  'https://example.com/products',
  'Extract all product names and prices',
  llm
);
```

## Core Patterns

- **Intent-based extraction** — describe data needs in natural language, LLM generates selectors per-run
- **Multi-step agent loop** — goal → plan → act → observe → repeat (max 20 steps with error recovery)
- **Self-healing selectors** — fallback chain: accessibility role → text match → LLM-generated CSS → visual similarity
- **API discovery** — intercept network calls to find hidden JSON APIs before scraping DOM
- **Stealth mode** — anti-bot evasion via realistic user-agent, viewport, and automation flag removal

## Technology Stack

| Component | Recommended | Alternatives |
|---|---|---|
| Browser Engine | Playwright | Puppeteer, Selenium |
| LLM | Claude 3.5 Sonnet | GPT-4o, Gemini 2.0 |
| Extraction | Crawl4AI | Firecrawl, Scrapling |
| Agent Framework | Browser-Use | Skyvern, Agent-E |

## Installation

### Claude Code

```bash
cp -R ai-agents/agentic-browser-automation ~/.claude/skills/agentic-browser-automation
```

### Cursor

```bash
cp -R ai-agents/agentic-browser-automation ~/.cursor/skills/agentic-browser-automation
```
