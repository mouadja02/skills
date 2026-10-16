# Phase 4: Tuning Data Lookup

Moved verbatim from SKILL.md so the entry file stays small. Read it when Phase 4 starts. Paths such as `./run/...` are relative to the working directory described in SKILL.md.

### Phase 4: Tuning Data Lookup

#### Objective
Lookup all the `Entries` using Fastah's `rfc8805-row-place-search` tool.

#### Execution Rules
- Generate a new **script** _only_ for payload generation (read the dataset and write one or more payload JSON files; do not call MCP from this script).
- Server only accepts 1000 entries per request, so if there are more than 1000 entries, split into multiple requests.
- The agent must read the generated payload files, construct the requests from them, and send those requests to the MCP server in batches of at most 1000 entries each.
- **On MCP failure:** If the MCP server is unreachable, returns an error, or returns no results for any batch, log a warning and continue to Phase 5. Set `TunedEntry: {}` for all affected entries. Do not block report generation. Notify the user clearly: `Tuning data lookup unavailable; the report will show validation results only.`
- Suggestions are **advisory only** — **never auto-populate** them.

#### Step 1: Build Lookup Payload with Deduplication

Load the dataset from: `./run/data/report-data.json`
- Read the `Entries` array. Each entry will be used to build the MCP lookup payload.

Reduce server requests by deduplicating identical entries:
- For each entry in `Entries`, compute a content hash (hash of `CountryCode` + `RegionCode` + `City`).
- Create a deduplication map: `{ contentHash -> { rowKey, payload, entryIndices: [] } }`. rowKey is a UUID that will be sent to the MCP server for matching responses.
- If an entry's hash already exists, append its **0-based array index** in `Entries` to that deduplication entry's `entryIndices` array.
- If hash is new, generate a **UUID (rowKey)** and create a new deduplication entry.

Build request batches:
- Extract unique deduplicated entries from the map, keeping them in deduplication order.
- Build request batches of up to 1000 items each.
- For each batch, keep an in-memory structure like `[{ rowKey, payload, entryIndices }, ...]` to match responses back by rowKey.
- When writing the MCP payload file, include the `rowKey` field with each payload object:

```json
[
    {"rowKey": "550e8400-e29b-41d4-a716-446655440000", "countryCode":"CA","regionCode":"CA-ON","cityName":"Toronto"},
    {"rowKey": "6ba7b810-9dad-11d1-80b4-00c04fd430c8", "countryCode":"IN","regionCode":"IN-KA","cityName":"Bangalore"},
    {"rowKey": "6ba7b811-9dad-11d1-80b4-00c04fd430c8", "countryCode":"IN","regionCode":"IN-KA"}
]
```

- When reading responses, match each response `rowKey` field to the corresponding deduplication entry to retrieve all associated `entryIndices`.

Rules:
- Write payload to: `./run/data/mcp-server-payload.json`
- Exit the script after writing the payload.

#### Step 2: Invoke Fastah MCP Tool

- An example `mcp.json` style configuration of Fastah MCP server is as follows:
```json
    "fastah-ip-geofeed": {
      "type": "http",
      "url": "https://mcp.fastah.ai/mcp"
    }
```
- Server: `https://mcp.fastah.ai/mcp`
- Tool and its Schema: before the first `tools/call`, the agent MUST send a `tools/list` request to read the input and output schema for **`rfc8805-row-place-search`**.
  Use the discovered schema as the authoritative source for field names, types, and constraints.
- The following is an illustrative example only; always defer to the schema returned by `tools/list`:

  ```json
  [
      {"rowKey": "550e8400-...", "countryCode":"CA", ...},
      {"rowKey": "690e9301-...", "countryCode":"ZZ", ...}
  ]
  ```
- Open `./run/data/mcp-server-payload.json` and send all deduplicated entries with their rowKeys.
- If there are more than 1000 deduplicated entries after deduplication, split into multiple requests of 1000 entries each.
- The server will respond with the same `rowKey` field in each response for mapping back.
- Do NOT use local data.

#### Step 3: Attach Tuned Data to Entries

- Generate a new **script** for attaching tuned data.
- Load both `./run/data/report-data.json` and the deduplication map (held in memory from Step 1, or re-derived from the payload file).
- For each response from the MCP server:
  - Extract the `rowKey` from the response.
  - Look up the `entryIndices` array associated with that `rowKey` from the deduplication map.
  - For each index in `entryIndices`, attach the best match to `Entries[index]`.
- Use the **first (best) match** from the response when available.

Create the field on each affected entry if it does not exist. Remap the MCP API response keys to Go struct field names:

```json
"TunedEntry": {
  "Name": "",
  "CountryCode": "",
  "RegionCode": "",
  "PlaceType": "",
  "H3Cells": [],
  "BoundingBox": []
}
```

The `TunedEntry` field is a **single object** (not an array). It holds the best match from the MCP server.

**MCP response key → JSON key mapping**:
| MCP API response key | JSON key                   |
|----------------------|----------------------------|
| `placeName`          | `Name`                     |
| `countryCode`        | `CountryCode`              |
| `stateCode`          | `RegionCode`               |
| `placeType`          | `PlaceType`                |
| `h3Cells`            | `H3Cells`                  |
| `boundingBox`        | `BoundingBox`              |

Entries with no UUID match (i.e. the MCP server returned no response for their UUID) must receive an empty `TunedEntry: {}` object — never leave the field absent.

- Write the dataset back to: `./run/data/report-data.json`
- Rules:
  - Maintain all existing validation flags.
  - Do NOT create additional intermediate files.
