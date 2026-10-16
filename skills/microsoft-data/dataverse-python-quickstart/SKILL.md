---
name: dataverse-python-quickstart
description: >-
  Generates quickstart Python snippets for the Dataverse SDK: installation, client creation with
  InteractiveBrowserCredential, single-record CRUD, bulk create and update, and paged retrieval. Use
  when getting started with Dataverse from Python.
source: "https://github.com/microsoft/skills"
attribution: "microsoft/skills by Microsoft"
license: MIT
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
