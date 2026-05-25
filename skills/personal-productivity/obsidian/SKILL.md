---
name: obsidian
description: "Obsidian vault: search/read/write notes, backlinks, Bases, Canvas."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# Obsidian

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use this for local Obsidian vault work. An Obsidian vault is a normal folder of Markdown files plus `.obsidian/` config.

## Sources

- App config: `~/Library/Application Support/obsidian/obsidian.json`
- Usual local vault path: `~/obsidian` (or configured path)
- Official CLI: `obsidian` (if installed)

## Common Operations

### Search notes

```bash
# Search across all vault notes
rg "search term" ~/obsidian/ -l
rg "search term" ~/obsidian/ -n

# Search with context
rg "search term" ~/obsidian/ -C 3

# Find notes with specific tags
rg "#tag-name" ~/obsidian/ -l
```

### Read note

```bash
cat ~/obsidian/path/to/note.md
```

### Create/update note

```bash
# Create new note
cat > ~/obsidian/new-note.md <<'EOF'
---
tags: [tag1, tag2]
created: 2025-01-01
---

# Note Title

Content here.
EOF
```

### Find backlinks (notes that link to a note)

```bash
rg "\[\[Note Name\]\]" ~/obsidian/ -l
rg "\[.*\]\(path/to/note\.md\)" ~/obsidian/ -l
```

### List all notes

```bash
find ~/obsidian -name "*.md" -not -path "*/.obsidian/*"
```

## Notes

- Obsidian uses double-bracket links: `[[Note Name]]`
- Tags use `#tag` in note bodies or `tags: [tag]` in YAML frontmatter
- Never modify `.obsidian/` config files unless explicitly asked
- Preserve YAML frontmatter format when editing notes
