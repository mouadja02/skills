// Lightweight, dependency-free browser for github.com/mouadja02/skills.
// Loads ./manifest.json, renders a searchable card grid in pages, and keeps a
// live install command in sync with whatever the visitor has selected.

const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];

const SORT_KEY = "skills:sort";
const THEME_KEY = "skills:theme";
const HARNESS_KEY = "skills:harnesses";
const PICKS_KEY = "skills:picks";
const SKELETON_COUNT = 9;

// Cards render a page at a time. Rendering all 810 built ~45k DOM nodes and
// ~13k tab stops, which made the grid unusable with a keyboard and pushed the
// document past 95,000px.
const PAGE_SIZE = 60;

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

// Task routes are an editorial layer over the 36 folder categories: folders are
// named after where code lives, and nobody arrives thinking "microsoft-data".
// Categories missing from this map still appear in the full category list, so a
// new folder degrades to "not featured" rather than "unreachable".
const TASK_ROUTES = [
  {
    id: "agents",
    label: "Build AI agents",
    blurb: "Agent architecture, evals, memory, prompts, MCP servers.",
    cats: ["agent-design", "agent-eval", "context-engineering", "prompting", "llm-tooling", "mcp"],
  },
  {
    id: "code",
    label: "Write & review code",
    blurb: "Implementation workflows, refactoring, review, testing.",
    cats: ["coding", "code-quality", "engineering-craft", "testing", "dev-workflow"],
  },
  {
    id: "ship",
    label: "Ship & operate",
    blurb: "CI/CD, containers, infrastructure, AWS and Azure.",
    cats: ["devops", "cloud-aws", "cloud-azure"],
  },
  {
    id: "interface",
    label: "Design interfaces",
    blurb: "UI systems, frontend frameworks, dashboards, branding.",
    cats: ["design-and-ui", "react-frontend", "streamlit", "creative"],
  },
  {
    id: "data",
    label: "Work with data",
    blurb: "Schema design, SQL, migrations, analytics, Power Platform.",
    cats: ["databases", "microsoft-data"],
  },
  {
    id: "product",
    label: "Plan & sell product",
    blurb: "Discovery, specs, strategy, positioning, growth.",
    cats: ["product-management", "business-strategy", "go-to-market", "marketing-and-growth", "finance"],
  },
  {
    id: "write",
    label: "Write & present",
    blurb: "READMEs, ADRs, diagrams, slides, research, comms.",
    cats: ["documentation", "diagrams-slides", "research", "communication", "personal-productivity"],
  },
  {
    id: "platform",
    label: "Backend & platforms",
    blurb: "APIs, .NET, Java, Microsoft agents, skill authoring.",
    cats: ["api-backend", "dotnet", "java-kotlin", "microsoft-agents", "skills-management", "messaging"],
  },
];

function loadStoredHarnesses() {
  try {
    const stored = JSON.parse(localStorage.getItem(HARNESS_KEY));
    if (Array.isArray(stored) && stored.length) return stored;
  } catch {}
  return ["claude-code"];
}

function loadStoredPicks() {
  try {
    const stored = JSON.parse(localStorage.getItem(PICKS_KEY));
    if (Array.isArray(stored)) return stored.filter((s) => typeof s === "string");
  } catch {}
  return [];
}

const state = {
  manifest: null,
  zips: null,
  filterText: "",
  filterCategory: null,
  filterRoute: null,
  recommendedSkillNames: null,
  sort: localStorage.getItem(SORT_KEY) || "name",
  catColor: new Map(),
  selectedHarnesses: loadStoredHarnesses(),
  picks: loadStoredPicks(),
  catsExpanded: false,
  // Windowing
  filtered: [],
  shown: 0,
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
    applyTheme(current === "dark" ? "light" : "dark");
    localStorage.setItem(THEME_KEY, document.documentElement.getAttribute("data-theme"));
  });

  // Follow system if user hasn't picked manually.
  if (!stored) {
    window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", (e) => {
      if (!localStorage.getItem(THEME_KEY)) applyTheme(e.matches ? "light" : "dark");
    });
  }
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const meta = $('meta[name="color-scheme"]');
  if (meta) meta.setAttribute("content", theme);
  // The control switches to the *other* theme, so name that, not the current one.
  const toggle = $("#themeToggle");
  if (toggle) {
    const next = theme === "dark" ? "light" : "dark";
    toggle.setAttribute("aria-label", `Switch to ${next} theme`);
    toggle.title = `Switch to ${next} theme`;
  }
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
    $("#grid").innerHTML = loadErrorHTML(err.message);
    $("#grid").setAttribute("aria-busy", "false");
    setSummary("The catalog could not be loaded.");
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
  state.manifest.categories.forEach((c, i) => state.catColor.set(c, i % 13));

  const total = state.manifest.count.toLocaleString();
  $("#skillCount").textContent = total;
  const heroBrowse = $("#heroBrowseCount");
  if (heroBrowse) heroBrowse.textContent = total;

  const search = $("#search");
  if (search) {
    search.placeholder = `Search ${total} skills — try “pytest”, “terraform”, “rag”…`;
  }

  $("#sortBy").value = state.sort;
  $("#sortBy").addEventListener("change", (e) => {
    state.sort = e.target.value;
    localStorage.setItem(SORT_KEY, state.sort);
    render();
  });

  // Drop picks that no longer exist in the manifest (skills get renamed).
  const known = new Set(state.manifest.skills.map((s) => s.install_path));
  state.picks = state.picks.filter((p) => known.has(p));
  savePicks();

  renderRoutes();
  renderCategories();
  renderHarnesses();
  bindAnatomy();
  bindSearch();
  bindGlobalCopy();
  bindSkillDetail();
  bindShowMore();
  bindTray();
  renderTray();

  $("#grid").setAttribute("aria-busy", "false");
  if (location.search) applyUrlState();
  else render();
}

/* ==========================================================================
   Skeletons, empty and error states
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

function loadErrorHTML(detail) {
  return `<div class="empty">
    <div class="empty-icon empty-icon--warn">
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M12 8v5M12 16.5v.5"/><circle cx="12" cy="12" r="9"/>
      </svg>
    </div>
    <p class="empty-title">The skill index didn&rsquo;t load</p>
    <p class="empty-desc">
      <code>manifest.json</code> returned ${escapeHtml(detail)}. If you&rsquo;re running this
      locally, generate it with <code>npm run build:manifest</code>, then reload.
      Otherwise the deploy is probably mid-update &mdash; reloading in a minute usually fixes it.
    </p>
    <button type="button" onclick="location.reload()">Reload the page</button>
  </div>`;
}

function emptyStateHTML() {
  const bits = [];
  if (state.filterText) bits.push(`<code>${escapeHtml(state.filterText)}</code>`);
  if (state.filterCategory) bits.push(`the <strong>${escapeHtml(categoryLabel(state.filterCategory))}</strong> category`);
  if (state.filterRoute) bits.push(`<strong>${escapeHtml(routeById(state.filterRoute)?.label ?? "")}</strong>`);
  const what = bits.length ? bits.join(" in ") : "these filters";

  return `<div class="empty">
    <div class="empty-icon">
      <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>
      </svg>
    </div>
    <p class="empty-title">Nothing matches ${what}</p>
    <p class="empty-desc">
      Search covers skill names, descriptions and install paths &mdash; a shorter or more
      general word usually finds it. Or clear the filters and browse all
      ${state.manifest.count.toLocaleString()}.
    </p>
    <button id="resetFilters" type="button">Clear all filters</button>
  </div>`;
}

/* ==========================================================================
   Hero: anatomy of an install command
   ========================================================================== */

// The old hero shipped `bash -s -- <selector> -d ~/.claude/skills/<name>` behind
// a Copy button, so the site's most prominent command was one that fails when
// pasted. These are real, runnable examples instead.
const ANATOMY = {
  one: {
    selector: "code-quality/code-review",
    dest: (h) => h.destBash("code-review"),
    note: "An exact install path installs that one skill.",
  },
  cat: {
    selector: "cloud-aws",
    dest: (h) => h.destBash("cloud-aws"),
    note: () => {
      const n = state.manifest?.counts_by_category?.["cloud-aws"];
      return `A bare category name installs every skill inside it${n ? ` — ${n} for cloud-aws` : ""}.`;
    },
  },
  glob: {
    selector: '"*rag*"',
    dest: (h) => h.destBash("rag-skills"),
    note: "A quoted glob installs every install path that matches. Quote it so your shell doesn’t expand it first.",
  },
};

function bindAnatomy() {
  const btns = $$(".anatomy-choice");
  if (!btns.length) return;
  btns.forEach((btn) => {
    btn.addEventListener("click", () => {
      btns.forEach((b) => {
        const on = b === btn;
        b.classList.toggle("active", on);
        b.setAttribute("aria-pressed", on ? "true" : "false");
      });
      updateAnatomy(btn.dataset.sel);
    });
    btn.setAttribute("aria-pressed", btn.classList.contains("active") ? "true" : "false");
  });
  updateAnatomy("one");
  bindCopy($(".anatomy"));
}

function updateAnatomy(kind) {
  if (!state.manifest) return;
  const spec = ANATOMY[kind] ?? ANATOMY.one;
  const { repo, default_branch } = state.manifest;
  const raw = `https://raw.githubusercontent.com/${repo}/${default_branch}`;
  const h = getPrimaryHarness();
  const code = $("#anatomyCode");
  const note = $("#anatomyNote");
  if (code) {
    code.textContent =
      `curl -fsSL ${raw}/install.sh \\\n  | bash -s -- ${spec.selector} -d ${spec.dest(h)}`;
  }
  if (note) note.textContent = typeof spec.note === "function" ? spec.note() : spec.note;

  // The example counts come from the manifest so they can't drift from it.
  const catEg = $('.anatomy-choice[data-sel="cat"] .anatomy-choice-eg');
  if (catEg) {
    const n = state.manifest.counts_by_category["cloud-aws"];
    if (n) catEg.textContent = `${n} at once`;
  }
}

function currentAnatomyKind() {
  return $(".anatomy-choice.active")?.dataset.sel ?? "one";
}

/* ==========================================================================
   Task routes
   ========================================================================== */

function routeById(id) {
  return TASK_ROUTES.find((r) => r.id === id) ?? null;
}

function routeCats(route) {
  // Only categories that actually exist in the manifest.
  const known = new Set(state.manifest.categories);
  return route.cats.filter((c) => known.has(c));
}

function routeCount(route) {
  const { counts_by_category } = state.manifest;
  return routeCats(route).reduce((n, c) => n + (counts_by_category[c] ?? 0), 0);
}

function renderRoutes() {
  const grid = $("#routesGrid");
  if (!grid) return;

  const covered = new Set(TASK_ROUTES.flatMap((r) => routeCats(r)));
  const orphans = state.manifest.categories.filter((c) => !covered.has(c));
  if (orphans.length) {
    // Not fatal: orphans stay reachable through the category list below.
    console.info(`[skills] categories not featured in a task route: ${orphans.join(", ")}`);
  }

  grid.innerHTML = TASK_ROUTES.map((r) => {
    const n = routeCount(r);
    return `<button class="route" type="button" data-route="${escapeHtml(r.id)}" aria-pressed="false">
      <span class="route-label">${escapeHtml(r.label)}</span>
      <span class="route-blurb">${escapeHtml(r.blurb)}</span>
      <span class="route-count"><strong>${n}</strong> skills</span>
    </button>`;
  }).join("");

  grid.addEventListener("click", (e) => {
    const btn = e.target.closest(".route");
    if (!btn) return;
    const id = btn.dataset.route;
    selectRoute(state.filterRoute === id ? null : id);
    focusResults();
  });
}

function selectRoute(id) {
  state.filterRoute = id;
  state.filterCategory = null;
  state.recommendedSkillNames = null;
  syncRouteButtons();
  syncCategoryButtons();
  render();
}

function syncRouteButtons() {
  $$(".route").forEach((b) => {
    const on = b.dataset.route === state.filterRoute;
    b.classList.toggle("active", on);
    b.setAttribute("aria-pressed", on ? "true" : "false");
  });
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

// How many pills stay visible before "show all". The rest are hidden with a
// class rather than removed, so expanding never re-renders the list. Ten pills
// wrap to six rows on a 375px screen, so narrow viewports show fewer.
const CATS_NARROW = window.matchMedia("(max-width: 620px)");
const collapsedCount = () => (CATS_NARROW.matches ? 5 : 10);

function renderCategories() {
  const container = $("#categories");
  const toggle = $("#catToggle");
  const { categories, counts_by_category } = state.manifest;

  // Most-populated first: the collapsed set should be the ten most likely to
  // be useful, not the ten that sort first alphabetically.
  const ordered = [...categories].sort(
    (a, b) => (counts_by_category[b] ?? 0) - (counts_by_category[a] ?? 0) || a.localeCompare(b)
  );

  container.innerHTML = "";
  container.appendChild(mkCat("all", state.manifest.count, true, null));
  ordered.forEach((c) => {
    container.appendChild(mkCat(c, counts_by_category[c], false, state.catColor.get(c)));
  });

  container.addEventListener("click", (e) => {
    const btn = e.target.closest(".cat");
    if (!btn) return;
    state.recommendedSkillNames = null;
    state.filterRoute = null;
    state.filterCategory = btn.dataset.cat === "all" ? null : btn.dataset.cat;
    syncRouteButtons();
    syncCategoryButtons();
    render();
  });

  if (!toggle) return;
  // Move the toggle into the pill container so it wraps as the last item in the
  // same flow instead of floating at the top-right of the region.
  container.appendChild(toggle);

  const sync = () => {
    const keep = collapsedCount();
    const pills = $$(".cat", container).filter((b) => b.dataset.cat !== "all");
    pills.forEach((b, i) => b.classList.toggle("cat--extra", i >= keep));
    const extras = Math.max(0, pills.length - keep);
    toggle.hidden = extras === 0;
    toggle.textContent = state.catsExpanded ? "Show fewer" : `+${extras} more`;
    toggle.setAttribute("aria-expanded", state.catsExpanded ? "true" : "false");
    container.classList.toggle("categories--expanded", state.catsExpanded);
  };

  sync();
  toggle.addEventListener("click", () => {
    state.catsExpanded = !state.catsExpanded;
    sync();
  });
  // Crossing the breakpoint changes how many pills fit, so the "+N more" count
  // has to follow it.
  CATS_NARROW.addEventListener("change", sync);
  renderCategories._syncPills = sync;
}

function mkCat(name, count, active = false, colorIdx = null) {
  const btn = document.createElement("button");
  btn.className = "cat" + (active ? " active" : "");
  btn.dataset.cat = name;
  btn.type = "button";
  // These are filter toggles, not tabs: there are no tab panels and no
  // arrow-key roving, so role="tab" was describing an interaction that
  // doesn't exist.
  btn.setAttribute("aria-pressed", active ? "true" : "false");
  if (colorIdx !== null) btn.dataset.catColor = colorIdx;
  const dot = colorIdx !== null ? `<span class="cat-dot" aria-hidden="true"></span>` : "";
  btn.innerHTML =
    `${dot}<span class="cat-name">${escapeHtml(categoryLabel(name))}</span>` +
    `<span class="cnt">${count}</span>`;
  return btn;
}

function syncCategoryButtons() {
  const active = state.filterCategory ?? "all";
  $$("#categories .cat").forEach((c) => {
    const on = c.dataset.cat === active;
    c.classList.toggle("active", on);
    c.setAttribute("aria-pressed", on ? "true" : "false");
  });
  // If the active category is one of the hidden extras, expand so it's visible.
  const activeBtn = $(`#categories .cat.active`);
  if (activeBtn?.classList.contains("cat--extra") && !state.catsExpanded) {
    $("#catToggle")?.click();
  }
}

/* ==========================================================================
   Orientation: what you're looking at, not just how many
   ========================================================================== */

function setSummary(html) {
  const el = $("#resultSummary");
  if (el) el.innerHTML = html;
}

function updateSummary(filtered) {
  const total = state.manifest.count;
  const n = filtered.length;
  const cats = new Set(filtered.map((s) => s.category)).size;
  const nStr = `<strong>${n.toLocaleString()}</strong>`;

  if (!n) {
    setSummary(`No matches. <strong>${total.toLocaleString()}</strong> skills in the full catalog.`);
  } else if (state.recommendedSkillNames?.length) {
    setSummary(`${nStr} skill${n === 1 ? "" : "s"} suggested for you, in the order the assistant ranked them.`);
  } else if (state.filterCategory) {
    setSummary(`${nStr} skill${n === 1 ? "" : "s"} in <strong>${escapeHtml(categoryLabel(state.filterCategory))}</strong>, of ${total.toLocaleString()} total.`);
  } else if (state.filterRoute && state.filterText) {
    setSummary(`${nStr} match${n === 1 ? "" : "es"} for &ldquo;${escapeHtml(state.filterText)}&rdquo; within <strong>${escapeHtml(routeById(state.filterRoute)?.label ?? "")}</strong>.`);
  } else if (state.filterRoute) {
    const r = routeById(state.filterRoute);
    setSummary(`${nStr} skill${n === 1 ? "" : "s"} for <strong>${escapeHtml(r?.label ?? "")}</strong>, across ${cats} categories.`);
  } else if (state.filterText) {
    setSummary(`${nStr} match${n === 1 ? "" : "es"} for &ldquo;${escapeHtml(state.filterText)}&rdquo;, across ${cats} categor${cats === 1 ? "y" : "ies"}.`);
  } else {
    setSummary(
      `The whole catalog: <strong>${total.toLocaleString()}</strong> skills across ` +
      `<strong>${state.manifest.categories.length}</strong> categories. ` +
      `Biggest are ${topCategoriesPhrase(3)}.`
    );
  }

  renderActiveFilters();
}

function topCategoriesPhrase(n) {
  const { counts_by_category } = state.manifest;
  return [...state.manifest.categories]
    .sort((a, b) => counts_by_category[b] - counts_by_category[a])
    .slice(0, n)
    .map((c) => `${categoryLabel(c)} (${counts_by_category[c]})`)
    .join(", ");
}

function renderActiveFilters() {
  const el = $("#activeFilters");
  if (!el) return;
  const chips = [];
  if (state.filterRoute) {
    chips.push({ kind: "route", label: routeById(state.filterRoute)?.label ?? "", clear: () => selectRoute(null) });
  }
  if (state.filterCategory) {
    chips.push({
      kind: "cat",
      label: categoryLabel(state.filterCategory),
      clear: () => { state.filterCategory = null; syncCategoryButtons(); render(); },
    });
  }
  if (state.filterText) {
    chips.push({
      kind: "q",
      label: `“${state.filterText}”`,
      clear: () => { $("#search").value = ""; state.filterText = ""; $("#searchClear").classList.add("hidden"); render(); },
    });
  }
  if (state.recommendedSkillNames?.length) {
    chips.push({
      kind: "rec",
      label: `${state.recommendedSkillNames.length} suggested`,
      clear: () => { state.recommendedSkillNames = null; render(); },
    });
  }

  if (!chips.length) {
    el.hidden = true;
    el.innerHTML = "";
    return;
  }

  el.hidden = false;
  el.innerHTML =
    `<span class="active-filters-label">Filtered by</span>` +
    chips.map((c, i) =>
      `<button class="chip" type="button" data-i="${i}">
        ${escapeHtml(c.label)}
        <span class="chip-x" aria-hidden="true">&times;</span>
        <span class="sr-only">— remove this filter</span>
      </button>`
    ).join("") +
    `<button class="chip chip--reset" type="button" data-reset>Clear all</button>` +
    `<button class="chip chip--share" type="button" id="shareBtn">Copy link to this view</button>`;

  $$(".chip[data-i]", el).forEach((btn) => {
    btn.addEventListener("click", () => chips[Number(btn.dataset.i)].clear());
  });
  $("[data-reset]", el)?.addEventListener("click", resetAllFilters);
  $("#shareBtn", el)?.addEventListener("click", () => copyShareUrl(location.href));
}

function resetAllFilters() {
  $("#search").value = "";
  $("#searchClear").classList.add("hidden");
  state.filterText = "";
  state.filterCategory = null;
  state.filterRoute = null;
  state.recommendedSkillNames = null;
  syncRouteButtons();
  syncCategoryButtons();
  render();
  focusResults();
}

/* ==========================================================================
   Live selector panel — what you picked, and the command it produces
   ========================================================================== */

// Turns the current view into a single install.sh selector when one exists.
// install.sh takes exactly one selector, so this is what makes "install this
// whole view" a single line rather than N lines.
function currentSelector() {
  if (state.filterCategory) {
    return { sel: state.filterCategory, kind: "category", dest: state.filterCategory };
  }
  if (state.filterRoute) return null; // spans several categories — no single selector
  if (state.recommendedSkillNames?.length) return null;
  if (state.filterText && /^[a-z0-9][a-z0-9-]*$/.test(state.filterText)) {
    // install.sh globs match install_path only, while the search box also looks
    // at descriptions. Count what the *command* would actually install, so the
    // panel never promises a set the command wouldn't produce.
    const globHits = state.manifest.skills.filter((s) =>
      s.install_path.toLowerCase().includes(state.filterText)
    ).length;
    if (!globHits) return null;
    return {
      sel: `"*${state.filterText}*"`,
      kind: "glob",
      dest: `${state.filterText}-skills`,
      globHits,
    };
  }
  return null;
}

function renderSelectorPanel(filtered) {
  const panel = $("#selectorPanel");
  if (!panel) return;
  const spec = currentSelector();

  if (!spec || !filtered.length) {
    panel.hidden = true;
    return;
  }

  const { repo, default_branch } = state.manifest;
  const raw = `https://raw.githubusercontent.com/${repo}/${default_branch}`;
  const harnesses = activeHarnesses();

  if (spec.kind === "category") {
    $("#selectorPanelTitle").textContent =
      `Install all ${filtered.length} in ${categoryLabel(state.filterCategory)}`;
    $("#selectorPanelSub").innerHTML =
      `One selector — the category name — stands in for every skill inside it.`;
  } else {
    const n = spec.globHits;
    $("#selectorPanelTitle").textContent =
      `Install the ${n} skill${n === 1 ? "" : "s"} whose path contains “${state.filterText}”`;
    const extra = filtered.length - n;
    $("#selectorPanelSub").innerHTML =
      `A quoted glob matches install paths, so it covers ` +
      `<code>*${escapeHtml(state.filterText)}*</code> in the path` +
      (extra > 0
        ? ` — not the ${extra} further result${extra === 1 ? "" : "s"} below that matched on description alone.`
        : `.`);
  }

  const variants = {
    bash: harnesses.map((h) => `curl -fsSL ${raw}/install.sh \\\n  | bash -s -- ${spec.sel} -d ${h.destBash(spec.dest)}`).join("\n"),
    ps: harnesses.map((h) => `& ([scriptblock]::Create((irm ${raw}/install.ps1))) ${spec.sel} -Dest ${h.destPs(spec.dest)}`).join("\n"),
    degit: spec.kind === "category"
      ? harnesses.map((h) => `npx degit ${repo}/skills/${spec.sel} ${h.destBash(spec.dest)}`).join("\n")
      : `# degit resolves one directory at a time, so a glob has no degit form.\n# Use the bash or PowerShell tab, or pick the skills individually.`,
  };
  $$(".selector-panel-code", panel).forEach((pre) => {
    $("code", pre).textContent = variants[pre.dataset.variant];
  });

  const dlLink = $("#catBannerDownload");
  const dlSize = $("#catBannerDownloadSize");
  const catZip = spec.kind === "category" ? state.zips?.categories?.[spec.sel] : null;
  if (catZip) {
    dlLink.href = zipHref(catZip);
    dlLink.setAttribute("download", `${spec.sel}.zip`);
    dlSize.textContent = `· ${formatBytes(catZip.bytes)}`;
    dlLink.classList.remove("hidden");
  } else {
    dlLink.classList.add("hidden");
  }

  bindTabs(panel, ".selector-panel-tabs .tab", ".selector-panel-code");
  bindCopy(panel);
  panel.hidden = false;
}

/* ==========================================================================
   Tabs / copy helpers
   ========================================================================== */

function bindTabs(scope, tabSel, paneSel) {
  const tabs = $$(tabSel, scope);
  const panes = $$(paneSel, scope);
  tabs.forEach((tab) => {
    tab.setAttribute("aria-pressed", tab.classList.contains("active") ? "true" : "false");
    if (tab._wired) return;
    tab._wired = true;
    tab.addEventListener("click", () => {
      tabs.forEach((t) => {
        const on = t === tab;
        t.classList.toggle("active", on);
        t.setAttribute("aria-pressed", on ? "true" : "false");
      });
      panes.forEach((p) => p.classList.toggle("hidden", p.dataset.variant !== tab.dataset.tab));
    });
  });
}

// navigator.clipboard fails on http:// origins and when the document isn't
// focused. The old fallback told people to press Ctrl+C with nothing selected,
// which copies nothing (and names the wrong key on a Mac). Select the text so
// the instruction is actually true.
async function copyText(text, sourceEl) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const node = sourceEl?.closest("pre")?.querySelector("code") ?? sourceEl;
    if (node) {
      const range = document.createRange();
      range.selectNodeContents(node);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    }
    return false;
  }
}

const COPY_FALLBACK_HINT = navigator.platform?.toLowerCase().includes("mac")
  ? "Selected it — press ⌘C"
  : "Selected it — press Ctrl+C";

function flashButton(btn, labelEl, okText, failText, ok) {
  const target = labelEl ?? btn;
  const orig = target.textContent;
  target.textContent = ok ? okText : failText;
  btn.classList.toggle("copied", ok);
  clearTimeout(btn._flashTimer);
  btn._flashTimer = setTimeout(() => {
    target.textContent = orig;
    btn.classList.remove("copied");
  }, 1600);
}

function bindCopy(scope) {
  $$(".copy", scope).forEach((btn) => {
    if (btn._wired) return;
    btn._wired = true;
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const target = btn.dataset.copyTarget
        ? document.querySelector(btn.dataset.copyTarget)
        : $("code", btn.parentElement);
      const ok = await copyText(target?.textContent ?? "", btn);
      flashButton(btn, null, "Copied", COPY_FALLBACK_HINT, ok);
    });
  });
}

function bindGlobalCopy() {
  bindCopy($(".mcp-section"));
}

/* ==========================================================================
   Render — paged
   ========================================================================== */

function currentFiltered() {
  const { skills } = state.manifest;
  const routeSet = state.filterRoute
    ? new Set(routeCats(routeById(state.filterRoute)))
    : null;

  let filtered = skills.filter((s) => {
    if (state.recommendedSkillNames?.length && !state.recommendedSkillNames.includes(s.name)) return false;
    if (routeSet && !routeSet.has(s.category)) return false;
    if (state.filterCategory && s.category !== state.filterCategory) return false;
    if (!state.filterText) return true;
    const hay = `${s.name} ${s.install_path} ${s.description}`.toLowerCase();
    return hay.includes(state.filterText);
  });

  return state.recommendedSkillNames?.length
    ? sortRecommendedSkills(filtered)
    : sortSkills(filtered, state.sort);
}

function render() {
  state.filtered = currentFiltered();
  state.shown = 0;

  updateSummary(state.filtered);
  renderSelectorPanel(state.filtered);

  const grid = $("#grid");
  grid.innerHTML = "";

  if (!state.filtered.length) {
    grid.innerHTML = emptyStateHTML();
    $("#resetFilters")?.addEventListener("click", resetAllFilters);
    $("#gridMore").hidden = true;
    updateUrl();
    updatePageTitle();
    return;
  }

  appendPage();
  updateUrl();
  updatePageTitle();
}

function appendPage() {
  const { repo, default_branch } = state.manifest;
  const tmpl = $("#cardTemplate");
  const grid = $("#grid");
  const slice = state.filtered.slice(state.shown, state.shown + PAGE_SIZE);

  const frag = document.createDocumentFragment();
  slice.forEach((skill, i) => {
    const card = renderCard(skill, tmpl, repo, default_branch);
    // Stagger entrance for the first few cards only — feels smooth, not slow.
    if (state.shown === 0 && i < 12) card.style.animationDelay = `${i * 30}ms`;
    frag.appendChild(card);
  });
  grid.appendChild(frag);
  state.shown += slice.length;

  updateShowMore();
  return slice.length;
}

function updateShowMore() {
  const wrap = $("#gridMore");
  const btn = $("#showMore");
  const note = $("#gridMoreNote");
  const remaining = state.filtered.length - state.shown;

  if (remaining <= 0) {
    btn.hidden = true;
    wrap.hidden = state.filtered.length <= PAGE_SIZE;
    note.textContent = wrap.hidden
      ? ""
      : `That’s all ${state.filtered.length.toLocaleString()} of them.`;
    return;
  }

  wrap.hidden = false;
  btn.hidden = false;
  const next = Math.min(PAGE_SIZE, remaining);
  btn.textContent = `Show ${next} more`;
  note.textContent = `Showing ${state.shown.toLocaleString()} of ${state.filtered.length.toLocaleString()} · ${remaining.toLocaleString()} to go`;
}

function bindShowMore() {
  $("#showMore")?.addEventListener("click", () => {
    const firstNew = state.shown;
    const added = appendPage();
    if (!added) return;
    // Move focus to the first newly revealed card so keyboard users continue
    // from where the list grew instead of being dropped back at the top.
    const cards = $$("#grid .card .card-open");
    cards[firstNew]?.focus({ preventScroll: true });
    cards[firstNew]?.scrollIntoView({ block: "center", behavior: "smooth" });
  });
}

// After a filter change the grid content is entirely new. Send focus to the
// summary line so a screen reader lands on "24 skills in Agent Eval" instead of
// staying on a control whose surroundings silently changed.
function focusResults() {
  const el = $("#resultSummary");
  if (!el) return;
  el.setAttribute("tabindex", "-1");
  el.focus({ preventScroll: true });
  $("#browse")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function sortSkills(skills, mode) {
  const arr = [...skills];
  switch (mode) {
    case "name-desc":
      arr.sort((a, b) => b.name.localeCompare(a.name));
      break;
    case "category":
      arr.sort((a, b) => a.category.localeCompare(b.category) || a.name.localeCompare(b.name));
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
  node.dataset.catColor = state.catColor.get(skill.category) ?? 0;

  // The title is the card's one primary action: it opens the detail panel, and
  // its ::after covers the whole card so the entire surface is clickable while
  // costing a single tab stop.
  const open = $(".card-open", node);
  open.textContent = skill.name;
  open.setAttribute("aria-label", `${skill.name} — open details`);
  open.addEventListener("click", () => openSkillDetail(skill));

  $(".card-category-name", node).textContent = categoryLabel(skill.category, { lower: true });

  const desc = $(".card-desc", node);
  desc.textContent = firstSentence(skill.description);

  const variants = installCommands(skill, repo, branch);

  const quick = $(".card-quick-copy", node);
  const quickLabel = $(".card-quick-copy-label", quick);
  quick.title = `Copy the ${activeHarnesses().map((h) => h.label).join(" + ")} install command`;
  quick.addEventListener("click", async (e) => {
    e.stopPropagation();
    const ok = await copyText(variants.bash, quick);
    flashButton(quick, quickLabel, "Copied", "Couldn’t copy", ok);
    showToast(ok ? `Install command copied — paste it in your terminal` : COPY_FALLBACK_HINT);
  });

  const pick = $(".card-pick", node);
  syncPickButton(pick, skill.install_path);
  pick.addEventListener("click", (e) => {
    e.stopPropagation();
    togglePick(skill.install_path);
  });

  return node;
}

// Card descriptions come from SKILL.md frontmatter and run to several hundred
// words. One sentence is enough to decide whether to open the card; the full
// text is in the detail panel.
function firstSentence(text) {
  const clean = String(text ?? "").replace(/\s+/g, " ").trim();
  const cut = clean.search(/\.\s|\.$|:\s—|\n/);
  const head = cut > 40 ? clean.slice(0, cut + 1) : clean;
  return head.length > 180 ? `${head.slice(0, 177).trimEnd()}…` : head;
}

/* ==========================================================================
   Shortlist ("picks")
   ========================================================================== */

function savePicks() {
  try { localStorage.setItem(PICKS_KEY, JSON.stringify(state.picks)); } catch {}
}

function togglePick(installPath) {
  const i = state.picks.indexOf(installPath);
  if (i === -1) state.picks.push(installPath);
  else state.picks.splice(i, 1);
  savePicks();
  $$(`.card[data-skill-path="${cssEscape(installPath)}"] .card-pick`).forEach((b) =>
    syncPickButton(b, installPath)
  );
  const sdPick = $(".sd-pick");
  if (sdPick && sdPick.dataset.path === installPath) syncPickButton(sdPick, installPath, true);
  renderTray();
}

function syncPickButton(btn, installPath, isDetail = false) {
  const on = state.picks.includes(installPath);
  btn.classList.toggle("picked", on);
  btn.setAttribute("aria-pressed", on ? "true" : "false");
  const label = $(isDetail ? ".sd-pick-label" : ".card-pick-label", btn);
  if (label) label.textContent = on ? (isDetail ? "In your picks" : "Added") : (isDetail ? "Add to picks" : "Add");
  btn.title = on ? "Remove from your picks" : "Add to your picks and install them together";
}

function skillByPath(p) {
  return state.manifest?.skills.find((s) => s.install_path === p) ?? null;
}

function renderTray() {
  const tray = $("#shortlistTray");
  if (!tray) return;
  const n = state.picks.length;
  if (!n) {
    tray.hidden = true;
    $("#trayPanel").hidden = true;
    $("#trayOpen").setAttribute("aria-expanded", "false");
    document.body.classList.remove("has-tray");
    return;
  }

  tray.hidden = false;
  document.body.classList.add("has-tray");
  $("#trayCount").textContent = n;
  $("#trayLabel").textContent = n === 1 ? "skill picked" : "skills picked";

  $("#trayChips").innerHTML = state.picks
    .map((p) => {
      const s = skillByPath(p);
      return `<button class="tray-chip" type="button" data-path="${escapeHtml(p)}" title="Remove ${escapeHtml(s?.name ?? p)}">
        ${escapeHtml(s?.name ?? p)}<span class="chip-x" aria-hidden="true">&times;</span>
        <span class="sr-only">— remove from picks</span>
      </button>`;
    })
    .join("");
  $$("#trayChips .tray-chip").forEach((b) =>
    b.addEventListener("click", () => togglePick(b.dataset.path))
  );

  renderTrayCommand();
}

// install.sh accepts exactly one selector, so an arbitrary shortlist is N
// commands. When every pick happens to sit in one category, or shares a
// distinctive path fragment, a single selector does the job instead — which is
// the whole point of the selector concept.
function collapsePicks(paths) {
  if (paths.length < 2) return null;
  const cats = new Set(paths.map((p) => p.split("/")[0]));
  if (cats.size === 1) {
    const cat = [...cats][0];
    const total = state.manifest.counts_by_category[cat] ?? 0;
    if (total === paths.length) {
      return { sel: cat, dest: cat, why: `All ${paths.length} picks are every skill in ${categoryLabel(cat)}.` };
    }
  }
  return null;
}

function renderTrayCommand() {
  const { repo, default_branch } = state.manifest;
  const raw = `https://raw.githubusercontent.com/${repo}/${default_branch}`;
  const harnesses = activeHarnesses();
  const paths = state.picks;

  $("#trayPanelCount").textContent = paths.length;

  const collapsed = collapsePicks(paths);
  const sub = $("#trayPanelSub");

  let bash, ps;
  if (collapsed) {
    sub.textContent = `${collapsed.why} One selector covers them all.`;
    bash = harnesses.map((h) => `curl -fsSL ${raw}/install.sh \\\n  | bash -s -- ${collapsed.sel} -d ${h.destBash(collapsed.dest)}`).join("\n");
    ps = harnesses.map((h) => `& ([scriptblock]::Create((irm ${raw}/install.ps1))) ${collapsed.sel} -Dest ${h.destPs(collapsed.dest)}`).join("\n");
  } else {
    sub.textContent =
      `install.sh takes one selector per run, so this is one line per skill. ` +
      `Paste the whole block — it runs top to bottom.`;
    bash = harnesses
      .flatMap((h) => paths.map((p) => `curl -fsSL ${raw}/install.sh | bash -s -- ${p} -d ${h.destBash(p.split("/").pop())}`))
      .join("\n");
    ps = harnesses
      .flatMap((h) => paths.map((p) => `& ([scriptblock]::Create((irm ${raw}/install.ps1))) ${p} -Dest ${h.destPs(p.split("/").pop())}`))
      .join("\n");
  }

  const panel = $("#trayPanel");
  $$(".tray-code", panel).forEach((pre) => {
    $("code", pre).textContent = pre.dataset.variant === "bash" ? bash : ps;
  });
  bindTabs(panel, ".tray-panel-tabs .tab", ".tray-code");
  bindCopy(panel);
}

function bindTray() {
  $("#trayClear")?.addEventListener("click", () => {
    const n = state.picks.length;
    state.picks = [];
    savePicks();
    $$(".card-pick").forEach((b) => {
      const path = b.closest(".card")?.dataset.skillPath;
      if (path) syncPickButton(b, path);
    });
    const sdPick = $(".sd-pick");
    if (sdPick?.dataset.path) syncPickButton(sdPick, sdPick.dataset.path, true);
    renderTray();
    showToast(`Cleared ${n} pick${n === 1 ? "" : "s"}`);
  });

  $("#trayOpen")?.addEventListener("click", () => {
    const panel = $("#trayPanel");
    const open = panel.hidden;
    panel.hidden = !open;
    $("#trayOpen").setAttribute("aria-expanded", open ? "true" : "false");
    $("#trayOpen").textContent = open ? "Hide the command" : "Get the command";
  });
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
  return state.selectedHarnesses.map((id) => HARNESSES.find((h) => h.id === id)).filter(Boolean);
}

function installCommands(skill, repo, branch) {
  const { install_path: ip, name } = skill;
  const raw = `https://raw.githubusercontent.com/${repo}/${branch}`;
  const harnesses = activeHarnesses();

  const bash = harnesses
    .map((h) => `curl -fsSL ${raw}/install.sh \\\n  | bash -s -- ${ip} -d ${h.destBash(name)}`)
    .join("\n");
  const ps = harnesses
    .map((h) => `& ([scriptblock]::Create((irm ${raw}/install.ps1))) ${ip} -Dest ${h.destPs(name)}`)
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
    el.innerHTML = `<svg viewBox="0 0 16 16" width="11" height="11" fill="currentColor" aria-hidden="true"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/></svg>${formatStars(stars)}`;
    el.classList.add("is-loaded");
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
  state.filterRoute = null;
  syncRouteButtons();
  syncCategoryButtons();
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
  $("#browse")?.scrollIntoView({ behavior: "smooth", block: "start" });
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
  const bar = $("#harnessBar");
  if (!bar) return;
  bar.innerHTML = HARNESSES.map((h) => {
    const on = state.selectedHarnesses.includes(h.id);
    return `<button class="harness${on ? " active" : ""}" type="button"
             data-harness-id="${h.id}" aria-pressed="${on ? "true" : "false"}"
             title="Install paths for ${escapeHtml(h.label)}">${escapeHtml(h.label)}</button>`;
  }).join("");

  bar.addEventListener("click", (e) => {
    const btn = e.target.closest(".harness");
    if (!btn) return;
    const id = btn.dataset.harnessId;
    const idx = state.selectedHarnesses.indexOf(id);
    if (idx === -1) {
      state.selectedHarnesses.push(id);
    } else if (state.selectedHarnesses.length > 1) {
      state.selectedHarnesses.splice(idx, 1);
    } else {
      showToast("Keep at least one tool selected — the commands need a destination.");
      return;
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
  updateAnatomy(currentAnatomyKind());
  if (state.picks.length) renderTrayCommand();
  refreshOpenDetailInstall();
  window.skillsBrowser.selectedHarnesses = [...state.selectedHarnesses];
}

/* ==========================================================================
   URL State — share by link
   ========================================================================== */

function updateUrl() {
  const params = new URLSearchParams();
  if (state.filterCategory) params.set("cat", state.filterCategory);
  if (state.filterRoute) params.set("route", state.filterRoute);
  if (state.filterText) params.set("q", state.filterText);
  if (state.recommendedSkillNames?.length) {
    const paths = state.recommendedSkillNames.map((name) => {
      const s = state.manifest?.skills.find((sk) => sk.name === name);
      return s?.install_path ?? name;
    });
    params.set("skills", paths.join(","));
  }
  const qs = params.toString();
  history.replaceState(null, "", qs ? `${location.pathname}?${qs}` : location.pathname);
}

function applyUrlState() {
  const params = new URLSearchParams(location.search);
  const catParam = params.get("cat");
  const routeParam = params.get("route");
  const qParam = params.get("q");
  const skillParam = params.get("skill");
  const skillsParam = params.get("skills");

  if (routeParam && routeById(routeParam)) {
    state.filterRoute = routeParam;
    syncRouteButtons();
  }

  if (catParam && state.manifest.categories.includes(catParam)) {
    state.filterCategory = catParam;
    state.filterRoute = null;
    syncRouteButtons();
    syncCategoryButtons();
  }

  if (skillsParam) {
    const paths = skillsParam.split(",").map((s) => s.trim()).filter(Boolean);
    if (filterToSkills(paths)) return;
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
    $("#searchClear")?.classList.remove("hidden");
  }

  render();

  if (skillParam) {
    const skill = findSkill(skillParam);
    if (skill) {
      setTimeout(() => {
        $("#browse")?.scrollIntoView({ behavior: "smooth", block: "start" });
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
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("visible");
  clearTimeout(toast._toastTimer);
  toast._toastTimer = setTimeout(() => toast.classList.remove("visible"), 2600);
}

async function copyShareUrl(url) {
  const ok = await copyText(url);
  showToast(ok ? "Link copied — it reopens this exact view" : COPY_FALLBACK_HINT);
}

function getSkillShareUrl(skill) {
  return `${location.origin}${location.pathname}?skill=${encodeURIComponent(skill.install_path)}`;
}

/* ==========================================================================
   Page title
   ========================================================================== */

function updatePageTitle() {
  let title = "Skills — Agent Skills for Claude Code, Cursor, Copilot & More";
  if (state.filterCategory) {
    title = `${categoryLabel(state.filterCategory)} — Skills`;
  } else if (state.filterRoute) {
    title = `${routeById(state.filterRoute)?.label ?? ""} — Skills`;
  } else if (state.filterText) {
    title = `"${state.filterText}" — Skills`;
  } else if (state.recommendedSkillNames?.length) {
    title = `${state.recommendedSkillNames.length} recommended skills — Skills`;
  }
  document.title = title;
}


// Category slugs render as display labels in several places. Naive
// slug.replace(/-/g," ") plus CSS text-transform:capitalize produced "Api
// Backend", "Cloud Aws", "Llm Tooling" — so casing is resolved here instead and
// the CSS transform is off.
const CATEGORY_ACRONYMS = {
  api: "API", aws: "AWS", ui: "UI", ux: "UX", llm: "LLM", mcp: "MCP",
  ai: "AI", seo: "SEO", qa: "QA", devops: "DevOps", dotnet: ".NET",
};
const CATEGORY_MINOR_WORDS = new Set(["and", "to", "of", "for"]);

// `lower` keeps the quieter all-lowercase tag style used on cards while still
// letting acronyms through as "cloud AWS" rather than "cloud aws".
function categoryLabel(slug, { lower = false } = {}) {
  if (!slug) return "";
  if (slug === "all") return "All";
  return slug
    .split("-")
    .map((word, i) => {
      const key = word.toLowerCase();
      if (CATEGORY_ACRONYMS[key]) return CATEGORY_ACRONYMS[key];
      if (lower) return key;
      if (i > 0 && CATEGORY_MINOR_WORDS.has(key)) return key;
      return key.charAt(0).toUpperCase() + key.slice(1);
    })
    .join(" ");
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
   Skill Detail Panel — the card's primary action lands here
   ========================================================================== */

const sdCache = new Map();
let sdReturnFocus = null;
let sdSkill = null;

function openSkillDetail(skill) {
  const panel = document.getElementById("skillDetail");
  if (!panel) return;

  sdSkill = skill;
  sdReturnFocus = document.activeElement;

  const { repo, default_branch } = state.manifest;

  const nameEl = panel.querySelector(".sd-name");
  const catEl = panel.querySelector(".sd-cat-badge");
  const ghLink = panel.querySelector(".sd-gh-link");
  if (nameEl) nameEl.textContent = skill.name;
  if (catEl) {
    catEl.textContent = categoryLabel(skill.category);
    catEl.dataset.catColor = state.catColor.get(skill.category) ?? 0;
  }
  if (ghLink) ghLink.href = `https://github.com/${repo}/blob/${default_branch}/${skill.path}/SKILL.md`;

  renderDetailInstall(skill, repo, default_branch);

  const contentEl = panel.querySelector(".sd-content");
  const filesEl = panel.querySelector(".sd-files");
  if (contentEl) contentEl.innerHTML = sdLoadingHtml();
  if (filesEl) filesEl.innerHTML = "";

  panel.setAttribute("aria-hidden", "false");
  panel.classList.add("open");
  document.getElementById("skillDetailOverlay")?.classList.add("visible");
  document.body.classList.add("sd-open");
  // Focus the close button rather than the panel: it is the reliable escape,
  // and it puts the keyboard user at the start of the panel's tab order.
  panel.querySelector("#skillDetailClose")?.focus();

  fetchSkillDetail(skill, repo, default_branch);
}

function renderDetailInstall(skill, repo, branch) {
  const panel = document.getElementById("skillDetail");
  const variants = installCommands(skill, repo, branch);
  panel.querySelectorAll(".sd-install-code").forEach((pre) => {
    pre.querySelector("code").textContent = variants[pre.dataset.variant] ?? "";
  });

  const pick = panel.querySelector(".sd-pick");
  if (pick) {
    pick.dataset.path = skill.install_path;
    syncPickButton(pick, skill.install_path, true);
  }

  const dl = panel.querySelector(".sd-download");
  const dlSize = panel.querySelector(".sd-download-size");
  const zip = state.zips?.skills?.[skill.install_path];
  if (zip) {
    dl.href = zipHref(zip);
    dl.setAttribute("download", `${skill.name}.zip`);
    dl.removeAttribute("target");
    dlSize.textContent = `· ${formatBytes(zip.bytes)}`;
    dl.title = `Download ${skill.name} as a .zip`;
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

  bindTabs(panel, ".sd-install-tabs .tab", ".sd-install-code");
  bindCopy(panel.querySelector(".sd-install"));
}

// Harness changes rewrite every install path, so an open panel has to catch up.
function refreshOpenDetailInstall() {
  const panel = document.getElementById("skillDetail");
  if (!panel?.classList.contains("open") || !sdSkill) return;
  renderDetailInstall(sdSkill, state.manifest.repo, state.manifest.default_branch);
}

function closeSkillDetail() {
  const panel = document.getElementById("skillDetail");
  if (!panel) return;
  panel.setAttribute("aria-hidden", "true");
  panel.classList.remove("open");
  document.getElementById("skillDetailOverlay")?.classList.remove("visible");
  document.body.classList.remove("sd-open");
  // Return focus to whatever opened the panel so the keyboard position in the
  // grid is not lost.
  if (sdReturnFocus?.isConnected) sdReturnFocus.focus({ preventScroll: true });
  sdReturnFocus = null;
  sdSkill = null;
}

function bindSkillDetail() {
  const panel = document.getElementById("skillDetail");
  document.getElementById("skillDetailClose")?.addEventListener("click", closeSkillDetail);
  document.getElementById("skillDetailOverlay")?.addEventListener("click", closeSkillDetail);

  panel?.querySelector(".sd-pick")?.addEventListener("click", (e) => {
    const path = e.currentTarget.dataset.path;
    if (path) togglePick(path);
  });

  panel?.querySelector(".sd-share")?.addEventListener("click", () => {
    if (sdSkill) copyShareUrl(getSkillShareUrl(sdSkill));
  });

  document.addEventListener("keydown", (e) => {
    if (!panel?.classList.contains("open")) return;
    if (e.key === "Escape") {
      closeSkillDetail();
      return;
    }
    // The panel is aria-modal; keep Tab inside it.
    if (e.key !== "Tab") return;
    const f = [...panel.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), textarea, select, [tabindex]:not([tabindex="-1"])'
    )].filter((el) => el.offsetParent !== null);
    if (!f.length) return;
    const first = f[0];
    const last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
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
