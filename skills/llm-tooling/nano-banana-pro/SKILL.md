---
name: nano-banana-pro
description: "Gemini image gen/edit via Nano Banana: text/image input, 512-4K workflows, draft→iterate→final."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# Nano Banana Pro — Gemini Image Generation & Editing

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Generate new images or edit existing ones using Google's Gemini Flash Image API (Gemini 3.1 Flash Image).

## Prerequisites

- `uv` installed (`brew install uv`)
- `GEMINI_API_KEY` environment variable set

## Usage

**Generate new image:**
```bash
uv run generate_image.py --prompt "your image description" --filename "output-name.png" [--resolution 512|1K|2K|4K] [--api-key KEY]
```

**Edit existing image:**
```bash
uv run generate_image.py --prompt "editing instructions" --filename "output-name.png" --input-image "path/to/input.png" [--resolution 512|1K|2K|4K]
```

## Default Workflow (draft → iterate → final)

Goal: fast iteration without burning time on 4K until the prompt is correct.

1. **Draft (1K)**: quick feedback loop
   ```bash
   uv run generate_image.py --prompt "<draft prompt>" --filename "$(date +%Y-%m-%d-%H-%M-%S)-draft.png" --resolution 1K
   ```

2. **Iterate**: adjust prompt in small diffs; keep filename new per run.

3. **Final (4K)**: only when prompt is locked
   ```bash
   uv run generate_image.py --prompt "<final prompt>" --filename "$(date +%Y-%m-%d-%H-%M-%S)-final.png" --resolution 4K
   ```

## Resolution Options

| Input | API Value |
|-------|-----------|
| "thumbnail", "tiny", "512" | `512` |
| Default (no mention) | `1K` |
| "1080p", "1K" | `1K` |
| "2K", "2048", "medium" | `2K` |
| "high-res", "4K", "ultra" | `4K` |

## Prompt Templates

**Generation:**
> "Create an image of: `<subject>`. Style: `<style>`. Composition: `<camera/shot>`. Lighting: `<lighting>`. Background: `<background>`. Color palette: `<palette>`. Avoid: `<list>`."

**Editing (preserve everything else):**
> "Change ONLY: `<single change>`. Keep identical: subject, composition/crop, pose, lighting, color palette, background, and overall style. Do not add new objects."

## Preflight & Common Failures

```bash
# Preflight
command -v uv
echo ${GEMINI_API_KEY:0:5}...  # show prefix only
```

Common failures:
- `Error: No API key provided.` → set `GEMINI_API_KEY` or pass `--api-key`
- `Error loading input image:` → wrong path; verify `--input-image` points to a real image
- `quota/permission/403` → wrong key, no access, or quota exceeded
