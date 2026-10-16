#!/usr/bin/env node
// Walks skills/ recursively, parses YAML frontmatter from every SKILL.md, and
// emits the canonical manifest into docs/ (machine-readable JSON + TSV) plus a
// hand-browseable SKILLS.md at the repo root.
//
// Single source of truth: docs/manifest.json. The Pages site reads it via a
// relative `./manifest.json` fetch; the install scripts and any external
// consumer fetch it via raw.githubusercontent.com/.../main/docs/manifest.json.
//
// Frontmatter is parsed with the `yaml` devDependency (see lib/frontmatter.mjs).
// Run with: node scripts/build-manifest.mjs

import { readdir, readFile, writeFile, mkdir, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, relative, sep, posix } from "node:path";
import { fileURLToPath } from "node:url";
import { readFrontmatter, oneLine } from "./lib/frontmatter.mjs";

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
const THIRD_PARTY_PATH = join(DOCS_DIR, "third-party-sources.md");

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
    let isDirectory = entry.isDirectory();
    let isFile = entry.isFile();
    // Cloud/virtual filesystems (notably OneDrive Files On-Demand on Windows)
    // return directory and file placeholders as reparse points, which readdir
    // reports as symbolic links — so isDirectory()/isFile() are both false.
    // Resolve the real type with stat so recursion still finds nested SKILL.md.
    // On a normal filesystem no entry is a symlink here, so this never runs and
    // the traversal is byte-for-byte identical.
    if (!isDirectory && !isFile && entry.isSymbolicLink()) {
      try {
        const info = await stat(full);
        isDirectory = info.isDirectory();
        isFile = info.isFile();
      } catch {
        // Broken link or unreadable placeholder: skip it.
      }
    }
    if (isDirectory) {
      await walk(full, out);
    } else if (isFile && entry.name === "SKILL.md") {
      out.push(full);
    }
  }
  return out;
}

// Repository root URL for a `source` value, so every skill imported from one
// upstream lands in the same attribution group. Non-GitHub sources (papers,
// documentation sites) are kept verbatim.
function sourceKey(source) {
  const first = String(source).split(/[;\s]+/)[0];
  const github = first.match(/^https:\/\/github\.com\/([^/]+)\/([^/#?]+)/);
  return github ? `https://github.com/${github[1]}/${github[2].replace(/\.git$/, "")}` : first;
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
      const relPath = toPosix(relative(ROOT, file));
      const { data: fm, error } = readFrontmatter(raw);
      const folder = relPath.replace(/\/SKILL\.md$/, "");
      const installPath = folder.replace(/^skills\//, "");

      if (error) {
        errors.push(`${relPath}: ${error}`);
        continue;
      }
      if (typeof fm.name !== "string" || !fm.name) {
        errors.push(`${relPath}: missing 'name' in frontmatter`);
        continue;
      }
      if (typeof fm.description !== "string" || !fm.description.trim()) {
        errors.push(`${relPath}: missing 'description' in frontmatter`);
        continue;
      }

      const skill = {
        name: fm.name,
        category: categoryOf(installPath),
        install_path: installPath,
        path: folder,
        depth: depthOf(installPath),
        description: oneLine(fm.description),
      };
      if (fm.license) skill.license = oneLine(fm.license);
      if (fm.source) skill.source = oneLine(fm.source);
      if (fm.attribution) skill.attribution = oneLine(fm.attribution);
      skills.push(skill);
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

  const thirdParty = await readFile(THIRD_PARTY_PATH, "utf8");
  await writeFile(
    THIRD_PARTY_PATH,
    replaceGeneratedBlock(thirdParty, "attribution-index", renderAttributionIndex(skills), "docs/third-party-sources.md"),
    "utf8"
  );

  console.log(`OK  docs/manifest.json  (${skills.length} skills)`);
  console.log(`OK  docs/manifest.tsv   (bash-friendly)`);
  console.log(`OK  SKILLS.md           (browsable index)`);
  console.log(`OK  skills/README.md     (${categories.length} categories)`);
  console.log(`OK  skills/*/README.md   (per-category indexes)`);
  console.log(`OK  README.md            (catalog metrics + categories)`);
  console.log(`OK  docs/third-party-sources.md (attribution index)`);

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

function replaceGeneratedBlock(content, name, body, file = "README.md") {
  const start = `<!-- generated:${name}:start -->`;
  const end = `<!-- generated:${name}:end -->`;
  const from = content.indexOf(start);
  const to = content.indexOf(end);
  if (from === -1 || to === -1 || to < from) {
    throw new Error(`${file} is missing generated block '${name}'`);
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

// One table per upstream, built from each skill's `source`/`attribution`/
// `license` frontmatter, so the credits page cannot drift from the skills.
function renderAttributionIndex(skills) {
  const groups = new Map();
  let unsourced = 0;
  for (const skill of skills) {
    if (!skill.source) {
      unsourced++;
      continue;
    }
    const key = sourceKey(skill.source);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(skill);
  }
  const ordered = [...groups.entries()].sort(
    (a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0])
  );
  const sourced = skills.length - unsourced;
  const lines = [];
  lines.push(
    `${sourced} of ${skills.length} skills declare an upstream \`source\`, across ${ordered.length} sources. The remaining ${unsourced} declare no upstream source.`
  );
  lines.push("");
  for (const [key, group] of ordered) {
    const licenses = [...new Set(group.map((s) => s.license || "not declared"))].sort();
    const credits = [...new Set(group.map((s) => s.attribution).filter(Boolean))];
    lines.push(`### ${escapePipes(key.replace(/^https:\/\/github\.com\//, ""))}`);
    lines.push("");
    lines.push(`Source: ${key}`);
    if (credits.length === 1) lines.push(`Credit: ${escapePipes(credits[0])}`);
    lines.push(`License: ${licenses.map((l) => compactTableText(l, 80)).join("; ")}`);
    lines.push("");
    lines.push(`| Install path | License |`);
    lines.push(`| --- | --- |`);
    for (const skill of group) {
      lines.push(
        `| [\`${skill.install_path}\`](../${skill.path}/SKILL.md) | ${compactTableText(skill.license || "not declared", 80)} |`
      );
    }
    lines.push("");
  }
  return lines.join("\n").trimEnd();
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
  lines.push(`installer="$(mktemp)"`);
  lines.push(
    `curl -fsSL https://raw.githubusercontent.com/${repo}/${default_branch}/install.sh -o "$installer"`
  );
  lines.push(`less "$installer"  # Review the downloaded script before continuing.`);
  lines.push(`bash "$installer" <install_path> -d <destination>`);
  lines.push(`rm "$installer"`);
  lines.push("```");
  lines.push("");
  lines.push("```powershell");
  lines.push(`# PowerShell (Windows):`);
  lines.push(`$installer = Join-Path ([System.IO.Path]::GetTempPath()) "skills-install.ps1"`);
  lines.push(
    `Invoke-WebRequest https://raw.githubusercontent.com/${repo}/${default_branch}/install.ps1 -OutFile $installer`
  );
  lines.push(`Get-Content $installer -Raw  # Review the downloaded script before continuing.`);
  lines.push(`& $installer <install_path> -Dest <destination>`);
  lines.push(`Remove-Item $installer`);
  lines.push("```");
  lines.push("");
  lines.push(
    `Where \`<install_path>\` is the value from the **Install path** column below (e.g. \`engineering-craft/superpowers-test-driven-development\`).`
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
