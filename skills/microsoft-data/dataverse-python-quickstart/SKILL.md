---
name: dataverse-python-quickstart
description: 'Generate Python SDK setup + CRUD + bulk + paging snippets using official patterns.'
source: "https://github.com/microsoft/skills"
attribution: "microsoft/skills by Microsoft"
---

> **Attribution:** Sourced from [microsoft/skills](https://github.com/microsoft/skills) by [Microsoft](https://microsoft.com).

You are assisting with Microsoft Dataverse SDK for Python (preview).
Generate concise Python snippets that:
- Install the SDK (pip install PowerPlatform-Dataverse-Client)
- Create a DataverseClient with InteractiveBrowserCredential
- Show CRUD single-record operations
- Show bulk create and bulk update (broadcast + 1:1)
- Show retrieve-multiple with paging (top, page_size)
- Optionally demonstrate file upload to a File column
Keep code aligned with official examples and avoid unannounced preview features.
