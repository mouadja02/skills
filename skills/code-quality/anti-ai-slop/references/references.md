# References — Source Citations

All patterns in this skill are derived from direct inspection of pre-2020 (and still-hand-curated post-2020) reference repos. Below is the complete list of sources, with the file paths and line numbers used in the research.

## Python repositories

### `psf/requests`
- `README.md` — opening line, brevity, "Cloning the repository" section
- `HISTORY.md` — category-prefixed changelog format with PR references
- `setup.py` — 6-line file delegating to `pyproject.toml`
- `src/requests/api.py` — `request()`, `get()`, `head()` with no type hints, asymmetric design, `kwargs.setdefault('allow_redirects', ...)` pattern, sub-banner "HTTP for humans."
- `src/requests/models.py` — `PreparedRequest.copy()` with no docstring; `_get_idna_encoded_host()` with local `import idna`; `import encodings.idna  # noqa: F401` with operational comment; comment citing issue #3578; `data.setter` with comment citing issue #16464

### `pallets/flask`
- `README.md` — opening line, brevity, three-sentence description
- `pyproject.toml` — `name = "Flask"` TitleCase, `version = "3.2.0.dev"`, `description = "A simple framework for building complex web applications."`, `[tool.tox]` block, `[tool.codespell]` ignore-words
- `CHANGES.rst` — `:issue:` and `:pr:` reference style
- `LICENSE.txt` — BSD-3-Clause with Pallets copyright preamble
- `src/flask/app.py` — `Flask.__init__` with Sphinx-style docstring; `Flask.add_url_rule`; weakref comment citing issue #3761; "if we provide automatic options" comment
- `docs/quickstart.rst` — code-first tutorial, "Why would you want to build URLs" rhetorical question, `.. warning::` block
- `tests/test_basic.py` — `test_options_work`, `test_method_route_no_methods` with `pytest.raises(TypeError)`, `random_uuid4` hardcoded for reproducibility, comment citing issue #1288

### `pytest-dev/pytest`
- `README.rst` — two-sentence abstract, 4-line code example, Features list
- `doc/en/getting-started.rst` — numbered steps with code blocks, no "Welcome to pytest!"
- `CHANGELOG.rst` — `.. _pytest-X.Y.Z:` anchors, `---` underline for sub-sections
- `testing/python/metafunc.py` — `test_parametrize_single_arg_trailing_comma` with docstring linking to issue #719; docstring literally `"#351"`; `assert metafunc._calls[0].params == ...` style

### `sqlalchemy/sqlalchemy`
- `README.rst` — title is "The Python SQL Toolkit and Object Relational Mapper"
- `lib/sqlalchemy/orm/session.py` — `Session._take_snapshot()` with no docstring on internal method; `assert parent is not None` for type narrowing; early-return pattern; `weakref.WeakKeyDictionary()` usage; `_is_transaction_boundary` and `is_begin` local variable pattern

### `pydantic/pydantic`
- `README.md` — "Data validation using Python type hints."

### `Textualize/rich`
- `README.md` — "Rich is a Python library for *rich* text and beautiful formatting in the terminal." (italics on "rich")
- `rich/console.py` — Google-style docstrings

### `encode/httpx`
- `README.md` — "HTTPX is a fully featured HTTP client library for Python 3."
- `httpx/_client.py` — `_redirect_headers()` with typo "If we've switch to a 'GET'", `import idna` (or equivalent local import pattern), docstrings that explain *why* strip headers; PEP 585 generics in type hints

### `django/django`
- `README.rst` — "Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. Thanks for checking it out."
- `docs/topics/db/models.txt` — calm expert voice: "A model is the single, definitive source of information about your data..."

### `celery/celery`
- `README.rst` — short, code-first

### `python/cpython`
- `LICENSE` — PSF copyright
- `Lib/urllib/request.py:97` — `raise ValueError("proxy URL with no authority: %r" % proxy)`
- `Lib/urllib/request.py:99` — `urlopen()` signature with `*, cafile=None, capath=None, cadefault=False, context=None`
- `Lib/urllib/request.py:108` — `i = meth.find("_"); protocol = meth[:i]; condition = meth[i+1:]` (string parsing for protocol_action dispatch)
- `Lib/urllib/request.py:119` — `for meth in dir(handler): if meth in [...]: # oops, coincidental match`
- `Lib/urllib/request.py:130` — `def request_host(request):` with 4 `host` assignments
- `Lib/urllib/request.py:165` — comment "By using the 'with' statement we are sure the session is closed..."
- `Lib/urllib/request.py:191` — RFC 2616 trade-off comment
- `Lib/urllib/request.py:341` — `def __init__(self, url, data=None, headers={}, ...)` (mutable default bug, year-2002 timestamp)
- `Lib/urllib/request.py:392` — `@data.setter` with comment citing issue #16464
- `Lib/urllib/request.py:441` — `assert hasattr(proxies, 'keys'), "proxies must be a mapping"` (assert for internal invariant)
- `Lib/urllib/request.py:521` — `class HTTPRedirectHandler(BaseHandler): max_repeats = 4; max_redirections = 10` (class attrs with operational comments)
- `Lib/urllib/request.py:621` — `add_password` mutating `self.passwd` directly
- `Lib/urllib/request.py:932` — `get_algorithm_impls` with `H = lambda x: hashlib.md5(x.encode("ascii")).hexdigest()` and `KD = lambda s, d: H("%s:%s" % (s, d))`
- `Lib/urllib/request.py:1079` — `HTTPCookieProcessor.__init__` with local `import http.cookiejar`
- `Lib/urllib/request.py:1183` — `add_handler` with hasattr boundary check
- `Lib/urllib/request.py:2096` — `try: try: ...; except OSError as err: raise URLError(err); ...; except: h.close(); raise` (nuclear cleanup pattern)
- `Lib/collections/__init__.py:96` — `class _Link(object): __slots__ = 'prev', 'next', 'key', '__weakref__'`
- `Lib/collections/__init__.py:391` — `def __len__(self): return len(set().union(*self.maps)) # reuses stored hash values if possible`
- `Lib/collections/__init__.py:415` — `def replace(self, old, new, maxsplit=-1):`
- `Lib/collections/__init__.py:444` — `def _count_elements(mapping, iterable):` with `mapping_get = mapping.get; for elem in iterable: mapping[elem] = mapping_get(elem, 0) + 1`

## C / Systems

### `torvalds/linux`
- `README` — the "Linus voice" reference
- `Documentation/process/coding-style.rst:9-31` — "Tabs are 8 characters"
- `Documentation/process/coding-style.rst:121-145` — K&R braces for control flow, opening brace on its own line for functions
- `Documentation/process/coding-style.rst:181` — "Unlike Modula-2 and Pascal programmers, C programmers do not use cute names like ThisVariableIsATemporaryCounter"
- `Documentation/process/coding-style.rst:189` — "Encoding the type of a function into the name (so-called Hungarian notation) is asinine"
- `Documentation/process/coding-style.rst:199-205` — `*` adjacent to name: `char *linux_banner;`
- `Documentation/process/coding-style.rst:241-251` — "Please don't use things like `vps_t`"
- `Documentation/process/coding-style.rst:415-435` — "Functions should be short and sweet, and do just one thing"
- `Documentation/process/coding-style.rst:454-481` — `goto` for centralized cleanup
- `Documentation/process/coding-style.rst:512-528` — "Comments say WHAT, not HOW"
- `Documentation/process/coding-style.rst:535-544` — kernel multi-line comment style
- `Documentation/process/coding-style.rst:700-723` — action-or-predicate rule for function return values
- `Documentation/process/coding-style.rst:783-790` — "Do not use incorrect contractions like `dont`"; "Kernel messages do not have to be terminated with a period"
- `Documentation/process/submitting-patches.rst:113-115` — "Describe your changes in imperative mood"
- `Documentation/process/submitting-patches.rst:130-138` — `lore.kernel.org` Message-ID links
- `Documentation/process/submitting-patches.rst:140-148` — sign-off tags
- `Documentation/process/submitting-patches.rst:269-292` — top-posting exchange
- `Documentation/process/submitting-patches.rst:354-360` — DCO text
- `Documentation/process/submitting-patches.rst:404-430` — `Reviewed-by:`, `Tested-by:`, etc.
- `Documentation/process/submitting-patches.rst:436-441` — `Assisted-by:` (added 2024)
- `Documentation/process/submitting-patches.rst:475-486` — `[PATCH N/M] subsystem: summary` subject
- `Documentation/process/submitting-patches.rst:520-538` — 70–75 char subject, no period
- `Documentation/process/submitting-patches.rst:564-565` — body wrapped at 75 columns
- `Documentation/process/submitting-patches.rst:626-642` — `---` separator

### `git/git`
- `README.md:3` — "Git is a fast, scalable, distributed revision control system with an unusually rich command set that provides both high-level operations and full access to internals."
- `README.md:53-65` — "The name 'git' was given by Linus Torvalds..." with the four-bullet etymology

### `curl/curl`
- `README` + `Readme.md` — long format-specs-list description (27 protocols)
- `COPYING` (license filename)
- `CHANGES.md` + `RELEASE-NOTES`
- `.circleci/` (CI)

### `redis/redis`
- `README.md`
- `00-RELEASENOTES` (changelog filename)
- `LICENSE.txt`
- `CONTRIBUTING.md` with embedded Redis Software Grant (CLA)

### `jqlang/jq`
- `README` and source — error format `jq: error: <message>`

## Go

### `golang/go`
- `README.md` — "Go is an open source programming language that makes it easy to build simple, reliable, and efficient software."
- `LICENSE` + `PATENTS` (dual files)
- `src/net/http/server.go` — `conn` struct with `// server is the server on which the connection arrived. // Immutable; never nil.`; `readRequest` with early returns; `connReader.backgroundRead` with "apt-get does" comment; package error format

### `kubernetes/kubernetes`
- `README.md` — "Production-Grade Container Scheduling and Management"
- `OWNERS` + `OWNERS_ALIASES` (Linux Foundation convention)
- `CHANGELOG.md`

### `prometheus/prometheus`
- `README.md` and source

### `hashicorp/terraform`
- `README.md` and source

### `gohugoio/hugo`
- `README.md`, `go.mod` with full dependency list

### `junegunn/fzf`
- `README.md` — `make` to install, plain `Highlights` section

### `spf13/cobra`
- `README.md:71-80` — "Commands represent actions, Args are things and Flags are modifiers..."

### `moby/moby`
- `README.md:21-30` — "Modular", "Batteries included but swappable", "Usable security", "Developer focused"

### `fatedier/frp`
- `README.md` — "frp is currently under development. You can try the latest release version in the `master` branch..."

## JavaScript / TypeScript

### `expressjs/express`
- `Readme.md` — "Fast, unopinionated, minimalist web framework for [Node.js](https://nodejs.org)."
- `lib/application.js:9-23` — `var finalhandler = require('finalhandler'); ...` (CommonJS, no TypeScript)
- `lib/application.js:36` — `app.init = function init() {`
- `lib/application.js:46` — `if (env === 'production') { this.enable('view cache'); }` (strict equality)
- `lib/application.js:71` — `this.cache = {}; this.engines = {}; ...`
- `lib/application.js:172` — `app.set = function set(setting, val) { if (arguments.length === 1) { return this.settings[setting]; } }` (overload)
- `lib/application.js:222` — `app.del = deprecate.function(app.delete, 'app.del: Use app.delete instead');` (one-liner)
- `package.json` — pre-2020 minimal

### `tj/n`
- `package.json` — `description: "Interactively Manage Your Node.js Versions"`, `files: ["bin/n"]`, `os: ["!win32"]`, `preferGlobal: true`
- `README.md`

### `tj/commander.js`
- `package.json` — `description: "The complete solution for node.js command-line interfaces."`
- `Readme.md`

### `sindresorhus/*` (especially `got`, `awesome`, `ky`)
- `package.json` + `readme.md` + GitHub About — same description repeated in all three places
- `keywords` includes competitor names

### `microsoft/TypeScript`
- `README.md:1` — `<!-- CODING AGENTS: READ AGENTS.md BEFORE WRITING CODE -->` (post-2024 anti-agent)
- `README.md:11-15` — installation, "Contribute" with explicit PR-type list

### `withastro/astro`
- `README.md:1-13` — banner image, "Build the web you want" tagline

### `remix-run/remix`
- `README.md:12-29` — "Welcome to Remix 3!" with numbered principles

### `vuejs/core`
- `README.md` — delegates to vuejs.org
- `.github/contributing.md` — conventional commits enforced by simple-git-hooks

### `lodash/lodash`
- `README.md:1-15` — minimal install instructions, no "Why Lodash?" essay

### `prettier/prettier`
- `README.md:31-43` — `### Input` / `### Output` pattern with code blocks

## Rust

### `burntsushi/ripgrep`
- `README.md:1` — "ripgrep is a line-oriented search tool..."
- `README.md` — "Why should I use ripgrep?" and "Why shouldn't I use ripgrep?" sections
- `GUIDE.md` — full guide
- `CHANGELOG.md` — `TBD` at top of unreleased; `[BUG #NNNN]` prefix tags; `15.0.0 (2025-10-15)` format
- `Cargo.toml` with `LICENSE-APACHE` + `LICENSE-MIT`

### `dtolnay/serde`
- `README.md` — "Serde is a framework for *ser*ializing and *de*serializing Rust data structures efficiently and generically." (italics on ser/de)
- "Getting help" section with the human admission: "It's acceptable to file a support issue in this repo but they tend not to get as many eyes..."

### `tokio-rs/tokio`
- `README.md:121-145` — LTS section with dates
- `Cargo.toml` — `rust-version = "1.71"`, technical keywords

### `clap-rs/clap`
- `README.md:1-22` — single-screen README, dual-licensed

### `rust-lang/rust`
- `LICENSE-APACHE` + `LICENSE-MIT`
- `RELEASES.md`
- `x.py` (custom build system)

### `dtolnay/thiserror`, `rust-lang/cargo`
- Real-world error patterns

## Methodology notes

1. **Source selection.** Repos were chosen to span (a) languages (Python, Go, JS/TS, Rust, C), (b) eras (pre-2015, 2015–2019, post-2020 still hand-curated), and (c) project types (libraries, frameworks, CLIs, databases, kernels, language tooling).

2. **What "pre-2020" means.** Most quoted code is from before 2020 to avoid AI-influenced patterns. Where a 2024+ repo maintains a hand-curated style (ripgrep, serde, tokio, curl), it was included as a "still human" reference.

3. **The AI tells were derived by comparison.** For each "AI pattern" listed, the corresponding "human pattern" was extracted from a real pre-2020 file at a specific line number. This is forensic, not aspirational.

4. **Edge cases.** Some 2024+ repos have AI-influenced READMEs (Astro, Ant Design with emoji). They are flagged as "not the pre-2020 baseline" and *not* used as human references. The pre-2020 repos are the target style.

5. **The "Linus voice."** Linux kernel `coding-style.rst` and `submitting-patches.rst` are the gold-standard reference documents for code style and commit messages respectively. They are quoted at length because the kernel is the largest, longest-running, and most closely-reviewed open source project in history.

## Verification

To verify any claim in this skill, fetch the cited file and check the line. For example, to verify the "We have HTTP for humans" sub-banner in `psf/requests`:

```
https://raw.githubusercontent.com/psf/requests/main/README.md
```

To verify the Linux kernel style guide on tabs:

```
https://raw.githubusercontent.com/torvalds/linux/master/Documentation/process/coding-style.rst
```

To verify the kernel commit-message convention:

```
https://raw.githubusercontent.com/torvalds/linux/master/Documentation/process/submitting-patches.rst
```

To verify the ripgrep "Why shouldn't I use ripgrep?" section:

```
https://raw.githubusercontent.com/BurntSushi/ripgrep/master/README.md
```

To verify the curl 27-protocols description:

```
https://raw.githubusercontent.com/curl/curl/master/README.md
```

To verify the git "name was given by Linus" etymology:

```
https://raw.githubusercontent.com/git/git/master/README.md
```

To verify the Flask `pyproject.toml`:

```
https://raw.githubusercontent.com/pallets/flask/main/pyproject.toml
```

To verify the `psf/requests` `setup.py` (6 lines):

```
https://raw.githubusercontent.com/psf/requests/main/setup.py
```

To verify the Express `package.json` (pre-2020 minimal):

```
https://raw.githubusercontent.com/expressjs/express/4.18.2/package.json
```
