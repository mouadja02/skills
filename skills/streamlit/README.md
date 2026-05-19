# streamlit

Skills for **building, editing, debugging, beautifying, and deploying Streamlit applications** — from single-page data apps to multi-page dashboards with custom components and Snowflake connections.

## Skills in this category

### Hub skill

| Skill | What it does |
| --- | --- |
| [`developing-with-streamlit`](./developing-with-streamlit/SKILL.md) | The routing hub for all Streamlit work — creating, editing, debugging, theming, and deploying Streamlit apps. Also handles custom components (CCv2), `st.components.v2`, and any HTML/JS/CSS component work. Routes to the appropriate sub-skill below. |

### Sub-skills

| Sub-skill | What it does |
| --- | --- |
| [`building-streamlit-chat-ui`](./developing-with-streamlit/skills/building-streamlit-chat-ui/SKILL.md) | Build conversational chat interfaces in Streamlit with streaming, message history, and LLM integration. |
| [`building-streamlit-custom-components-v2`](./developing-with-streamlit/skills/building-streamlit-custom-components-v2/SKILL.md) | Build packaged custom Streamlit components using CCv2 — `pyproject.toml`, `asset_dir`, bidirectional JS/Python communication. |
| [`building-streamlit-dashboards`](./developing-with-streamlit/skills/building-streamlit-dashboards/SKILL.md) | Build multi-panel KPI dashboards with charts, filters, and real-time data refresh. |
| [`building-streamlit-multipage-apps`](./developing-with-streamlit/skills/building-streamlit-multipage-apps/SKILL.md) | Structure multi-page Streamlit applications with navigation, shared state, and page routing. |
| [`choosing-streamlit-selection-widgets`](./developing-with-streamlit/skills/choosing-streamlit-selection-widgets/SKILL.md) | Pick and configure the right selection widgets (`selectbox`, `multiselect`, `radio`, `checkbox`, etc.) for any use case. |
| [`connecting-streamlit-to-snowflake`](./developing-with-streamlit/skills/connecting-streamlit-to-snowflake/SKILL.md) | Connect Streamlit apps to Snowflake using `st.connection`, secrets management, and Snowpark. |
| [`creating-streamlit-themes`](./developing-with-streamlit/skills/creating-streamlit-themes/SKILL.md) | Create and apply custom Streamlit themes via `config.toml`, CSS overrides, and dynamic theming. |
| [`displaying-streamlit-data`](./developing-with-streamlit/skills/displaying-streamlit-data/SKILL.md) | Display data effectively — `st.dataframe`, `st.table`, `st.metric`, Altair/Plotly/Matplotlib/Vega-Lite charts. |
| [`improving-streamlit-design`](./developing-with-streamlit/skills/improving-streamlit-design/SKILL.md) | Redesign, polish, and beautify existing Streamlit apps — UX review, color, spacing, hierarchy, and component choice. |
| [`optimizing-streamlit-performance`](./developing-with-streamlit/skills/optimizing-streamlit-performance/SKILL.md) | Speed up Streamlit apps — `@st.cache_data`, `@st.cache_resource`, fragment caching, rerun minimization. |
| [`organizing-streamlit-code`](./developing-with-streamlit/skills/organizing-streamlit-code/SKILL.md) | Refactor Streamlit codebases — module structure, separation of concerns, reusable components. |
| [`setting-up-streamlit-environment`](./developing-with-streamlit/skills/setting-up-streamlit-environment/SKILL.md) | Set up a Streamlit project from scratch — `requirements.txt`, secrets, `.streamlit/config.toml`, virtual environments. |
| [`using-streamlit-cli`](./developing-with-streamlit/skills/using-streamlit-cli/SKILL.md) | Use the Streamlit CLI — `streamlit run`, `streamlit config`, `streamlit cache clear`, deployment commands. |
| [`using-streamlit-custom-components`](./developing-with-streamlit/skills/using-streamlit-custom-components/SKILL.md) | Use third-party or inline custom components in Streamlit via `st.components.v1` and `st.components.v2`. |
| [`using-streamlit-layouts`](./developing-with-streamlit/skills/using-streamlit-layouts/SKILL.md) | Master Streamlit layout primitives — `st.columns`, `st.tabs`, `st.expander`, `st.sidebar`, `st.container`. |
| [`using-streamlit-markdown`](./developing-with-streamlit/skills/using-streamlit-markdown/SKILL.md) | Use `st.markdown` effectively — HTML rendering, unsafe_allow_html, styled text, LaTeX, badges. |
| [`using-streamlit-session-state`](./developing-with-streamlit/skills/using-streamlit-session-state/SKILL.md) | Manage `st.session_state` — callbacks, initialization patterns, cross-page state, and avoiding rerun loops. |

## When to use this folder

- "Create / edit / debug / beautify a Streamlit app"
- "Build a Streamlit dashboard / chat UI / multi-page app"
- "Style or theme my Streamlit app"
- "Connect Streamlit to Snowflake"
- "Build a custom component" / "use `st.components.v2`"
- "Optimize Streamlit performance"
- "Organize my Streamlit codebase"

## Related categories

- [`data-and-backend/`](../data-and-backend/) — Python FastAPI, Snowflake SQL, dbt — the data layer Streamlit apps connect to.
- [`design-and-ui/`](../design-and-ui/) — broader frontend design, design systems, and theming patterns.
- [`ai-agents/`](../ai-agents/) — agent patterns that often surface through a Streamlit frontend.
