import "../../docs/catalog-search.js";

const { tokens } = globalThis.skillCatalogSearch;

function fieldText(value) {
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (Array.isArray(value)) return value.map(fieldText).join(" ");
  return "";
}

function uniqueWords(text, limit) {
  return [...new Set(tokens(text))].slice(0, limit).join(" ");
}

export function extractSearchFields(frontmatter, body) {
  const headers = [
    frontmatter.license, frontmatter.attribution, frontmatter.source, frontmatter.platform,
    frontmatter.platforms, frontmatter.compatibility, frontmatter.triggers,
    frontmatter.tags, frontmatter.keywords, frontmatter.metadata?.tags,
    frontmatter.metadata?.keywords, frontmatter.version, frontmatter["allowed-tools"],
  ].map(fieldText).join(" ");

  const activation = [];
  const headings = [];
  let headingDepth = 0;
  let fence = "";
  for (const line of body.split("\n")) {
    const marker = /^\s*(```+|~~~+)/.exec(line)?.[1][0];
    if (marker) {
      if (!fence || marker === fence) fence = fence ? "" : marker;
      continue;
    }
    if (fence) continue;
    const heading = /^(#{1,6})\s+(.+)$/.exec(line);
    if (heading) {
      const depth = heading[1].length;
      const title = heading[2].replace(/#+$/, "").trim();
      if (headingDepth && depth <= headingDepth) headingDepth = 0;
      if (/^(?:when|where) to use\b|^use cases\b/i.test(title)) headingDepth = depth;
      if (depth <= 3) headings.push(title);
    } else if (headingDepth && line.trim()) {
      activation.push(line.trim());
    }
  }
  return {
    use: uniqueWords([...activation, ...headings].join(" "), 75),
    headers: uniqueWords(headers, 60),
  };
}
