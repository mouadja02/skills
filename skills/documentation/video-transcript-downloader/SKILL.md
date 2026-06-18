---
name: video-transcript-downloader
description: "yt-dlp video downloads: video, audio, subtitles, transcripts, clips, playlists — YouTube and more."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
version: "1.0.0"
---

# Video Transcript Downloader

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

## When to Use

- Downloading video, audio, or subtitle tracks from YouTube and other platforms
- Extracting transcripts or captions for content analysis
- Clipping segments or downloading playlists via yt-dlp

Download and extract transcripts/video/audio from YouTube and other video platforms using `yt-dlp`.

## Capabilities

- Print a transcript as a clean paragraph (timestamps optional).
- Download video/audio/subtitles.

Transcript behavior:
- YouTube: fetch via `youtube-transcript-plus` when possible.
- Otherwise: pull subtitles via `yt-dlp`, then clean into a paragraph.

## Transcript

```bash
# Clean paragraph transcript (default)
yt-dlp --write-auto-subs --skip-download --sub-format vtt --sub-langs en URL
# Or use yt-dlp subtitles

# With timestamps
yt-dlp --write-auto-subs --skip-download --convert-subs srt --sub-langs en URL
```

## Download Video / Audio / Subtitles

```bash
# Video
yt-dlp URL -o '%(title)s.%(ext)s'

# Audio only
yt-dlp -x --audio-format mp3 URL

# Subtitles
yt-dlp --write-subs --skip-download --sub-langs en URL

# List available formats
yt-dlp -F URL

# Download specific format
yt-dlp -f 137+140 URL

# Prefer MP4 without re-encoding
yt-dlp --remux-video mp4 URL
```

## Notes

- Default transcript output is a single paragraph. Use timestamp-preserving formats only when asked.
- Bracketed cues like `[Music]` appear in auto-generated subtitles; filter with `sed` or `grep -v '^\[' `.
- For playlists: `yt-dlp --yes-playlist URL`

## Troubleshooting

```bash
# Install dependencies
brew install yt-dlp ffmpeg

# Verify
yt-dlp --version
ffmpeg -version | head -n 1
```
