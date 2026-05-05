// Lightweight, dependency-free browser for github.com/mouadja02/skills.
// Loads ./manifest.json, renders a searchable card grid, exposes per-skill
// install commands across bash, PowerShell, degit, and git sparse-checkout.

const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];

const SORT_KEY = "skills:sort";
const THEME_KEY = "skills:theme";
const SKELETON_COUNT = 9;

const state = {
  manifest: null,
  zips: null,
  filterText: "",
  filterCategory: null,
  sort: localStorage.getItem(SORT_KEY) || "name",
  catColor: new Map(),
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
  bindHeroTabs();
  bindSearch();
  bindGlobalCopy();

  $("#grid").setAttribute("aria-busy", "false");
  render();
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
    state.filterText = e.target.value.toLowerCase().trim();
    clearBtn.classList.toggle("hidden", !state.filterText);
    render();
  });

  clearBtn.addEventListener("click", () => {
    input.value = "";
    state.filterText = "";
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

  const dest = `~/.claude/skills/${cat}`;
  const psDest = `$HOME\\.claude\\skills\\${cat}`;
  const raw = `https://raw.githubusercontent.com/${repo}/${default_branch}`;
  const variants = {
    bash: `curl -fsSL ${raw}/install.sh \\\n  | bash -s -- ${cat} -d ${dest}`,
    ps:
      `$content = irm ${raw}/install.ps1\n` +
      `iex $content\n` +
      `Install-Skill ${cat} -Dest ${psDest}`,
    degit: `npx degit ${repo}/skills/${cat} ${dest}`,
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
    if (state.filterCategory && s.category !== state.filterCategory) return false;
    if (!state.filterText) return true;
    const hay = `${s.name} ${s.install_path} ${s.description}`.toLowerCase();
    return hay.includes(state.filterText);
  });

  filtered = sortSkills(filtered, state.sort);

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
      state.filterCategory = null;
      $$("#categories .cat").forEach((c) =>
        c.classList.toggle("active", c.dataset.cat === "all")
      );
      renderCategoryBanner();
      render();
    });
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

function renderCard(skill, tmpl, repo, branch) {
  const node = tmpl.content.firstElementChild.cloneNode(true);
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

function installCommands(skill, repo, branch) {
  const { install_path, name } = skill;
  const ip = install_path;
  const dest = `~/.claude/skills/${name}`;
  const psDest = `$HOME\\.claude\\skills\\${name}`;
  const raw = `https://raw.githubusercontent.com/${repo}/${branch}`;
  return {
    bash:
      `curl -fsSL ${raw}/install.sh \\\n  | bash -s -- ${ip} -d ${dest}`,
    ps:
      `$content = irm ${raw}/install.ps1\n` +
      `iex $content\n` +
      `Install-Skill -Skill ${ip} -Dest ${psDest}`,
    degit: `npx degit ${repo}/skills/${ip} ${dest}`,
    sparse:
      `git clone --no-checkout --depth 1 --filter=blob:none \\\n` +
      `  https://github.com/${repo}.git skills-tmp && cd skills-tmp \\\n` +
      `  && git sparse-checkout init --cone \\\n` +
      `  && git sparse-checkout set skills/${ip} \\\n` +
      `  && git checkout && mv skills/${ip} ${dest} && cd .. && rm -rf skills-tmp`,
  };
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

init();
