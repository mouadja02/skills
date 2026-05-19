# data-and-backend

Skills for **Python backends, SQL warehouses, and dbt transformations** — the server-side and data layer.

## Skills in this category

### Python backend

| Skill | What it does |
| --- | --- |
| [`python-fastapi-llm`](./python-fastapi-llm/SKILL.md) | Build Python APIs that integrate LLMs — FastAPI, streaming responses, file uploads for AI processing, async patterns, Pydantic schemas for structured outputs, retry strategies, background AI jobs. |

### SQL & warehousing

| Skill | What it does |
| --- | --- |
| [`snowflake-sql`](./snowflake-sql/SKILL.md) | Snowflake SQL & DDL — dynamic tables, streams, tasks, stages, file formats, Snowpark, `QUALIFY`, `FLATTEN`, `LATERAL FLATTEN`, `PARSE_JSON`, VARIANT/OBJECT/ARRAY, clustering keys, time travel, search optimization. |

### dbt

| Skill | What it does |
| --- | --- |
| [`dbt-expert`](./dbt-expert/SKILL.md) | Any dbt work — models, schema.yml, sources.yml, tests, macros, snapshots, seeds, exposures, incremental strategies, project structure for Snowflake. |
| [`etl-to-dbt`](./etl-to-dbt/SKILL.md) | Convert ETL artifacts to dbt — Informatica IICS, PowerCenter, Talend, DataStage. Mapping XML/JSON analysis, transformation logic extraction, ETL data type → Snowflake type mapping. |

## When to use this folder

- "Build a Python API with LLM streaming"
- "Write Snowflake SQL / dbt models / sources.yml"
- "Migrate this Informatica mapping to dbt"

## Related categories

- [`streamlit/`](../streamlit/) — Streamlit apps and dashboards that connect to data backends (now in its own category).
- [`openrouter/`](../openrouter/) — the OpenRouter SDK family that the Python backend skill calls into.
- [`ai-agents/`](../ai-agents/) — agent patterns that often run *on top of* a FastAPI backend.
