---
name: create-github-issues-for-unmet-specification-requirements
description: >-
  Creates GitHub issues for the requirements in a specification that are not implemented yet, using
  the feature_request.yml template. Use when auditing a spec against the code and tracking the gaps.
license: MIT
source: "https://github.com/github/awesome-copilot"
attribution: "github/awesome-copilot by GitHub Community"
---

> **Attribution:** Sourced from [github/awesome-copilot](https://github.com/github/awesome-copilot) by [GitHub Community](https://github.com/github), licensed MIT. Modified for this collection.

# Create GitHub Issues for Unmet Specification Requirements

Create GitHub Issues for unimplemented requirements in the specification at `${file}`.

## Process

1. Analyze specification file to extract all requirements
2. Check codebase implementation status for each requirement
3. Search existing issues using `search_issues` to avoid duplicates
4. Create new issue per unimplemented requirement using `create_issue`
5. Use `feature_request.yml` template (fallback to default)

## Requirements

- One issue per unimplemented requirement from specification
- Clear requirement ID and description mapping
- Include implementation guidance and acceptance criteria
- Verify against existing issues before creation

## Issue Content

- Title: Requirement ID and brief description
- Description: Detailed requirement, implementation method, and context
- Labels: feature, enhancement (as appropriate)

## Implementation Check

- Search codebase for related code patterns
- Check related specification files in `/spec/` directory
- Verify requirement isn't partially implemented
