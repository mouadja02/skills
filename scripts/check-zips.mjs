#!/usr/bin/env node
// Verifies generated ZIP coverage, integrity, checksums, safe paths, and hygiene.

import { createHash } from "node:crypto";
import { readFile, readdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { basename, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";
import AdmZip from "adm-zip";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const ROOT = join(__dirname, "..");
const ZIPS_DIR = join(ROOT, "docs", "zips");
const MANIFEST_PATH = join(ROOT, "docs", "manifest.json");
const SUMMARY_PATH = join(ZIPS_DIR, "_summary.json");
const FORBIDDEN_DIRS = new Set([
  "__pycache__",
  ".pytest_cache",
  ".ruff_cache",
  ".mypy_cache",
  ".cache",
  ".tmp",
  ".git",
  "node_modules",
  ".venv",
  "venv",
]);
const FORBIDDEN_FILES = new Set([".DS_Store", "Thumbs.db", "desktop.ini", ".env"]);

function toPosix(path) {
  return path.split(sep).join("/");
}

function forbiddenMember(name) {
  if (!name || name.includes("\\") || name.startsWith("/") || /^[A-Za-z]:/.test(name)) {
    return "absolute, empty, or non-POSIX path";
  }
  const segments = name.split("/").filter(Boolean);
  if (segments.includes("..")) return "path traversal";
  if (segments.some((segment) => FORBIDDEN_DIRS.has(segment))) return "excluded directory";
  const file = segments.at(-1) || "";
  if (FORBIDDEN_FILES.has(file)) return "excluded file";
  if (/\.(?:py[co]|sw[op]|tmp)$/i.test(file)) return "cache or temporary file";
  if (/^\.env\.(?:local|production|development|test)$/i.test(file)) return "environment file";
  return null;
}

async function listFiles(dir, out = []) {
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) await listFiles(full, out);
    else if (entry.isFile()) out.push(full);
  }
  return out;
}

async function verifyChecksum(zipPath, summaryMeta, errors) {
  const sidecar = `${zipPath}.sha256`;
  const data = await readFile(zipPath);
  const actual = createHash("sha256").update(data).digest("hex");
  if (!existsSync(sidecar)) {
    errors.push(`${toPosix(relative(ROOT, zipPath))}: missing checksum sidecar`);
  } else {
    const text = (await readFile(sidecar, "utf8")).trim();
    const expected = `${actual}  ${basename(zipPath)}`;
    if (text !== expected) errors.push(`${toPosix(relative(ROOT, sidecar))}: checksum mismatch`);
  }
  if (!summaryMeta || summaryMeta.sha256 !== actual || summaryMeta.bytes !== data.length) {
    errors.push(`${toPosix(relative(ROOT, zipPath))}: summary hash or size mismatch`);
  }
  return data.length;
}

function summaryMetadata(summary, archivePath) {
  if (archivePath === "all.zip") return summary.all;
  if (archivePath.startsWith("skill/") && archivePath.endsWith(".zip")) {
    return summary.skills?.[archivePath.slice("skill/".length, -".zip".length)];
  }
  if (archivePath.startsWith("category/") && archivePath.endsWith(".zip")) {
    return summary.categories?.[archivePath.slice("category/".length, -".zip".length)];
  }
  return null;
}

async function main() {
  const errors = [];
  if (!existsSync(MANIFEST_PATH) || !existsSync(SUMMARY_PATH)) {
    console.error("ERROR: manifest or ZIP summary missing; run npm run build:zips first.");
    process.exit(1);
  }

  const manifest = JSON.parse(await readFile(MANIFEST_PATH, "utf8"));
  const summary = JSON.parse(await readFile(SUMMARY_PATH, "utf8"));
  const expected = new Set([
    ...manifest.skills.map((skill) => `skill/${skill.install_path}.zip`),
    ...manifest.categories.map((category) => `category/${category}.zip`),
    "all.zip",
  ]);
  const generatedFiles = (await listFiles(ZIPS_DIR)).sort();
  const zipFiles = generatedFiles.filter((path) => path.endsWith(".zip"));
  const actual = new Set(zipFiles.map((path) => toPosix(relative(ZIPS_DIR, path))));
  const expectedFiles = new Set([
    ...expected,
    ...[...expected].map((path) => `${path}.sha256`),
    "_summary.json",
  ]);
  const actualFiles = new Set(generatedFiles.map((path) => toPosix(relative(ZIPS_DIR, path))));

  for (const path of expected) if (!actual.has(path)) errors.push(`${path}: expected archive missing`);
  for (const path of actual) if (!expected.has(path)) errors.push(`${path}: unexpected stale archive`);
  for (const path of expectedFiles) if (!actualFiles.has(path)) errors.push(`${path}: expected artifact missing`);
  for (const path of actualFiles) if (!expectedFiles.has(path)) errors.push(`${path}: unexpected stale artifact`);
  if (summary.skill_count !== manifest.count) errors.push("summary skill_count does not match manifest");
  if (summary.category_count !== manifest.categories.length) errors.push("summary category_count does not match manifest");
  if (Object.keys(summary.skills || {}).length !== manifest.count) errors.push("summary skills map is incomplete");
  if (Object.keys(summary.categories || {}).length !== manifest.categories.length) errors.push("summary categories map is incomplete");

  let totalBytes = 0;
  for (const zipPath of zipFiles) {
    const archivePath = toPosix(relative(ZIPS_DIR, zipPath));
    let archive;
    try {
      archive = new AdmZip(zipPath);
      if (!archive.test()) errors.push(`${toPosix(relative(ROOT, zipPath))}: integrity test failed`);
    } catch (error) {
      errors.push(`${toPosix(relative(ROOT, zipPath))}: unreadable archive: ${error.message}`);
      continue;
    }
    const seen = new Set();
    for (const entry of archive.getEntries()) {
      if (seen.has(entry.entryName)) {
        errors.push(`${toPosix(relative(ROOT, zipPath))}: duplicate member ${entry.entryName}`);
      }
      seen.add(entry.entryName);
      const reason = forbiddenMember(entry.entryName);
      if (reason) errors.push(`${toPosix(relative(ROOT, zipPath))}: ${reason}: ${entry.entryName}`);
    }
    totalBytes += await verifyChecksum(zipPath, summaryMetadata(summary, archivePath), errors);
  }
  if (summary.total_bytes !== totalBytes) errors.push("summary total_bytes does not match archives");

  if (errors.length) {
    console.error(`ZIP audit failed with ${errors.length} issue(s):`);
    for (const error of errors.slice(0, 100)) console.error(`  - ${error}`);
    if (errors.length > 100) console.error(`  - ... ${errors.length - 100} more`);
    process.exit(1);
  }

  console.log(`OK  ${zipFiles.length} archives are present and readable`);
  console.log("OK  archive counts, checksums, member paths, and exclusion rules pass");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
