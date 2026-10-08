# Skills AI Proxy — Cloudflare Worker

A thin CORS-aware proxy that sits between the GitHub Pages frontend and NVIDIA's
chat completions API. It solves two problems at once:

1. **CORS** — NVIDIA's API doesn't set `Access-Control-Allow-Origin`, so browsers
   block direct requests. The Worker adds the header.
2. **Secret safety** — The NVIDIA API key is stored in Cloudflare's secret store
   and never reaches the browser.

```
Browser (GitHub Pages)
  │  POST /v1/chat/completions   (no Auth header)
  ▼
Cloudflare Worker  ←── NVIDIA_API_KEY (secret)
  │  POST https://integrate.api.nvidia.com/v1/chat/completions
  │  Authorization: Bearer <key>
  ▼
NVIDIA API
  │  SSE stream
  ▼
Cloudflare Worker  (adds CORS headers)
  │  SSE stream + Access-Control-Allow-Origin
  ▼
Browser
```

---

## Prerequisites

- [Cloudflare account](https://dash.cloudflare.com/sign-up) (free tier is fine)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/)
  ```bash
  npm install -g wrangler
  wrangler login
  ```

---

## Deploy the Worker

```bash
# From the repo root:
cd cloudflare-worker

# 1. Set the NVIDIA API key as a secret (never stored in wrangler.toml)
wrangler secret put NVIDIA_API_KEY
# Paste your nvapi-... key when prompted

# 2. (Optional) Pin the model
wrangler secret put NVIDIA_MODEL
# e.g. stepfun-ai/step-3.5-flash

# 3. (Optional) Restrict to your GitHub Pages domain
wrangler secret put ALLOWED_ORIGIN
# e.g. https://mouadja02.github.io

# 4. Deploy
wrangler deploy
```

After deploy, Wrangler prints the Worker URL:
```
https://skills-ai-proxy.<your-subdomain>.workers.dev
```

---

## Wire the Worker URL into GitHub Pages

1. Go to your repo → **Settings → Secrets and variables → Actions**.
2. Add a new secret:
   - **Name:** `PROXY_URL`
   - **Value:** `https://skills-ai-proxy.<your-subdomain>.workers.dev`
3. Remove the old `NVIDIA_API_KEY` secret from GitHub (it's no longer needed there).
4. Re-run the **Build & Deploy** workflow (or push any change) to regenerate
   `docs/chat-config.js` with the new proxy URL.

---

## Local testing

```bash
wrangler dev
# Worker runs on http://localhost:8787

# Test with curl:
curl -X POST http://localhost:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}],"stream":false}'
```

---

## Environment variables / secrets reference

| Name            | Required | Description                                                  |
|-----------------|----------|--------------------------------------------------------------|
| `NVIDIA_API_KEY`| Yes      | Your `nvapi-...` key from NVIDIA NGC                         |
| `NVIDIA_MODEL`  | No       | Model ID override (default: `stepfun-ai/step-3.5-flash`)     |
| `ALLOWED_ORIGIN`| No       | Restrict CORS to one or more origins, comma-separated (default: `*`) |

---

## Troubleshooting CORS errors

If the browser console shows:

> Response to preflight request doesn't pass access control check: It does not
> have HTTP ok status.

The Worker returned a non-2xx status (usually **403**) for the `OPTIONS`
preflight — almost always because `ALLOWED_ORIGIN` doesn't exactly match the
page's origin (protocol + host, no path, no trailing slash). Fix it with:

```bash
# Check what's currently set (shows names only, not values)
wrangler secret list

# Re-set it to the exact origin shown in the browser address bar
wrangler secret put ALLOWED_ORIGIN
# e.g. https://mouadja02.github.io   (no trailing slash)

# Or, to unblock quickly while debugging, delete the restriction entirely:
wrangler secret delete ALLOWED_ORIGIN

wrangler deploy
```

`wrangler tail` will log `Rejected origin "..." — does not match ALLOWED_ORIGIN.`
when a request is denied, which shows the exact origin the browser sent so you
can compare it against the secret value.

---

## Updating the Worker

```bash
cd cloudflare-worker
wrangler deploy          # re-deploy after editing worker.js
wrangler secret put ...  # rotate secrets anytime
```
