#!/usr/bin/env node
// Generates downloadable ZIP archives served by the GitHub Pages site.
//
//   docs/zips/skill/<install_path>.zip      one per skill
//   docs/zips/category/<category>.zip       one per category (all its skills)
//   docs/zips/all.zip                       all skills
//   docs/zips/_summary.json                 metadata: file sizes, sha if useful
//
// Each ZIP unzips to a folder named after the skill (or the category), so the
// user can drop the result straight into ~/.claude/skills/.
//
// Run with: node scripts/build-zips.mjs
//
// Requires: adm-zip (devDependency in package.json).
// CI installs it; locally run `npm install` first.

import { createHash } from "node:crypto";
import { readFile, writeFile, mkdir, rm } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join, posix, basename } from "node:path";
import { fileURLToPath } from "node:url";
import AdmZip from "adm-zip";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const ROOT = join(__dirname, "..");
const MANIFEST_PATH = join(ROOT, "docs", "manifest.json");
const SKILLS_DIR = join(ROOT, "skills");
const ZIPS_DIR = join(ROOT, "docs", "zips");
const SKILL_DIR = join(ZIPS_DIR, "skill");
const CATEGORY_DIR = join(ZIPS_DIR, "category");
const ALL_ZIP_PATH = join(ZIPS_DIR, "all.zip");
const SUMMARY_PATH = join(ZIPS_DIR, "_summary.json");
const PUBLIC_BASE_URL = process.env.SKILLS_PUBLIC_BASE_URL || "";

async function zipMetadata(outPath, relativeUrl, extra = {}) {
  const data = await readFile(outPath);
  const sha256 = createHash("sha256").update(data).digest("hex");
  await writeFile(`${outPath}.sha256`, `${sha256}  ${basename(outPath)}\n`, "utf8");
  return {
    ...extra,
    bytes: data.length,
    sha256,
    url: relativeUrl,
    ...(PUBLIC_BASE_URL
      ? { public_url: `${PUBLIC_BASE_URL.replace(/\/+$/, "")}/${relativeUrl}` }
      : {}),
  };
}

async function main() {
  if (!existsSync(MANIFEST_PATH)) {
    console.error(
      "ERROR: docs/manifest.json not found. Run `node scripts/build-manifest.mjs` first."
    );
    process.exit(1);
  }

  const manifest = JSON.parse(await readFile(MANIFEST_PATH, "utf8"));

  // Wipe and recreate to avoid stale zips from removed skills.
  await rm(ZIPS_DIR, { recursive: true, force: true });
  await mkdir(SKILL_DIR, { recursive: true });
  await mkdir(CATEGORY_DIR, { recursive: true });

  const summary = {
    generated_at: new Date().toISOString(),
    repo: manifest.repo,
    branch: manifest.default_branch,
    public_base_url: PUBLIC_BASE_URL || null,
    skill_count: 0,
    category_count: 0,
    total_bytes: 0,
    all: null,
    skills: {},
    categories: {},
  };

  console.log(`Building per-skill ZIPs (${manifest.skills.length})...`);
  for (const skill of manifest.skills) {
    const folder = join(ROOT, skill.path); // skills/<install_path>
    if (!existsSync(folder)) {
      console.warn(`  skip ${skill.install_path}: source missing`);
      continue;
    }

    const zip = new AdmZip();
    const skillName = basename(skill.install_path);
    // Place files under "<skill-name>/..." inside the zip so unzipping yields
    // a single tidy folder ready to drop into ~/.claude/skills/.
    zip.addLocalFolder(folder, skillName);

    const outPath = join(SKILL_DIR, skill.install_path) + ".zip";
    await mkdir(dirname(outPath), { recursive: true });
    zip.writeZip(outPath);

    const meta = await zipMetadata(outPath, `zips/skill/${skill.install_path}.zip`);
    summary.skills[skill.install_path] = meta;
    summary.skill_count++;
    summary.total_bytes += meta.bytes;
  }

  console.log(`Building per-category ZIPs (${manifest.categories.length})...`);
  for (const category of manifest.categories) {
    const folder = join(SKILLS_DIR, category);
    if (!existsSync(folder)) continue;

    const zip = new AdmZip();
    zip.addLocalFolder(folder, category);

    const outPath = join(CATEGORY_DIR, category + ".zip");
    zip.writeZip(outPath);

    const meta = await zipMetadata(outPath, `zips/category/${category}.zip`, {
      skill_count: manifest.counts_by_category[category] ?? 0,
    });
    summary.categories[category] = meta;
    summary.category_count++;
    summary.total_bytes += meta.bytes;
  }

  console.log("Building all-skills ZIP...");
  const allZip = new AdmZip();
  allZip.addLocalFolder(SKILLS_DIR, "skills");
  allZip.writeZip(ALL_ZIP_PATH);
  summary.all = await zipMetadata(ALL_ZIP_PATH, "zips/all.zip", {
    skill_count: manifest.count,
  });
  summary.total_bytes += summary.all.bytes;

  await writeFile(SUMMARY_PATH, JSON.stringify(summary, null, 2) + "\n", "utf8");

  const mb = (summary.total_bytes / 1024 / 1024).toFixed(2);
  console.log(
    `OK  ${summary.skill_count} skill zips + ${summary.category_count} category zips + all.zip  (${mb} MB total)`
  );
  console.log(`OK  docs/zips/_summary.json`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
