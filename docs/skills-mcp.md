# Local Skills MCP Quickstart

Use the local Skills MCP server when you want an agent to discover this repo's skills without loading the whole library into its context window.

Keep this server local by default. It is a stdio MCP server: your MCP client starts a local Node.js process, the process reads this cloned repository, and tools return only the small slices the agent asks for.

## What You Get

- Compact category and skill discovery.
- Search across skill names, install paths, and descriptions.
- On-demand reads of `SKILL.md`, category docs, and bundled reference files.
- A guided workflow that nudges agents to narrow first and read full docs last.
- Optional copying of selected skills into a workspace skills directory.
- No network service, hosting, database, auth, or runtime npm dependencies.

## Prerequisites

- Node.js 18 or newer.
- A local clone of this repository.
- An MCP-capable client that supports stdio servers.

## 1. Clone And Prepare

```bash
git clone https://github.com/mouadja02/skills.git
cd skills
npm install
npm run build:manifest
```

`npm run build:manifest` refreshes `docs/manifest.json`, which the MCP server uses as its compact index.

## 2. Add The MCP Server To Your Client

Configure your MCP client to run the server directly with `node`.

By default, the server tries to refresh the local clone before the first tool call in each MCP server process. It runs `git pull --ff-only` and then reloads the checked-in `docs/manifest.json`. If the repo has local changes, refresh is skipped to avoid overwriting work.

Windows example:

```json
{
  "mcpServers": {
    "repo-skills": {
      "command": "node",
      "args": ["C:/Users/mouad/Desktop/skills/scripts/skills-mcp.mjs"],
      "cwd": "C:/Users/mouad/Desktop/skills"
    }
  }
}
```

macOS/Linux example:

```json
{
  "mcpServers": {
    "repo-skills": {
      "command": "node",
      "args": ["/Users/you/src/skills/scripts/skills-mcp.mjs"],
      "cwd": "/Users/you/src/skills"
    }
  }
}
```

Disable auto-refresh in MCP JSON when you need fully offline or pinned behavior:

```json
{
  "mcpServers": {
    "repo-skills": {
      "command": "node",
      "args": ["C:/Users/mouad/Desktop/skills/scripts/skills-mcp.mjs"],
      "cwd": "C:/Users/mouad/Desktop/skills",
      "env": {
        "SKILLS_MCP_AUTO_REFRESH": "false"
      }
    }
  }
}
```

You can also disable it with an argument:

```json
{
  "mcpServers": {
    "repo-skills": {
      "command": "node",
      "args": [
        "C:/Users/mouad/Desktop/skills/scripts/skills-mcp.mjs",
        "--no-auto-refresh"
      ],
      "cwd": "C:/Users/mouad/Desktop/skills"
    }
  }
}
```

Use absolute paths. Replace the paths with your local clone path.

Do not configure a client with plain `npm run mcp`: npm writes banners to stdout, and stdio MCP servers must write only JSON-RPC messages to stdout. If you run it manually through npm, use:

```bash
npm --silent run mcp
```

## 3. Ask The Agent To Discover Skills

Give the agent a workflow like this:

```text
Use the repo-skills MCP server. Do not load the whole skill library.
First call list_categories. Pick the most relevant category, then call list_skills.
Use get_skill for previews. Only call read_skill_doc for the final selected skills.
If a skill is useful, install it into this workspace's .claude/skills directory.
```

The intended interaction is:

1. `list_categories`
2. `list_skills` for one category, or `search_skills` when the category is unclear
3. `get_skill` for metadata, bundled files, and a short preview
4. `read_skill_doc` only for selected skills
5. `list_skill_files` and `read_skill_file` only for needed references
6. `install_skill` when the agent should copy a chosen skill into the workspace

This order keeps context usage small.

## 4. Install A Skill Into A Workspace

To copy one selected skill into a Claude project:

```json
{
  "skill": "coding/nasa-inspired-coding-rules",
  "destination": "C:/path/to/project/.claude/skills",
  "overwrite": false
}
```

This creates:

```text
C:/path/to/project/.claude/skills/nasa-inspired-coding-rules
```

To preserve category folders:

```json
{
  "skill": "coding/nasa-inspired-coding-rules",
  "destination": "C:/path/to/project/.claude/skills",
  "preserve_path": true,
  "overwrite": false
}
```

This creates:

```text
C:/path/to/project/.claude/skills/coding/nasa-inspired-coding-rules
```

## Available Tools

| Tool | Use |
| --- | --- |
| `list_categories` | Start here. Returns category names and counts. |
| `list_skills` | Lists compact skill metadata for one category. Supports filtering and pagination. |
| `search_skills` | Searches all skill names, install paths, and descriptions. |
| `get_skill` | Returns one skill's metadata, file list, and short preview. |
| `read_skill_doc` | Reads one selected skill's `SKILL.md`. |
| `read_category_doc` | Reads one category's `README.md`. |
| `list_skill_files` | Lists bundled files for one skill. |
| `read_skill_file` | Reads a supporting file inside one skill folder. |
| `install_skill` | Copies one skill folder into a target workspace directory. |

## Manual Smoke Test

PowerShell:

```powershell
@'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_categories","arguments":{}}}
'@ | node scripts\skills-mcp.mjs
```

bash/zsh:

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_categories","arguments":{}}}' \
  | node scripts/skills-mcp.mjs
```

You should see JSON-RPC responses, including a `tools/list` result and a category list.

## Updating The Local Index

Auto-refresh handles ordinary updates when the MCP client starts a new server process. Run this manually after adding, editing, pulling, or reorganizing skills yourself:

```bash
npm run build:manifest
```

Restart your MCP client after updating the repo if it keeps long-lived MCP server processes.

Auto-refresh behavior:

- Runs once before the first `tools/call`.
- Uses `git pull --ff-only`, so it will not create merge commits.
- Reloads the checked-in `docs/manifest.json` after a successful pull.
- Skips when the repository has local changes.
- Reports refresh status in each tool response under `server.auto_refresh`.
- Disable with `SKILLS_MCP_AUTO_REFRESH=false` or `--no-auto-refresh`.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Client says server returned invalid JSON | Make sure the MCP config runs `node .../scripts/skills-mcp.mjs` directly, not plain `npm run mcp`. |
| `docs/manifest.json` is missing or stale | Run `npm run build:manifest` from the repo root. |
| Auto-refresh is skipped | Check for local changes with `git status`; commit, stash, or disable auto-refresh. |
| Auto-refresh fails offline | Set `SKILLS_MCP_AUTO_REFRESH=false` for offline sessions. |
| Skill name is ambiguous | Use the full `install_path`, for example `coding/test-driven-development`. |
| `install_skill` says destination exists | Pick another destination or pass `"overwrite": true`. |
| Agent loads too much context | Tell it to use `list_categories`, `list_skills`, and `get_skill` before `read_skill_doc`. |
| Paths fail on Windows | Use absolute paths with forward slashes or escaped backslashes in JSON. |

## Why Local, Not Hosted

Local stdio is the recommended default for this repo:

- It can copy skills directly into local workspaces.
- It avoids exposing your full skills library over the network.
- It needs no auth or hosting maintenance.
- It is fast because it reads local files and a local manifest.

Only build a hosted HTTP MCP later if remote/cloud agents need access from machines where the repo is not cloned.
