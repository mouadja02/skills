// Shared publication policy for skill packages.
//
// The Git index decides which files a skill has; this policy then drops local
// residue (caches, editor state, credentials) that must never ship. ZIP builds,
// the ZIP audit, the skill linter, and MCP install_skill all apply it, so every
// route delivers the same files and tracked residue fails before merge.
//
// No npm dependencies: the MCP server imports this module at runtime.

import { execFileSync } from "node:child_process";

// Names are compared lowercased.
export const EXCLUDED_DIRECTORY_NAMES = new Set([
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
export const EXCLUDED_FILE_NAMES = new Set([
  ".ds_store",
  "thumbs.db",
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

// Returns why a path must not be published, or null when it may be. Accepts
// POSIX or Windows separators; every segment is checked.
export function excludedReason(path) {
  const segments = path.replaceAll("\\", "/").split("/").filter(Boolean);
  if (segments.some((segment) => EXCLUDED_DIRECTORY_NAMES.has(segment.toLowerCase()))) return "excluded directory";
  const lowerFile = (segments.at(-1) || "").toLowerCase();
  if (EXCLUDED_FILE_NAMES.has(lowerFile)) return "excluded file";
  if (SENSITIVE_DATA_FILE.test(lowerFile)) return "credential-like filename";
  if (/\.(?:py[co]|sw[op]|tmp|log|pem|key|p12|pfx|tfstate)$/i.test(lowerFile) || lowerFile.includes(".tfstate.")) {
    return "cache, credential, state, log, or temporary file";
  }
  if (lowerFile.startsWith(".env.") && !SAFE_ENV_TEMPLATES.has(lowerFile)) return "environment file";
  return null;
}

function gitPaths(root, args) {
  // Literal pathspecs: a path is never read as a glob.
  const output = execFileSync("git", ["--literal-pathspecs", ...args], { cwd: root, encoding: "buffer", maxBuffer: 64 * 1024 * 1024 });
  return output.toString("utf8").split("\0").filter(Boolean).map((path) => path.replaceAll("\\", "/"));
}

// Reads the publication allowlist for `pathspec` (relative to `root`) from the
// Git index: tracked files, every directory that contains one, and the
// untracked files Git does not ignore. Throws when `root` is not a checkout.
export function gitPublicationAllowlist(root, pathspec = "skills") {
  const files = new Set(gitPaths(root, ["ls-files", "-z", "--cached", "--", pathspec]));
  const untracked = gitPaths(root, ["ls-files", "-z", "--others", "--exclude-standard", "--", pathspec]);
  const dirs = new Set([pathspec]);
  for (const file of files) {
    const parts = file.split("/");
    for (let index = 1; index < parts.length; index++) dirs.add(parts.slice(0, index).join("/"));
  }
  return { files, dirs, untracked };
}
