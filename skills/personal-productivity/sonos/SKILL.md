---
name: sonos
description: "Sonos control: search, queue, playlists, rooms/groups, volume, YouTube playback."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
version: "1.0.0"
platform: macos
---

# Sonos

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use for Sonos music, playback, queue, room/group, and YouTube workflows.

## When to Use

- Controlling Sonos speakers: play, pause, volume, queue management
- Discovering speakers on the local network via mDNS
- Managing Sonos room groups and playback state

## Rules

- Prefer existing local Sonos tooling in the current repo before inventing shell/API calls.
- Do not change speaker groups, queues, or playback unless the user asks for it.

## Sonos API (HTTP)

Sonos exposes a local HTTP API at `http://<speaker-ip>:1400/`:

```bash
# Discover speakers
dns-sd -B _sonos._tcp local

# Get current state
curl -s http://<speaker-ip>:1400/state

# Play/pause
curl -s http://<speaker-ip>:1400/Play
curl -s http://<speaker-ip>:1400/Pause

# Volume
curl -s http://<speaker-ip>:1400/Volume  # get
curl -s "http://<speaker-ip>:1400/Volume?Volume=50"  # set

# Queue
curl -s http://<speaker-ip>:1400/Queue  # get queue
curl -s "http://<speaker-ip>:1400/Queue?detailed=1"  # with metadata
```

## Sonos CLI Tools

If a Sonos CLI tool is available in the current environment:

```bash
# Common operations
sonos play
sonos pause
sonos stop
sonos volume 50
sonos next
sonos previous
sonos queue
```

## Notes

- Speaker discovery uses mDNS (`_sonos._tcp`).
- Group operations require the coordinator's IP.
- Do not modify playback/groups without explicit user request.
