/**
 * Skills AI Assistant — chat.js
 *
 * Integrates with NVIDIA's API (OpenAI-compatible) to help users discover,
 * install, and troubleshoot agent skills. Reads the local manifest.json for
 * a live skills index and streams responses token-by-token.
 *
 * Config (injected at build time via GitHub Actions into chat-config.js):
 *   window.CHAT_CFG = { proxyUrl: "https://skills-ai-proxy.<you>.workers.dev" }
 *
 * The NVIDIA API key lives exclusively in the Cloudflare Worker secret store.
 * The browser never sees or sends the key — the Worker adds it server-side.
 */

(() => {
  "use strict";

  /* =====================================================================
     Config & constants
     ===================================================================== */

  const CFG = window.CHAT_CFG || {};
  // The proxy URL points to the Cloudflare Worker that adds the NVIDIA API key.
  // Falls back to a placeholder so errors are descriptive rather than silent.
  const PROXY_URL = (CFG.proxyUrl || "").replace(/\/$/, "");
  const CHAT_COMPLETIONS_PATH = "/v1/chat/completions";

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
  | bash -s -- <category/skill-name> -d ${primaryDest}<skill-name>

# Install via PowerShell
$content = irm https://raw.githubusercontent.com/mouadja02/skills/main/install.ps1
iex $content
Install-Skill <category/skill-name> -Dest ${primaryDest}<skill-name>

# Install a whole category
bash install.sh engineering-craft -d ${primaryDest}

# Install with degit
npx degit mouadja02/skills/skills/<category/skill-name> ${primaryDest}<skill-name>
\`\`\``;

    const selectedHarnesses = window.skillsBrowser?.selectedHarnesses ?? ["claude-code"];
    const harnessNames = {
      "claude-code": "Claude Code", cursor: "Cursor", copilot: "GitHub Copilot",
      windsurf: "Windsurf", opencode: "OpenCode", codex: "Codex",
    };
    const harnessDests = {
      "claude-code": { project: ".claude/skills/", user: "~/.claude/skills/" },
      cursor:        { project: ".cursor/rules/",  user: "~/.cursor/rules/" },
      copilot:       { project: ".github/instructions/", user: "~/.copilot/skills/" },
      windsurf:      { project: ".windsurf/skills/", user: "~/.codeium/windsurf/skills/" },
      opencode:      { project: ".opencode/skills/", user: "~/.opencode/skills/" },
      codex:         { project: ".codex/skills/",  user: "~/.codex/skills/" },
    };
    const primaryHarness = selectedHarnesses[0] ?? "claude-code";
    const primaryDest = harnessDests[primaryHarness]?.user ?? "~/.claude/skills/";
    const selectedLabels = selectedHarnesses.map((id) => harnessNames[id] ?? id).join(", ");
    const destLines = selectedHarnesses
      .map((id) => `- ${harnessNames[id] ?? id}: \`${harnessDests[id]?.user ?? "~/.claude/skills/"}\``)
      .join("\n");

    return `You are **SkillBot**, an expert AI assistant for the Skills library — a curated collection of ${mf.count} installable agent skills for Claude Code, Cursor, GitHub Copilot, Windsurf, OpenCode, Codex, and more.

The user has selected the following tool(s): **${selectedLabels}**. Tailor install command destinations accordingly.

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

User's selected tool destination(s):
${destLines}

## Skills index (${mf.count} skills across ${mf.categories.length} categories)
${index}

## Response style
- Be concise, helpful, and friendly
- When listing skills, show 3–8 relevant ones with a one-line description each
- Mention skills with their exact selector, e.g. \`engineering-craft/refactor-code\`, so the UI can link them
- Always include install commands when relevant — use the bash variant by default
- For debugging help, ask one clarifying question at a time
- Format code blocks correctly with the right language tag
- If the user wants more detail about a skill, give a fuller description + usage tips

## Scope
Your expertise is this skills library and everything around it: finding the right skill, installing it, understanding what it does, debugging issues, comparing options, and general questions about Claude Code, Cursor, Copilot, Windsurf, OpenCode, Codex, AI agents, and MCP.

For questions clearly outside this scope (e.g. "what's the weather?", "write me a poem about cats") reply with one friendly sentence declining and suggest a skills-related follow-up instead.

When in doubt, assume the user is asking about something development or productivity related and try to connect it to a relevant skill.`;
  }

  /* =====================================================================
     NVIDIA API — streaming fetch
     ===================================================================== */

  function completionsEndpoint() {
    if (!PROXY_URL) return "";
    return PROXY_URL.endsWith(CHAT_COMPLETIONS_PATH)
      ? PROXY_URL
      : `${PROXY_URL}${CHAT_COMPLETIONS_PATH}`;
  }

  function looksLikeHtml(text) {
    return /<\/?(html|head|body|title|center|h1)\b/i.test(text);
  }

  function formatApiError(response, errText) {
    if (response.status === 405 && looksLikeHtml(errText)) {
      return "Chat proxy URL is misconfigured. PROXY_URL must point to your Cloudflare Worker, not the GitHub Pages site or NVIDIA API directly.";
    }

    if (looksLikeHtml(errText)) {
      return `Chat proxy returned an HTML error page (${response.status}). Check that PROXY_URL points to the deployed Cloudflare Worker.`;
    }

    return `API error ${response.status}: ${errText || response.statusText}`;
  }

  async function streamCompletion(messages, onToken, onDone, onError) {
    if (!PROXY_URL) {
      onError(new Error("Chat proxy is not configured. Set PROXY_URL in GitHub Secrets and redeploy."));
      return;
    }

    const endpoint = completionsEndpoint();
    let response;
    try {
      // No Authorization header here — the Cloudflare Worker adds the NVIDIA
      // API key server-side, so the key is never exposed in the browser.
      response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
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
      onError(new Error(formatApiError(response, errText)));
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
    const codeBlocks = [];
    const source = String(text || "")
      .replace(/\r\n/g, "\n")
      .replace(/```([\w-]*)\n?([\s\S]*?)```/g, (_, lang, code) => {
        const id = codeBlocks.length;
        codeBlocks.push(codeBlockHtml(lang, code));
        return `\n@@CODE_BLOCK_${id}@@\n`;
      });

    const lines = source.split("\n");
    const out = [];
    let paragraph = [];
    let listType = null;

    const flushParagraph = () => {
      if (!paragraph.length) return;
      out.push(`<p>${formatInline(paragraph.join(" "))}</p>`);
      paragraph = [];
    };

    const closeList = () => {
      if (!listType) return;
      out.push(`</${listType}>`);
      listType = null;
    };

    const openList = (type) => {
      if (listType === type) return;
      closeList();
      out.push(`<${type}>`);
      listType = type;
    };

    for (const rawLine of lines) {
      const line = rawLine.trimEnd();
      const trimmed = line.trim();
      const codeMatch = trimmed.match(/^@@CODE_BLOCK_(\d+)@@$/);

      if (!trimmed) {
        flushParagraph();
        closeList();
        continue;
      }

      if (codeMatch) {
        flushParagraph();
        closeList();
        out.push(codeBlocks[Number(codeMatch[1])] || "");
        continue;
      }

      if (/^---+$/.test(trimmed)) {
        flushParagraph();
        closeList();
        out.push("<hr>");
        continue;
      }

      const heading = trimmed.match(/^(#{2,4})\s+(.+)$/);
      if (heading) {
        flushParagraph();
        closeList();
        const tag = heading[1].length === 2 ? "h3" : "h4";
        out.push(`<${tag}>${formatInline(heading[2])}</${tag}>`);
        continue;
      }

      const unordered = trimmed.match(/^[-*]\s+(.+)$/);
      if (unordered) {
        flushParagraph();
        openList("ul");
        out.push(`<li>${formatInline(unordered[1])}</li>`);
        continue;
      }

      const ordered = trimmed.match(/^\d+\.\s+(.+)$/);
      if (ordered) {
        flushParagraph();
        openList("ol");
        out.push(`<li>${formatInline(ordered[1])}</li>`);
        continue;
      }

      closeList();
      paragraph.push(trimmed);
    }

    flushParagraph();
    closeList();
    return out.join("\n");
  }

  function codeBlockHtml(lang, code) {
    const langLabel = lang ? `<span class="cb-lang">${escHtml(lang)}</span>` : "";
    return `<div class="cb-wrap">${langLabel}<button class="cb-copy" type="button" title="Copy">Copy</button><pre class="cb-pre"><code>${escHtml(code.trimEnd())}</code></pre></div>`;
  }

  function formatInline(raw) {
    const inlineCode = [];
    let out = String(raw || "").replace(/`([^`]+)`/g, (_, code) => {
      const id = inlineCode.length;
      inlineCode.push(code);
      return `@@INLINE_CODE_${id}@@`;
    });

    out = escHtml(out);
    out = linkSkillRefs(out);
    out = out.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, (_, label, url) =>
      `<a href="${escAttr(url)}" target="_blank" rel="noopener">${label}</a>`
    );
    out = out.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    out = out.replace(/\*([^*\n]+?)\*/g, "<em>$1</em>");
    out = out.replace(/@@INLINE_CODE_(\d+)@@/g, (_, id) => inlineCodeHtml(inlineCode[Number(id)] || ""));

    return out;
  }

  function inlineCodeHtml(code) {
    const skill = findSkillRef(code.trim());
    if (skill) return skillAnchor(skill, code.trim());
    return `<code>${escHtml(code)}</code>`;
  }

  function linkSkillRefs(html) {
    if (!manifest?.skills?.length) return html;
    return html.replace(/(^|[^\w/="-])([a-z][a-z0-9-]*(?:\/[a-z][a-z0-9-]*)?)(?=$|[^\w/-])/gi, (match, prefix, ref) => {
      const skill = findSkillRef(ref);
      return skill ? `${prefix}${skillAnchor(skill, ref)}` : match;
    });
  }

  function findSkillRef(ref) {
    const needle = String(ref || "").toLowerCase().trim();
    if (!needle || !manifest?.skills?.length) return null;
    return manifest.skills.find(skill =>
      skill.name.toLowerCase() === needle ||
      skill.install_path.toLowerCase() === needle ||
      `${skill.category}/${skill.name}`.toLowerCase() === needle
    ) || null;
  }

  function skillAnchor(skill, label) {
    return `<a class="skill-ref" href="#skill=${encodeURIComponent(skill.install_path)}" data-skill="${escAttr(skill.name)}" data-skill-path="${escAttr(skill.install_path)}" title="Show ${escAttr(skill.name)} in the skills grid">${escHtml(label)}</a>`;
  }

  function escHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function escAttr(s) {
    return escHtml(s).replace(/"/g, "&quot;");
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
        openSkillReference(link.dataset.skillPath || link.dataset.skill);
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

  function openSkillReference(ref) {
    if (window.skillsBrowser?.focusSkill?.(ref)) return;
    filterToSkill(ref);
  }

  function filterToSkill(name) {
    const searchInput = document.getElementById("search");
    if (!searchInput) return;
    searchInput.value = name;
    searchInput.dispatchEvent(new Event("input", { bubbles: true }));
    document.getElementById("browse")?.scrollIntoView({ behavior: "smooth" });
  }

  function appendRecommendationActions(inner, text) {
    const skills = extractMentionedSkills(text);
    if (skills.length < 2 || inner.querySelector(".skill-actions")) return;

    const actions = document.createElement("div");
    actions.className = "skill-actions";

    const filterBtn = document.createElement("button");
    filterBtn.type = "button";
    filterBtn.className = "skill-actions-filter";
    filterBtn.textContent = `Show ${skills.length} recommended skills`;
    filterBtn.addEventListener("click", () => {
      if (window.skillsBrowser?.filterToSkills?.(skills.map(skill => skill.install_path))) {
        closePanel();
      }
    });

    actions.appendChild(filterBtn);
    inner.appendChild(actions);
  }

  function extractMentionedSkills(text) {
    if (!manifest?.skills?.length) return [];
    const haystack = String(text || "").toLowerCase();
    return manifest.skills
      .map(skill => {
        const refs = [skill.install_path, `${skill.category}/${skill.name}`, skill.name];
        const indexes = refs
          .map(ref => skillRefIndex(haystack, ref.toLowerCase()))
          .filter(index => index >= 0);
        return indexes.length ? { skill, index: Math.min(...indexes) } : null;
      })
      .filter(Boolean)
      .sort((a, b) => a.index - b.index)
      .slice(0, 8)
      .map(item => item.skill);
  }

  function skillRefIndex(haystack, ref) {
    if (ref.includes("/") || ref.includes("-")) return haystack.indexOf(ref);
    const match = haystack.match(new RegExp(`(^|[^a-z0-9/-])${escapeRegex(ref)}($|[^a-z0-9/-])`, "i"));
    return match ? match.index : -1;
  }

  function escapeRegex(s) {
    return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
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
    let assistantInner = null;
    let assistantWrap = null;

    const ensureAssistantMessage = () => {
      if (typingEl.isConnected) typingEl.remove();
      if (!assistantInner || !assistantWrap) {
        const msg = appendMessage("assistant", "", true);
        assistantInner = msg.inner;
        assistantWrap = msg.wrap;
      }
      return assistantInner;
    };

    await streamCompletion(
      messages,
      // onToken
      (token) => {
        fullResponse += token;
        setInnerContent(ensureAssistantMessage(), fullResponse);
        scrollToBottom();
      },
      // onDone
      () => {
        if (typingEl.isConnected) typingEl.remove();
        if (!fullResponse) {
          ensureAssistantMessage();
          setInnerContent(assistantInner, "_No response received._");
        } else {
          appendRecommendationActions(assistantInner, fullResponse);
        }
        assistantWrap?.removeAttribute("data-streaming");
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
        ensureAssistantMessage();
        setInnerContent(assistantInner, `**Error:** ${msg}\n\nPlease try again.`);
        assistantWrap?.removeAttribute("data-streaming");
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

    // Show error badge if proxy URL is not configured
    if (!PROXY_URL) {
      fab.classList.add("fab--no-key");
      fab.title = "AI assistant not configured (missing PROXY_URL)";
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
