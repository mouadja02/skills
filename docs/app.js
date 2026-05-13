// Lightweight, dependency-free browser for github.com/mouadja02/skills.
// Loads ./manifest.json, renders a searchable card grid, exposes per-skill
// install commands across bash, PowerShell, degit, and git sparse-checkout.

const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];

const SORT_KEY = "skills:sort";
const THEME_KEY = "skills:theme";
const HARNESS_KEY = "skills:harnesses";
const SKELETON_COUNT = 9;

const HARNESSES = [
  { id: "claude-code", label: "Claude Code",
    destBash: (n) => `~/.claude/skills/${n}`,      destPs: (n) => `$HOME\\.claude\\skills\\${n}` },
  { id: "cursor",      label: "Cursor",
    destBash: (n) => `~/.cursor/rules/${n}`,        destPs: (n) => `$HOME\\.cursor\\rules\\${n}` },
  { id: "copilot",     label: "Copilot",
    destBash: (n) => `./.github/instructions/${n}`, destPs: (n) => `.\\.github\\instructions\\${n}` },
  { id: "windsurf",    label: "Windsurf",
    destBash: (n) => `~/.codeium/windsurf/skills/${n}`, destPs: (n) => `$HOME\\.codeium\\windsurf\\skills\\${n}` },
  { id: "opencode",    label: "OpenCode",
    destBash: (n) => `~/.opencode/skills/${n}`,     destPs: (n) => `$HOME\\.opencode\\skills\\${n}` },
  { id: "codex",       label: "Codex",
    destBash: (n) => `~/.codex/skills/${n}`,        destPs: (n) => `$HOME\\.codex\\skills\\${n}` },
];

function loadStoredHarnesses() {
  try {
    const stored = JSON.parse(localStorage.getItem(HARNESS_KEY));
    if (Array.isArray(stored) && stored.length) return stored;
  } catch {}
  return ["claude-code"];
}

const state = {
  manifest: null,
  zips: null,
  filterText: "",
  filterCategory: null,
  recommendedSkillNames: null,
  sort: localStorage.getItem(SORT_KEY) || "name",
  catColor: new Map(),
  selectedHarnesses: loadStoredHarnesses(),
};

/* ==========================================================================
   Theme
   ========================================================================== */

function initTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
  const initial = stored || (prefersLight ? "light" : "dark");
  applyTheme(initial);

  $("#themeToggle")?.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    applyTheme(next);
    localStorage.setItem(THEME_KEY, next);
  });

  // Follow system if user hasn't picked manually.
  if (!stored) {
    window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", (e) => {
      if (!localStorage.getItem(THEME_KEY)) {
        applyTheme(e.matches ? "light" : "dark");
      }
    });
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const meta = $('meta[name="color-scheme"]');
  if (meta) meta.setAttribute("content", theme);
}

/* ==========================================================================
   Init
   ========================================================================== */

async function init() {
  initTheme();
  showSkeletons();

  try {
    const res = await fetch("./manifest.json", { cache: "no-cache" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.manifest = await res.json();
    // Expose manifest globally so chat.js can reuse it without a second fetch
    window.skillsManifest = state.manifest;
  } catch (err) {
    $("#grid").innerHTML = `<div class="empty">
      <div class="empty-icon">!</div>
      <p class="empty-title">Couldn't load the skill index</p>
      <p class="empty-desc">${escapeHtml(err.message)}</p>
    </div>`;
    return;
  }

  // ZIP summary is best-effort. If the deploy didn't generate zips (e.g. local
  // preview without `npm run build:zips`), the download buttons fall back to a
  // tarball helper instead.
  try {
    const res = await fetch("./zips/_summary.json", { cache: "no-cache" });
    if (res.ok) state.zips = await res.json();
  } catch {
    // intentionally ignored
  }

  // Fire-and-forget star count.
  fetchStarCount(state.manifest.repo);

  // Assign a stable color index per category (max 13 hues).
  state.manifest.categories.forEach((c, i) => {
    state.catColor.set(c, i % 13);
  });

  $("#skillCount").textContent = state.manifest.count.toLocaleString();
  $("#totalCount").textContent = state.manifest.count.toLocaleString();
  $("#statSkills").textContent = state.manifest.count.toLocaleString();
  $("#statCategories").textContent = state.manifest.categories.length.toLocaleString();

  $("#sortBy").value = state.sort;
  $("#sortBy").addEventListener("change", (e) => {
    state.sort = e.target.value;
    localStorage.setItem(SORT_KEY, state.sort);
    render();
  });

  renderCategories();
  renderHarnesses();
  bindHeroTabs();
  bindSearch();
  bindGlobalCopy();
  bindShareButton();
  bindSkillDetail();
  updateHeroCommands();

  $("#grid").setAttribute("aria-busy", "false");
  if (location.search) {
    applyUrlState();
  } else {
    render();
  }
}

/* ==========================================================================
   Skeletons & empty states
   ========================================================================== */

function showSkeletons() {
  const grid = $("#grid");
  const tmpl = $("#skeletonTemplate");
  if (!tmpl) return;
  const frag = document.createDocumentFragment();
  for (let i = 0; i < SKELETON_COUNT; i++) {
    frag.appendChild(tmpl.content.firstElementChild.cloneNode(true));
  }
  grid.innerHTML = "";
  grid.appendChild(frag);
}

function emptyStateHTML() {
  return `<div class="empty">
    <div class="empty-icon">
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>
      </svg>
    </div>
    <p class="empty-title">No skills match your filters</p>
    <p class="empty-desc">Try a different search term or clear the active category.</p>
    <button id="resetFilters" type="button">Reset filters</button>
  </div>`;
}

/* ==========================================================================
   Search
   ========================================================================== */

function bindSearch() {
  const input = $("#search");
  const clearBtn = $("#searchClear");

  input.addEventListener("input", (e) => {
    state.recommendedSkillNames = null;
    state.filterText = e.target.value.toLowerCase().trim();
    clearBtn.classList.toggle("hidden", !state.filterText);
    render();
  });

  clearBtn.addEventListener("click", () => {
    input.value = "";
    state.filterText = "";
    state.recommendedSkillNames = null;
    clearBtn.classList.add("hidden");
    input.focus();
    render();
  });

  // `/` to focus search; Esc to clear when focused.
  document.addEventListener("keydown", (e) => {
    const target = e.target;
    const isTyping = target instanceof HTMLElement &&
      (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);

    if (e.key === "/" && !isTyping) {
      e.preventDefault();
      input.focus();
      input.select();
    }
    if (e.key === "Escape" && document.activeElement === input) {
      if (input.value) {
        input.value = "";
        state.filterText = "";
        state.recommendedSkillNames = null;
        clearBtn.classList.add("hidden");
        render();
      } else {
        input.blur();
      }
    }
  });
}

/* ==========================================================================
   Categories
   ========================================================================== */

function renderCategories() {
  const container = $("#categories");
  const wrap = container.parentElement;
  const { categories, counts_by_category, count } = state.manifest;
  container.innerHTML = "";
  container.appendChild(mkCat("all", count, true, null));
  for (const c of categories) {
    container.appendChild(mkCat(c, counts_by_category[c], false, state.catColor.get(c)));
  }
  container.addEventListener("click", (e) => {
    const btn = e.target.closest(".cat");
    if (!btn) return;
    state.recommendedSkillNames = null;
    state.filterCategory = btn.dataset.cat === "all" ? null : btn.dataset.cat;
    $$(".cat", container).forEach((el) =>
      el.classList.toggle("active", el.dataset.cat === btn.dataset.cat)
    );
    renderCategoryBanner();
    updateMetaActive();
    render();
    // Keep clicked pill in view on mobile.
    btn.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
  });

  // Detect overflow to fade the right edge and indicate scrollability.
  const checkOverflow = () => {
    const overflowing = container.scrollWidth > container.clientWidth + 2;
    const atEnd = container.scrollLeft + container.clientWidth >= container.scrollWidth - 4;
    wrap.classList.toggle("has-overflow", overflowing && !atEnd);
  };
  checkOverflow();
  container.addEventListener("scroll", checkOverflow, { passive: true });
  window.addEventListener("resize", checkOverflow);

  renderCategoryBanner();
}

function mkCat(name, count, active = false, colorIdx = null) {
  const btn = document.createElement("button");
  btn.className = "cat" + (active ? " active" : "");
  btn.dataset.cat = name;
  btn.type = "button";
  btn.setAttribute("role", "tab");
  btn.setAttribute("aria-selected", active ? "true" : "false");
  if (colorIdx !== null) btn.dataset.catColor = colorIdx;
  const dot = colorIdx !== null
    ? `<span class="cat-dot" aria-hidden="true"></span>`
    : "";
  const display = name === "all" ? "All" : name.replace(/-/g, " ");
  btn.innerHTML = `${dot}<span class="cat-name">${escapeHtml(display)}</span><span class="cnt">${count}</span>`;
  return btn;
}

function updateMetaActive() {
  const el = $("#metaActive");
  if (!el) return;
  if (state.filterCategory) {
    el.classList.remove("hidden");
    el.innerHTML = `· ${escapeHtml(state.filterCategory.replace(/-/g, " "))}
      <button type="button" aria-label="Clear category filter">×</button>`;
    $("button", el).addEventListener("click", () => {
      state.filterCategory = null;
      state.recommendedSkillNames = null;
      $$("#categories .cat").forEach((c) =>
        c.classList.toggle("active", c.dataset.cat === "all")
      );
      renderCategoryBanner();
      updateMetaActive();
      render();
    });
  } else {
    el.classList.add("hidden");
    el.innerHTML = "";
  }
}

function renderCategoryBanner() {
  const banner = $("#categoryBanner");
  const cat = state.filterCategory;
  if (!cat) {
    banner.classList.add("hidden");
    return;
  }
  const { repo, default_branch, counts_by_category } = state.manifest;
  const count = counts_by_category[cat] ?? 0;
  $("#catBannerName").textContent = cat;
  $("#catBannerCount").textContent = count.toLocaleString();

  const raw = `https://raw.githubusercontent.com/${repo}/${default_branch}`;
  const harnesses = activeHarnesses();
  const variants = {
    bash: harnesses.map((h) => `curl -fsSL ${raw}/install.sh \\\n  | bash -s -- ${cat} -d ${h.destBash(cat)}`).join("\n"),
    ps: harnesses.map((h) => `$content = irm ${raw}/install.ps1\niex $content\nInstall-Skill ${cat} -Dest ${h.destPs(cat)}`).join("\n"),
    degit: harnesses.map((h) => `npx degit ${repo}/skills/${cat} ${h.destBash(cat)}`).join("\n"),
  };
  $$(".category-banner-code", banner).forEach((pre) => {
    $("code", pre).textContent = variants[pre.dataset.variant];
  });

  const dlLink = $("#catBannerDownload");
  const dlSize = $("#catBannerDownloadSize");
  const catZip = state.zips?.categories?.[cat];
  if (catZip) {
    dlLink.href = zipHref(catZip);
    dlLink.setAttribute("download", `${cat}.zip`);
    dlSize.textContent = `· ${formatBytes(catZip.bytes)}`;
    dlLink.classList.remove("hidden");
  } else {
    dlLink.classList.add("hidden");
  }

  bindTabs(banner, ".category-banner-tabs .tab", ".category-banner-code");
  bindCopy(banner);
  banner.classList.remove("hidden");
}

/* ==========================================================================
   Tabs / copy helpers
   ========================================================================== */

function bindTabs(scope, tabSel, paneSel) {
  const tabs = $$(tabSel, scope);
  const panes = $$(paneSel, scope);
  tabs.forEach((tab) => {
    if (tab._wired) return;
    tab._wired = true;
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.toggle("active", t === tab));
      panes.forEach((p) =>
        p.classList.toggle("hidden", p.dataset.variant !== tab.dataset.tab)
      );
    });
  });
}

function bindCopy(scope) {
  $$(".copy", scope).forEach((btn) => {
    if (btn._wired) return;
    btn._wired = true;
    btn.addEventListener("click", async () => {
      const target = btn.dataset.copyTarget
        ? document.querySelector(btn.dataset.copyTarget)
        : $("code", btn.parentElement);
      const code = target?.textContent ?? "";
      const orig = btn.textContent;
      try {
        await navigator.clipboard.writeText(code);
        btn.classList.add("copied");
        btn.textContent = "Copied";
        setTimeout(() => {
          btn.classList.remove("copied");
          btn.textContent = orig;
        }, 1400);
      } catch {
        btn.textContent = "Press Ctrl+C";
        setTimeout(() => (btn.textContent = orig), 1400);
      }
    });
  });
}

function bindGlobalCopy() {
  // Hero copy buttons rely on data-copy-target, so we wire them once.
  bindCopy(document.querySelector(".hero"));
}

function bindHeroTabs() {
  const tabs = $$(".hero .install-tabs .tab");
  const codes = {
    bash: $("#bashHero"),
    ps: $("#psHero"),
  };
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.toggle("active", t === tab));
      Object.entries(codes).forEach(([key, el]) =>
        el.classList.toggle("hidden", key !== tab.dataset.tab)
      );
    });
  });
}

/* ==========================================================================
   Render
   ========================================================================== */

function render() {
  const { skills, repo, default_branch } = state.manifest;
  let filtered = skills.filter((s) => {
    if (state.recommendedSkillNames?.length && !state.recommendedSkillNames.includes(s.name)) {
      return false;
    }
    if (state.filterCategory && s.category !== state.filterCategory) return false;
    if (!state.filterText) return true;
    const hay = `${s.name} ${s.install_path} ${s.description}`.toLowerCase();
    return hay.includes(state.filterText);
  });

  filtered = state.recommendedSkillNames?.length
    ? sortRecommendedSkills(filtered)
    : sortSkills(filtered, state.sort);

  $("#visibleCount").textContent = filtered.length.toLocaleString();
  updateMetaActive();

  const grid = $("#grid");
  grid.innerHTML = "";

  if (!filtered.length) {
    grid.innerHTML = emptyStateHTML();
    $("#resetFilters")?.addEventListener("click", () => {
      $("#search").value = "";
      $("#searchClear").classList.add("hidden");
      state.filterText = "";
      state.recommendedSkillNames = null;
      state.filterCategory = null;
      $$("#categories .cat").forEach((c) =>
        c.classList.toggle("active", c.dataset.cat === "all")
      );
      renderCategoryBanner();
      render();
    });
    updateUrl();
    updatePageTitle();
    return;
  }

  const tmpl = $("#cardTemplate");
  const frag = document.createDocumentFragment();
  filtered.forEach((skill, i) => {
    const card = renderCard(skill, tmpl, repo, default_branch);
    // Stagger entrance for the first few cards only — feels smooth, not slow.
    if (i < 12) card.style.animationDelay = `${i * 30}ms`;
    frag.appendChild(card);
  });
  grid.appendChild(frag);
  updateUrl();
  updatePageTitle();
}

function sortSkills(skills, mode) {
  const arr = [...skills];
  switch (mode) {
    case "name-desc":
      arr.sort((a, b) => b.name.localeCompare(a.name));
      break;
    case "category":
      arr.sort((a, b) =>
        a.category.localeCompare(b.category) || a.name.localeCompare(b.name)
      );
      break;
    case "name":
    default:
      arr.sort((a, b) => a.name.localeCompare(b.name));
  }
  return arr;
}

function sortRecommendedSkills(skills) {
  const order = new Map(state.recommendedSkillNames.map((name, index) => [name, index]));
  return [...skills].sort((a, b) => (order.get(a.name) ?? 999) - (order.get(b.name) ?? 999));
}

function renderCard(skill, tmpl, repo, branch) {
  const node = tmpl.content.firstElementChild.cloneNode(true);
  node.id = `skill-${slugify(skill.install_path)}`;
  node.dataset.skillName = skill.name;
  node.dataset.skillPath = skill.install_path;
  $(".card-name", node).textContent = skill.name;

  const colorIdx = state.catColor.get(skill.category) ?? 0;
  node.dataset.catColor = colorIdx;

  const cat = $(".card-category", node);
  $(".card-category-name", cat).textContent = skill.category.replace(/-/g, " ");
  cat.href = `#cat=${encodeURIComponent(skill.category)}`;
  cat.setAttribute("aria-label", `Filter by category ${skill.category}`);
  cat.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    const btn = $(`.cat[data-cat="${cssEscape(skill.category)}"]`);
    if (btn) btn.click();
    document.querySelector("#browse")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  $(".card-desc", node).textContent = skill.description;

  const variants = installCommands(skill, repo, branch);
  for (const [variant, code] of Object.entries(variants)) {
    const pre = $(`pre[data-variant="${variant}"]`, node);
    if (pre) $("code", pre).textContent = code;
  }

  const tabs = $$(".install-tabs .tab", node);
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.toggle("active", t === tab));
      $$(".card-install pre", node).forEach((pre) =>
        pre.classList.toggle("hidden", pre.dataset.variant !== tab.dataset.tab)
      );
    });
  });

  $$(".copy", node).forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const code = $("code", btn.parentElement).textContent;
      const orig = btn.textContent;
      try {
        await navigator.clipboard.writeText(code);
        btn.classList.add("copied");
        btn.textContent = "Copied";
        setTimeout(() => {
          btn.classList.remove("copied");
          btn.textContent = orig;
        }, 1400);
      } catch {
        btn.textContent = "Press Ctrl+C";
        setTimeout(() => (btn.textContent = orig), 1400);
      }
    });
  });

  // Quick-copy CTA: copies the bash variant directly.
  const quick = $(".card-quick-copy", node);
  const quickLabel = $(".card-quick-copy-label", quick);
  quick.addEventListener("click", async (e) => {
    e.stopPropagation();
    const orig = quickLabel.textContent;
    try {
      await navigator.clipboard.writeText(variants.bash);
      quick.classList.add("copied");
      quickLabel.textContent = "Copied!";
      setTimeout(() => {
        quick.classList.remove("copied");
        quickLabel.textContent = orig;
      }, 1400);
    } catch {
      quickLabel.textContent = "Press Ctrl+C";
      setTimeout(() => (quickLabel.textContent = orig), 1400);
    }
  });

  // Open the card on Enter / Space when the article itself is focused.
  node.addEventListener("keydown", (e) => {
    if (e.target !== node) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      const details = $(".card-install", node);
      details.open = !details.open;
    }
  });

  const src = $(".card-source", node);
  src.href = `https://github.com/${repo}/blob/${branch}/${skill.path}/SKILL.md`;
  src.setAttribute("aria-label", `View SKILL.md for ${skill.name} on GitHub`);

  $(".card-share", node)?.addEventListener("click", (e) => {
    e.stopPropagation();
    copyShareUrl(getSkillShareUrl(skill));
  });

  $(".card-read", node)?.addEventListener("click", (e) => {
    e.stopPropagation();
    openSkillDetail(skill);
  });

  const dl = $(".card-download", node);
  const dlSize = $(".card-download-size", node);
  const zip = state.zips?.skills?.[skill.install_path];
  if (zip) {
    dl.href = zipHref(zip);
    dl.setAttribute("download", `${skill.name}.zip`);
    dlSize.textContent = `· ${formatBytes(zip.bytes)}`;
  } else {
    dl.href = `https://download-directory.github.io/?url=${encodeURIComponent(
      `https://github.com/${repo}/tree/${branch}/${skill.path}`
    )}`;
    dl.removeAttribute("download");
    dl.target = "_blank";
    dl.rel = "noopener";
    dlSize.textContent = "";
    dl.title = "Download via download-directory.github.io";
  }

  return node;
}

/* ==========================================================================
   Helpers
   ========================================================================== */

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

function zipHref(zip) {
  if (zip.public_url) return zip.public_url.trim();
  if (/^https?:\/\//.test(zip.url)) return zip.url.trim();
  return `./${zip.url}`;
}

function getPrimaryHarness() {
  return HARNESSES.find((h) => h.id === state.selectedHarnesses[0]) ?? HARNESSES[0];
}

function activeHarnesses() {
  return state.selectedHarnesses
    .map((id) => HARNESSES.find((h) => h.id === id))
    .filter(Boolean);
}

function installCommands(skill, repo, branch) {
  const { install_path: ip, name } = skill;
  const raw = `https://raw.githubusercontent.com/${repo}/${branch}`;
  const harnesses = activeHarnesses();

  const bash = harnesses
    .map((h) => `curl -fsSL ${raw}/install.sh \\\n  | bash -s -- ${ip} -d ${h.destBash(name)}`)
    .join("\n");
  const ps = harnesses
    .map((h) => `$content = irm ${raw}/install.ps1\niex $content\nInstall-Skill -Skill ${ip} -Dest ${h.destPs(name)}`)
    .join("\n");
  const degit = harnesses
    .map((h) => `npx degit ${repo}/skills/${ip} ${h.destBash(name)}`)
    .join("\n");
  const sparse = harnesses
    .map((h) =>
      `git clone --no-checkout --depth 1 --filter=blob:none \\\n` +
      `  https://github.com/${repo}.git skills-tmp && cd skills-tmp \\\n` +
      `  && git sparse-checkout init --cone \\\n` +
      `  && git sparse-checkout set skills/${ip} \\\n` +
      `  && git checkout && mv skills/${ip} ${h.destBash(name)} && cd .. && rm -rf skills-tmp`
    )
    .join("\n");

  return { bash, ps, degit, sparse };
}

async function fetchStarCount(repo) {
  const el = $("#repoStars");
  if (!el || !repo) return;
  try {
    const res = await fetch(`https://api.github.com/repos/${repo}`, { cache: "force-cache" });
    if (!res.ok) return;
    const data = await res.json();
    const stars = data.stargazers_count;
    if (typeof stars !== "number") return;
    el.textContent = formatStars(stars);
    el.style.cssText = "display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:999px;background:var(--bg-elev-2);color:var(--text-faint);font-size:11.5px;font-weight:600;font-variant-numeric:tabular-nums;";
    el.innerHTML = `<svg viewBox="0 0 16 16" width="11" height="11" fill="currentColor" aria-hidden="true"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/></svg>${formatStars(stars)}`;
  } catch {
    // intentionally ignored — non-critical
  }
}

function formatStars(n) {
  if (n < 1000) return String(n);
  return `${(n / 1000).toFixed(1)}k`;
}

function findSkill(ref) {
  const needle = String(ref || "").trim().toLowerCase();
  if (!needle || !state.manifest?.skills) return null;
  return state.manifest.skills.find((skill) =>
    skill.name.toLowerCase() === needle ||
    skill.install_path.toLowerCase() === needle ||
    `${skill.category}/${skill.name}`.toLowerCase() === needle
  ) || null;
}

function setAllCategoryActive() {
  state.filterCategory = null;
  $$("#categories .cat").forEach((c) =>
    c.classList.toggle("active", c.dataset.cat === "all")
  );
  renderCategoryBanner();
  updateMetaActive();
}

function highlightSkillCard(skillName) {
  requestAnimationFrame(() => {
    const card = $(`.card[data-skill-name="${cssEscape(skillName)}"]`);
    if (!card) return;
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    card.classList.add("card--spotlight");
    setTimeout(() => card.classList.remove("card--spotlight"), 2200);
  });
}

function focusSkill(ref) {
  const skill = findSkill(ref);
  if (!skill) return false;
  const input = $("#search");
  const clearBtn = $("#searchClear");

  state.recommendedSkillNames = null;
  state.filterText = skill.name.toLowerCase();
  if (input) input.value = skill.name;
  clearBtn?.classList.remove("hidden");
  setAllCategoryActive();
  render();
  highlightSkillCard(skill.name);
  return true;
}

function filterToSkills(refs) {
  const unique = [];
  const seen = new Set();
  for (const ref of refs || []) {
    const skill = findSkill(ref);
    if (!skill || seen.has(skill.name)) continue;
    seen.add(skill.name);
    unique.push(skill);
  }
  if (!unique.length) return false;

  state.recommendedSkillNames = unique.map((skill) => skill.name);
  state.filterText = "";
  const input = $("#search");
  const clearBtn = $("#searchClear");
  if (input) input.value = "";
  clearBtn?.classList.add("hidden");
  setAllCategoryActive();
  render();
  document.querySelector("#browse")?.scrollIntoView({ behavior: "smooth", block: "start" });
  return true;
}

window.skillsBrowser = {
  focusSkill,
  filterToSkills,
  selectedHarnesses: [...state.selectedHarnesses],
};

/* ==========================================================================
   Harness / Tool Selector
   ========================================================================== */

function renderHarnesses() {
  const bar = document.getElementById("harnessBar");
  if (!bar) return;
  bar.innerHTML = HARNESSES.map((h) =>
    `<button class="harness${state.selectedHarnesses.includes(h.id) ? " active" : ""}"
             type="button" data-harness-id="${h.id}"
             aria-pressed="${state.selectedHarnesses.includes(h.id) ? "true" : "false"}">${escapeHtml(h.label)}</button>`
  ).join("");
  bar.addEventListener("click", (e) => {
    const btn = e.target.closest(".harness");
    if (!btn) return;
    const id = btn.dataset.harnessId;
    const idx = state.selectedHarnesses.indexOf(id);
    if (idx === -1) {
      state.selectedHarnesses.push(id);
    } else if (state.selectedHarnesses.length > 1) {
      state.selectedHarnesses.splice(idx, 1);
    }
    localStorage.setItem(HARNESS_KEY, JSON.stringify(state.selectedHarnesses));
    $$(".harness", bar).forEach((b) => {
      const active = state.selectedHarnesses.includes(b.dataset.harnessId);
      b.classList.toggle("active", active);
      b.setAttribute("aria-pressed", active ? "true" : "false");
    });
    onHarnessChange();
  });
}

function onHarnessChange() {
  render();
  renderCategoryBanner();
  updateHeroCommands();
  window.skillsBrowser.selectedHarnesses = [...state.selectedHarnesses];
}

function updateHeroCommands() {
  if (!state.manifest) return;
  const { repo, default_branch } = state.manifest;
  const raw = `https://raw.githubusercontent.com/${repo}/${default_branch}`;
  const primary = getPrimaryHarness();
  const bashEl = document.querySelector("#bashHero code");
  const psEl = document.querySelector("#psHero code");
  if (bashEl) {
    bashEl.textContent =
      `curl -fsSL ${raw}/install.sh \\\n  | bash -s -- <selector> -d ${primary.destBash("<name>")}`;
  }
  if (psEl) {
    psEl.textContent =
      `$content = irm ${raw}/install.ps1\niex $content\nInstall-Skill <selector> -Dest ${primary.destPs("<name>")}`;
  }
}

/* ==========================================================================
   URL State — share by link
   ========================================================================== */

function updateUrl() {
  const params = new URLSearchParams();
  if (state.filterCategory) params.set("cat", state.filterCategory);
  if (state.filterText) params.set("q", state.filterText);
  if (state.recommendedSkillNames?.length) {
    const paths = state.recommendedSkillNames.map((name) => {
      const s = state.manifest?.skills.find((sk) => sk.name === name);
      return s?.install_path ?? name;
    });
    params.set("skills", paths.join(","));
  }
  const qs = params.toString();
  const newUrl = qs ? `${location.pathname}?${qs}` : location.pathname;
  history.replaceState(null, "", newUrl);

  const shareBtn = document.getElementById("shareBtn");
  if (shareBtn) shareBtn.classList.toggle("hidden", !qs);
}

function applyUrlState() {
  const params = new URLSearchParams(location.search);
  const catParam = params.get("cat");
  const qParam = params.get("q");
  const skillParam = params.get("skill");
  const skillsParam = params.get("skills");

  if (catParam && state.manifest.categories.includes(catParam)) {
    state.filterCategory = catParam;
    $$("#categories .cat").forEach((c) =>
      c.classList.toggle("active", c.dataset.cat === catParam)
    );
    renderCategoryBanner();
    updateMetaActive();
  }

  if (skillsParam) {
    const paths = skillsParam.split(",").map((s) => s.trim()).filter(Boolean);
    filterToSkills(paths);
    return;
  }

  if (skillParam) {
    const skill = findSkill(skillParam);
    if (skill) {
      state.filterText = skill.name.toLowerCase();
      const input = $("#search");
      if (input) input.value = skill.name;
      $("#searchClear")?.classList.remove("hidden");
    }
  } else if (qParam) {
    state.filterText = qParam.toLowerCase();
    const input = $("#search");
    if (input) input.value = qParam;
    if (qParam) $("#searchClear")?.classList.remove("hidden");
  }

  render();

  if (skillParam) {
    const skill = findSkill(skillParam);
    if (skill) {
      setTimeout(() => {
        document.querySelector("#browse")?.scrollIntoView({ behavior: "smooth", block: "start" });
        highlightSkillCard(skill.name);
      }, 150);
    }
  }
}

/* ==========================================================================
   Share helpers
   ========================================================================== */

function showToast(msg) {
  let toast = document.getElementById("shareToast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "shareToast";
    toast.className = "share-toast";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("visible");
  clearTimeout(toast._toastTimer);
  toast._toastTimer = setTimeout(() => toast.classList.remove("visible"), 2200);
}

async function copyShareUrl(url) {
  try {
    await navigator.clipboard.writeText(url);
    showToast("Link copied!");
  } catch {
    showToast("Press Ctrl+C to copy");
  }
}

function getSkillShareUrl(skill) {
  return `${location.origin}${location.pathname}?skill=${encodeURIComponent(skill.install_path)}`;
}

function bindShareButton() {
  const btn = document.getElementById("shareBtn");
  if (!btn) return;
  btn.addEventListener("click", () => copyShareUrl(location.href));
}

/* ==========================================================================
   Page title
   ========================================================================== */

function updatePageTitle() {
  let title = "Skills — Agent Skills for Claude Code, Cursor, Copilot & More";
  if (state.filterCategory) {
    title = `${state.filterCategory.replace(/-/g, " ")} — Skills`;
  } else if (state.filterText) {
    title = `"${state.filterText}" — Skills`;
  } else if (state.recommendedSkillNames?.length) {
    title = `${state.recommendedSkillNames.length} recommended skills — Skills`;
  }
  document.title = title;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function cssEscape(s) {
  return String(s).replace(/[^a-zA-Z0-9_-]/g, (c) => `\\${c}`);
}

function slugify(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

/* ==========================================================================
   Skill Detail Panel
   ========================================================================== */

const sdCache = new Map();

function openSkillDetail(skill) {
  const panel = document.getElementById("skillDetail");
  if (!panel) return;

  const { repo, default_branch } = state.manifest;

  // Populate header
  const nameEl = panel.querySelector(".sd-name");
  const catEl = panel.querySelector(".sd-cat-badge");
  const ghLink = panel.querySelector(".sd-gh-link");
  if (nameEl) nameEl.textContent = skill.name;
  if (catEl) {
    catEl.textContent = skill.category.replace(/-/g, " ");
    catEl.dataset.catColor = state.catColor.get(skill.category) ?? 0;
  }
  if (ghLink) ghLink.href = `https://github.com/${repo}/blob/${default_branch}/${skill.path}/SKILL.md`;

  // Reset content areas
  const contentEl = panel.querySelector(".sd-content");
  const filesEl = panel.querySelector(".sd-files");
  if (contentEl) contentEl.innerHTML = sdLoadingHtml();
  if (filesEl) filesEl.innerHTML = "";

  // Show
  panel.setAttribute("aria-hidden", "false");
  panel.classList.add("open");
  document.getElementById("skillDetailOverlay")?.classList.add("visible");
  document.body.classList.add("sd-open");
  panel.focus();

  fetchSkillDetail(skill, repo, default_branch);
}

function closeSkillDetail() {
  const panel = document.getElementById("skillDetail");
  if (!panel) return;
  panel.setAttribute("aria-hidden", "true");
  panel.classList.remove("open");
  document.getElementById("skillDetailOverlay")?.classList.remove("visible");
  document.body.classList.remove("sd-open");
}

function bindSkillDetail() {
  document.getElementById("skillDetailClose")?.addEventListener("click", closeSkillDetail);
  document.getElementById("skillDetailOverlay")?.addEventListener("click", closeSkillDetail);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && document.getElementById("skillDetail")?.classList.contains("open")) {
      closeSkillDetail();
    }
  });
}

async function fetchSkillDetail(skill, repo, branch) {
  const panel = document.getElementById("skillDetail");
  const contentEl = panel?.querySelector(".sd-content");
  const filesEl = panel?.querySelector(".sd-files");
  if (!contentEl) return;

  const key = skill.install_path;
  if (sdCache.has(key)) {
    const { markdown, files } = sdCache.get(key);
    contentEl.innerHTML = sdMdToHtml(markdown);
    bindSdCopy(contentEl);
    renderSdFiles(filesEl, files, repo, branch);
    return;
  }

  const rawUrl = `https://raw.githubusercontent.com/${repo}/${branch}/${skill.path}/SKILL.md`;
  try {
    const res = await fetch(rawUrl);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const markdown = await res.text();
    contentEl.innerHTML = sdMdToHtml(markdown);
    bindSdCopy(contentEl);

    // Folder listing — best-effort via GitHub API
    let files = [];
    try {
      const ar = await fetch(`https://api.github.com/repos/${repo}/contents/${skill.path}`);
      if (ar.ok) {
        const all = await ar.json();
        files = Array.isArray(all) ? all.filter((f) => f.name !== "SKILL.md") : [];
      }
    } catch { /* optional */ }

    sdCache.set(key, { markdown, files });
    renderSdFiles(filesEl, files, repo, branch);
  } catch (err) {
    contentEl.innerHTML = `<div class="sd-error">
      <p>Could not load skill content.</p>
      <small>${escapeHtml(err.message)}</small>
    </div>`;
  }
}

function sdLoadingHtml() {
  return `<div class="sd-loading" aria-label="Loading">
    <span class="sd-dot"></span><span class="sd-dot"></span><span class="sd-dot"></span>
  </div>`;
}

/* ---------- File tree ---------- */

function renderSdFiles(el, files, repo, branch) {
  if (!el || !files.length) return;
  el.innerHTML = `<div class="sd-files-hd">
    <svg viewBox="0 0 16 16" width="14" height="14" fill="currentColor" aria-hidden="true">
      <path d="M1.75 1A1.75 1.75 0 0 0 0 2.75v10.5C0 14.216.784 15 1.75 15h12.5A1.75 1.75 0 0 0 16 13.25v-8.5A1.75 1.75 0 0 0 14.25 3H7.5a.25.25 0 0 1-.2-.1l-.9-1.2C6.07 1.26 5.55 1 5 1H1.75Z"/>
    </svg>
    <span>Additional files</span>
  </div>
  <ul class="sd-tree">${files.map(sdFileItemHtml).join("")}</ul>`;
  bindSdTree(el, repo, branch);
}

function sdFileItemHtml(f) {
  if (f.type === "dir") {
    return `<li class="sd-ti sd-ti--dir" data-path="${escapeHtml(f.path)}">
      <button class="sd-ti-btn" type="button">
        <svg class="sd-ti-icon" viewBox="0 0 16 16" width="14" height="14" fill="currentColor" aria-hidden="true">
          <path d="M1.75 1A1.75 1.75 0 0 0 0 2.75v10.5C0 14.216.784 15 1.75 15h12.5A1.75 1.75 0 0 0 16 13.25v-8.5A1.75 1.75 0 0 0 14.25 3H7.5a.25.25 0 0 1-.2-.1l-.9-1.2C6.07 1.26 5.55 1 5 1H1.75Z"/>
        </svg>
        <span class="sd-ti-name">${escapeHtml(f.name)}/</span>
        <svg class="sd-ti-caret" viewBox="0 0 16 16" width="11" height="11" fill="currentColor" aria-hidden="true">
          <path d="M6.22 3.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L9.94 8 6.22 4.28a.75.75 0 0 1 0-1.06Z"/>
        </svg>
      </button>
      <ul class="sd-tree sd-tree--sub hidden"></ul>
    </li>`;
  }
  const isMd = /\.(md|mdx|txt)$/i.test(f.name);
  return `<li class="sd-ti sd-ti--file">
    <button class="sd-ti-btn" type="button"
            data-raw="${escapeHtml(f.download_url ?? "")}"
            data-path="${escapeHtml(f.path)}"
            data-md="${isMd}">
      <svg class="sd-ti-icon" viewBox="0 0 16 16" width="14" height="14" fill="currentColor" aria-hidden="true">
        <path d="M2 1.75C2 .784 2.784 0 3.75 0h6.586c.464 0 .909.184 1.237.513l2.914 2.914c.329.328.513.773.513 1.237v9.586A1.75 1.75 0 0 1 13.25 16h-9.5A1.75 1.75 0 0 1 2 14.25Zm1.75-.25a.25.25 0 0 0-.25.25v12.5c0 .138.112.25.25.25h9.5a.25.25 0 0 0 .25-.25V6h-2.75A1.75 1.75 0 0 1 8.75 4.25V1.5Zm6.75.062V4.25c0 .138.112.25.25.25h2.688l-.011-.013-2.914-2.914-.013-.011Z"/>
      </svg>
      <span class="sd-ti-name">${escapeHtml(f.name)}</span>
    </button>
    <div class="sd-ti-body hidden"></div>
  </li>`;
}

function bindSdTree(root, repo, branch) {
  root.addEventListener("click", async (e) => {
    const btn = e.target.closest(".sd-ti-btn");
    if (!btn) return;
    const li = btn.closest(".sd-ti");
    if (!li) return;

    if (li.classList.contains("sd-ti--dir")) {
      const sub = li.querySelector(".sd-tree--sub");
      const isOpen = !sub.classList.contains("hidden");
      btn.querySelector(".sd-ti-caret")?.classList.toggle("open", !isOpen);
      sub.classList.toggle("hidden", isOpen);

      if (!isOpen && !sub.dataset.loaded) {
        sub.innerHTML = `<li class="sd-ti-msg">Loading…</li>`;
        try {
          const ar = await fetch(`https://api.github.com/repos/${repo}/contents/${li.dataset.path}`);
          if (!ar.ok) throw new Error(`HTTP ${ar.status}`);
          const items = await ar.json();
          sub.dataset.loaded = "1";
          sub.innerHTML = Array.isArray(items) ? items.map(sdFileItemHtml).join("") : "";
          bindSdTree(sub, repo, branch);
        } catch (err) {
          sub.innerHTML = `<li class="sd-ti-msg sd-ti-msg--err">Failed: ${escapeHtml(err.message)}</li>`;
        }
      }
      return;
    }

    // File
    const body = li.querySelector(".sd-ti-body");
    const isOpen = !body.classList.contains("hidden");
    body.classList.toggle("hidden", isOpen);
    if (isOpen || body.dataset.loaded) return;

    const rawUrl = btn.dataset.raw ||
      `https://raw.githubusercontent.com/${repo}/${branch}/${btn.dataset.path}`;
    const isMd = btn.dataset.md === "true";

    body.innerHTML = sdLoadingHtml();
    try {
      const r = await fetch(rawUrl);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const text = await r.text();
      body.dataset.loaded = "1";
      if (isMd) {
        body.innerHTML = `<div class="sd-file-md">${sdMdToHtml(text)}</div>`;
        bindSdCopy(body);
      } else {
        body.innerHTML = `<pre class="sd-file-raw"><code>${escapeHtml(text)}</code></pre>`;
      }
    } catch (err) {
      body.innerHTML = `<div class="sd-error"><small>${escapeHtml(err.message)}</small></div>`;
    }
  });
}

/* ---------- Copy buttons inside rendered markdown ---------- */

function bindSdCopy(root) {
  root.querySelectorAll(".sd-copy").forEach((btn) => {
    if (btn._wired) return;
    btn._wired = true;
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const code = btn.closest(".sd-code-wrap")?.querySelector("code")?.textContent ?? "";
      const orig = btn.textContent;
      try {
        await navigator.clipboard.writeText(code);
        btn.classList.add("copied");
        btn.textContent = "Copied!";
        setTimeout(() => { btn.classList.remove("copied"); btn.textContent = orig; }, 1400);
      } catch {
        btn.textContent = "Press Ctrl+C";
        setTimeout(() => (btn.textContent = orig), 1400);
      }
    });
  });
}

/* ---------- Markdown → HTML renderer for skill content ---------- */

function sdMdToHtml(md) {
  // Strip YAML frontmatter
  const src = md.replace(/^---[\s\S]*?---\n?/, "").trim();
  const lines = src.split("\n");
  const out = [];
  let i = 0;

  // Inline formatting (applied to already-escaped text)
  const inlineFmt = (raw) => {
    // Split on code spans first to avoid processing their content
    return raw.split(/(`[^`\n]+`)/g).map((part, idx) => {
      if (idx % 2 === 1) {
        // Code span — escape and wrap
        return `<code class="sd-ic">${escapeHtml(part.slice(1, -1))}</code>`;
      }
      let s = escapeHtml(part);
      s = s.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
      s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
      s = s.replace(/\*([^*\n]+)\*/g, "<em>$1</em>");
      s = s.replace(/_([^_\n]+)_/g, "<em>$1</em>");
      s = s.replace(/\[([^\]\n]+)\]\(([^)\n]+)\)/g,
        (_, text, url) => `<a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(text)}</a>`);
      return s;
    }).join("");
  };

  while (i < lines.length) {
    const line = lines[i];
    const trim = line.trim();

    // ── Code fence ──────────────────────────────────────────────────────
    if (trim.startsWith("```")) {
      const lang = trim.slice(3).trim();
      const code = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        code.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      const escaped = code.join("\n")
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      out.push(
        `<div class="sd-code-wrap">` +
        (lang ? `<span class="sd-code-lang">${escapeHtml(lang)}</span>` : "") +
        `<button class="sd-copy" type="button">Copy</button>` +
        `<pre><code>${escaped}</code></pre></div>`
      );
      continue;
    }

    // ── Heading ──────────────────────────────────────────────────────────
    const hm = trim.match(/^(#{1,4})\s+(.+)$/);
    if (hm) {
      const n = hm[1].length;
      const id = slugify(hm[2]);
      out.push(`<h${n} id="${id}" class="sd-h sd-h${n}">${inlineFmt(hm[2])}</h${n}>`);
      i++;
      continue;
    }

    // ── Horizontal rule ──────────────────────────────────────────────────
    if (trim === "---" || trim === "***" || trim === "___") {
      out.push(`<hr class="sd-hr">`);
      i++;
      continue;
    }

    // ── Table ────────────────────────────────────────────────────────────
    if (trim.startsWith("|") && trim.endsWith("|") &&
        i + 1 < lines.length && /^\|[\s\-:|]+\|$/.test(lines[i + 1].trim())) {
      const tLines = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tLines.push(lines[i]);
        i++;
      }
      const cells = (l) => l.split("|").slice(1, -1).map((c) => c.trim());
      const hdr = cells(tLines[0]);
      const bdy = tLines.slice(2);
      let t = `<div class="sd-table-wrap"><table class="sd-table"><thead><tr>`;
      hdr.forEach((c) => { t += `<th>${inlineFmt(c)}</th>`; });
      t += `</tr></thead><tbody>`;
      bdy.forEach((row) => {
        t += "<tr>";
        cells(row).forEach((c) => { t += `<td>${inlineFmt(c)}</td>`; });
        t += "</tr>";
      });
      t += `</tbody></table></div>`;
      out.push(t);
      continue;
    }

    // ── Blockquote ───────────────────────────────────────────────────────
    if (trim.startsWith(">")) {
      const qLines = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        qLines.push(lines[i].trim().slice(1).trim());
        i++;
      }
      out.push(`<blockquote class="sd-bq">${inlineFmt(qLines.join(" "))}</blockquote>`);
      continue;
    }

    // ── Unordered list ───────────────────────────────────────────────────
    if (/^\s*[-*+] /.test(line)) {
      let html = "";
      let prevDepth = -1;
      const stack = [];
      while (i < lines.length && /^\s*[-*+] /.test(lines[i])) {
        const indent = lines[i].match(/^(\s*)/)[1].length;
        const depth = Math.floor(indent / 2);
        const content = lines[i].replace(/^\s*[-*+] /, "");
        while (stack.length > depth) { html += "</ul>"; stack.pop(); }
        if (stack.length < depth) { html += `<ul class="sd-ul sd-ul--sub">`; stack.push(depth); }
        if (stack.length === 0 && prevDepth < 0) { html += `<ul class="sd-ul">`; stack.push(0); }
        html += `<li>${inlineFmt(content)}</li>`;
        prevDepth = depth;
        i++;
      }
      while (stack.length) { html += "</ul>"; stack.pop(); }
      out.push(html);
      continue;
    }

    // ── Ordered list ─────────────────────────────────────────────────────
    if (/^\d+\.\s/.test(trim)) {
      let html = `<ol class="sd-ol">`;
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        html += `<li>${inlineFmt(lines[i].replace(/^\d+\.\s/, ""))}</li>`;
        i++;
      }
      html += `</ol>`;
      out.push(html);
      continue;
    }

    // ── Blank line ───────────────────────────────────────────────────────
    if (!trim) { i++; continue; }

    // ── Paragraph ────────────────────────────────────────────────────────
    const pLines = [];
    while (i < lines.length) {
      const t = lines[i].trim();
      if (!t) break;
      if (/^#{1,4}\s/.test(t) || t.startsWith("```") || t.startsWith(">")) break;
      if (/^\s*[-*+] /.test(lines[i]) || /^\d+\.\s/.test(t)) break;
      if (t.startsWith("|") || t === "---" || t === "***") break;
      pLines.push(lines[i]);
      i++;
    }
    if (pLines.length) {
      out.push(`<p class="sd-p">${inlineFmt(pLines.join(" "))}</p>`);
    }
  }

  return out.join("\n");
}

init();
