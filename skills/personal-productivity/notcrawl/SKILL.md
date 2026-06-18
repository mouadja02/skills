---
name: notcrawl
description: "Notion archive: desktop/API sync, Markdown export, page search, read-only SQL."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
version: "1.0.0"
---

# notcrawl

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

## When to Use

- Searching or reading from a local Notion archive
- Syncing Notion content via desktop cache or API
- Exporting Notion pages to Markdown

Use this for local Notion archive questions. Desktop reads local cache; API sync needs `NOTION_TOKEN` and page access.

## Sources

- DB: `~/.notcrawl/notcrawl.db`
- Pages: `~/.notcrawl/pages`
- CLI: `notcrawl`

## Common Operations

### Search pages

```bash
notcrawl search "search term"
notcrawl search "search term" --limit 20
```

### Read a page

```bash
notcrawl page <page-id>
notcrawl page <page-id> --format markdown
```

### List pages

```bash
notcrawl list
notcrawl list --type database
```

### Sync from Notion API

```bash
NOTION_TOKEN="your-token" notcrawl sync
```

### Direct SQLite query

```bash
sqlite3 ~/.notcrawl/notcrawl.db "SELECT title, url FROM pages WHERE title LIKE '%search%' LIMIT 10"
```

## Notes

- Desktop reads are local/cached — good for search, old thread review, discovery.
- API sync requires `NOTION_TOKEN` and appropriate Notion integration access.
- The local DB is read-only from this tool's perspective; do not modify it.
- Page IDs are UUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
