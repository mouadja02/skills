---
name: beeper
description: "Beeper local cache: contact hints, room lookup, WhatsApp/iMessage traces, FTS search."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# Beeper

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use this for local Beeper history questions, especially vague contact hints across iMessage/WhatsApp bridges.

## Source

- DB: `~/Library/Application Support/BeeperTexts/index.db`
- FTS: `mx_room_messages_fts`

Start by inspecting accounts/rooms before broad searching.

## Common Queries

### Inspect accounts and rooms

```bash
sqlite3 ~/Library/Application\ Support/BeeperTexts/index.db \
  "SELECT id, name, bridge_type FROM mx_rooms LIMIT 20"
```

### Search messages (FTS)

```bash
sqlite3 ~/Library/Application\ Support/BeeperTexts/index.db \
  "SELECT snippet(mx_room_messages_fts) FROM mx_room_messages_fts WHERE mx_room_messages_fts MATCH 'search term' LIMIT 10"
```

### Find contact by name

```bash
sqlite3 ~/Library/Application\ Support/BeeperTexts/index.db \
  "SELECT id, name, bridge_type FROM mx_rooms WHERE name LIKE '%contact name%' LIMIT 20"
```

### Get messages from a specific room

```bash
sqlite3 ~/Library/Application\ Support/BeeperTexts/index.db \
  "SELECT timestamp, sender, body FROM mx_room_messages WHERE room_id = '<room-id>' ORDER BY timestamp DESC LIMIT 20"
```

### Cross-bridge contact search

```bash
sqlite3 ~/Library/Application\ Support/BeeperTexts/index.db \
  "SELECT r.name, r.bridge_type, COUNT(m.id) as msg_count 
   FROM mx_rooms r 
   LEFT JOIN mx_room_messages m ON r.id = m.room_id 
   WHERE r.name LIKE '%search%' 
   GROUP BY r.id 
   LIMIT 20"
```

## Notes

- This is read-only local history — Beeper app must be installed.
- FTS (Full-Text Search) is faster for content search; use direct tables for structural queries.
- `bridge_type` identifies the messaging platform (e.g., `whatsapp`, `imessage`, `signal`).
