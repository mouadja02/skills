#!/usr/bin/env node
// Verifies generated ZIP coverage, integrity, checksums, safe paths, and hygiene.

import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFile, readdir, lstat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { basename, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";
import AdmZip from "adm-zip";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const ROOT = join(__dirname, "..");
const ZIPS_DIR = join(ROOT, "docs", "zips");
const MANIFEST_PATH = join(ROOT, "docs", "manifest.json");
const SUMMARY_PATH = join(ZIPS_DIR, "_summary.json");
const SKILLS_DIR = join(ROOT, "skills");
const FORBIDDEN_DIRS = new Set([
  "__pycache__",
  ".pytest_cache",
  ".ruff_cache",
  ".mypy_cache",
  ".cache",
  ".tmp",
  ".git",
  ".idea",
  ".direnv",
  ".aws",
  ".ssh",
  ".gnupg",
  ".kube",
  ".tox",
  ".nox",
  "node_modules",
  ".venv",
  "venv",
]);
const FORBIDDEN_FILES = new Set([
  ".DS_Store",
  "Thumbs.db",
  "desktop.ini",
  ".env",
  ".envrc",
  ".coverage",
  ".npmrc",
  ".pypirc",
  ".netrc",
  ".git-credentials",
  ".authinfo",
  "credentials.json",
  "service-account.json",
  "application_default_credentials.json",
  "secrets.json",
  "id_rsa",
  "id_ed25519",
]);
const SAFE_ENV_TEMPLATES = new Set([".env.example", ".env.sample", ".env.template"]);
const SENSITIVE_DATA_FILE = /^(?:token|access-token|refresh-token|password|passwd|secret|credentials?|api-key|apikey|private-key)(?:\.(?:txt|json|ya?ml|ini|conf|cfg))?$/i;
let TRACKED_FILES = new Set();
let TRACKED_DIRS = new Set();

function gitPaths(args) {
  const output = execFileSync("git", args, { cwd: ROOT, encoding: "buffer" });
  return output.toString("utf8").split("\0").filter(Boolean).map((path) => path.replaceAll("\\", "/"));
}

function initializeGitAllowlist() {
  const untracked = gitPaths(["ls-files", "-z", "--others", "--exclude-standard", "--", "skills"]);
  if (untracked.length) {
    throw new Error(`Refusing to audit with untracked skill files: ${JSON.stringify(untracked.slice(0, 20))}`);
  }
  TRACKED_FILES = new Set(gitPaths(["ls-files", "-z", "--cached", "--", "skills"]));
  TRACKED_DIRS = new Set(["skills"]);
  for (const file of TRACKED_FILES) {
    const parts = file.split("/");
    for (let index = 1; index < parts.length; index++) TRACKED_DIRS.add(parts.slice(0, index).join("/"));
  }
}

function toPosix(path) {
  return path.split(sep).join("/");
}

function forbiddenMember(name) {
  if (!name || name.includes("\\") || name.startsWith("/") || /^[A-Za-z]:/.test(name)) {
    return "absolute, empty, or non-POSIX path";
  }
  const segments = name.split("/").filter(Boolean);
  if (segments.includes("..")) return "path traversal";
  if (segments.some((segment) => FORBIDDEN_DIRS.has(segment.toLowerCase()))) return "excluded directory";
  const file = segments.at(-1) || "";
  const lowerFile = file.toLowerCase();
  if (FORBIDDEN_FILES.has(lowerFile)) return "excluded file";
  if (SENSITIVE_DATA_FILE.test(lowerFile)) return "credential-like filename";
  if (/\.(?:py[co]|sw[op]|tmp|log|pem|key|p12|pfx|tfstate)$/i.test(lowerFile) || lowerFile.includes(".tfstate.")) {
    return "cache, credential, state, log, or temporary file";
  }
  if (lowerFile.startsWith(".env.") && !SAFE_ENV_TEMPLATES.has(lowerFile)) return "environment file";
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

function verifyDownloadPath(summary, archivePath, meta, errors) {
  if (!meta) return;
  const relativeUrl = `zips/${archivePath}`;
  if (meta.url !== relativeUrl) errors.push(`${archivePath}: summary relative URL mismatch`);
  const base = summary.public_base_url;
  if (base === null || base === "") {
    if (Object.hasOwn(meta, "public_url")) errors.push(`${archivePath}: unexpected public URL without base`);
    return;
  }
  let parsed;
  try {
    parsed = new URL(base);
  } catch {
    errors.push("summary public_base_url is not a valid URL");
    return;
  }
  if (parsed.protocol !== "https:" || parsed.username || parsed.password || parsed.search || parsed.hash) {
    errors.push("summary public_base_url must be a credential-free HTTPS base URL");
    return;
  }
  const canonicalBase = parsed.href.replace(/\/+$/, "");
  const declaredBase = base.replace(/\/+$/, "");
  if (canonicalBase !== declaredBase) {
    errors.push("summary public_base_url must use its canonical URL form");
    return;
  }
  const expected = `${declaredBase}/${relativeUrl}`;
  if (meta.public_url !== expected) errors.push(`${archivePath}: summary public URL mismatch`);
}

async function expectedArchiveMembers(archivePath, manifest, errors) {
  let localRoot;
  let zipRoot;
  if (archivePath === "all.zip") {
    localRoot = SKILLS_DIR;
    zipRoot = "skills";
  } else if (archivePath.startsWith("category/") && archivePath.endsWith(".zip")) {
    zipRoot = archivePath.slice("category/".length, -".zip".length);
    localRoot = join(SKILLS_DIR, zipRoot);
  } else if (archivePath.startsWith("skill/") && archivePath.endsWith(".zip")) {
    const installPath = archivePath.slice("skill/".length, -".zip".length);
    const skill = manifest.skills.find((item) => item.install_path === installPath);
    if (!skill) return new Set();
    localRoot = join(ROOT, skill.path);
    zipRoot = basename(installPath);
  } else {
    return new Set();
  }

  const expected = new Set();
  async function walk(localDir, zipDir) {
    const entries = await readdir(localDir, { withFileTypes: true });
    entries.sort((a, b) => a.name.localeCompare(b.name));
    for (const entry of entries) {
      const localPath = join(localDir, entry.name);
      const zipPath = `${zipDir}/${entry.name}`;
      if (forbiddenMember(zipPath)) continue;
      const stats = await lstat(localPath);
      if (stats.isSymbolicLink()) {
        errors.push(`${archivePath}: source contains symbolic link ${zipPath}`);
      } else if (stats.isDirectory()) {
        if (!TRACKED_DIRS.has(toPosix(relative(ROOT, localPath)))) continue;
        expected.add(`${zipPath}/`);
        await walk(localPath, zipPath);
      } else if (stats.isFile()) {
        if (!TRACKED_FILES.has(toPosix(relative(ROOT, localPath)))) continue;
        expected.add(zipPath);
      } else {
        errors.push(`${archivePath}: source contains special file ${zipPath}`);
      }
    }
  }
  await walk(localRoot, zipRoot);
  return expected;
}

async function main() {
  initializeGitAllowlist();
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
    const metadata = summaryMetadata(summary, archivePath);
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
    const expectedMembers = await expectedArchiveMembers(archivePath, manifest, errors);
    for (const member of expectedMembers) {
      if (!seen.has(member)) errors.push(`${archivePath}: expected member missing: ${member}`);
    }
    for (const member of seen) {
      if (!expectedMembers.has(member)) errors.push(`${archivePath}: unexpected member: ${member}`);
    }
    verifyDownloadPath(summary, archivePath, metadata, errors);
    totalBytes += await verifyChecksum(zipPath, metadata, errors);
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
