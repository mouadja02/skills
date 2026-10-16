// Shared SKILL.md frontmatter reader for the build and lint scripts.
//
// Clients such as Claude Code parse frontmatter with a real YAML parser, so a
// block that is not valid YAML never loads there. The previous hand-rolled
// reader accepted such blocks (and misread valid multi-line plain scalars), so
// the build reported skills as fine that clients silently dropped. Parse with
// `yaml` instead, and surface the parser's error so the build can fail on it.

import { parse } from "yaml";

const FRONTMATTER_RE = /^---\n([\s\S]*?)\n---[ \t]*(?:\n|$)/;

export function normalizeNewlines(raw) {
  return raw.replace(/^﻿/, "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
}

// Returns { data, body, error }. `data` is null when the block is missing or
// unparsable; `error` then explains why. `body` is everything after the block.
export function readFrontmatter(raw) {
  const content = normalizeNewlines(raw);
  const match = content.match(FRONTMATTER_RE);
  if (!match) {
    return { data: null, body: content, error: "missing or unterminated YAML frontmatter" };
  }
  const body = content.slice(match[0].length);
  let data;
  try {
    data = parse(match[1], { prettyErrors: true });
  } catch (err) {
    const first = String(err.message).split("\n")[0];
    return { data: null, body, error: `frontmatter is not valid YAML: ${first}` };
  }
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    return { data: null, body, error: "frontmatter is not a YAML mapping" };
  }
  return { data, body, error: null };
}

// Descriptions are router text: collapse the newlines that block scalars keep.
export function oneLine(value) {
  return String(value).replace(/\s+/g, " ").trim();
}
