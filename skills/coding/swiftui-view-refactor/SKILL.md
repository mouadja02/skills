---
name: swiftui-view-refactor
description: "SwiftUI view refactor/review: layout ordering, DI, Observation, MV patterns, view models."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger — originally by @Dimillian (Dimillian/Skills)"
---

# SwiftUI View Refactor

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete). Originally created by [@Dimillian](https://github.com/Dimillian) from [Dimillian/Skills](https://github.com/Dimillian/Skills) (2025-12-31).

## Overview

Apply a consistent structure and dependency pattern to SwiftUI views, with a focus on ordering, Model-View (MV) patterns, careful view model handling, and correct Observation usage.

## Core Guidelines

### 1) View ordering (top → bottom)

- Environment
- `private`/`public` `let`
- `@State` / other stored properties
- computed `var` (non-view)
- `init`
- `body`
- computed view builders / other view helpers
- helper / async functions

### 2) Prefer MV (Model-View) patterns

- Default to MV: Views are lightweight state expressions; models/services own business logic.
- Favor `@State`, `@Environment`, `@Query`, and `task`/`onChange` for orchestration.
- Inject services and shared models via `@Environment`; keep views small and composable.
- Split large views into subviews rather than introducing a view model.

### 3) Split large bodies and view properties

- If `body` grows beyond a screen or has multiple logical sections, split it into smaller subviews.
- Extract large computed view properties into dedicated `View` types when they carry state or complex branching.
- Prefer passing small inputs (data, bindings, callbacks) over reusing the entire parent view state.

```swift
// ✅ Extracted sections
var body: some View {
    VStack(alignment: .leading, spacing: 16) {
        HeaderSection(title: title, isPinned: isPinned)
        DetailsSection(details: details)
        ActionsSection(onSave: onSave, onCancel: onCancel)
    }
}
```

### 4) View model handling (only if already present)

- Do not introduce a view model unless the request or existing code clearly calls for one.
- If a view model exists, make it non-optional when possible.
- Pass dependencies to the view via `init`, then pass them into the view model in the view's `init`.

```swift
// ✅ Observation-based view model
@State private var viewModel: SomeViewModel

init(dependency: Dependency) {
    _viewModel = State(initialValue: SomeViewModel(dependency: dependency))
}
```

### 5) Observation usage

- For `@Observable` reference types, store them as `@State` in the root view.
- Pass observables down explicitly as needed; avoid optional state unless required.

## Workflow

1. Reorder the view to match the ordering rules.
2. Favor MV: move lightweight orchestration into the view using `@State`, `@Environment`, `@Query`, `task`, and `onChange`.
3. If a view model exists, replace optional view models with a non-optional `@State` view model initialized in `init`.
4. Confirm Observation usage: `@State` for root `@Observable` view models, no redundant wrappers.
5. Keep behavior intact: do not change layout or business logic unless requested.

## Notes

- Prefer small, explicit helpers over large conditional blocks.
- Keep computed view builders below `body` and non-view computed vars above `init`.
