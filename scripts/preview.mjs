#!/usr/bin/env node
// Minimal zero-dependency static server to preview docs/ locally.
// Usage: node scripts/preview.mjs [--port 4173]

import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const ROOT = join(__dirname, "..", "docs");

const args = process.argv.slice(2);
let port = 4173;
for (let i = 0; i < args.length; i++) {
  if ((args[i] === "--port" || args[i] === "-p") && args[i + 1]) {
    port = Number(args[++i]);
  }
}

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".mjs": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".tsv": "text/tab-separated-values; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".ico": "image/x-icon",
  ".zip": "application/zip",
  ".webmanifest": "application/manifest+json",
};

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host}`);
    let urlPath = decodeURIComponent(url.pathname);
    if (urlPath.endsWith("/")) urlPath += "index.html";

    const safe = normalize(urlPath).replace(/^([./\\])+/, "");
    const filePath = join(ROOT, safe);
    if (!filePath.startsWith(ROOT + sep) && filePath !== ROOT) {
      res.writeHead(403).end("forbidden");
      return;
    }

    const st = await stat(filePath);
    const target = st.isDirectory() ? join(filePath, "index.html") : filePath;
    const data = await readFile(target);
    const mime = MIME[extname(target).toLowerCase()] || "application/octet-stream";

    res.writeHead(200, {
      "content-type": mime,
      "cache-control": "no-cache",
      "access-control-allow-origin": "*",
    });
    res.end(data);
  } catch (err) {
    res.writeHead(err.code === "ENOENT" ? 404 : 500).end(String(err.message));
  }
});

server.listen(port, () => {
  console.log(`Serving ${ROOT}`);
  console.log(`http://localhost:${port}/`);
});
