---
name: openai-image-gen
description: "OpenAI Images API: batches, prompt sampler, gallery — gpt-image-1 and variants."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# OpenAI Image Gen

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Generate images via OpenAI Images API with batch support and an auto-generated HTML gallery.

## Setup

- Requires `OPENAI_API_KEY` environment variable.
- Requires Python 3 and the `openai` package.

## Usage

```bash
# Basic run (generates random structured prompts)
python3 gen.py

# Custom count
python3 gen.py --count 16

# Custom model
python3 gen.py --model gpt-image-1.5

# Custom prompt
python3 gen.py --prompt "ultra-detailed studio photo of a lobster astronaut" --count 4

# Custom size and quality
python3 gen.py --size 1536x1024 --quality high --out-dir ./out/images
```

## Output

- `*.png` images in the output directory
- `prompts.json` (prompt ↔ file mapping)
- `index.html` (thumbnail gallery for quick review)

```bash
# Open gallery
open ~/tmp/openai-image-gen-*/index.html
```

## Common Options

| Flag | Description |
|------|-------------|
| `--count N` | Number of images to generate |
| `--model MODEL` | Model to use (e.g., `gpt-image-1`, `gpt-image-1.5`) |
| `--prompt TEXT` | Custom prompt (overrides random generation) |
| `--size WxH` | Image size (e.g., `1024x1024`, `1536x1024`) |
| `--quality LEVEL` | Quality level (`standard`, `high`) |
| `--out-dir PATH` | Output directory |
