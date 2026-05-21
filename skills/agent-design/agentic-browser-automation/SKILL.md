---
name: "agentic-browser-automation"
description: "Build AI-powered browser agents that autonomously navigate, scrape, fill forms, and extract data from dynamic websites using LLM reasoning + Playwright. Use when the user wants to create a browser agent, build an autonomous scraper, implement self-healing selectors, replace brittle browser automation with AI, build a web agent, use Browser-Use or Skyvern patterns, extract structured data from any website using natural language, or create adaptive web scrapers that survive site changes."
---

# Agentic Browser Automation

**Tier:** POWERFUL
**Category:** AI Agents
**Domain:** Browser Automation / Web Scraping / Agentic Workflows

## Overview

Build autonomous browser agents that use LLMs to reason about web pages and perform multi-step tasks — navigating, clicking, filling forms, extracting data, and recovering from failures — without hardcoded selectors. This replaces brittle CSS/XPath scraping with intent-driven, self-healing automation.

## When to Use

- Building a web scraper that survives site redesigns
- Creating an agent that fills forms or completes multi-step web workflows
- Replacing fragile Selenium/Puppeteer scripts with AI-driven automation
- Extracting structured data from any website using natural language
- Building autonomous research agents that browse and collect info
- Implementing self-healing selectors that adapt to DOM changes
- Creating Browser-Use / Skyvern-style agentic browser workflows

## Architecture

```
┌─────────────────────────────────────┐
│          Orchestrator               │
│  (Breaks goal into browser steps)   │
├─────────────────────────────────────┤
│       LLM Reasoning Layer           │
│  • Page understanding (DOM→action)  │
│  • Selector generation (NL→CSS)     │
│  • Error recovery (failure→retry)   │
│  • Data extraction (page→JSON)      │
├─────────────────────────────────────┤
│      Browser Control Layer          │
│  Playwright / Puppeteer             │
│  • Navigation, clicks, typing       │
│  • Screenshot + accessibility tree  │
│  • Network interception (API disc.) │
│  • Stealth mode (anti-bot evasion)  │
├─────────────────────────────────────┤
│         Output Layer                │
│  Structured JSON / CSV / DB         │
└─────────────────────────────────────┘
```

## Core Patterns

### 1. Intent-Based Extraction (Zero-Selector)

Describe what you want in natural language instead of hardcoding selectors:

```typescript
async function extractWithIntent(url: string, intent: string, llm: LLMClient) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle' });

  // Use accessibility tree — much smaller than raw DOM
  const snapshot = await page.accessibility.snapshot();
  const result = await llm.complete(`
    Extract data matching: "${intent}"
    Page structure: ${JSON.stringify(snapshot)}
    Return only valid JSON array.
  `);
  await browser.close();
  return JSON.parse(result);
}
```

### 2. Multi-Step Agent Loop

```typescript
async function agentLoop(goal: string, page: Page, llm: LLMClient) {
  const history: ActionResult[] = [];
  for (let i = 0; i < 20; i++) { // max 20 steps
    const tree = await page.accessibility.snapshot();
    const action = await llm.complete(`
      Goal: ${goal}
      Current URL: ${page.url()}
      History: ${JSON.stringify(history.slice(-5))}
      Page: ${JSON.stringify(tree)}
      Return JSON: { type, selector?, value?, reason }
      Types: click | type | navigate | scroll | extract | done
    `);
    const parsed = JSON.parse(action);
    if (parsed.type === 'done') return parsed.data;
    try {
      await executeAction(page, parsed);
      history.push({ ...parsed, success: true });
    } catch (e) {
      history.push({ ...parsed, success: false, error: e.message });
    }
  }
}
```

### 3. Self-Healing Selectors

```typescript
async function findElementAdaptive(page: Page, description: string, llm: LLMClient) {
  // Strategy 1: Accessibility role
  const byRole = await page.$(`role=${guessRole(description)}`).catch(() => null);
  if (byRole) return byRole;
  // Strategy 2: Text content
  const byText = await page.getByText(extractText(description)).first();
  if (byText) return byText;
  // Strategy 3: LLM generates selector from simplified DOM
  const dom = await getSimplifiedDOM(page);
  const selector = await llm.complete(
    `CSS selector for "${description}" in: ${dom}. Return selector only.`
  );
  return await page.$(selector.trim());
}
```

### 4. API Discovery (Network-First)

Before scraping DOM, check if there's a hidden JSON API:

```typescript
async function discoverAPIs(page: Page, url: string) {
  const apis: any[] = [];
  page.on('response', async (r) => {
    if ((r.headers()['content-type'] || '').includes('json')) {
      apis.push({ url: r.url(), method: r.request().method() });
    }
  });
  await page.goto(url, { waitUntil: 'networkidle' });
  await autoScroll(page);
  return apis;
}
```

### 5. Stealth Configuration

```typescript
const context = await browser.newContext({
  userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...',
  viewport: { width: 1920, height: 1080 },
  locale: 'en-US',
  timezoneId: 'America/New_York',
});
await context.addInitScript(() => {
  Object.defineProperty(navigator, 'webdriver', { get: () => false });
});
```

## Technology Stack

| Component | Recommended | Alternatives |
|---|---|---|
| Browser Engine | Playwright | Puppeteer, Selenium |
| LLM | Claude 3.5 Sonnet | GPT-4o, Gemini 2.0 |
| Extraction | Crawl4AI | Firecrawl, Scrapling |
| Agent Framework | Browser-Use | Skyvern, Agent-E |
| Validation | Zod | Pydantic (Python) |

## Common Pitfalls

1. **Sending raw HTML to LLM** — Use accessibility tree or simplified DOM instead
2. **Not handling dynamic content** — Always wait for network idle or specific elements
3. **Ignoring API endpoints** — Many SPAs have JSON APIs easier than DOM scraping
4. **No rate limiting** — Always add delays and respect robots.txt
5. **No error budget** — Set max retries and max cost limits per task
6. **Screenshot-only reasoning** — Combine screenshots with accessibility tree

## Security & Ethics

- Respect `robots.txt` and rate limit (max 1 req/sec default)
- Include descriptive `User-Agent` identifying your bot
- Do not scrape personal data without consent (GDPR/CCPA)
- Set cost guardrails (max LLM tokens per task)
- Log all agent actions for auditability
