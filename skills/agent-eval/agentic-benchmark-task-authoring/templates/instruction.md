# <Task title>

<One paragraph: what the work is and why it matters, in operator terms.>

## Inputs

- `/app/in/<input-a>` — <what it contains, encoding, one row per what>
- `/app/in/<input-b>` — <what it contains>

Both files are already present. Do not download anything; the environment has no outbound network.

## Deliverable

Write `<absolute output path>` as <format: JSON object / JSON array / CSV> with exactly this shape:

```json
{
  "field_a": "<type and meaning>",
  "field_b": 0
}
```

Requirements:

- <ordering, sorting, or key requirement>
- <units, precision, or timezone requirement>
- <what to do with missing, duplicated, or malformed input>

## Constraints

- Only use what is already installed in the environment.
- The output path is exactly `<absolute output path>`; other locations are not read.
- <explicit non-goals: what the work must not do>

## Definition of done

The output exists at the exact path, parses as the specified format, and satisfies every requirement above for the supplied inputs, including the edge cases named in Constraints.
