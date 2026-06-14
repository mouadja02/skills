# Prose — Human Voice Catalog

The voice patterns for READMEs, docs, commit messages, changelogs, tutorials, and any other prose. All examples are real, quoted from the pre-2020 reference repos in the research.

## The opening line

The single biggest tell. The opening sentence of a README, a tutorial, a doc page, or a `description` field is almost always a *minimal, plain definition*. No adjectives, no value proposition, no "we are excited to announce."

### Real openings, verbatim

| Source | Opening |
|---|---|
| `psf/requests` | `**Requests** is a simple, yet elegant, HTTP library.` |
| `pallets/flask` | `Flask is a lightweight WSGI web application framework. It is designed to make getting started quick and easy, with the ability to scale up to complex applications.` |
| `pydantic/pydantic` | `Data validation using Python type hints.` |
| `Textualize/rich` | `Rich is a Python library for *rich* text and beautiful formatting in the terminal.` |
| `encode/httpx` | `HTTPX is a fully featured HTTP client library for Python 3.` |
| `sqlalchemy/sqlalchemy` | `The Python SQL Toolkit and Object Relational Mapper` |
| `django/django` | `Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. Thanks for checking it out.` |
| `burntsushi/ripgrep` | `ripgrep is a line-oriented search tool that recursively searches the current directory for a regex pattern.` |
| `dtolnay/serde` | `Serde is a framework for *ser*ializing and *de*serializing Rust data structures efficiently and generically.` |
| `tokio-rs/tokio` | `A runtime for writing reliable, asynchronous, and slim applications with the Rust programming language.` |
| `git/git` | `Git is a fast, scalable, distributed revision control system with an unusually rich command set that provides both high-level operations and full access to internals.` |
| `golang/go` | `Go is an open source programming language that makes it easy to build simple, reliable, and efficient software.` |
| `expressjs/express` | `Fast, unopinionated, minimalist web framework for node.` |
| `tj/n` | `Node version management` |
| `tj/commander.js` | `The complete solution for node.js command-line interfaces.` |
| `psf/requests` (sub-banner) | `HTTP for humans.` |
| `django/django` (famous tagline) | `The Web framework for perfectionists with deadlines.` |
| `sindresorhus/got` | `🌐 Human-friendly and powerful HTTP request library for Node.js` |
| `curl/curl` | `A command line tool and library for transferring data with URL syntax, supporting DICT, FILE, FTP, FTPS, GOPHER, GOPHERS, HTTP, HTTPS, IMAP, IMAPS, LDAP, LDAPS, MQTT, MQTTS, POP3, POP3S, RTSP, SCP, SFTP, SMB, SMBS, SMTP, SMTPS, TELNET, TFTP, WS and WSS.` |

The curl one is the gem: 27 protocols listed because that's what curl actually does. The point isn't the length — the point is that it serves a real purpose.

### AI openings to avoid

> `Welcome to **FastApp**, a cutting-edge, lightning-fast Python framework that empowers developers to seamlessly build modern web applications. Whether you're a seasoned developer or just starting out, FastApp is designed to streamline your workflow and revolutionize the way you think about web development.`

Three adjectives stacked (`cutting-edge, lightning-fast, modern`), two filler verbs (`empowers`, `streamline`), one value claim (`revolutionize the way you think about`), and an explicit "whether you're a beginner" hedge. Six tells in one sentence.

## The description field

The `description` in `pyproject.toml` / `package.json` / Cargo.toml / GitHub About is the single most AI-slop-prone field. The pre-2020 pattern is brutally short.

### Templates by project type

**Library:**
- `[Noun] is a [adjective] [category] for [purpose].` — `pallets/flask: A simple framework for building complex web applications.`
- `[Noun] is a [adjective] [category].` — `psf/requests: A simple, yet elegant, HTTP library.`
- `A [adjective] [category].` — `pydantic: Data validation using Python type hints.`

**CLI:**
- `[Verb] [noun] in/from [place].` — `ripgrep README: rg recursively searches the current directory for a regex pattern.`
- `[Noun] version management` — `tj/n: Node version management`
- `[Tool] is a [adjective] [category] for [purpose].` — `jq: jq is a lightweight and flexible command-line JSON processor.`

**Framework:**
- `[Noun] is a [adjective] [category] that [verb] [purpose].` — `Django README: Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design.`
- `Fast, unopinionated, minimalist web framework for [runtime].` — `express: Fast, unopinionated, minimalist web framework for node.`

**Compiler / runtime:**
- `[Name] is an open source [category] that [verb] [purpose].` — `golang/go: Go is an open source programming language that makes it easy to build simple, reliable, and efficient software.`

**System / daemon:**
- `[Name] is a [category] for [purpose].` — `redis/redis (paraphrase): Redis is an in-memory data structure store used as a database, cache, and message broker.`

**Database / storage:**
- `[Name] is the [adjective] [category].` — `postgres/postgres: PostgreSQL is a powerful, open source object-relational database system.`

**Rust crate:**
- `[Name] is a [category] for [purpose].` — `serde: Serde is a framework for *ser*ializing and *de*serializing Rust data structures efficiently and generically.`

## The section header

### Banned emoji headers

Real repos use **zero emojis in titles or section headers**. Strip these:

- `## ✨ Features` → `## Features`
- `## 🚀 Quick Start` → `## Install` or `## Getting started`
- `## 📚 Documentation` → `## Documentation`
- `## 🤝 Contributing` → `## Contributing`
- `## 💡 Examples` → `## Examples`
- `## 🛠️ Installation` → `## Install`
- `## 🎉 Get Started` → `## Getting started`
- `## ❤️ Sponsors` → `## Sponsors`
- `## ⚡ Performance` → `## Performance`
- `## 🔒 Security` → `## Security`
- `## 🌟 Showcase` → `## Showcase` or delete
- `## 🔧 Configuration` → `## Configuration` or `## Options`

### Real section header patterns

Plain prose headers, sometimes with question marks for tone:

- `## Why Sinatra?` — `sinatra/sinatra` (a question header; the section answers "we think it's the right size")
- `## Highlights` — `junegunn/fzf`
- `## Feature highlights` — `libuv/libuv`
- `## Why should I use ripgrep?` — `burntsushi/ripgrep` (and `## Why shouldn't I use ripgrep?` — the gem)
- `## What about ... ?` — common in compiler docs
- `## Don't do X` — common in guides (real `## Don't use tabs` headers in kernel docs)
- `## Cloning the repository` — `psf/requests` (the "I hit this, you will too" section)

The "Why should I use X?" **and** "Why shouldn't I use X?" pair is a strong human signal. The maintainer is telling you when their tool is the wrong choice. AI never does this.

## The voice — by project era and style

### The "Linus voice" — direct, opinionated, occasionally profane

From `linux/Documentation/process/coding-style.rst`:

> First off, I'd suggest printing out a copy of the GNU coding standards, and NOT read it. Burn them, it's a great symbolic gesture.

The kernel `submitting-patches.rst` ends with a quote exchange about top-posting that's dry and lore-rich:

> A: Because it messes up the order in which people normally read text.
> Q: Why is top-posting such a bad thing?
> A: Top-posting.
> Q: What is the most annoying thing in e-mail?

### The "antirez voice" — Italian-influenced English, technical confidence

From `redis/redis` README and commits, the maintainer writes confidently about tradeoffs, doesn't hedge, sometimes poetic. Real maintainers have a face.

### The "DHH voice" — opinionated, slogan-y

> `The Web framework for perfectionists with deadlines.`

The slogan is the whole point. Real slogans are *short, surprising, and take a stance*.

### The "Sindre Sorhus voice" — one phrase, repeated everywhere

In `sindresorhus/got/package.json` and `readme.md` and the GitHub About, the description is **identical**:

> `🌐 Human-friendly and powerful HTTP request library for Node.js`

Sindre repeats the same description in three places. The emoji is a single `🌐` and it's a personal signature, not decoration.

### The "TJ Holowaychuk voice" — minimal, pre-2015

TJ-era repos had no `description` field at all in many cases. His best repos have one-line About sections or no description. The "tone" was implicit — the code spoke.

### The "Linus style" git README

From `git/git/README.md`:

> The name "git" was given by Linus Torvalds when he wrote the very first version. He described the tool as "the stupid content tracker" and the name as (depending on your mood):
> - random three-letter combination that is pronounceable, and not actually used by any common UNIX command.
> - stupid. contemptible and despicable. simple. Take your pick from the dictionary of slang.
> - "global information tracker": you're in a good mood, and it actually works for you. Angels sing, and a light suddenly fills the room.
> - "goddamn idiotic truckload of sh*t": when it breaks

This is *unmistakably* human. The bullet item "when it breaks" with the "goddamn idiotic truckload of sh*t" expansion is the maintainer's sense of humor. AI never writes this.

## The error message

| Source | Error message |
|---|---|
| `cpython@3.8.0/Lib/urllib/request.py:97` | `raise ValueError("proxy URL with no authority: %r" % proxy)` |
| `pallets/flask` | `"'static_folder' must be set to serve static_files."` (RuntimeError) |
| `pallets/flask` | `"Resources can only be opened for reading."` (ValueError) |
| `encode/httpx` | `"Cannot send a request, as the client has been closed."` (RuntimeError) |
| `encode/httpx` | `"Invalid 'auth' argument: ..."` (TypeError) |
| `psf/requests` | `"Invalid URL {url!r}: No scheme supplied. Perhaps you meant https://{url}?"` |
| `sqlalchemy/sqlalchemy` | `"Can't start a SAVEPOINT transaction when no existing transaction is in progress"` |
| `git` | `fatal: not a git repository` |
| `jq` | `jq: error: <message>` |

### The rules

- **Lowercase first letter** (kernel convention, stdlib convention).
- **No trailing period** for short messages.
- **Include the actual value** with `repr()` or `%r`.
- **State the constraint, not the apology.** `"must be set to serve static_files"` is the constraint. `"please configure static_folder"` is the apology.
- **One line, one sentence.** If you can't fix it in 80 chars, you have two problems.
- **Suggest a fix only when obvious.** `Perhaps you meant https://{url}?` is allowed because the fix is mechanical. "Please contact support" is never allowed.

## The changelog entry

### Real pattern (from `psf/requests/HISTORY.md`)

```
2.32.0 (2024-05-20)
-------------------

**Security**
- Fixed an issue where setting `verify=False` on the first request...

**Improvements**
- `verify=True` now reuses a global SSLContext...

**Bugfixes**
- Fixed bug in length detection where emoji length was incorrectly...

**Deprecations**
- Requests has officially added support for CPython 3.12

**Documentation**
- Various typo fixes and doc improvements.
```

Every entry has a PR/issue number. Categories are stable across years. No emoji. No exclamations.

### Real pattern (from `pallets/flask/CHANGES.rst`)

```rst
- ``stream_with_context`` does not fail inside async views. :issue:`5774`
- When using ``follow_redirects`` in the test client, the final state
  of ``session`` is correct. :issue:`5786`
- Add new customization points to the ``Flask`` app object for many
  previously global behaviors.
  - ``flask.url_for`` will call ``app.url_for``. :issue:`4568`
```

Short verb-phrase title, optional bullet expansion, then `:issue:` or `:pr:` reference. No emoji. No "we are excited to announce."

### Real pattern (from `burntsushi/ripgrep/CHANGELOG.md`)

```md
15.0.0 (2025-10-15)
===================

ripgrep 15 is a new major version release of ripgrep that mostly has bug fixes,
some minor performance improvements and minor new features. Here are some
highlights:

* Several bugs around gitignore matching have been fixed.
* A memory usage regression when handling very large gitignore files has
  been fixed.
* `rg -vf file`, where `file` is empty, now matches everything.

Bug fixes:

* [BUG #3212](https://github.com/BurntSushi/ripgrep/pull/3212):
  Don't check for the existence of `.jj` when `--no-ignore` is used.
```

Lead paragraph summarizes the release. Bullet list of highlights. Categorized list with `[BUG #NNNN]` / `[FEATURE #NNNN]` / `[PERF #NNNN]` prefix tags. No emoji.

### Banned changelog patterns

- `## [2.0.0] - 2025-11-15 🎉` — no emoji, no `[version]`
- `### ✨ Exciting New Features` — no emoji, no "Exciting"
- `We are thrilled to introduce a brand new caching mechanism that will revolutionize performance!` — write `Added caching to Client.send. (#1234)`
- `Various improvements and bug fixes.` — empty calorie. Either list them or move on.

## The commit message

### Kernel convention (the gold standard)

From `linux/Documentation/process/submitting-patches.rst`:

- **Imperative mood.** "make xyzzy do frotz" not "This patch makes xyzzy do frotz".
- **70-75 char subject, no period.** Descriptive but not filename.
- **Body wrapped at 75 columns.**
- **`---` separator** after sign-off, before diffstat and patch changelog.
- **Sign-off tags:** `Signed-off-by:`, `Acked-by:`, `Co-developed-by:`, `Reported-by:`, `Tested-by:`, `Reviewed-by:`, `Suggested-by:`, `Fixes:`, `Link:`, `Closes:`, `Cc:`.
- **Reference SHA-1s with oneline summary**, never bare SHA. `Commit e21d2170f36602ae2708 ("video: remove unnecessary platform_set_drvdata()") removed the unnecessary platform_set_drvdata(), but left the variable "dev" unused, delete it.`
- **Use `lore.kernel.org` Message-ID links**, not mailinator/web links.
- **Don't top-post.** Use interleaved replies.
- **`Assisted-by:` tag** if you used any AI tool (added 2024 in the kernel).

### Conventional commits (the modern equivalent)

Vue uses conventional commits enforced by git hooks:

```
feat(http): add support for HTTP/2
fix(parser): handle empty request body
docs(readme): update installation instructions
chore(deps): bump axios to 1.6.0
```

The format is `<type>(<scope>): <description>`. Types are `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`, `revert`. Scopes are project-specific.

## The tutorial voice

### Flask's quickstart (the canonical human pattern)

The quickstart opens with code:

```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"
```

*Then* explains:

> So what did that code do?
> 1. First we imported the :class:`~flask.Flask` class...
> 2. Next we create an instance of this class...
> 3. We then use the :meth:`~flask.Flask.route` decorator...

**Show the code, then explain.** AI pattern: tell users what they're about to learn, *then* show the code.

### Pytest's getting started (terse, no narrative)

> 1. Run the following command in your command line:
>    ```
>    pip install -U pytest
>    ```
> 2. Check that you installed the correct version:
>    ```
>    $ pytest --version
>    pytest 9.1.0
>    ```

No "Welcome to pytest!". Numbered steps with code blocks. Done.

### The "What NOT to do" box

Real docs include warnings and admonitions. Flask uses `.. warning::` blocks:

```
.. warning::
    The debugger allows executing arbitrary Python code from the
    browser. It is protected by a pin, but still represents a major
    security risk. Do not run the development server or debugger in a
    production environment.
```

Django uses `.. admonition::` and `.. note::` blocks. These convey genuine, learned-from-experience warnings. The kernel uses `.. warning::` and `.. note::` too.

## Transformations

### 1. Library description

**Before (AI):**
> Welcome to **FastApp**, a cutting-edge, lightning-fast Python framework that empowers developers to seamlessly build modern web applications. Whether you're a seasoned developer or just starting out, FastApp is designed to streamline your workflow and revolutionize the way you think about web development.

**After (human):**
> `FastApp` is a web framework.
>
> ```python
> >>> from fastapp import FastApp
> >>> app = FastApp()
> >>> @app.route('/')
> ... def hello():
> ...     return 'Hello, World!'
> ```

### 2. Tutorial opening

**Before (AI):**
> ## 🚀 Introduction
>
> In this comprehensive guide, we will explore the powerful features and capabilities of **SuperLib**. Whether you're a beginner just starting your journey or an experienced developer looking to take your skills to the next level, this README has something for everyone. Let's dive in!

**After (human):**
> `SuperLib` validates JSON.
>
> ```python
> >>> from superlib import validate
> >>> validate('{"x": 1}')
> {'x': 1}
> ```

### 3. Feature section

**Before (AI):**
> ## ✨ Features
>
> - 🌈 Modern API design with full type safety
> - 📦 Zero-config setup — get started in seconds
> - 🛡️ Built-in security with state-of-the-art encryption
> - 🚀 Blazing fast performance
> - 💡 Intuitive developer experience

**After (human):**
> `SuperLib` reads JSON, validates against a schema, and returns a typed object. It does not do anything else.

### 4. Closing flourish

**Before (AI):**
> And there you have it! You've successfully built a robust API. 🎉
> Happy coding! 🚀

**After (human):**
> See `docs/advanced.md` for the full options.

### 5. Error message

**Before (AI):**
> `An unexpected error occurred while processing your request. Please ensure that you have provided a valid input and try again. If the problem persists, please don't hesitate to reach out to our support team for assistance.`

**After (human):**
> `ValueError: invalid input: ''`

### 6. Changelog entry

**Before (AI):**
> ## [2.0.0] - 2025-11-15 🎉
>
> ### ✨ Exciting New Features
>
> - 🚀 We are thrilled to introduce a brand new caching mechanism that will revolutionize performance!
> - 💡 We've enhanced the API with intuitive new methods for easier integration.
> - 🛡️ Security has been significantly improved with state-of-the-art encryption.

**After (human):**
> ```
> 2.0.0 (2025-11-15)
> -------------------
>
> - Added caching to `Client.send`. (#1234)
> - `Client.timeout` now accepts a float in seconds. (#1235)
> - Fixed race in connection pool that could cause `TooManyRedirects` on concurrent reuse. (#1236)
> - Dropped support for Python 3.8. (#1237)
> ```

### 7. PR description

**Before (AI):**
> This PR introduces a comprehensive enhancement to our caching infrastructure, leveraging cutting-edge algorithms to deliver blazing-fast performance and seamless integration. We've added robust error handling and a state-of-the-art invalidation strategy. Tests have been thoroughly updated to ensure reliability.

**After (human):**
> Cache the response body when the server returns `Cache-Control: max-age=N`.
>
> Adds `Client.cache_dir` and `Client.cache_ttl`. Falls back to disk if `/tmp` is full.
>
> Fixes #1234.

## Anti-pattern reference table

| Pattern | Where it appears | Replacement |
|---|---|---|
| `## 🚀 Quick Start` | AI READMEs | `## Install` |
| `## ✨ Features` | AI READMEs | `## Features` or just delete the header, the list is the section |
| `In this tutorial, we will...` | AI tutorials | Start with the code |
| `Let's dive in!` | AI openings | (delete) |
| `Whether you're a beginner or an expert` | AI READMEs | (delete; the user is the user) |
| `Happy coding!` | AI closings | (delete) |
| `leverage` | AI everywhere | `use` |
| `utilize` | AI everywhere | `use` |
| `facilitate` | AI everywhere | `help`, `let`, or (delete) |
| `in order to` | AI everywhere | `to` |
| `Furthermore, ...` | AI transitions | (delete or use `And` / `Also`) |
| `Moreover, ...` | AI transitions | (delete) |
| `It's important to note that ...` | AI filler | (state the thing directly) |
| `a wide range of` | AI filler | `many` |
| `a variety of` | AI filler | `many` |
| `numerous` | AI filler | `many` |
| `robust solution` | AI everywhere | name the property |
| `seamless integration` | AI everywhere | describe the actual integration |
| `cutting-edge` | AI everywhere | (delete) |
| `state-of-the-art` | AI everywhere | (delete) |
| `next-generation` | AI everywhere | `version 2` |
| `modern web` | AI everywhere | (delete) |
| `developer experience` | AI everywhere | (delete) |
| `production-grade` | AI everywhere | `in production at X, Y, Z` |
| `battle-tested` | AI everywhere | `in production since 2014` |
| `Please don't hesitate to reach out...` | AI error messages | (delete) |
| `We are thrilled to announce...` | AI changelogs | `Added X. (#1234)` |
| `And that's how easy it is!` | AI closings | (delete) |
| `# Issue #1288: ...` | AI comments | `# Issue 1288: ...` (no `#` after `Issue`) |
| `# Increment counter by 1` | AI comments | (delete) |
| `def calculate_total_price(items, tax_rate):` + 4-line docstring | AI everywhere | `def price(items, tax): return ...` |
| Stack of 4+ badges in the first 15 lines | AI READMEs | 4-8 badges max: build status, license, version, downloads |
| `Whether you're building X or Y, our tool is the perfect choice for...` | AI sales | (delete) |
| `If you have any questions, please feel free to open an issue` | AI closings | `Open an issue if you have questions.` |
| `Made with ❤️ by [Author]` | AI READMEs | `Author: [Name](link)` or just an authors list |
