// Install @huggingface/transformers@3.8.1 in a separate working directory and
// pass its path as --model-tools <directory>. No hosted inference is used.
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { readFrontmatter } from "./lib/frontmatter.mjs";
import { extractSearchFields } from "./lib/catalog-search-index.mjs";

const ROOT = fileURLToPath(new URL("../", import.meta.url));
const MODEL = "Xenova/all-MiniLM-L6-v2";
const REVISION = "751bff37182d3f1213fa05d7196b954e230abad9";
const { tokens, createRanker } = globalThis.skillCatalogSearch;
const modelArg = process.argv.indexOf("--model-tools");
if (modelArg < 0 || !process.argv[modelArg + 1]) {
  throw new Error("Usage: node scripts/evaluate-search.mjs --model-tools <directory with @huggingface/transformers>");
}

async function readJson(relativePath) {
  return JSON.parse(await readFile(resolve(ROOT, relativePath), "utf8"));
}

const { skills } = await readJson("docs/manifest.json");
const queries = await readJson("scripts/search-queries.json");
const index = {};
const texts = [];
const frequency = new Map();
for (const skill of skills) {
  const raw = await readFile(resolve(ROOT, skill.path, "SKILL.md"), "utf8");
  const { data, body, error } = readFrontmatter(raw);
  if (error) throw new Error(`${skill.path}: ${error}`);
  const fields = extractSearchFields(data, body);
  index[skill.install_path] = fields;
  const text = `${skill.name.replaceAll("-", " ")}. ${skill.description} ${fields.use}`;
  texts.push(text);
  for (const word of new Set(tokens(text))) {
    if (/^[a-z][a-z0-9]{2,23}$/.test(word)) frequency.set(word, (frequency.get(word) || 0) + 1);
  }
}

const resolver = createRequire(resolve(process.argv[modelArg + 1], "package.json"));
const transformers = await import(pathToFileURL(resolver.resolve("@huggingface/transformers")));
const { pipeline, env } = transformers.default || transformers;
env.cacheDir = resolve(ROOT, ".tmp/search-model-cache");
const embed = await pipeline("feature-extraction", MODEL, { revision: REVISION, dtype: "q8", device: "cpu" });

async function embedAll(values) {
  const vectors = [];
  for (let offset = 0; offset < values.length; offset += 16) {
    const features = await embed(values.slice(offset, offset + 16), { pooling: "mean", normalize: true });
    vectors.push(...features.tolist());
  }
  return vectors;
}

const vocabulary = [...frequency]
  .filter(([, count]) => count >= 3 && count < skills.length / 5)
  .sort(([a, countA], [b, countB]) => countB - countA || a.localeCompare(b, "en"))
  .slice(0, 1600)
  .map(([word]) => word);
const vectors = await embedAll(texts);
const wordVectors = await embedAll(vocabulary);
function similarity(first, second) {
  let dot = 0;
  for (let i = 0; i < first.length; i++) dot += first[i] * second[i];
  return dot;
}

for (let i = 0; i < skills.length; i++) {
  const key = skills[i].install_path;
  const present = new Set(tokens(`${texts[i]} ${key} ${index[key].headers}`));
  index[key].expand = vocabulary
    .flatMap((word, j) => present.has(word) ? [] : [{ word, score: similarity(vectors[i], wordVectors[j]) }])
    .filter(({ score }) => score >= 0.28)
    .sort((a, b) => b.score - a.score || a.word.localeCompare(b.word, "en"))
    .slice(0, 10)
    .map(({ word }) => word);
}

const rankers = [
  createRanker(skills, index, { synonyms: false, expansion: false }),
  createRanker(skills, index, { synonyms: true, expansion: false }),
  createRanker(skills, index, { synonyms: false, expansion: true }),
];
const totals = [0, 0, 0];
const results = queries.map(({ query, expected, expectedHeader }) => {
  const relevant = new Set(expected || skills.filter(skill => {
    const actual = String(skill[expectedHeader] || "").toLowerCase();
    return actual.includes(query.toLowerCase());
  }).map(skill => skill.install_path));
  if (!skills.some(skill => relevant.has(skill.install_path))) throw new Error(`No expected skill for ${query}`);
  const ranks = rankers.map((rank, i) => {
    const top = rank(query).slice(0, 5);
    const position = top.findIndex(({ skill }) => relevant.has(skill.install_path)) + 1;
    totals[i] += Number(position > 0);
    return position || null;
  });
  return { query, ranks };
});
console.log(JSON.stringify({ model: MODEL, revision: REVISION, corpus: skills.length, vocabulary: vocabulary.length,
  queryCount: queries.length, hitAt5: { lexical: totals[0], synonyms: totals[1], expansion: totals[2] }, results }, null, 2));
