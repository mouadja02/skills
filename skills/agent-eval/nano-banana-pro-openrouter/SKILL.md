---
name: nano-banana-pro-openrouter
description: 'Generate or edit images via OpenRouter with the Gemini 3 Pro Image model'
version: "1.0.1"
metadata:
  emoji: 🍌
  requires:
    bins:
      - uv
    env:
      - OPENROUTER_API_KEY
  primaryEnv: OPENROUTER_API_KEY
---


# Nano Banana Pro OpenRouter

## Overview

Generate or edit images with OpenRouter using the `google/gemini-3-pro-image-preview` model. Support prompt-only generation, single-image edits, and multi-image composition.

### Prompt-only generation

```
uv run {baseDir}/scripts/generate_image.py \
  --prompt "A cinematic sunset over snow-capped mountains" \
  --filename sunset.png
```

### Edit a single image

```
uv run {baseDir}/scripts/generate_image.py \
  --prompt "Replace the sky with a dramatic aurora" \
  --input-image input.jpg \
  --filename aurora.png
```

### Compose multiple images

```
uv run {baseDir}/scripts/generate_image.py \
  --prompt "Combine the subjects into a single studio portrait" \
  --input-image face1.jpg \
  --input-image face2.jpg \
  --filename composite.png
```

## Resolution

- Use `--resolution` with `1K`, `2K`, or `4K`.
- Default is `1K` if not specified.

## System prompt customization

The skill reads an optional system prompt from `assets/SYSTEM_TEMPLATE`. This allows you to customize the image generation behavior without modifying code.

## Behavior and constraints

- Accept up to 3 input images via repeated `--input-image`.
- `--filename` accepts relative paths (saves to current directory) or absolute paths.
- If multiple images are returned, append `-1`, `-2`, etc. to the filename.
- Print `MEDIA: <path>` for each saved image. Do not read images back into the response.

## Troubleshooting

If the script exits non-zero, check stderr against these common blockers:

| Symptom | Resolution |
|---------|------------|
| `OPENROUTER_API_KEY is not set` | Ask the user to set it. PowerShell: `$env:OPENROUTER_API_KEY = "sk-or-..."` / bash: `export OPENROUTER_API_KEY="sk-or-..."` |
| `uv: command not found` or not recognized | Install `uv` with a package manager when available: `brew install uv` on macOS or `winget install --id astral-sh.uv -e` on Windows. For the standalone installer, download it to a file, inspect it, and execute that saved file as shown below. Then restart the terminal. |
| `AuthenticationError` / HTTP 401 | Key is invalid or has no credits. Verify at <https://openrouter.ai/settings/keys>. |

Standalone installer fallback:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh -o uv-install.sh
less uv-install.sh
sh uv-install.sh
rm uv-install.sh
```

```powershell
# Windows PowerShell
Invoke-WebRequest https://astral.sh/uv/install.ps1 -OutFile uv-install.ps1
Get-Content uv-install.ps1 | More
powershell -ExecutionPolicy ByPass -File .\uv-install.ps1
Remove-Item .\uv-install.ps1
```

Do not execute the downloaded installer until its contents have been reviewed.
The canonical installation options are documented at
<https://docs.astral.sh/uv/getting-started/installation/>.

For transient errors (HTTP 429, network timeouts), retry once after 30 seconds. Do not retry the same error more than twice — surface the issue to the user instead.
