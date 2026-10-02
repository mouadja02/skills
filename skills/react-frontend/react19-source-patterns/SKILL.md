---
name: react19-source-patterns
description: 'Use when migrating React source files to React 19 APIs, refs, context, and component defaults.'
version: "1.0.1"
license: MIT
source: "https://github.com/github/awesome-copilot"
attribution: "github/awesome-copilot by GitHub Community"
---

> **Attribution:** Sourced from [github/awesome-copilot](https://github.com/github/awesome-copilot) by [GitHub Community](https://github.com/github).

# React 19 Source Migration Patterns

Reference for every source-file migration required for React 19.

## When to Use

- Migrating a React 18 application or component library to React 19.
- Replacing APIs removed in React 19, including legacy roots, legacy context, and string refs.
- Reviewing `ref`, `defaultProps`, `propTypes`, or `useRef` changes during an upgrade.

## Quick Reference Table

| Pattern | Action | Reference |
|---|---|---|
| `ReactDOM.render(...)` | → `createRoot().render()` | See references/api-migrations.md |
| `ReactDOM.hydrate(...)` | → `hydrateRoot(...)` | See references/api-migrations.md |
| `unmountComponentAtNode` | → `root.unmount()` | Inline fix |
| `ReactDOM.findDOMNode` | → direct ref | Inline fix |
| `forwardRef(...)` wrapper | → ref as direct prop | See references/api-migrations.md |
| Function component `.defaultProps = {}` | → ES6 default params | See references/api-migrations.md |
| `useRef()` no arg | → `useRef(null)` | Inline fix  add `null` |
| Legacy Context | → `createContext` | [→ api-migrations.md#legacy-context](references/api-migrations.md#legacy-context) |
| String refs `this.refs.x` | → `createRef()` | [→ api-migrations.md#string-refs](references/api-migrations.md#string-refs) |
| `import React from 'react'` (unused) | Remove | Only if no `React.` usage in file |

## PropTypes Rule

In React 19, component `.propTypes` assignments are silently ignored. Migrate runtime assumptions to TypeScript or another explicit type-checking solution; do not present retained assignments as active validation. The standalone `prop-types` package can still be invoked directly, but React no longer runs those component checks.

If an assignment must remain temporarily, mark it as non-enforcing and track its replacement:

```jsx
// React 19 ignores this assignment; retained temporarily as documentation.
// TODO: replace with TypeScript or another explicit validation boundary.
```

## Read the Reference

For full before/after code for each migration, read **`references/api-migrations.md`**. It contains the complete patterns including edge cases for `forwardRef` with `useImperativeHandle`, `defaultProps` null vs undefined behavior, and legacy context provider/consumer cross-file migrations.
