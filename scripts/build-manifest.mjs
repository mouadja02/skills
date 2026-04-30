#!/usr/bin/env node
// Walks skills/ recursively, parses YAML frontmatter from every SKILL.md, and
// emits the canonical manifest into docs/ (machine-readable JSON + TSV) plus a
// hand-browseable SKILLS.md at the repo root.
//
// Single source of truth: docs/manifest.json. The Pages site reads it via a
// relative `./manifest.json` fetch; the install scripts and any external
// consumer fetch it via raw.githubusercontent.com/.../main/docs/manifest.json.
//
// Zero dependencies. Run with: node scripts/build-manifest.mjs

import { readdir, readFile, writeFile, mkdir, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, relative, sep, posix } from "node:path";
import { fileURLToPath } from "node:url";

const REPO = "mouadja02/skills";
const DEFAULT_BRANCH = "main";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const ROOT = join(__dirname, "..");
const SKILLS_DIR = join(ROOT, "skills");
const SKILLS_INDEX_PATH = join(ROOT, "SKILLS.md");
const DOCS_DIR = join(ROOT, "docs");
const MANIFEST_PATH = join(DOCS_DIR, "manifest.json");
const MANIFEST_TSV_PATH = join(DOCS_DIR, "manifest.tsv");

async function walk(dir, out = []) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      await walk(full, out);
    } else if (entry.isFile() && entry.name === "SKILL.md") {
      out.push(full);
    }
  }
  return out;
}

// Minimal YAML frontmatter parser. Handles:
//   key: value
//   key: "value"
//   key: >
//     multiline value
//     more text
//   key: |
//     literal block
function parseFrontmatter(rawContent) {
  // Normalize CRLF -> LF so end-of-line anchors and trims behave consistently.
  const content = rawContent.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  if (!content.startsWith("---")) return {};
  const end = content.indexOf("\n---", 3);
  if (end === -1) return {};
  const block = content.slice(3, end).replace(/^\n/, "");
  const lines = block.split("\n");

  const result = {};
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const m = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!m) {
      i++;
      continue;
    }
    const [, key, rawValue] = m;
    const value = rawValue.trim();

    if (value === ">" || value === "|" || value === ">-" || value === "|-") {
      // Folded (>) joins lines with a space; literal (|) keeps newlines.
      // Indentation is whatever indent the next non-empty line uses.
      const folded = value.startsWith(">");
      const collected = [];
      let baseIndent = null;
      i++;
      while (i < lines.length) {
        const next = lines[i];
        if (next.trim() === "") {
          collected.push("");
          i++;
          continue;
        }
        const indentMatch = next.match(/^(\s+)/);
        if (!indentMatch) break;
        if (baseIndent === null) baseIndent = indentMatch[1].length;
        if (indentMatch[1].length < baseIndent) break;
        collected.push(next.slice(baseIndent));
        i++;
      }
      result[key] = folded
        ? collected.join(" ").replace(/\s+/g, " ").trim()
        : collected.join("\n").trimEnd();
      continue;
    }

    // Strip surrounding quotes if present.
    let v = value;
    if (
      (v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))
    ) {
      v = v.slice(1, -1);
    }
    result[key] = v;
    i++;
  }
  return result;
}

function toPosix(p) {
  return p.split(sep).join(posix.sep);
}

function categoryOf(installPath) {
  const idx = installPath.indexOf("/");
  return idx === -1 ? installPath : installPath.slice(0, idx);
}

function depthOf(installPath) {
  return installPath.split("/").length;
}

async function main() {
  if (!existsSync(SKILLS_DIR)) {
    console.error(`ERROR: ${SKILLS_DIR} does not exist`);
    process.exit(1);
  }

  const files = await walk(SKILLS_DIR);
  const skills = [];
  const errors = [];

  for (const file of files) {
    try {
      const raw = await readFile(file, "utf8");
      const fm = parseFrontmatter(raw);
      const relPath = toPosix(relative(ROOT, file));
      const folder = relPath.replace(/\/SKILL\.md$/, "");
      const installPath = folder.replace(/^skills\//, "");

      if (!fm.name) {
        errors.push(`${relPath}: missing 'name' in frontmatter`);
        continue;
      }
      if (!fm.description) {
        errors.push(`${relPath}: missing 'description' in frontmatter`);
        continue;
      }

      skills.push({
        name: fm.name,
        category: categoryOf(installPath),
        install_path: installPath,
        path: folder,
        depth: depthOf(installPath),
        description: fm.description,
      });
    } catch (err) {
      errors.push(`${file}: ${err.message}`);
    }
  }

  skills.sort((a, b) => a.install_path.localeCompare(b.install_path));

  const categories = [...new Set(skills.map((s) => s.category))].sort();
  const byCategory = Object.fromEntries(
    categories.map((c) => [c, skills.filter((s) => s.category === c).length])
  );

  const manifest = {
    version: 1,
    generated_at: new Date().toISOString(),
    repo: REPO,
    default_branch: DEFAULT_BRANCH,
    count: skills.length,
    categories,
    counts_by_category: byCategory,
    skills,
  };

  await mkdir(DOCS_DIR, { recursive: true });

  const json = JSON.stringify(manifest, null, 2) + "\n";
  await writeFile(MANIFEST_PATH, json, "utf8");

  // TSV: install_path \t category \t name \t description (one skill per line).
  // Used by install.sh because pure-bash JSON parsing isn't portable. Tabs and
  // newlines are stripped from descriptions to keep the format unambiguous.
  const tsv =
    "install_path\tcategory\tname\tdescription\n" +
    skills
      .map((s) =>
        [
          s.install_path,
          s.category,
          s.name,
          s.description.replace(/[\t\r\n]+/g, " ").trim(),
        ].join("\t")
      )
      .join("\n") +
    "\n";
  await writeFile(MANIFEST_TSV_PATH, tsv, "utf8");

  // Hand-browseable markdown index at the repo root for github.com viewers.
  const md = renderSkillsMd(manifest);
  await writeFile(SKILLS_INDEX_PATH, md, "utf8");

  console.log(`OK  docs/manifest.json  (${skills.length} skills)`);
  console.log(`OK  docs/manifest.tsv   (bash-friendly)`);
  console.log(`OK  SKILLS.md           (browsable index)`);

  if (errors.length) {
    console.error(`\n${errors.length} error(s):`);
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }
}

function escapePipes(s) {
  return s.replace(/\|/g, "\\|").replace(/\r?\n/g, " ");
}

function renderSkillsMd({ count, categories, counts_by_category, skills, repo, default_branch }) {
  const lines = [];
  lines.push(`# Skills Index`);
  lines.push("");
  lines.push(
    `Auto-generated from \`SKILL.md\` frontmatter by \`scripts/build-manifest.mjs\`. Do not edit by hand.`
  );
  lines.push("");
  lines.push(`**Total:** ${count} skills across ${categories.length} categories.`);
  lines.push("");
  lines.push(`## Install one skill`);
  lines.push("");
  lines.push("```bash");
  lines.push(
    `# bash / zsh (macOS, Linux, WSL, Git Bash):`
  );
  lines.push(
    `curl -fsSL https://raw.githubusercontent.com/${repo}/${default_branch}/install.sh | bash -s -- <install_path> -d <destination>`
  );
  lines.push("```");
  lines.push("");
  lines.push("```powershell");
  lines.push(`# PowerShell (Windows):`);
  lines.push(
    `iwr https://raw.githubusercontent.com/${repo}/${default_branch}/install.ps1 -UseBasicParsing | iex; Install-Skill <install_path> -Dest <destination>`
  );
  lines.push("```");
  lines.push("");
  lines.push(
    `Where \`<install_path>\` is the value from the **Install path** column below (e.g. \`engineering-craft/test-driven-development\`).`
  );
  lines.push("");
  lines.push(`## Categories`);
  lines.push("");
  lines.push(`| Category | Skills |`);
  lines.push(`| --- | ---: |`);
  for (const c of categories) {
    lines.push(`| [\`${c}\`](#${c}) | ${counts_by_category[c]} |`);
  }
  lines.push("");

  for (const c of categories) {
    lines.push(`## ${c}`);
    lines.push("");
    lines.push(`| Skill | Install path | Description |`);
    lines.push(`| --- | --- | --- |`);
    for (const s of skills.filter((s) => s.category === c)) {
      lines.push(
        `| [\`${s.name}\`](./${s.path}/SKILL.md) | \`${s.install_path}\` | ${escapePipes(s.description)} |`
      );
    }
    lines.push("");
  }

  return lines.join("\n");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
