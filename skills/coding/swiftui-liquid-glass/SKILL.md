---
name: swiftui-liquid-glass
description: "SwiftUI Liquid Glass (iOS 26+): implement, adopt, refactor, review correctness/perf/design."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger — originally by @Dimillian (Dimillian/Skills)"
version: "1.0.0"
platform: apple
---

# SwiftUI Liquid Glass

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete). Originally created by [@Dimillian](https://github.com/Dimillian) from [Dimillian/Skills](https://github.com/Dimillian/Skills) (2025-12-31).

## When to Use

- Implementing iOS 26+ Liquid Glass effects in SwiftUI
- Reviewing correctness of `glassEffect` and `GlassEffectContainer` usage
- Refactoring existing UI to adopt the Liquid Glass design language

## Overview

Use this skill to build or review SwiftUI features that fully align with the iOS 26+ Liquid Glass API. Prioritize native APIs (`glassEffect`, `GlassEffectContainer`, glass button styles) and Apple design guidance. Keep usage consistent, interactive where needed, and performance aware.

## Workflow Decision Tree

### 1) Review an existing feature
- Inspect where Liquid Glass should be used and where it should not.
- Verify correct modifier order, shape usage, and container placement.
- Check for iOS 26+ availability handling and sensible fallbacks.

### 2) Improve a feature using Liquid Glass
- Identify target components for glass treatment (surfaces, chips, buttons, cards).
- Refactor to use `GlassEffectContainer` where multiple glass elements appear.
- Introduce interactive glass only for tappable or focusable elements.

### 3) Implement a new feature using Liquid Glass
- Design the glass surfaces and interactions first (shape, prominence, grouping).
- Add glass modifiers after layout/appearance modifiers.
- Add morphing transitions only when the view hierarchy changes with animation.

## Core Guidelines

- Prefer native Liquid Glass APIs over custom blurs.
- Use `GlassEffectContainer` when multiple glass elements coexist.
- Apply `.glassEffect(...)` after layout and visual modifiers.
- Use `.interactive()` for elements that respond to touch/pointer.
- Keep shapes consistent across related elements for a cohesive look.
- Gate with `#available(iOS 26, *)` and provide a non-glass fallback.

## Review Checklist

- **Availability**: `#available(iOS 26, *)` present with fallback UI.
- **Composition**: Multiple glass views wrapped in `GlassEffectContainer`.
- **Modifier order**: `glassEffect` applied after layout/appearance modifiers.
- **Interactivity**: `interactive()` only where user interaction exists.
- **Transitions**: `glassEffectID` used with `@Namespace` for morphing.
- **Consistency**: Shapes, tinting, and spacing align across the feature.

## Quick Snippets

```swift
if #available(iOS 26, *) {
    Text("Hello")
        .padding()
        .glassEffect(.regular.interactive(), in: .rect(cornerRadius: 16))
} else {
    Text("Hello")
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
}
```

```swift
GlassEffectContainer(spacing: 24) {
    HStack(spacing: 24) {
        Image(systemName: "scribble.variable")
            .frame(width: 72, height: 72)
            .font(.system(size: 32))
            .glassEffect()
        Image(systemName: "eraser.fill")
            .frame(width: 72, height: 72)
            .font(.system(size: 32))
            .glassEffect()
    }
}
```

```swift
Button("Confirm") { }
    .buttonStyle(.glassProminent)
```

## Implementation Checklist

- [ ] Target elements and desired glass prominence defined
- [ ] Grouped glass elements wrapped in `GlassEffectContainer`
- [ ] `.glassEffect(.regular.tint(...).interactive(), in: .rect(cornerRadius: ...))` applied as needed
- [ ] `.buttonStyle(.glass)` / `.buttonStyle(.glassProminent)` for actions
- [ ] Morphing transitions with `glassEffectID` when hierarchy changes
- [ ] Fallback materials and visuals for earlier iOS versions provided
