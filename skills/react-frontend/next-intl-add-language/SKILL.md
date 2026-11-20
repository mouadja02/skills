---
name: next-intl-add-language
description: >-
  Use when adding a locale to a Next.js application that uses next-intl—updates message catalogs, centralized routing, request loading, locale navigation, and version-appropriate proxy or middleware wiring.
version: "1.1.0"
license: MIT
source: "https://github.com/github/awesome-copilot"
attribution: "github/awesome-copilot by GitHub Community"
---

> **Attribution:** Sourced from [github/awesome-copilot](https://github.com/github/awesome-copilot) by [GitHub Community](https://github.com/github), licensed MIT. Modified for this collection.

# Add a locale to a next-intl application

## When to Use

- Add a language or regional locale to an existing Next.js App Router project that uses `next-intl`.
- Repair a locale that appears in the URL but has missing messages, invalid routing, or a broken language switcher.
- Migrate locale routing between Next.js 15's `middleware.ts` convention and Next.js 16's `proxy.ts` convention.

Do not use this workflow for the Pages Router, a different i18n library, or a project that intentionally loads locales dynamically from a service. Inspect the repository before assuming the paths below; they are common conventions, not universal filenames.

## 1. Establish the application's contract

Identify:

- the installed Next.js and `next-intl` versions from the lockfile;
- the source locale and target locale tag, using the project's existing BCP 47 style;
- the message directory and whether catalogs are JSON, TypeScript, or split by namespace;
- the central `defineRouting` configuration, request configuration, locale-aware navigation wrapper, and language-switcher component;
- whether locale lists are static or generated from domains, tenant configuration, or another source.

Search for `defineRouting`, `getRequestConfig`, `createNavigation`, `createMiddleware`, `routing.locales`, and existing locale-switch calls. Do not introduce a second locale list when the project already derives these values centrally.

## 2. Create a complete message catalog

Copy the source catalog to the target locale's expected path, preserve its nested object and array shape, and translate user-visible values without changing keys, interpolation placeholders, ICU syntax, rich-text tags, or plural/select branches.

Compare leaf-key paths mechanically rather than relying on file size. A target catalog must have no missing or extra keys unless the application explicitly supports fallback or locale-specific messages. Also check that placeholders used by corresponding source and target messages are identical.

For JSON catalogs, this dependency-free parity check can be adapted to the project's paths:

```bash
node - <<'NODE'
const fs = require('node:fs');
const flatten = (value, prefix = '', out = new Map()) => {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    for (const [key, child] of Object.entries(value)) {
      flatten(child, prefix ? `${prefix}.${key}` : key, out);
    }
  } else {
    out.set(prefix, value);
  }
  return out;
};
const placeholders = (value) =>
  [...String(value).matchAll(/\{([^{}]+)\}/g)].map((match) => match[1]).sort();
const source = flatten(JSON.parse(fs.readFileSync('messages/en.json', 'utf8')));
const target = flatten(JSON.parse(fs.readFileSync('messages/fr.json', 'utf8')));
const missing = [...source.keys()].filter((key) => !target.has(key));
const extra = [...target.keys()].filter((key) => !source.has(key));
const placeholderMismatch = [...source.keys()].filter(
  (key) => target.has(key) &&
    JSON.stringify(placeholders(source.get(key))) !== JSON.stringify(placeholders(target.get(key)))
);
if (missing.length || extra.length || placeholderMismatch.length) {
  console.error(JSON.stringify({missing, extra, placeholderMismatch}, null, 2));
  process.exit(1);
}
console.log('Message key and placeholder parity: %d/%d', source.size, target.size);
NODE
```

## 3. Register the locale once

Add the target locale to the existing `locales` value supplied to `defineRouting` in the project's routing configuration, commonly `src/i18n/routing.ts`. Update `domains`, `localePrefix`, localized `pathnames`, or other routing options only when the target locale requires them.

Treat the routing configuration as the source of truth. A proxy or middleware that calls `createMiddleware(routing)` consumes this list and normally does **not** need a duplicate locale edit.

If the project also validates route parameters, generates static parameters, emits alternate metadata, or builds a sitemap from a separate static list, either derive those values from `routing.locales` or update and test the deliberate secondary contract.

## 4. Verify messages load for each request

Inspect the function passed to `getRequestConfig`. Confirm that it:

1. validates or normalizes the requested locale against the supported locale list;
2. loads the target catalog from the actual target path;
3. returns the effective locale when required by the installed `next-intl` version;
4. fails predictably for unsupported locale tags rather than silently importing an arbitrary path.

Exercise one known target-locale message and one unsupported locale. Dynamic imports should be constrained by the validated locale list.

## 5. Keep proxy or middleware wiring version-aware

Current next-intl routing uses the same `createMiddleware(routing)` API under both file conventions:

- Next.js 16 and later: the conventional entry point is `src/proxy.ts` (or `proxy.ts`).
- Next.js 15 and earlier: the conventional entry point is `src/middleware.ts` (or `middleware.ts`).

Update the existing entry point; do not create both. Confirm its matcher includes application pages while excluding internal, API, and static-asset routes appropriate to the project. If routes can contain dots, verify explicit matcher coverage instead of assuming every dotted pathname is a file.

Do not rename `middleware.ts` to `proxy.ts` merely as part of adding a locale unless the installed Next.js version or an existing migration requires it.

## 6. Update locale-aware navigation

Add the locale to any visible language menu only after routing and messages work. Prefer the project's wrappers from `createNavigation(routing)` or next-intl's locale-aware `Link`/router APIs so a switch preserves the intended pathname and updates the locale cookie through navigation.

For each switcher entry, verify:

- the displayed language name and accessibility label are correct;
- the locale value exactly matches the routing configuration;
- the current path's dynamic parameters and query string are handled according to the app's policy;
- keyboard focus, selected state, and unsupported-locale behavior remain usable.

Avoid manually concatenating `/${locale}` onto paths; localized pathnames, prefix policies, and domain routing can make that incorrect.

## 7. Exercise the complete path

Run the repository's normal formatter, type checker, tests, and production build. Then verify at least:

1. **Normal:** a direct request to a target-locale route renders a translated message and locale-aware links.
2. **Edge:** an unsupported locale and a target catalog with a missing key fail according to the application's documented fallback or rejection policy.
3. **Should not affect:** the source locale still renders, and a locale switch preserves the intended route and parameters.

If the app statically renders locale routes, confirm `generateStaticParams` covers the target locale through `routing.locales`. For domain routing, test the target locale on every domain where it is declared.

Record the exact versions, changed locale sources, key-parity result, commands, and observed routes. Do not claim completion from translated JSON alone.

## Canonical references

- [next-intl locale routing setup](https://next-intl.dev/docs/routing/setup)
- [next-intl proxy and middleware behavior](https://next-intl.dev/docs/routing/middleware)
- [next-intl routing configuration](https://next-intl.dev/docs/routing/configuration)
