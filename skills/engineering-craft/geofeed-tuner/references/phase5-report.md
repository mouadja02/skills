# Phase 5: Generate Tuning Report

Moved verbatim from SKILL.md so the entry file stays small. Read it when Phase 5 starts. Paths such as `./run/...` and `./scripts/...` are relative to the working directory described in SKILL.md.

### Phase 5: Generate Tuning Report

Generate a **self-contained HTML report** by rendering the template at `./scripts/templates/index.html` with data from `./run/data/report-data.json` and `./run/data/comments.json`.

Write the completed report to `./run/report/geofeed-report.html`. After generating, attempt to open it in the system's default browser (e.g., `webbrowser.open()`). If running in a headless environment, CI pipeline, or remote container where no browser is available, skip the browser step and instead present the file path to the user so they can open or download it.

**The template uses Go `html/template` syntax** (`{{.Field}}`, `{{range}}`, `{{if eq}}`, etc.). Write a Python script that reads the template, builds a rendering context from the JSON data files, and processes the template placeholders to produce final HTML. Do not modify the template file itself — all processing happens in the Python script at render time.

#### Step 1: Replace Metadata Placeholders

Replace each `{{.Metadata.X}}` placeholder in the template with the corresponding value from `report-data.json`. Since JSON keys match the template placeholder, the mapping is direct — `{{.Metadata.InputFile}}` maps to the `InputFile` JSON key, etc.

| Template placeholder                   | JSON key (`report-data.json`)     |
|----------------------------------------|-----------------------------------|
| `{{.Metadata.InputFile}}`              | `InputFile`                       |
| `{{.Metadata.Timestamp}}`              | `Timestamp`                       |
| `{{.Metadata.TotalEntries}}`           | `TotalEntries`                    |
| `{{.Metadata.IpV4Entries}}`            | `IpV4Entries`                     |
| `{{.Metadata.IpV6Entries}}`            | `IpV6Entries`                     |
| `{{.Metadata.InvalidEntries}}`         | `InvalidEntries`                  |
| `{{.Metadata.Errors}}`                 | `Errors`                          |
| `{{.Metadata.Warnings}}`               | `Warnings`                        |
| `{{.Metadata.Suggestions}}`            | `Suggestions`                     |
| `{{.Metadata.OK}}`                     | `OK`                              |
| `{{.Metadata.CityLevelAccuracy}}`      | `CityLevelAccuracy`               |
| `{{.Metadata.RegionLevelAccuracy}}`    | `RegionLevelAccuracy`             |
| `{{.Metadata.CountryLevelAccuracy}}`   | `CountryLevelAccuracy`            |
| `{{.Metadata.DoNotGeolocate}}`         | `DoNotGeolocate` (metadata)       |

**Note on `{{.Metadata.Timestamp}}`:** This placeholder appears inside a JavaScript `new Date(...)` call. Replace it with the raw integer value (no HTML escaping needed for a numeric literal inside `<script>`). All other metadata values should be HTML-escaped since they appear inside HTML element text.

#### Step 2: Replace the Comment Map Placeholder

Locate this pattern in the template:
```javascript
const commentMap = {{.Comments}};
```

Replace `{{.Comments}}` with the serialized JSON object from `./run/data/comments.json`. The JSON is embedded directly as a JavaScript object literal (not inside a string), so no extra escaping is needed:

```python
comments_json = json.dumps(comments)
template = template.replace("{{.Comments}}", comments_json)
```

#### Step 3: Expand the Entries Range Block

The template contains a `{{range .Entries}}...{{end}}` block inside `<tbody id="entriesTableBody">`. Process it as follows:

1. **Extract** the range block body using regex. **Critical:** The block contains nested `{{end}}` tags (from `{{if eq .Status ...}}`, `{{if .Checked}}`, and `{{range .Messages}}`). A naive non-greedy match like `\{\{range \.Entries\}\}(.*?)\{\{end\}\}` will match the **first** inner `{{end}}`, truncating the block. Instead, anchor the outer `{{end}}` to the `</tbody>` that follows it:
    ```python
    m = re.search(
        r'\{\{range \.Entries\}\}(.*?)\{\{end\}\}\s*</tbody>',
        template,
        re.DOTALL,
    )
    entry_body = m.group(1)  # template text for one entry iteration
    ```
    This ensures you capture the full block body including all three `<tr>` rows and the nested `{{range .Messages}}...{{end}}`.
2. **Iterate** over each entry in `report-data.json`'s `Entries` array.
3. **Expand** the block body for each entry using the processing order below.
4. **Replace** the entire match (from `{{range .Entries}}` through `</tbody>`) with the concatenated expanded HTML followed by `</tbody>`.

**Processing order for each entry** (innermost constructs first to avoid `{{end}}` confusion):
1. Evaluate `{{if eq .Status ...}}...{{end}}` conditionals (status badge class and icon).
2. Evaluate `{{if .Checked}}...{{end}}` conditional (message checkbox).
3. Expand `{{range .Messages}}...{{end}}` inner range.
4. Replace simple `{{.Field}}` placeholders.

##### Entry Field Mapping

Within the range block body, replace these placeholders for each entry. Since JSON keys match the template placeholder, the template placeholder `{{.X}}` maps directly to JSON key `X`:

| Template placeholder           | JSON key (`Entries[]`)       | Notes                                                        |
|--------------------------------|------------------------------|--------------------------------------------------------------|
| `{{.Line}}`                    | `Line`                       | Direct integer value                                         |
| `{{.IPPrefix}}`                | `IPPrefix`                   | HTML-escaped                                                 |
| `{{.CountryCode}}`             | `CountryCode`                | HTML-escaped                                                 |
| `{{.RegionCode}}`              | `RegionCode`                 | HTML-escaped                                                 |
| `{{.City}}`                    | `City`                       | HTML-escaped                                                 |
| `{{.Status}}`                  | `Status`                     | HTML-escaped                                                 |
| `{{.HasError}}`                | `HasError`                   | Lowercase string: `"true"` or `"false"`                      |
| `{{.HasWarning}}`              | `HasWarning`                 | Lowercase string: `"true"` or `"false"`                      |
| `{{.HasSuggestion}}`           | `HasSuggestion`              | Lowercase string: `"true"` or `"false"`                      |
| `{{.GeocodingHint}}`           | `GeocodingHint`              | Empty string `""`                                            |
| `{{.DoNotGeolocate}}`          | `DoNotGeolocate`             | `"true"` or `"false"`                                        |
| `{{.Tunable}}`                 | `Tunable`                    | `"true"` or `"false"`                                        |
| `{{.TunedEntry.CountryCode}}`  | `TunedEntry.CountryCode`     | `""` if `TunedEntry` is empty `{}`                           |
| `{{.TunedEntry.RegionCode}}`   | `TunedEntry.RegionCode`      | `""` if `TunedEntry` is empty `{}`                           |
| `{{.TunedEntry.Name}}`         | `TunedEntry.Name`            | `""` if `TunedEntry` is empty `{}`                           |
| `{{.TunedEntry.H3Cells}}`      | `TunedEntry.H3Cells`         | Bracket-wrapped space-separated; `"[]"` if empty (see format below) |
| `{{.TunedEntry.BoundingBox}}`  | `TunedEntry.BoundingBox`     | Bracket-wrapped space-separated; `"[]"` if empty (see format below) |

**`data-h3-cells` and `data-bounding-box` format:** These are **NOT JSON arrays**. They are bracket-wrapped, space-separated values. Do **not** use JSON serialization (no quotes around string elements, no commas between numbers). Examples:
- `[836752fffffffff 836755fffffffff]` — correct
- `["836752fffffffff","836755fffffffff"]` — **WRONG**, quotes will break parsing
- `[-71.70 10.73 -71.52 10.55]` — correct
- `[]` — correct for empty

##### Evaluating Status Conditionals

**Process these BEFORE replacing simple `{{.Field}}` placeholders** — otherwise the `{{end}}` markers get consumed and the regex won't match.

The template uses `{{if eq .Status "..."}}` conditionals for the status badge CSS class and icon. Evaluate these by checking the entry's `status` value and keeping only the matching branch text.

The status badge line contains **two** `{{if eq .Status ...}}...{{end}}` blocks on a single line — one for the CSS class, one for the icon. Use `re.sub` with a callback to resolve all occurrences:

```python
STATUS_CSS = {"ERROR": "error", "WARNING": "warning", "SUGGESTION": "suggestion", "OK": "ok"}
STATUS_ICON = {
    "ERROR": "bi-x-circle-fill",
    "WARNING": "bi-exclamation-triangle-fill",
    "SUGGESTION": "bi-lightbulb-fill",
    "OK": "bi-check-circle-fill",
}

def resolve_status_if(match_obj, status):
    """Pick the branch matching `status` from a {{if eq .Status ...}}...{{end}} block."""
    block = match_obj.group(0)
    # Try each branch: {{if eq .Status "X"}}val{{else if ...}}val{{else}}val{{end}}
    for st, val in [("ERROR",), ("WARNING",), ("SUGGESTION",)]:
        # not needed to parse generically — just map from the known patterns
    ...
```

A simpler approach: since there are exactly two known patterns, replace them as literal strings:
```python
css_class = STATUS_CSS.get(status, "ok")
icon_class = STATUS_ICON.get(status, "bi-check-circle-fill")
body = body.replace(
    '{{if eq .Status "ERROR"}}error{{else if eq .Status "WARNING"}}warning{{else if eq .Status "SUGGESTION"}}suggestion{{else}}ok{{end}}',
    css_class,
)
body = body.replace(
    '{{if eq .Status "ERROR"}}bi-x-circle-fill{{else if eq .Status "WARNING"}}bi-exclamation-triangle-fill{{else if eq .Status "SUGGESTION"}}bi-lightbulb-fill{{else}}bi-check-circle-fill{{end}}',
    icon_class,
)
```
This avoids regex entirely and is safe because these exact strings appear verbatim in the template.

#### Step 4: Expand the Nested Messages Range

The `{{range .Messages}}...{{end}}` block contains a **nested** `{{if .Checked}} checked{{else}} disabled{{end}}` conditional, so its inner `{{end}}` would cause a simple non-greedy regex to match too early. Anchor the regex to `</td>` (the tag immediately after the messages range closing `{{end}}`) to capture the full block body:

```python
msg_match = re.search(
    r'\{\{range \.Messages\}\}(.*?)\{\{end\}\}\s*(?=</td>)',
    body, re.DOTALL
)
```

The lookahead `(?=</td>)` ensures the regex skips past the checkbox conditional's `{{end}}` (which is followed by `>`, not `</td>`) and matches only the range-closing `{{end}}` (which is followed by whitespace then `</td>`).

For each message in the entry's `Messages` array, clone the captured block body and expand it:

1. **Resolve the checkbox conditional** per message (must happen before simple placeholder replacement to remove the nested `{{end}}`):
   ```python
   if msg.get("Checked"):
       msg_body = msg_body.replace(
           '{{if .Checked}} checked{{else}} disabled{{end}}', ' checked'
       )
   else:
       msg_body = msg_body.replace(
           '{{if .Checked}} checked{{else}} disabled{{end}}', ' disabled'
       )
   ```

2. **Replace message field placeholders**:

   | Template placeholder | Source                            | Notes                          |
   |--------------------------|-----------------------------------|--------------------------------|
   | `{{.ID}}`                | `Messages[i].ID`                  | Direct string value from JSON  |
   | `{{.Text}}`              | `Messages[i].Text`                | HTML-escaped                   |

3. **Concatenate** all expanded message blocks and replace the original `{{range .Messages}}...{{end}}` match (`msg_match.group(0)`) with the result:
   ```python
   body = body[:msg_match.start()] + "".join(expanded_msgs) + body[msg_match.end():]
   ```

If `Messages` is empty, replace the entire matched region with an empty string (no message divs — only the issues header remains).

#### Output Guarantees

- The report must be readable in any modern browser without extra network dependencies beyond the CDN links already in the template (`leaflet`, `h3-js`, `bootstrap-icons`, Raleway font).
- All values embedded in HTML must be **HTML-escaped** (`<`, `>`, `&`, `"`) to prevent rendering issues.
- `commentMap` is embedded as a direct JavaScript object literal (not inside a string), so no JS string escaping is needed — just emit valid JSON.
- All values must be derived **only from analysis output**, not recomputed heuristically.
