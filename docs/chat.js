/**
 * Skills AI Assistant — chat.js
 *
 * Integrates with NVIDIA's API (OpenAI-compatible) to help users discover,
 * install, and troubleshoot agent skills. Reads the local manifest.json for
 * a live skills index and streams responses token-by-token.
 *
 * Config (injected at build time via GitHub Actions into chat-config.js):
 *   window.CHAT_CFG = { apiKey: "nvapi-...", model: "stepfun-ai/step-3.5-flash" }
 */

(() => {
  "use strict";

  /* =====================================================================
     Config & constants
     ===================================================================== */

  const CFG = window.CHAT_CFG || {};
  const API_KEY   = CFG.apiKey || "";
  const API_MODEL = CFG.model  || "stepfun-ai/step-3.5-flash";
  const API_BASE  = "https://integrate.api.nvidia.com/v1";

  const MAX_HISTORY   = 20;   // kept messages in context
  const MAX_TOKENS    = 2048;
  const TEMPERATURE   = 0.65;

  // Suggested openers shown in empty state
  const STARTERS = [
    "Find me skills for building AI agents",
    "How do I install a skill in Cursor?",
    "What testing skills are available?",
    "Show me Azure / cloud skills",
    "I need help debugging a skill install",
    "What's in the engineering-craft category?",
  ];

  // Off-topic guard — topics we quickly reject without an API call
  const OFFTOPIC_PATTERNS = [
    /recipe|cook|food|meal|restaurant/i,
    /sport|football|soccer|basketball|nba|nfl/i,
    /weather|forecast|rain|temperature outside/i,
    /stock price|crypto|bitcoin|ethereum|invest/i,
    /movie|series|netflix|actor|actress|celebrity/i,
    /dating|relationship|love advice/i,
    /joke|funny|humor|meme/i,
    /politic|president|election|government/i,
    /religion|god|prayer|church/i,
    /write me a song|compose music/i,
  ];

  // Keywords that signal an on-topic message about skills / dev tools
  const ONTOPIC_KEYWORDS = [
    /skill|category|install|download|cursor|claude|agent|mcp|llm|ai|copilot/i,
    /devops|docker|terraform|azure|aws|gcp|cloud|linux/i,
    /engineer|developer|code|coding|debug|test|framework|backend|frontend/i,
    /python|javascript|typescript|java|kotlin|rust|go|ruby|swift|php/i,
    /react|vue|next|nuxt|spring|fastapi|django|flask/i,
    /database|sql|postgres|mongodb|snowflake|bigquery/i,
    /product|pm|agile|scrum|sprint|roadmap|prd/i,
    /marketing|seo|content|copywriting|gtm|growth/i,
    /design|ui|ux|figma|tailwind|css|banner|brand/i,
    /documentation|readme|diagram|slides|presentation/i,
    /business|strategy|cto|ceo|cfo|cmo|board|startup/i,
    /how|what|which|find|list|show|help|setup|configure/i,
  ];

  /* =====================================================================
     State
     ===================================================================== */

  let manifest   = null;   // loaded from manifest.json
  let systemPrompt = "";   // built after manifest loads
  let history    = [];     // { role, content }[]
  let streaming  = false;  // lock to prevent parallel requests
  let panelOpen  = false;

  /* =====================================================================
     DOM helpers
     ===================================================================== */

  const q  = (sel, ctx = document) => ctx.querySelector(sel);
  const qa = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

  /* =====================================================================
     Build system prompt from manifest
     ===================================================================== */

  function buildSystemPrompt(mf) {
    // Compact skills index: category > name: first 120 chars of description
    const byCategory = {};
    for (const sk of mf.skills) {
      if (!byCategory[sk.category]) byCategory[sk.category] = [];
      const snippet = (sk.description || "").slice(0, 120).replace(/\n/g, " ");
      byCategory[sk.category].push(`${sk.name}: ${snippet}`);
    }

    const index = Object.entries(byCategory)
      .map(([cat, items]) => `\n### ${cat} (${items.length} skills)\n` + items.join("\n"))
      .join("\n");

    const installSnippet = `\`\`\`bash
# Install one skill (bash)
curl -fsSL https://raw.githubusercontent.com/mouadja02/skills/main/install.sh \\
  | bash -s -- <category/skill-name> -d <destination>

# Install via PowerShell
$content = irm https://raw.githubusercontent.com/mouadja02/skills/main/install.ps1
iex $content
Install-Skill <category/skill-name> -Dest <destination>

# Install a whole category
bash install.sh engineering-craft -d ~/.claude/skills/

# Install with degit
npx degit mouadja02/skills/skills/<category/skill-name> <destination>
\`\`\``;

    return `You are **SkillBot**, an expert AI assistant for the Skills library — a curated collection of ${mf.count} installable agent skills for Claude Code and Cursor.

## Your mission
Help users:
1. **Discover** the right skills for their needs (search by task, language, category, keyword)
2. **Install** skills with the correct one-line commands (bash, PowerShell, degit, git sparse-checkout)
3. **Understand** what a skill does, when to use it, and how to configure it
4. **Debug** install failures, missing dependencies, or skill-not-triggering issues
5. **Compare** similar skills and recommend the best fit

## Install commands
${installSnippet}

Skill selector formats:
- Single skill: \`engineering-craft/test-driven-development\`
- Whole category: \`engineering-craft\`
- Glob pattern: \`"ai-agents/*"\` or \`"*mcp*"\`

Destinations:
- Claude Code project: \`.claude/skills/\`
- Cursor project: \`.cursor/skills/\`
- Cursor user-level: \`~/.cursor/skills/\`

## Skills index (${mf.count} skills across ${mf.categories.length} categories)
${index}

## Response style
- Be concise, helpful, and friendly
- When listing skills, show 3–8 relevant ones with a one-line description each
- Always include install commands when relevant — use the bash variant by default
- For debugging help, ask one clarifying question at a time
- Format code blocks correctly with the right language tag
- If the user wants more detail about a skill, give a fuller description + usage tips

## Scope constraint
You ONLY answer questions about:
- The skills in this library (finding, installing, using, debugging them)
- Claude Code and Cursor AI assistants
- Agent development, MCP (Model Context Protocol), AI agents
- Dev tools and workflows closely related to using skills

If asked about anything completely unrelated (recipes, sports, weather, politics, etc.), politely decline in one sentence and redirect to skills topics.`;
  }

  /* =====================================================================
     Preprocessing — off-topic guard
     ===================================================================== */

  function classifyMessage(text) {
    const t = text.trim().toLowerCase();

    // Very short messages are likely on-topic (hi, help, etc.)
    if (t.length < 15) return "ontopic";

    // Check obvious off-topic patterns
    for (const pat of OFFTOPIC_PATTERNS) {
      if (pat.test(t)) return "offtopic";
    }

    // Check on-topic keywords
    for (const pat of ONTOPIC_KEYWORDS) {
      if (pat.test(t)) return "ontopic";
    }

    // Ambiguous — let the LLM decide (system prompt will guard)
    return "ambiguous";
  }

  const OFFTOPIC_REPLY = "I'm focused on helping you find and use agent skills from this library. " +
    "Try asking something like: *\"Find me skills for React testing\"* or *\"How do I install a skill in Cursor?\"*";

  /* =====================================================================
     NVIDIA API — streaming fetch
     ===================================================================== */

  async function streamCompletion(messages, onToken, onDone, onError) {
    if (!API_KEY) {
      onError(new Error("API key not configured. See deployment instructions."));
      return;
    }

    let response;
    try {
      response = await fetch(`${API_BASE}/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${API_KEY}`,
        },
        body: JSON.stringify({
          model: API_MODEL,
          messages,
          temperature: TEMPERATURE,
          top_p: 0.9,
          max_tokens: MAX_TOKENS,
          stream: true,
        }),
      });
    } catch (err) {
      onError(err);
      return;
    }

    if (!response.ok) {
      const errText = await response.text().catch(() => response.statusText);
      onError(new Error(`API error ${response.status}: ${errText}`));
      return;
    }

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop(); // keep incomplete last line

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6).trim();
          if (data === "[DONE]") { onDone(); return; }

          try {
            const json = JSON.parse(data);
            const choices = json.choices;
            if (!choices?.length) continue;
            const delta = choices[0].delta;
            if (delta?.content) onToken(delta.content);
          } catch {
            // malformed chunk — skip
          }
        }
      }
    } catch (err) {
      onError(err);
      return;
    }

    onDone();
  }

  /* =====================================================================
     Markdown renderer (minimal, no deps)
     ===================================================================== */

  function renderMarkdown(text) {
    // Escape HTML first
    let out = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Code blocks  ```lang\n...\n```
    out = out.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
      const langLabel = lang ? `<span class="cb-lang">${escHtml(lang)}</span>` : "";
      return `<div class="cb-wrap">${langLabel}<button class="cb-copy" type="button" title="Copy">Copy</button><pre class="cb-pre"><code>${code.trimEnd()}</code></pre></div>`;
    });

    // Inline code `...`
    out = out.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Bold **...**
    out = out.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

    // Italic *...*  (but not ** already consumed)
    out = out.replace(/\*([^*\n]+?)\*/g, "<em>$1</em>");

    // Skill name references → clickable filter links
    if (manifest) {
      const nameSet = new Set(manifest.skills.map(s => s.name));
      out = out.replace(/`?([a-z][a-z0-9-]{2,}\/[a-z][a-z0-9-]{2,})`?/g, (match, path) => {
        const parts = path.split("/");
        const name  = parts[parts.length - 1];
        if (nameSet.has(name)) {
          return `<a class="skill-ref" href="#" data-skill="${escHtml(name)}">${escHtml(path)}</a>`;
        }
        return match;
      });
    }

    // ### Heading
    out = out.replace(/^### (.+)$/gm, "<h4>$1</h4>");
    // ## Heading
    out = out.replace(/^## (.+)$/gm, "<h3>$1</h3>");

    // Unordered list lines (- or *)
    out = out.replace(/^[*\-] (.+)$/gm, "<li>$1</li>");
    out = out.replace(/(<li>.*<\/li>(\n|$))+/g, "<ul>$&</ul>");

    // Numbered list
    out = out.replace(/^\d+\. (.+)$/gm, "<li>$1</li>");

    // Horizontal rule ---
    out = out.replace(/^---+$/gm, "<hr>");

    // Paragraphs — split on blank lines
    const parts = out.split(/\n{2,}/);
    out = parts.map(p => {
      const trimmed = p.trim();
      if (!trimmed) return "";
      // Don't wrap block-level elements
      if (/^<(h[1-6]|ul|ol|li|hr|div|pre|blockquote)/.test(trimmed)) return trimmed;
      return `<p>${trimmed.replace(/\n/g, "<br>")}</p>`;
    }).join("\n");

    return out;
  }

  function escHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /* =====================================================================
     UI — render a message bubble
     ===================================================================== */

  function appendMessage(role, content, streaming = false) {
    const messages = q("#chatMessages");
    const wrap = document.createElement("div");
    wrap.className = `chat-msg chat-msg--${role}`;
    if (streaming) wrap.dataset.streaming = "true";

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";

    if (role === "assistant") {
      const avatar = document.createElement("span");
      avatar.className = "chat-avatar";
      avatar.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 0-16 8 8 0 0 1 0 16zm-1-11h2v6h-2zm0-4h2v2h-2z"/></svg>`;
      wrap.appendChild(avatar);
    }

    const inner = document.createElement("div");
    inner.className = "chat-bubble-inner";
    bubble.appendChild(inner);
    wrap.appendChild(bubble);
    messages.appendChild(wrap);
    scrollToBottom();

    return { wrap, inner };
  }

  function setInnerContent(inner, text, isMarkdown = true) {
    inner.innerHTML = isMarkdown ? renderMarkdown(text) : escHtml(text);
    // Wire up code copy buttons
    qa(".cb-copy", inner).forEach(btn => {
      btn.addEventListener("click", () => {
        const code = btn.nextElementSibling?.textContent || "";
        navigator.clipboard.writeText(code).then(() => {
          btn.textContent = "Copied!";
          setTimeout(() => { btn.textContent = "Copy"; }, 1500);
        });
      });
    });
    // Wire up skill-ref links
    qa(".skill-ref", inner).forEach(link => {
      link.addEventListener("click", e => {
        e.preventDefault();
        const name = link.dataset.skill;
        filterToSkill(name);
        closePanel();
      });
    });
  }

  /* =====================================================================
     Typing indicator
     ===================================================================== */

  function showTyping() {
    const messages = q("#chatMessages");
    const el = document.createElement("div");
    el.className = "chat-msg chat-msg--assistant chat-typing";
    el.id = "chatTyping";
    el.innerHTML = `
      <span class="chat-avatar" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 0-16 8 8 0 0 1 0 16zm-1-11h2v6h-2zm0-4h2v2h-2z"/></svg>
      </span>
      <div class="chat-bubble"><div class="chat-bubble-inner">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div></div>`;
    messages.appendChild(el);
    scrollToBottom();
    return el;
  }

  function removeTyping() {
    q("#chatTyping")?.remove();
  }

  /* =====================================================================
     Auto-scroll
     ===================================================================== */

  function scrollToBottom() {
    const messages = q("#chatMessages");
    if (!messages) return;
    requestAnimationFrame(() => {
      messages.scrollTop = messages.scrollHeight;
    });
  }

  /* =====================================================================
     Filter the skills grid to a skill name
     ===================================================================== */

  function filterToSkill(name) {
    const searchInput = document.getElementById("search");
    if (!searchInput) return;
    searchInput.value = name;
    searchInput.dispatchEvent(new Event("input", { bubbles: true }));
    document.getElementById("browse")?.scrollIntoView({ behavior: "smooth" });
  }

  /* =====================================================================
     Send a message
     ===================================================================== */

  async function sendMessage(text) {
    if (streaming || !text.trim()) return;

    const userText = text.trim();
    hideStarters();

    // Render user bubble
    const { inner: userInner } = appendMessage("user", userText);
    setInnerContent(userInner, userText, false);

    // Guard: off-topic?
    const cls = classifyMessage(userText);
    if (cls === "offtopic") {
      const { inner } = appendMessage("assistant", "");
      setInnerContent(inner, OFFTOPIC_REPLY);
      return;
    }

    // Push to history
    history.push({ role: "user", content: userText });
    if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);

    // Show typing
    streaming = true;
    setSendDisabled(true);
    const typingEl = showTyping();

    // Build messages array for the API
    const messages = [
      { role: "system", content: systemPrompt },
      ...history,
    ];

    let fullResponse = "";
    let { inner: assistantInner, wrap: assistantWrap } = appendMessage("assistant", "", true);

    await streamCompletion(
      messages,
      // onToken
      (token) => {
        if (typingEl.isConnected) typingEl.remove();
        fullResponse += token;
        setInnerContent(assistantInner, fullResponse);
        scrollToBottom();
      },
      // onDone
      () => {
        if (typingEl.isConnected) typingEl.remove();
        if (!fullResponse) {
          setInnerContent(assistantInner, "_No response received._");
        }
        assistantWrap.removeAttribute("data-streaming");
        history.push({ role: "assistant", content: fullResponse });
        if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);
        streaming = false;
        setSendDisabled(false);
        scrollToBottom();
      },
      // onError
      (err) => {
        if (typingEl.isConnected) typingEl.remove();
        const msg = err.message || "Something went wrong.";
        setInnerContent(assistantInner, `⚠️ **Error:** ${escHtml(msg)}\n\nPlease try again.`);
        assistantWrap.removeAttribute("data-streaming");
        streaming = false;
        setSendDisabled(false);
        scrollToBottom();
      }
    );
  }

  /* =====================================================================
     UI helpers
     ===================================================================== */

  function setSendDisabled(disabled) {
    const btn = q("#chatSend");
    if (btn) btn.disabled = disabled;
  }

  function hideStarters() {
    q("#chatStarters")?.classList.add("hidden");
  }

  function openPanel() {
    panelOpen = true;
    const panel = q("#chatPanel");
    const overlay = q("#chatOverlay");
    panel?.classList.add("open");
    overlay?.classList.add("visible");
    q("#chatFab")?.setAttribute("aria-expanded", "true");
    q("#chatInput")?.focus();
  }

  function closePanel() {
    panelOpen = false;
    const panel = q("#chatPanel");
    const overlay = q("#chatOverlay");
    panel?.classList.remove("open");
    overlay?.classList.remove("visible");
    q("#chatFab")?.setAttribute("aria-expanded", "false");
  }

  /* =====================================================================
     Welcome message
     ===================================================================== */

  function showWelcome() {
    const { inner } = appendMessage("assistant", "");
    const count = manifest?.count ?? "504";
    const categories = manifest?.categories?.length ?? 13;
    setInnerContent(inner,
      `Hi! I'm **SkillBot** 👋\n\nI can help you explore **${count} agent skills** across **${categories} categories** for Claude Code and Cursor.\n\n` +
      `Ask me to find skills, explain install commands, or troubleshoot issues — I've got the full index in my context.`
    );
  }

  /* =====================================================================
     Starters
     ===================================================================== */

  function renderStarters() {
    const container = q("#chatStarters");
    if (!container) return;
    container.innerHTML = "";
    const shuffled = [...STARTERS].sort(() => Math.random() - 0.5).slice(0, 4);
    shuffled.forEach(text => {
      const btn = document.createElement("button");
      btn.className = "chat-starter";
      btn.type = "button";
      btn.textContent = text;
      btn.addEventListener("click", () => {
        q("#chatInput").value = text;
        sendMessage(text);
        q("#chatInput").value = "";
      });
      container.appendChild(btn);
    });
  }

  /* =====================================================================
     Init
     ===================================================================== */

  function initChat() {
    const fab     = q("#chatFab");
    const panel   = q("#chatPanel");
    const overlay = q("#chatOverlay");
    const input   = q("#chatInput");
    const sendBtn = q("#chatSend");
    const closeBtn = q("#chatClose");
    const clearBtn = q("#chatClear");

    if (!fab || !panel || !input) {
      console.warn("[chat] Required DOM elements missing.");
      return;
    }

    // Show error badge if no API key
    if (!API_KEY) {
      fab.classList.add("fab--no-key");
      fab.title = "AI assistant not configured (missing API key)";
    }

    // FAB click — open / close
    fab.addEventListener("click", () => {
      if (panelOpen) {
        closePanel();
      } else {
        openPanel();
        if (!q("#chatMessages .chat-msg")) {
          showWelcome();
          renderStarters();
        }
      }
    });

    // Overlay click — close
    overlay?.addEventListener("click", closePanel);

    // Close button
    closeBtn?.addEventListener("click", closePanel);

    // Clear conversation
    clearBtn?.addEventListener("click", () => {
      history = [];
      const messages = q("#chatMessages");
      if (messages) messages.innerHTML = "";
      showWelcome();
      renderStarters();
      q("#chatStarters")?.classList.remove("hidden");
    });

    // Send on Enter (Shift+Enter = newline)
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });

    // Auto-resize textarea
    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 140) + "px";
    });

    sendBtn?.addEventListener("click", handleSend);

    function handleSend() {
      const val = input.value.trim();
      if (!val || streaming) return;
      input.value = "";
      input.style.height = "auto";
      sendMessage(val);
    }

    // Keyboard shortcut: / focuses search, Escape closes panel
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && panelOpen) closePanel();
    });
  }

  /* =====================================================================
     Bootstrap — wait for manifest, then init
     ===================================================================== */

  async function bootstrap() {
    // Try to grab the already-loaded manifest from the main app's state,
    // or fetch it fresh.
    try {
      let mf = null;

      // Poll for window.skillsManifest (set by app.js) or fetch ourselves
      for (let i = 0; i < 20 && !mf; i++) {
        if (window.skillsManifest) {
          mf = window.skillsManifest;
        } else {
          await new Promise(r => setTimeout(r, 200));
        }
      }

      if (!mf) {
        const res = await fetch("./manifest.json");
        if (res.ok) mf = await res.json();
      }

      if (mf) {
        manifest = mf;
        systemPrompt = buildSystemPrompt(mf);
      }
    } catch (e) {
      console.warn("[chat] Could not load manifest:", e);
    }

    initChat();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrap);
  } else {
    bootstrap();
  }
})();
