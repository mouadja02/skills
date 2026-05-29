#!/usr/bin/env node
// Zero-dependency MCP server for this skills repository.
//
// It intentionally exposes compact discovery tools first, then full document
// reads only on demand. That keeps an agent's context window small while still
// making the whole skill library reachable.

import { createInterface } from "node:readline";
import {
  cp,
  mkdir,
  readdir,
  readFile,
  stat,
} from "node:fs/promises";
import { existsSync } from "node:fs";
import {
  basename,
  dirname,
  isAbsolute,
  join,
  relative,
  resolve,
  sep,
} from "node:path";
import { fileURLToPath } from "node:url";

const SERVER_NAME = "repo-skills";
const SERVER_VERSION = "0.1.0";
const DEFAULT_PROTOCOL_VERSION = "2025-06-18";
const MAX_LIST_LIMIT = 100;
const DEFAULT_DOC_CHARS = 24000;

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const ROOT = resolve(process.env.SKILLS_REPO_ROOT || join(__dirname, ".."));
const SKILLS_DIR = join(ROOT, "skills");
const MANIFEST_PATH = join(ROOT, "docs", "manifest.json");

let manifestCache = null;

const TOOLS = [
  {
    name: "list_categories",
    title: "List Skill Categories",
    description:
      "Start here. Return compact category names and skill counts so the agent can choose a focused category before loading any skill content.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      properties: {
        query: {
          type: "string",
          description: "Optional case-insensitive filter for category names.",
        },
      },
    },
  },
  {
    name: "list_skills",
    title: "List Skills In Category",
    description:
      "List compact skill metadata in one category. Use after list_categories and before reading a full SKILL.md file.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["category"],
      properties: {
        category: {
          type: "string",
          description: "Category name, for example coding or testing.",
        },
        query: {
          type: "string",
          description: "Optional filter over skill name, install path, and description.",
        },
        limit: {
          type: "integer",
          minimum: 1,
          maximum: MAX_LIST_LIMIT,
          default: 50,
        },
        cursor: {
          type: "string",
          description: "Optional numeric cursor returned by a previous call.",
        },
      },
    },
  },
  {
    name: "search_skills",
    title: "Search Skills",
    description:
      "Search names, install paths, and descriptions across the repository. Use when the right category is unclear or the user gives a pattern such as testing, MCP, React, docs, security, or migration.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["query"],
      properties: {
        query: {
          type: "string",
          description: "Search words or pattern.",
        },
        category: {
          type: "string",
          description: "Optional category to restrict results.",
        },
        limit: {
          type: "integer",
          minimum: 1,
          maximum: MAX_LIST_LIMIT,
          default: 25,
        },
      },
    },
  },
  {
    name: "get_skill",
    title: "Get Skill Metadata",
    description:
      "Return one skill's metadata, install path, file list, and a short SKILL.md preview. Use this before read_skill_doc to avoid loading large docs unnecessarily.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["skill"],
      properties: {
        skill: {
          type: "string",
          description: "Skill name or install path, for example coding/test-driven-development.",
        },
        preview_chars: {
          type: "integer",
          minimum: 0,
          maximum: 8000,
          default: 2000,
        },
      },
    },
  },
  {
    name: "read_skill_doc",
    title: "Read Skill Document",
    description:
      "Read the selected skill's SKILL.md. Use only after choosing a small number of relevant skills.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["skill"],
      properties: {
        skill: {
          type: "string",
          description: "Skill name or install path.",
        },
        max_chars: {
          type: "integer",
          minimum: 1000,
          maximum: 120000,
          default: DEFAULT_DOC_CHARS,
        },
      },
    },
  },
  {
    name: "read_category_doc",
    title: "Read Category Document",
    description:
      "Read a category README.md after selecting a category. This is useful for category-level guidance without loading every skill.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["category"],
      properties: {
        category: {
          type: "string",
          description: "Category name.",
        },
        max_chars: {
          type: "integer",
          minimum: 1000,
          maximum: 120000,
          default: DEFAULT_DOC_CHARS,
        },
      },
    },
  },
  {
    name: "list_skill_files",
    title: "List Skill Files",
    description:
      "List files bundled with a skill, including references, scripts, templates, assets, and evals. Use before reading supporting files.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["skill"],
      properties: {
        skill: {
          type: "string",
          description: "Skill name or install path.",
        },
      },
    },
  },
  {
    name: "read_skill_file",
    title: "Read Skill Supporting File",
    description:
      "Read a text file inside a selected skill folder, such as references/foo.md or evals/evals.json. Path traversal is blocked.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["skill", "relative_path"],
      properties: {
        skill: {
          type: "string",
          description: "Skill name or install path.",
        },
        relative_path: {
          type: "string",
          description: "Path relative to the skill folder, for example references/patterns.md.",
        },
        max_chars: {
          type: "integer",
          minimum: 1000,
          maximum: 120000,
          default: DEFAULT_DOC_CHARS,
        },
      },
    },
  },
  {
    name: "install_skill",
    title: "Copy Skill To Workspace",
    description:
      "Copy one skill folder into a workspace skills directory. Use only after the user or host approves file writes. Refuses to overwrite unless overwrite is true.",
    inputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["skill", "destination"],
      properties: {
        skill: {
          type: "string",
          description: "Skill name or install path.",
        },
        destination: {
          type: "string",
          description:
            "Destination directory. The skill folder is copied inside this directory unless preserve_path is true.",
        },
        preserve_path: {
          type: "boolean",
          default: false,
          description:
            "When true, copy as destination/<install_path>. When false, copy as destination/<skill-folder-name>.",
        },
        overwrite: {
          type: "boolean",
          default: false,
          description: "Allow replacing an existing destination folder.",
        },
      },
    },
  },
];

async function loadManifest() {
  if (manifestCache) return manifestCache;
  const raw = await readFile(MANIFEST_PATH, "utf8");
  manifestCache = JSON.parse(raw);
  return manifestCache;
}

function clampLimit(value, fallback = 50) {
  const n = Number.isInteger(value) ? value : fallback;
  return Math.max(1, Math.min(MAX_LIST_LIMIT, n));
}

function truncateText(text, maxChars) {
  if (text.length <= maxChars) return { text, truncated: false };
  return {
    text: text.slice(0, maxChars) + "\n\n[truncated]",
    truncated: true,
  };
}

function normalizeForSearch(value) {
  return String(value || "").toLowerCase();
}

function tokens(query) {
  return normalizeForSearch(query)
    .split(/[^a-z0-9_+#.-]+/i)
    .map((x) => x.trim())
    .filter(Boolean);
}

function skillSearchText(skill) {
  return normalizeForSearch(
    `${skill.name} ${skill.install_path} ${skill.category} ${skill.description}`
  );
}

function scoreSkill(skill, queryTokens) {
  const haystack = skillSearchText(skill);
  let score = 0;
  for (const token of queryTokens) {
    if (skill.name.toLowerCase() === token) score += 25;
    if (skill.install_path.toLowerCase().includes(token)) score += 8;
    if (skill.name.toLowerCase().includes(token)) score += 6;
    if (haystack.includes(token)) score += 2;
  }
  return score;
}

function toSkillSummary(skill) {
  return {
    name: skill.name,
    category: skill.category,
    install_path: skill.install_path,
    path: skill.path,
    description: skill.description,
  };
}

async function resolveSkill(skillRef) {
  const manifest = await loadManifest();
  const wanted = normalizeForSearch(skillRef);
  if (!wanted) throw new Error("skill is required");

  const exact = manifest.skills.filter(
    (skill) =>
      skill.install_path.toLowerCase() === wanted ||
      skill.name.toLowerCase() === wanted
  );
  if (exact.length === 1) return exact[0];

  if (exact.length > 1) {
    throw new Error(
      `Ambiguous skill name "${skillRef}". Use install_path. Matches: ${exact
        .map((x) => x.install_path)
        .slice(0, 12)
        .join(", ")}`
    );
  }

  const partial = manifest.skills.filter(
    (skill) =>
      skill.install_path.toLowerCase().includes(wanted) ||
      skill.name.toLowerCase().includes(wanted)
  );

  if (partial.length === 1) return partial[0];
  if (partial.length > 1) {
    throw new Error(
      `Ambiguous skill "${skillRef}". Use install_path. Matches: ${partial
        .map((x) => x.install_path)
        .slice(0, 12)
        .join(", ")}`
    );
  }

  throw new Error(`Skill not found: ${skillRef}`);
}

async function resolveCategory(categoryRef) {
  const manifest = await loadManifest();
  const wanted = normalizeForSearch(categoryRef);
  if (!wanted) throw new Error("category is required");

  if (manifest.categories.includes(wanted)) return wanted;

  const matches = manifest.categories.filter((category) =>
    category.toLowerCase().includes(wanted)
  );
  if (matches.length === 1) return matches[0];
  if (matches.length > 1) {
    throw new Error(
      `Ambiguous category "${categoryRef}". Matches: ${matches.join(", ")}`
    );
  }
  throw new Error(`Category not found: ${categoryRef}`);
}

function safeJoin(base, relativePath) {
  const target = resolve(base, relativePath || "");
  const baseWithSep = base.endsWith(sep) ? base : base + sep;
  if (target !== base && !target.startsWith(baseWithSep)) {
    throw new Error("Path traversal is not allowed");
  }
  return target;
}

async function walkFiles(dir, out = [], base = dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      await walkFiles(full, out, base);
    } else if (entry.isFile()) {
      const info = await stat(full);
      out.push({
        path: relative(base, full).split(sep).join("/"),
        size_bytes: info.size,
      });
    }
  }
  return out.sort((a, b) => a.path.localeCompare(b.path));
}

async function toolListCategories(args) {
  const manifest = await loadManifest();
  const query = normalizeForSearch(args?.query);
  const categories = manifest.categories
    .filter((category) => !query || category.includes(query))
    .map((category) => ({
      category,
      count: manifest.counts_by_category[category] || 0,
    }));

  return {
    repo: manifest.repo,
    total_skills: manifest.count,
    categories,
    next_step:
      "Call list_skills with one category, or search_skills if the category is unclear.",
  };
}

async function toolListSkills(args) {
  const manifest = await loadManifest();
  const category = await resolveCategory(args?.category);
  const queryTokens = tokens(args?.query || "");
  const limit = clampLimit(args?.limit, 50);
  const start = Math.max(0, Number.parseInt(args?.cursor || "0", 10) || 0);

  let skills = manifest.skills.filter((skill) => skill.category === category);
  if (queryTokens.length) {
    skills = skills
      .map((skill) => ({ skill, score: scoreSkill(skill, queryTokens) }))
      .filter((entry) => entry.score > 0)
      .sort(
        (a, b) =>
          b.score - a.score ||
          a.skill.install_path.localeCompare(b.skill.install_path)
      )
      .map((entry) => entry.skill);
  }

  const page = skills.slice(start, start + limit).map(toSkillSummary);
  const nextCursor = start + limit < skills.length ? String(start + limit) : undefined;

  return {
    category,
    total_matches: skills.length,
    skills: page,
    nextCursor,
    next_step:
      "Call get_skill for a compact preview, then read_skill_doc only for selected skills.",
  };
}

async function toolSearchSkills(args) {
  const manifest = await loadManifest();
  const queryTokens = tokens(args?.query);
  if (!queryTokens.length) throw new Error("query is required");
  const limit = clampLimit(args?.limit, 25);
  const category = args?.category ? await resolveCategory(args.category) : null;

  const results = manifest.skills
    .filter((skill) => !category || skill.category === category)
    .map((skill) => ({ skill, score: scoreSkill(skill, queryTokens) }))
    .filter((entry) => entry.score > 0)
    .sort(
      (a, b) =>
        b.score - a.score ||
        a.skill.install_path.localeCompare(b.skill.install_path)
    )
    .slice(0, limit)
    .map((entry) => ({ ...toSkillSummary(entry.skill), score: entry.score }));

  return {
    query: args.query,
    category,
    total_returned: results.length,
    skills: results,
    next_step:
      "Call get_skill on likely matches. Prefer install_path when names are ambiguous.",
  };
}

async function toolGetSkill(args) {
  const skill = await resolveSkill(args?.skill);
  const skillDir = join(ROOT, skill.path);
  const raw = await readFile(join(skillDir, "SKILL.md"), "utf8");
  const maxChars = Math.max(0, Math.min(8000, args?.preview_chars ?? 2000));
  const preview = truncateText(raw, maxChars);
  const files = await walkFiles(skillDir);

  return {
    skill: toSkillSummary(skill),
    root: skill.path,
    files,
    preview: preview.text,
    preview_truncated: preview.truncated,
    next_step:
      "Call read_skill_doc for the full instructions, or install_skill to copy this skill into a workspace.",
  };
}

async function toolReadSkillDoc(args) {
  const skill = await resolveSkill(args?.skill);
  const raw = await readFile(join(ROOT, skill.path, "SKILL.md"), "utf8");
  const maxChars = Math.min(120000, Math.max(1000, args?.max_chars ?? DEFAULT_DOC_CHARS));
  const doc = truncateText(raw, maxChars);

  return {
    skill: toSkillSummary(skill),
    document: "SKILL.md",
    text: doc.text,
    truncated: doc.truncated,
  };
}

async function toolReadCategoryDoc(args) {
  const category = await resolveCategory(args?.category);
  const path = join(SKILLS_DIR, category, "README.md");
  if (!existsSync(path)) throw new Error(`README.md not found for category: ${category}`);
  const raw = await readFile(path, "utf8");
  const maxChars = Math.min(120000, Math.max(1000, args?.max_chars ?? DEFAULT_DOC_CHARS));
  const doc = truncateText(raw, maxChars);

  return {
    category,
    document: `skills/${category}/README.md`,
    text: doc.text,
    truncated: doc.truncated,
  };
}

async function toolListSkillFiles(args) {
  const skill = await resolveSkill(args?.skill);
  const files = await walkFiles(join(ROOT, skill.path));
  return {
    skill: toSkillSummary(skill),
    files,
    next_step:
      "Call read_skill_file for specific references or scripts. Call read_skill_doc for SKILL.md.",
  };
}

async function toolReadSkillFile(args) {
  const skill = await resolveSkill(args?.skill);
  const skillDir = join(ROOT, skill.path);
  const target = safeJoin(skillDir, args?.relative_path);
  if (!existsSync(target)) throw new Error(`File not found: ${args.relative_path}`);
  const info = await stat(target);
  if (!info.isFile()) throw new Error(`Not a file: ${args.relative_path}`);
  const raw = await readFile(target, "utf8");
  const maxChars = Math.min(120000, Math.max(1000, args?.max_chars ?? DEFAULT_DOC_CHARS));
  const doc = truncateText(raw, maxChars);

  return {
    skill: toSkillSummary(skill),
    document: args.relative_path,
    text: doc.text,
    truncated: doc.truncated,
  };
}

async function toolInstallSkill(args) {
  const skill = await resolveSkill(args?.skill);
  const destination = args?.destination;
  if (!destination || typeof destination !== "string") {
    throw new Error("destination is required");
  }

  const source = join(ROOT, skill.path);
  const destinationRoot = isAbsolute(destination)
    ? resolve(destination)
    : resolve(process.cwd(), destination);
  const target = args?.preserve_path
    ? join(destinationRoot, ...skill.install_path.split("/"))
    : join(destinationRoot, basename(skill.path));

  if (existsSync(target) && !args?.overwrite) {
    throw new Error(
      `Destination exists: ${target}. Pass overwrite=true to replace it.`
    );
  }

  await mkdir(dirname(target), { recursive: true });
  await cp(source, target, {
    recursive: true,
    force: Boolean(args?.overwrite),
    errorOnExist: !args?.overwrite,
  });

  return {
    skill: toSkillSummary(skill),
    copied_from: source,
    copied_to: target,
    overwrite: Boolean(args?.overwrite),
  };
}

const TOOL_HANDLERS = {
  list_categories: toolListCategories,
  list_skills: toolListSkills,
  search_skills: toolSearchSkills,
  get_skill: toolGetSkill,
  read_skill_doc: toolReadSkillDoc,
  read_category_doc: toolReadCategoryDoc,
  list_skill_files: toolListSkillFiles,
  read_skill_file: toolReadSkillFile,
  install_skill: toolInstallSkill,
};

function send(message) {
  process.stdout.write(JSON.stringify(message) + "\n");
}

function respond(id, result) {
  send({ jsonrpc: "2.0", id, result });
}

function respondError(id, code, message, data) {
  send({
    jsonrpc: "2.0",
    id,
    error: { code, message, ...(data === undefined ? {} : { data }) },
  });
}

function toolResult(value) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(value, null, 2),
      },
    ],
    isError: false,
  };
}

function toolError(error) {
  return {
    content: [
      {
        type: "text",
        text: error?.message || String(error),
      },
    ],
    isError: true,
  };
}

async function handleRequest(message) {
  const { id, method, params = {} } = message;

  if (method === "initialize") {
    respond(id, {
      protocolVersion: params.protocolVersion || DEFAULT_PROTOCOL_VERSION,
      capabilities: {
        tools: {
          listChanged: false,
        },
      },
      serverInfo: {
        name: SERVER_NAME,
        version: SERVER_VERSION,
      },
      instructions:
        "Use list_categories first, list_skills or search_skills second, get_skill third, and read_skill_doc only for selected skills. Use install_skill to copy chosen skills into the workspace.",
    });
    return;
  }

  if (method === "ping") {
    respond(id, {});
    return;
  }

  if (method === "tools/list") {
    respond(id, { tools: TOOLS });
    return;
  }

  if (method === "tools/call") {
    const name = params.name;
    const handler = TOOL_HANDLERS[name];
    if (!handler) {
      respondError(id, -32602, `Unknown tool: ${name}`);
      return;
    }

    try {
      const result = await handler(params.arguments || {});
      respond(id, toolResult(result));
    } catch (error) {
      respond(id, toolError(error));
    }
    return;
  }

  respondError(id, -32601, `Method not found: ${method}`);
}

async function handleMessage(line) {
  if (!line.trim()) return;

  let message;
  try {
    message = JSON.parse(line.replace(/^\uFEFF/, ""));
  } catch (error) {
    respondError(null, -32700, "Parse error", error.message);
    return;
  }

  if (!message || message.jsonrpc !== "2.0") {
    respondError(message?.id ?? null, -32600, "Invalid JSON-RPC message");
    return;
  }

  // Notifications have no id and require no response.
  if (message.id === undefined) {
    return;
  }

  try {
    await handleRequest(message);
  } catch (error) {
    respondError(message.id, -32603, error?.message || "Internal error");
  }
}

const rl = createInterface({
  input: process.stdin,
  crlfDelay: Infinity,
});

let messageQueue = Promise.resolve();

rl.on("line", (line) => {
  messageQueue = messageQueue
    .then(() => handleMessage(line))
    .catch((error) => {
      console.error(error);
    });
});
