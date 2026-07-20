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
const SKILLS_README_PATH = join(SKILLS_DIR, "README.md");
const ROOT_README_PATH = join(ROOT, "README.md");
const DOCS_DIR = join(ROOT, "docs");
const MANIFEST_PATH = join(DOCS_DIR, "manifest.json");
const MANIFEST_TSV_PATH = join(DOCS_DIR, "manifest.tsv");

const CATEGORY_DESCRIPTIONS = {
  "agent-design": "Agent architecture, orchestration, harnesses, safety, scaffolding, and coding-agent interfaces.",
  "agent-eval": "Agent evaluation, RAG evaluation, memory, autoresearch, benchmarking, and lifecycle improvement.",
  "api-backend": "API design, backend implementation, OpenAPI, TypeSpec, FastAPI, and integrations.",
  "business-strategy": "Executive advisory, board preparation, operating systems, and strategic decision support.",
  "cloud-aws": "AWS services and agentic workflows: Bedrock, Lambda/serverless, databases, analytics/data lake, storage, networking, IAM, CDK/CloudFormation, cost, and observability.",
  "cloud-azure": "Azure, AWS, cloud architecture, IoT, pricing, deployment, and operations.",
  "code-quality": "Code review, refactoring, static analysis, security review, and integrity checks.",
  communication: "Decision frameworks, stakeholder communication, proposals, and concise trade-off analysis.",
  coding: "Language-agnostic implementation workflows, planning, debugging, security, and shipping.",
  "context-engineering": "Context design, compression, evolving memory, provenance, and codebase knowledge acquisition.",
  creative: "Creative ideation, concept visualization, generative methods, and reusable design prompts.",
  databases: "Database design, SQL optimization, migrations, analytics, Snowflake, PostgreSQL, and dbt.",
  "design-and-ui": "Frontend design, UI systems, visual artifacts, animation, branding, and accessibility.",
  "dev-workflow": "Git, GitHub, CLI tooling, release workflows, local automation, and developer productivity.",
  devops: "CI/CD, containers, infrastructure as code, Linux operations, observability, and security.",
  "diagrams-slides": "Diagrams, presentations, meeting artifacts, and professional visual communication.",
  documentation: "READMEs, ADRs, project documentation, Markdown tooling, conversion, and publishing.",
  dotnet: ".NET, C#, WinUI, MVVM, NuGet, testing, and VS Code extension development.",
  "engineering-craft": "Senior engineering practices, planning, mentoring, verification, and cross-cutting craft.",
  finance: "Financial modeling, valuation, Excel authoring, investment analysis, and presentation workflows.",
  "go-to-market": "Launch planning, positioning, pricing, partnerships, enterprise sales, and PLG.",
  "java-kotlin": "Java, Kotlin, Spring Boot, testing, refactoring, and migration workflows.",
  "llm-tooling": "LLM observability, evaluation, serving, vector search, OpenRouter, Phoenix, Arize, Qdrant, and vLLM.",
  "marketing-and-growth": "Marketing strategy, content, acquisition, SEO, CRO, and lifecycle growth.",
  mcp: "Model Context Protocol server generation, tooling, deployment, and security.",
  messaging: "Messaging integrations and relay workflows.",
  "microsoft-agents": "Microsoft Copilot agents, declarative agents, Foundry, Entra, and MCP tooling.",
  "microsoft-data": "Power BI, Power Apps, Power Automate, Dataverse, and Power Platform architecture.",
  "personal-productivity": "Personal productivity, reminders, communication, notes, and connected tools.",
  "product-management": "Product discovery, specifications, delivery planning, analytics, and agile workflows.",
  prompting: "Prompt engineering, optimization, safety review, and creative-thinking frameworks.",
  "react-frontend": "React, Vue, Next.js, mobile frontend frameworks, migrations, and testing.",
  research: "Research workflows, public-record investigation, source collection, and evidence synthesis.",
  "skills-management": "Skill authoring, discovery, cleanup, Copilot configuration, and terse interaction modes.",
  streamlit: "Streamlit applications, dashboards, chat UIs, components, layouts, and performance.",
  testing: "Testing, QA, Playwright, pytest, debugging, and evaluation strategy.",
};

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
  // Strip UTF-8 BOM (EF BB BF) if present — many editors write it.
  const noBom = rawContent.replace(/^﻿/, "");
  // Normalize CRLF -> LF so end-of-line anchors and trims behave consistently.
  const content = noBom.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
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

  const manifestCore = {
    version: 1,
    repo: REPO,
    default_branch: DEFAULT_BRANCH,
    count: skills.length,
    categories,
    counts_by_category: byCategory,
    skills,
  };

  // Keep unchanged builds byte-for-byte stable. Previously every invocation
  // replaced generated_at, which made clean validation impossible and caused
  // the deploy workflow to push a follow-up commit after every merge.
  let generatedAt = new Date().toISOString();
  if (existsSync(MANIFEST_PATH)) {
    try {
      const previous = JSON.parse(await readFile(MANIFEST_PATH, "utf8"));
      const { generated_at: previousGeneratedAt, ...previousCore } = previous;
      if (
        typeof previousGeneratedAt === "string" &&
        JSON.stringify(previousCore) === JSON.stringify(manifestCore)
      ) {
        generatedAt = previousGeneratedAt;
      }
    } catch {
      // A malformed prior manifest must not block regeneration from source.
    }
  }

  const { version, ...manifestRest } = manifestCore;
  const manifest = { version, generated_at: generatedAt, ...manifestRest };

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

  await writeFile(SKILLS_README_PATH, renderSkillsReadme(manifest), "utf8");
  for (const category of categories) {
    await writeFile(
      join(SKILLS_DIR, category, "README.md"),
      renderCategoryReadme(manifest, category),
      "utf8"
    );
  }

  const rootReadme = await readFile(ROOT_README_PATH, "utf8");
  await writeFile(ROOT_README_PATH, updateRootReadme(rootReadme, manifest), "utf8");

  console.log(`OK  docs/manifest.json  (${skills.length} skills)`);
  console.log(`OK  docs/manifest.tsv   (bash-friendly)`);
  console.log(`OK  SKILLS.md           (browsable index)`);
  console.log(`OK  skills/README.md     (${categories.length} categories)`);
  console.log(`OK  skills/*/README.md   (per-category indexes)`);
  console.log(`OK  README.md            (catalog metrics + categories)`);

  if (errors.length) {
    console.error(`\n${errors.length} error(s):`);
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }
}

function escapePipes(s) {
  return s.replace(/\|/g, "\\|").replace(/\r?\n/g, " ");
}

function compactTableText(s, maxLength = 240) {
  const normalized = escapePipes(s).replace(/\s+/g, " ").trim();
  return normalized.length <= maxLength
    ? normalized
    : `${normalized.slice(0, maxLength - 3).trimEnd()}...`;
}

function categoryDescription(category) {
  return CATEGORY_DESCRIPTIONS[category] ?? "Agent skills grouped by their primary domain.";
}

function renderSkillsReadme(manifest) {
  const lines = [];
  lines.push(`# Skills Index`);
  lines.push("");
  lines.push(`<!-- generated:skills-readme -->`);
  lines.push("");
  lines.push(
    `This index is generated from \`SKILL.md\` frontmatter by \`scripts/build-manifest.mjs\`. Do not edit it by hand.`
  );
  lines.push("");
  lines.push(
    `**Total:** ${manifest.count} skills across ${manifest.categories.length} categories.`
  );
  lines.push("");
  lines.push(`## Categories`);
  lines.push("");
  lines.push(`| Category | Skills | Scope |`);
  lines.push(`| --- | ---: | --- |`);
  for (const category of manifest.categories) {
    lines.push(
      `| [\`${category}\`](./${category}/) | ${manifest.counts_by_category[category]} | ${categoryDescription(category)} |`
    );
  }
  lines.push("");
  lines.push(`## Browse Every Skill`);
  lines.push("");
  lines.push(
    `Use [\`../SKILLS.md\`](../SKILLS.md) for the complete install-path index, or open a category README for a focused table.`
  );
  lines.push("");
  lines.push(`## Adding Or Editing A Skill`);
  lines.push("");
  lines.push(
    `Follow [\`../CONTRIBUTING.md\`](../CONTRIBUTING.md). Run \`npm run build:manifest\` after changing any \`SKILL.md\` file so this index and every category README remain current.`
  );
  lines.push("");
  return lines.join("\n");
}

function renderCategoryReadme(manifest, category) {
  const categorySkills = manifest.skills.filter((skill) => skill.category === category);
  const categoryDir = join(SKILLS_DIR, category);
  const lines = [];
  lines.push(`# ${category}`);
  lines.push("");
  lines.push(`<!-- generated:category-readme -->`);
  lines.push("");
  lines.push(
    `> Auto-generated from \`SKILL.md\` frontmatter by \`scripts/build-manifest.mjs\`. Do not edit this file by hand.`
  );
  lines.push("");
  lines.push(categoryDescription(category));
  lines.push("");
  lines.push(`**Total:** ${categorySkills.length} skills.`);
  lines.push("");
  lines.push(`## Skills In This Category`);
  lines.push("");
  lines.push(`| Skill | Install path | Description |`);
  lines.push(`| --- | --- | --- |`);
  for (const skill of categorySkills) {
    const target = toPosix(relative(categoryDir, join(ROOT, skill.path, "SKILL.md")));
    lines.push(
      `| [\`${skill.name}\`](${target}) | \`${skill.install_path}\` | ${compactTableText(skill.description)} |`
    );
  }
  lines.push("");
  lines.push(`[Back to the category index](../README.md)`);
  lines.push("");
  return lines.join("\n");
}

function generatedBlock(name, body) {
  return `<!-- generated:${name}:start -->\n${body}\n<!-- generated:${name}:end -->`;
}

function replaceGeneratedBlock(content, name, body) {
  const start = `<!-- generated:${name}:start -->`;
  const end = `<!-- generated:${name}:end -->`;
  const from = content.indexOf(start);
  const to = content.indexOf(end);
  if (from === -1 || to === -1 || to < from) {
    throw new Error(`README.md is missing generated block '${name}'`);
  }
  return (
    content.slice(0, from) +
    generatedBlock(name, body) +
    content.slice(to + end.length)
  );
}

function renderRootCatalog(manifest) {
  const lines = [];
  lines.push(`| Category | Skills | Scope |`);
  lines.push(`| --- | ---: | --- |`);
  for (const category of manifest.categories) {
    lines.push(
      `| [\`${category}\`](./skills/${category}/) | ${manifest.counts_by_category[category]} | ${categoryDescription(category)} |`
    );
  }
  return lines.join("\n");
}

function updateRootReadme(content, manifest) {
  const metrics = `A curated collection of **${manifest.count} Agent Skills** across **${manifest.categories.length} categories** for Claude Code, Cursor, and other clients that discover \`SKILL.md\` files recursively.`;
  return replaceGeneratedBlock(
    replaceGeneratedBlock(content, "catalog-metrics", metrics),
    "category-catalog",
    renderRootCatalog(manifest)
  );
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
