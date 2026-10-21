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
// Frontmatter is parsed with the `yaml` devDependency, the same way clients
// parse it. Run with: node scripts/check-skills.mjs [--quiet]

import { readdir, readFile, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, dirname, resolve, relative, basename, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { readFrontmatter } from "./lib/frontmatter.mjs";
import { excludedReason, gitPublicationAllowlist } from "./lib/archive-policy.mjs";

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

function stripFences(markdown) {
  return markdown.replace(/^([ \t]*)(`{3,}|~{3,})[^\n]*\n[\s\S]*?^\1\2[^\n]*$/gm, "");
}

// Markdown inside fenced blocks or inline code spans is illustrative syntax, not
// a reference we can resolve — skills legitimately document `![alt](logo.png)`.
function stripCode(markdown) {
  return stripFences(markdown).replace(/(`+)[^`\n]*?\1/g, "");
}

// Prose such as "see `references/checklist.md`" points the agent at a bundled
// file without a Markdown link. Those references silently break when a skill is
// imported without its supporting files, so resolve them too (warning only:
// some skills name files the agent is meant to create).
const BUNDLED_DIRS =
  "references|reference|scripts|assets|templates|examples|agents|resources|rules|prompts|checklists|workflows|guides|patterns|schemas|evals|commands";
const BUNDLED_REF_RE = new RegExp(
  `(?<![\\w./-])((?:\\./)?(?:${BUNDLED_DIRS})/[\\w./-]*?[\\w-]\\.(?:md|py|sh|js|mjs|ts|json|yaml|yml|txt|html|csv|ps1|sql|toml))(?![\\w])`,
  "g"
);

function collectBundledRefs(markdown) {
  return [...new Set([...stripFences(markdown).matchAll(BUNDLED_REF_RE)].map((m) => m[1]))];
}

// A nested skill may lean on files its parent bundle ships.
function resolvesInSkillOrBundle(dir, target) {
  let current = dir;
  for (let i = 0; i < 4; i++) {
    if (existsSync(resolve(current, target))) return true;
    const parent = dirname(current);
    if (parent === SKILLS_DIR || parent === current) return false;
    current = parent;
  }
  return false;
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

    const { data: fm, body, error } = readFrontmatter(raw);
    if (error) {
      errors.push(`${rel}: ${error}`);
      continue;
    }

    if (fm.name !== undefined && typeof fm.name !== "string") {
      errors.push(`${rel}: name must be a string, got ${JSON.stringify(fm.name)}`);
    }
    if (fm.description !== undefined && typeof fm.description !== "string") {
      errors.push(`${rel}: description must be a string`);
    }
    const name = typeof fm.name === "string" ? fm.name : "";
    const description = typeof fm.description === "string" ? fm.description.trim() : "";

    if (!name) {
      errors.push(`${rel}: frontmatter is missing required field 'name'`);
    } else {
      if (!NAME_RE.test(name)) {
        errors.push(`${rel}: name "${name}" must match ${NAME_RE} (lowercase kebab-case, no colons or spaces)`);
      }
      if (name.length > NAME_MAX) {
        errors.push(`${rel}: name is ${name.length} chars, over the ${NAME_MAX} limit`);
      }
      // Anthropic's skill rules reserve these words; claude.ai and the Claude API
      // refuse to upload a skill whose name contains one.
      if (/anthropic|claude/.test(name)) {
        warnings.push(`${rel}: name "${name}" contains a reserved word ("anthropic"/"claude") and cannot be uploaded to claude.ai or the Claude API`);
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
    if (fm.version === undefined && fm.metadata?.version === undefined) {
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

    for (const ref of collectBundledRefs(body)) {
      if (!resolvesInSkillOrBundle(dir, ref)) {
        warnings.push(`${rel}: mentions bundled file "${ref}", which is not in the skill folder`);
      }
    }

    if (fm.source && !fm.attribution) {
      warnings.push(`${rel}: has a source but no attribution line`);
    }
  }

  // ZIPs drop residue such as caches and credentials, but the tarball fallback
  // and clones ship every tracked file. Fail on tracked residue here so all
  // routes deliver the same package.
  for (const file of [...gitPublicationAllowlist(ROOT).files].sort()) {
    const reason = excludedReason(file);
    if (reason) errors.push(`${file}: tracked but excluded from every package (${reason}); remove it from Git`);
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
  console.log(`OK  frontmatter parses as YAML`);
  console.log(`OK  names unique, kebab-case, and matching their folders`);
  console.log(`OK  descriptions within ${DESC_MAX} chars`);
  console.log(`OK  relative links in SKILL.md resolve`);
  console.log(`OK  no tracked files excluded by the archive policy`);
  if (warnings.length) console.log(`--  ${warnings.length} warning(s) (non-blocking)`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
