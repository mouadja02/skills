#!/usr/bin/env node
// Validates every skills/**/SKILL.md against the contract in CONTRIBUTING.md.
//
// build-manifest.mjs trusts whatever frontmatter it finds and check-docs.mjs only
// audits the *generated* indexes, so nothing previously checked the skills
// themselves. This script closes that gap: it is the only place that can catch a
// skill that will not load in a client, or two skills that overwrite each other
// on install.
//
// Errors fail the build. Warnings are reported and do not.
//
// Zero dependencies. Run with: node scripts/check-skills.mjs [--quiet]

import { readdir, readFile, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, dirname, resolve, relative, basename, sep } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const ROOT = join(__dirname, "..");
const SKILLS_DIR = join(ROOT, "skills");

// Client-side identifier rule. Claude Code and Cursor both key skills by this
// string; anything outside [a-z0-9-] is rejected or silently mangled.
const NAME_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const NAME_MAX = 64;
// Hard cap enforced by Claude Code on the description field.
const DESC_MAX = 1024;
// Below this a description is almost never a usable router rule.
const DESC_MIN_WARN = 60;

const toPosix = (p) => p.split(sep).join("/");

async function walk(dir, out = []) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = join(dir, entry.name);
    let isDirectory = entry.isDirectory();
    let isFile = entry.isFile();
    // Mirrors build-manifest.mjs: OneDrive Files On-Demand placeholders report
    // as symlinks, so resolve the real type before deciding how to recurse.
    if (!isDirectory && !isFile && entry.isSymbolicLink()) {
      try {
        const info = await stat(full);
        isDirectory = info.isDirectory();
        isFile = info.isFile();
      } catch {
        continue;
      }
    }
    if (isDirectory) await walk(full, out);
    else if (isFile && entry.name === "SKILL.md") out.push(full);
  }
  return out;
}

// Same minimal frontmatter reader as build-manifest.mjs, kept deliberately
// permissive: the point is to report what a client would see, not to be a
// conforming YAML parser.
function parseFrontmatter(raw) {
  const content = raw.replace(/^﻿/, "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  if (!content.startsWith("---")) return null;
  const end = content.indexOf("\n---", 3);
  if (end === -1) return null;
  const block = content.slice(3, end).replace(/^\n/, "");
  const lines = block.split("\n");
  const result = {};
  let i = 0;
  while (i < lines.length) {
    const match = lines[i].match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!match) {
      i++;
      continue;
    }
    const [, key, rest] = match;
    if (["|", ">", "|-", ">-"].includes(rest.trim())) {
      const parts = [];
      i++;
      while (i < lines.length && (lines[i].startsWith("  ") || lines[i].trim() === "")) {
        parts.push(lines[i].trim());
        i++;
      }
      result[key] = parts.join(" ").trim();
      continue;
    }
    let value = rest.trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    result[key] = value;
    i++;
  }
  return { fm: result, body: content.slice(end + 4) };
}

// Markdown inside fenced blocks or inline code spans is illustrative syntax, not
// a reference we can resolve — skills legitimately document `![alt](logo.png)`.
function stripCode(markdown) {
  return markdown
    .replace(/^([ \t]*)(`{3,}|~{3,})[^\n]*\n[\s\S]*?^\1\2[^\n]*$/gm, "")
    .replace(/(`+)[^`\n]*?\1/g, "");
}

// Template placeholders that are documentation, not links we can resolve.
function isPlaceholderTarget(target) {
  return (
    /[{}<>*]/.test(target) ||
    target.includes("...") ||
    /(^|\/)(path|url|link|relative-url)(\/|$)/i.test(target) ||
    /path\/to\//i.test(target) ||
    /\byour[-_]/i.test(target)
  );
}

function collectLinks(markdown) {
  return [...stripCode(markdown).matchAll(/\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g)].map((m) => m[1]);
}

async function main() {
  const quiet = process.argv.includes("--quiet");
  const files = (await walk(SKILLS_DIR)).sort();
  const errors = [];
  const warnings = [];
  const byName = new Map();
  const byFolder = new Map();

  for (const file of files) {
    const rel = toPosix(relative(ROOT, file));
    const dir = dirname(file);
    const installPath = toPosix(relative(SKILLS_DIR, dir));
    const folder = basename(dir);
    const depth = installPath.split("/").length;
    const raw = await readFile(file, "utf8");

    if (raw.charCodeAt(0) === 0xfeff) {
      errors.push(`${rel}: starts with a UTF-8 BOM (breaks strict YAML frontmatter parsers)`);
    }

    const parsed = parseFrontmatter(raw);
    if (!parsed) {
      errors.push(`${rel}: missing or unterminated YAML frontmatter`);
      continue;
    }
    const { fm, body } = parsed;

    const name = fm.name || "";
    const description = fm.description || "";

    if (!name) {
      errors.push(`${rel}: frontmatter is missing required field 'name'`);
    } else {
      if (!NAME_RE.test(name)) {
        errors.push(`${rel}: name "${name}" must match ${NAME_RE} (lowercase kebab-case, no colons or spaces)`);
      }
      if (name.length > NAME_MAX) {
        errors.push(`${rel}: name is ${name.length} chars, over the ${NAME_MAX} limit`);
      }
      // Top-level skills are the installable unit and must be addressable by
      // folder. Skills nested inside a bundle may carry a namespaced name to
      // stay globally unique (see llm-tooling/qdrant-*).
      if (depth === 2 && name !== folder) {
        errors.push(`${rel}: name "${name}" does not match folder "${folder}"`);
      }
      if (!byName.has(name)) byName.set(name, []);
      byName.get(name).push(installPath);
    }

    if (!description) {
      errors.push(`${rel}: frontmatter is missing required field 'description'`);
    } else {
      if (description.length > DESC_MAX) {
        errors.push(`${rel}: description is ${description.length} chars, over the ${DESC_MAX} limit`);
      } else if (description.length < DESC_MIN_WARN) {
        warnings.push(`${rel}: description is only ${description.length} chars — state when to use the skill, not just what it is`);
      }
    }

    if (!byFolder.has(folder)) byFolder.set(folder, []);
    byFolder.get(folder).push(installPath);

    if (!/^#{2,}\s.*when to use/im.test(body)) {
      warnings.push(`${rel}: no "## When to Use" section`);
    }
    if (!fm.version && !/^\s*version:/m.test(raw)) {
      warnings.push(`${rel}: no version in frontmatter`);
    }
    if (!fm.license) {
      warnings.push(`${rel}: no license in frontmatter`);
    }

    for (const link of collectLinks(body)) {
      if (link.includes("://") || link.startsWith("#") || link.startsWith("mailto:")) continue;
      const target = link.split("#")[0].trim();
      if (!target || isPlaceholderTarget(target)) continue;
      if (target.startsWith("/")) {
        errors.push(`${rel}: link "${link}" is an absolute path and will not resolve for an installed skill`);
        continue;
      }
      const resolved = resolve(dir, target);
      if (!existsSync(resolved)) {
        errors.push(`${rel}: broken relative link "${link}"`);
      } else if (toPosix(relative(dir, resolved)).startsWith("..")) {
        warnings.push(`${rel}: link "${link}" escapes the skill folder and breaks when the skill is installed alone`);
      }
    }
  }

  for (const [name, paths] of byName) {
    if (paths.length > 1) {
      errors.push(`duplicate skill name "${name}" in: ${paths.join(", ")}`);
    }
  }
  for (const [folder, paths] of byFolder) {
    if (paths.length > 1) {
      warnings.push(`duplicate folder name "${folder}" — these install to the same destination: ${paths.join(", ")}`);
    }
  }

  if (warnings.length && !quiet) {
    console.warn(`check-skills: ${warnings.length} warning(s)`);
    for (const warning of warnings) console.warn(`  ! ${warning}`);
    console.warn("");
  }

  if (errors.length) {
    console.error(`Skill validation failed with ${errors.length} error(s):`);
    for (const error of errors) console.error(`  - ${error}`);
    process.exit(1);
  }

  console.log(`OK  ${files.length} skills valid`);
  console.log(`OK  names unique, kebab-case, and matching their folders`);
  console.log(`OK  descriptions within ${DESC_MAX} chars`);
  console.log(`OK  relative links in SKILL.md resolve`);
  if (warnings.length) console.log(`--  ${warnings.length} warning(s) (non-blocking)`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
