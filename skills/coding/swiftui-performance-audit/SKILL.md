---
name: swiftui-performance-audit
description: "SwiftUI performance audit: render, scroll, CPU/memory, view updates, layout, Instruments."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger — originally by @Dimillian (Dimillian/Skills)"
version: "1.0.0"
platform: apple
---

# SwiftUI Performance Audit

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete). Originally created by [@Dimillian](https://github.com/Dimillian) from [Dimillian/Skills](https://github.com/Dimillian/Skills) (2025-12-31).

## When to Use

- Auditing SwiftUI view rendering, scrolling, or CPU/memory performance
- Identifying unnecessary view updates, body re-evaluations, or layout thrashing
- Guiding the user to profile with Instruments when code review is inconclusive

## Overview

Audit SwiftUI view performance end-to-end, from instrumentation and baselining to root-cause analysis and concrete remediation steps.

## Workflow Decision Tree

- If the user provides code, start with "Code-First Review."
- If the user only describes symptoms, ask for minimal code/context, then do "Code-First Review."
- If code review is inconclusive, go to "Guide the User to Profile" and ask for a trace or screenshots.

## 1. Code-First Review

Collect:
- Target view/feature code.
- Data flow: state, environment, observable models.
- Symptoms and reproduction steps.

Focus on:
- View invalidation storms from broad state changes.
- Unstable identity in lists (`id` churn, `UUID()` per render).
- Heavy work in `body` (formatting, sorting, image decoding).
- Layout thrash (deep stacks, `GeometryReader`, preference chains).
- Large images without downsampling or resizing.
- Over-animated hierarchies (implicit animations on large trees).

## 2. Guide the User to Profile

Explain how to collect data with Instruments:
- Use the SwiftUI template in Instruments (Release build).
- Reproduce the exact interaction (scroll, navigation, animation).
- Capture SwiftUI timeline and Time Profiler.
- Export or screenshot the relevant lanes and the call tree.

## 3. Analyze and Diagnose

Prioritize likely SwiftUI culprits:
- View invalidation storms from broad state changes.
- Unstable identity in lists (`id` churn, `UUID()` per render).
- Heavy work in `body` (formatting, sorting, image decoding).
- Layout thrash (deep stacks, `GeometryReader`, preference chains).
- Large images without downsampling or resizing.
- Over-animated hierarchies (implicit animations on large trees).

## 4. Remediate

Apply targeted fixes:
- Narrow state scope (`@State`/`@Observable` closer to leaf views).
- Stabilize identities for `ForEach` and lists.
- Move heavy work out of `body` (precompute, cache, `@State`).
- Use `equatable()` or value wrappers for expensive subtrees.
- Downsample images before rendering.
- Reduce layout complexity or use fixed sizing where possible.

## Common Code Smells (and Fixes)

### Expensive formatters in `body`

```swift
// ❌ Slow allocation on every render
var body: some View {
    let number = NumberFormatter()
    Text(number.string(from: 42)!)
}

// ✅ Cached formatter
final class Formatters {
    static let number = NumberFormatter()
}
```

### Unstable identity in ForEach

```swift
// ❌ UUID() per render — destroys identity
ForEach(items, id: \.self) { item in Row(item) }

// ✅ Stable Identifiable ID
ForEach(items) { item in Row(item) }
```

### Sorting/filtering in body

```swift
// ❌ Runs on every body eval
List {
    ForEach(items.sorted(by: sortRule)) { item in Row(item) }
}

// ✅ Sort once before view updates
let sortedItems = items.sorted(by: sortRule)
```

### Broad dependencies in observable models

```swift
// ❌ Whole view tree re-renders on any items change
@Observable class Model { var items: [Item] = [] }
var body: some View { Row(isFavorite: model.items.contains(item)) }

// ✅ Granular view models or per-item state
```

## 5. Verify

Ask the user to re-run the same capture and compare with baseline metrics.
Summarize the delta (CPU, frame drops, memory peak) if provided.

## Outputs

Provide:
- A short metrics table (before/after if available).
- Top issues (ordered by impact).
- Proposed fixes with estimated effort.
