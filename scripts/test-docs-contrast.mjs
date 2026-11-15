// Regression test: light-theme text must meet WCAG AA normal-text contrast
// (4.5:1) on the background it is actually drawn on.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const CSS = fileURLToPath(new URL("../docs/style.css", import.meta.url));

function luminance(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const v = parseInt(hex.slice(i, i + 2), 16) / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

// Composite a foreground colour at the given opacity over a background.
function blend(fg, bg, alpha) {
  return (
    "#" +
    [1, 3, 5]
      .map((i) => {
        const f = parseInt(fg.slice(i, i + 2), 16);
        const b = parseInt(bg.slice(i, i + 2), 16);
        return Math.round(f * alpha + b * (1 - alpha)).toString(16).padStart(2, "0");
      })
      .join("")
  );
}

// Declarations of the last rule whose selector list includes `selector`
// (later rules win the cascade). Comments are stripped first.
async function lastRuleBody(selector, optional = false) {
  const css = (await readFile(CSS, "utf8")).replace(/\/\*[\s\S]*?\*\//g, "");
  let body;
  for (const m of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const selectors = m[1].split(",").map((s) => s.trim().replace(/\s+/g, " "));
    if (selectors.includes(selector)) body = m[2];
  }
  if (!optional) assert.ok(body !== undefined, `no rule for ${selector}`);
  return body;
}

function declared(body, prop, fallback) {
  const m = body.match(new RegExp(`(?:^|[;\\s])${prop}:\\s*(#[0-9a-fA-F]{6})`));
  return m ? m[1] : fallback;
}

test("light-theme category label colours meet 4.5:1 on #fff", async () => {
  const css = await readFile(CSS, "utf8");
  const pattern =
    /\[data-theme="light"\] \.card\[data-cat-color="(\d+)"\] \.card-category/g;
  const failures = [];
  let checked = 0;
  for (const match of css.matchAll(pattern)) {
    const hue = match[1];
    const rule = css.slice(match.index, css.indexOf("}", match.index));
    const color = rule.match(/color:\s*(#[0-9a-fA-F]{6})/);
    assert.ok(color, `hue ${hue} has no hex colour`);
    checked += 1;
    const ratio = contrast(color[1], "#ffffff");
    if (ratio < 4.5) {
      failures.push(`hue ${hue} ${color[1]} is ${ratio.toFixed(2)}:1`);
    }
  }
  assert.equal(checked, 13, "expected 13 light category colours");
  assert.deepEqual(failures, []);
});

test("active 'All' category pill meets 4.5:1 on its background", async () => {
  // #d0e4e7 is the rendered background of the active pill and its count.
  // Falls back to the theme accent, which the pill uses unless overridden.
  const root = await lastRuleBody('[data-theme="light"]');
  const accent = declared(root, "--accent", "#000000");
  const pill = await lastRuleBody('[data-theme="light"] .cat.active', true);
  const fg = pill ? declared(pill, "color", accent) : accent;
  const ratio = contrast(fg, "#d0e4e7");
  assert.ok(ratio >= 4.5, `active pill ${fg} is ${ratio.toFixed(2)}:1`);
});

test("light hero example label meets 4.5:1 on its active background", async () => {
  // The label inherits the accent colour and fades with the rule's opacity.
  const alphaOf = (body) => Number(body?.match(/opacity:\s*([0-9.]+)/)?.[1] ?? 1);
  const base = await lastRuleBody(".anatomy-choice.active .anatomy-choice-eg");
  const light = await lastRuleBody(
    '[data-theme="light"] .anatomy-choice.active .anatomy-choice-eg',
    true
  );
  const root = await lastRuleBody('[data-theme="light"]');
  const accent = declared(root, "--accent", "#000000");
  const shown = blend(accent, "#f0f7f7", light ? alphaOf(light) : alphaOf(base));
  const ratio = contrast(shown, "#f0f7f7");
  assert.ok(ratio >= 4.5, `anatomy example ${shown} is ${ratio.toFixed(2)}:1`);
});
