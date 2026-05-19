/**
 * Skills AI Proxy — Cloudflare Worker
 *
 * A thin CORS-aware proxy that forwards chat completion requests to NVIDIA's
 * OpenAI-compatible API. The NVIDIA API key lives only in this Worker's secret
 * store — it is never shipped to the browser.
 *
 * Environment secrets (set via `wrangler secret put`):
 *   NVIDIA_API_KEY  — your nvapi-... key
 *   NVIDIA_MODEL    — (optional) model override, e.g. stepfun-ai/step-3.5-flash
 *   ALLOWED_ORIGIN  — (optional) restrict to your Pages domain, e.g. https://you.github.io
 */

const NVIDIA_COMPLETIONS = "https://integrate.api.nvidia.com/v1/chat/completions";
const DEFAULT_MODEL      = "stepfun-ai/step-3.5-flash";
const MAX_TOKENS_CAP     = 4096;

// ─── CORS helpers ──────────────────────────────────────────────────────────────

function corsHeaders(origin, env) {
  const allowed = env.ALLOWED_ORIGIN || "*";
  // If a specific origin is configured, only allow that origin.
  // Otherwise reflect the request origin (or '*' for open access).
  const allowOrigin =
    allowed === "*"
      ? "*"
      : origin === allowed
      ? origin
      : null;

  if (!allowOrigin) return null; // reject

  return {
    "Access-Control-Allow-Origin":  allowOrigin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age":       "86400",
    // Vary so caches don't serve the wrong ACAO header to different origins
    "Vary": "Origin",
  };
}

function preflight(headers) {
  return new Response(null, { status: 204, headers });
}

function jsonError(status, message, corsHdrs) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { "Content-Type": "application/json", ...corsHdrs },
  });
}

// ─── Main handler ──────────────────────────────────────────────────────────────

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const cors   = corsHeaders(origin, env);

    // Reject requests from disallowed origins
    if (cors === null) {
      return new Response("Forbidden", { status: 403 });
    }

    // Preflight (OPTIONS)
    if (request.method === "OPTIONS") {
      return preflight(cors);
    }

    // Only accept POST to /v1/chat/completions
    const url = new URL(request.url);
    if (request.method !== "POST" || url.pathname !== "/v1/chat/completions") {
      return jsonError(404, "Not found — only POST /v1/chat/completions is supported.", cors);
    }

    // Validate API key is configured
    const apiKey = env.NVIDIA_API_KEY;
    if (!apiKey) {
      return jsonError(500, "Worker is not configured: missing NVIDIA_API_KEY secret.", cors);
    }

    // Parse request body
    let body;
    try {
      body = await request.json();
    } catch {
      return jsonError(400, "Invalid JSON body.", cors);
    }

    // Safety: cap max_tokens
    if (!body.max_tokens || body.max_tokens > MAX_TOKENS_CAP) {
      body.max_tokens = MAX_TOKENS_CAP;
    }

    // Override model from Worker secret if provided
    const model = env.NVIDIA_MODEL || DEFAULT_MODEL;
    body.model = model;

    // Forward to NVIDIA — add the real API key here on the server side
    let upstream;
    try {
      upstream = await fetch(NVIDIA_COMPLETIONS, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${apiKey}`,
        },
        body: JSON.stringify(body),
      });
    } catch (err) {
      return jsonError(502, `Upstream fetch failed: ${err.message}`, cors);
    }

    // Pass the streaming body through with CORS headers added.
    // We clone only the headers we care about so the stream is not buffered.
    const upstreamContentType =
      upstream.headers.get("Content-Type") || "text/event-stream; charset=utf-8";

    const responseHeaders = {
      "Content-Type": upstreamContentType,
      ...cors,
    };

    // Propagate non-2xx status codes from NVIDIA (e.g. 429, 401, 400)
    return new Response(upstream.body, {
      status:  upstream.status,
      headers: responseHeaders,
    });
  },
};
