---
name: swift-concurrency-expert
description: "Swift concurrency review/fix: compiler errors, Sendable, actor isolation, Swift 6.2+ remediation."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger — originally by @Dimillian (Dimillian/Skills)"
version: "1.0.0"
platform: apple
---

# Swift Concurrency Expert

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete). Originally created by [@Dimillian](https://github.com/Dimillian) from [Dimillian/Skills](https://github.com/Dimillian/Skills) (2025-12-31).

## Overview

Review and fix Swift Concurrency issues in Swift 6.2+ codebases by applying actor isolation, Sendable safety, and modern concurrency patterns with minimal behavior changes.

## When to Use

- Fixing Swift 6 strict concurrency compiler errors
- Reviewing Sendable conformance, actor isolation, and data race safety
- Migrating pre-Swift 6 async code to strict concurrency
- Choosing between actors, `@MainActor`, `nonisolated`, and `@Sendable`

## Workflow

### 1. Triage the issue

- Capture the exact compiler diagnostics and the offending symbol(s).
- Identify the current actor context (`@MainActor`, `actor`, `nonisolated`) and whether a default actor isolation mode is enabled.
- Confirm whether the code is UI-bound or intended to run off the main actor.

### 2. Apply the smallest safe fix

Prefer edits that preserve existing behavior while satisfying data-race safety.

Common fixes:
- **UI-bound types**: annotate the type or relevant members with `@MainActor`.
- **Protocol conformance on main actor types**: make the conformance isolated (e.g., `extension Foo: @MainActor SomeProtocol`).
- **Global/static state**: protect with `@MainActor` or move into an actor.
- **Background work**: move expensive work into a `@concurrent` async function on a `nonisolated` type or use an `actor` to guard mutable state.
- **Sendable errors**: prefer immutable/value types; add `Sendable` conformance only when correct; avoid `@unchecked Sendable` unless you can prove thread safety.

## Key Patterns

### @MainActor annotation

```swift
// UI-bound type
@MainActor
class ViewModel: ObservableObject {
    @Published var items: [Item] = []
}

// Protocol conformance
extension MyView: @MainActor SomeProtocol { ... }
```

### Actor for shared mutable state

```swift
actor DataCache {
    private var cache: [String: Data] = [:]
    
    func store(_ data: Data, for key: String) {
        cache[key] = data
    }
    
    func retrieve(for key: String) -> Data? {
        cache[key]
    }
}
```

### Sendable conformance

```swift
// Immutable value type - safe
struct Config: Sendable {
    let apiKey: String
    let baseURL: URL
}

// Only use @unchecked when you can manually guarantee thread safety
final class ThreadSafeCache: @unchecked Sendable {
    private let lock = NSLock()
    private var cache: [String: Any] = [:]
}
```

## Diagnostic Checklist

- [ ] Compiler diagnostic captured exactly
- [ ] Actor context identified (`@MainActor`, `actor`, `nonisolated`, implicit)
- [ ] Fix preserves existing behavior
- [ ] No `@unchecked Sendable` without proven thread safety
- [ ] No unnecessary `await` or `Task { }` wrappers added
