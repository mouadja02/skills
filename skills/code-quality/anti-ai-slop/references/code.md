# Code — Per-Language Tells and Human Patterns

The forensic catalog of code-level signals that distinguish AI-generated code from human-written code. All examples are real, quoted from pre-2020 reference repos in the research: `cpython@3.8.0/Lib`, `requests@v2.20.0`, `express@4.16.0`, `go@1.13/src/net/http`, `ripgrep`, `serde`.

## Quick reference — the top tells

| Tell | Human | AI |
|---|---|---|
| Type hint density | 0–1 per file (`requests/api.py`) | 5–15 per file, `Optional[Any]` everywhere |
| Comment density | Sparse, explains *why* | Dense, paraphrases *what* |
| Variable names | Terse in small scopes (`i, n, p, k`) | Verbose, unique per state (`initial_host_value_without_port`) |
| Docstrings | One line, imperative ("Sends an email.") | Multi-paragraph, paraphrases function name |
| Error messages | One line, lowercase, includes the value | Multi-line, apologetic, suggests contacting support |
| Imports | Top-level unless reason not to | All top-level, breaking circular deps |
| Test names | `test_raises_on_empty_input` | `test_function_behavior` |
| `try/except` | Targeted, specific | Broad, swallows errors silently |
| Constants | Class attribute, lowercase, commented | `MAX_X = 3` SCREAMING_SNAKE wall |
| Defensive code | At boundaries, after-the-fact | Everywhere, preemptively |
| Walrus `:=` in conditionals | Rare | Frequent |
| `match` for simple chains | Rare | Frequent |
| f-strings in `logger.info` | Use `%s` placeholders | Direct f-strings, breaking laziness |
| `assert` for input validation | Never (assert is for invariants) | Common |
| `**kwargs` forwarding | Added when needed | Added preemptively |
| `if __name__ == "__main__": main()` | Only for big scripts | Wraps any 5-line script |

## Python — the deep catalog

### Tell #1 — Over-commenting that explains the obvious

**Real human code (`cpython@3.8.0/Lib/urllib/request.py:119`):**
```python
for meth in dir(handler):
    if meth in ["redirect_request", "do_open", "proxy_open"]:
        # oops, coincidental match
        continue
```
The `# oops` admits a real bug pattern. The comment says *why*, not *what*.

**AI version:**
```python
# Loop through all the methods in the handler's directory
for method_name in dir(handler):
    # Check if this is a coincidental match
    if method_name in ["redirect_request", "do_open", "proxy_open"]:
        # Skip this method as it's a false positive
        continue
    # Find the underscore separator
    separator_index = method_name.find("_")
```
Every line is a tautology. The variable names `method_name` and `separator_index` are textbook "verbose AI names."

### Tell #2 — Defensive bloat: `try/except` everywhere with overly broad excepts

**Real human code (`cpython@3.8.0/Lib/urllib/request.py:2096`):**
```python
try:
    try:
        h.request(req.get_method(), req.selector, req.data, headers,
                  encode_chunked=req.has_header('Transfer-encoding'))
    except OSError as err: # timeout error
        raise URLError(err)
    r = h.getresponse()
except:
    h.close()
    raise
```
Bare `except:` is unusual *but* the comment shows the author knew the precise failure mode. 8 lines, brutally direct.

**AI version:**
```python
try:
    try:
        response = http_connection.request(
            method=req.get_method(),
            url=req.selector,
            body=req.data,
            headers=headers,
            encode_chunked=req.has_header('Transfer-encoding')
        )
    except (OSError, ConnectionError, TimeoutError, socket.gaierror) as err:
        raise URLError(f"Failed to establish connection: {err}")
    return http_connection.getresponse()
except Exception as e:
    try:
        http_connection.close()
    except Exception:
        pass
    raise
```
24 lines. The 4-way catch where the human knew it was just `OSError`. The nested `try` to suppress close-failures is the AI-paranoia signature.

### Tell #3 — Perfect symmetry: every function returns Optional, every body delegates

**Real human code (`requests/api.py:23`):**
```python
def request(method, url, **kwargs):
    with sessions.Session() as session:
        return session.request(method=method, url=url, **kwargs)


def get(url, params=None, **kwargs):
    kwargs.setdefault('allow_redirects', True)
    return request('get', url, params=params, **kwargs)
```
Asymmetric, flat, reuses `request`.

**AI version:**
```python
def get(url: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Response:
    return _request_with_session("GET", url, params=params, **kwargs)

def post(url: str, data: Optional[Any] = None, json: Optional[Any] = None, **kwargs: Any) -> Response:
    return _request_with_session("POST", url, data=data, json=json, **kwargs)
```
Every function gets `Optional[...]` annotations. Every body becomes a delegate. Adds no real value.

### Tell #4 — Type-annotation overkill

**Real human code (`requests/api.py`):** zero type hints. Not one.

**AI version:**
```python
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, TypeAlias, Union, Callable, Mapping, Sequence

UserId: TypeAlias = int
UserDict: TypeAlias = Dict[str, Any]

def fetch_user(
    user_id: UserId,
    *,
    include_orders: bool = False,
    session: Optional[Session] = None,
) -> UserDict:
    ...
```
`TypeAlias` for a single identifier is AI waste. The 13-name import list (`Any, Callable, Dict, List, ...`) is the "import everything from typing" tic.

### Tell #5 — Verbose error messages

**Real human code:** `raise ValueError("proxy URL with no authority: %r" % proxy)` — 1 line, lowercase, includes the value.

**AI version:**
```python
raise ValueError(
    f"Invalid proxy URL provided: The URL '{proxy}' does not contain a valid "
    f"authority component. A valid proxy URL must include a hostname and "
    f"optionally a port, separated by '://'. Please check your proxy "
    f"configuration and try again."
)
```
Six lines. The phrase `"Please check your proxy configuration and try again"` is the dead giveaway — LLMs have been RLHF'd to be helpful in error messages.

### Tell #6 — Magic constants in SCREAMING_SNAKE_CASE

**Real human code (`cpython@3.8.0/Lib/urllib/request.py:521`):**
```python
class HTTPRedirectHandler(BaseHandler):
    # maximum number of redirections to any single URL
    # this is needed because of the state that cookies introduce
    max_repeats = 4
    # maximum total number of redirections (regardless of URL) before
    # assuming we're in a loop
    max_redirections = 10
```
Class attributes. Lowercase. Inline. The comment tells you *why* (cookies).

**AI version:**
```python
class HTTPRedirectHandler(BaseHandler):
    MAX_REPEATS_PER_URL: int = 4
    MAX_TOTAL_REDIRECTS: int = 10
    DEFAULT_REDIRECT_TIMEOUT_MS: int = 30000
    REDIRECT_STATUS_CODES: Tuple[int, ...] = (301, 302, 303, 307, 308)
```
A 4-constant wall. `DEFAULT_REDIRECT_TIMEOUT_MS` exists *at all* when it isn't used is also AI-add — humans don't add constants for things that aren't wired up.

### Tell #7 — Excessive dataclass / Pydantic for trivial data

**Real human code (`cpython@3.8.0/Lib/urllib/request.py:340`):**
```python
class Request:
    def __init__(self, url, data=None, headers={},
                 origin_req_host=None, unverifiable=False,
                 method=None):
        self.full_url = url
        self.headers = {}
        ...
```
Plain class. `__init__` sets attrs by hand. `headers={}` is a bug (mutable default) — a *human* bug from 2002. AI doesn't write this bug.

**AI version:**
```python
@dataclass
class Request:
    url: str
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    data: Optional[Union[bytes, str, IO]] = None
    origin_req_host: Optional[str] = None
    unverifiable: bool = False
    timeout: Optional[float] = None
    cookies: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.url:
            raise ValueError("URL cannot be empty")
```
Eight fields when the human has four. Plus a `metadata: Dict[str, Any]` field that no real code uses — that's AI speculatively adding "extensibility."

### Tell #8 — Logging at INFO level for everything

**Real human code (`cpython@3.8.0/Lib/urllib/request.py`):** Zero log statements in 2,300 lines.

**AI version:**
```python
logger.info(f"Fetching URL: {url}")
logger.debug(f"Request headers: {headers}")
logger.info(f"Request method: {method}")
logger.debug(f"Connecting to host: {host}")
logger.info(f"Sending request body of size: {len(data)}")
logger.info(f"Total request time: {elapsed:.2f}s")
```
Five `INFO` logs for one HTTP call. AI treats logging as a form of progress reporting; humans treat it as for actual problems.

### Tell #9 — The `main()` wrapper in scripts that don't need it

**Real human code:** the module is a library, no `if __name__ == "__main__":` block.

**AI version of a small script:**
```python
def main():
    """Main entry point for the URL fetcher script."""
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    response = fetch_url(url)
    print(response.text)

if __name__ == "__main__":
    main()
```
A 3-line script wrapped in `main()` + `if __name__`. This is one of the most reliable AI tells.

### Tell #10 — Walrus operators in places that hurt readability

**Real human code (`cpython@3.8.0/Lib/urllib/request.py:111`):**
```python
for elt in l:
    k, v = elt.split('=', 1)
    if v[0] == '"' and v[-1] == '"':
        v = v[1:-1]
    parsed[k] = v
```
Walrus-free. `k, v, l` tight. 4 lines of clear intent.

**AI version:**
```python
parsed: Dict[str, str] = {}
for element in element_list:
    if (parts := element.split('=', 1)) and len(parts) == 2:
        if (value := parts[1]) and len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            parsed[parts[0]] = value[1:-1]
```
Walrus everywhere. The `if (parts := element.split('=', 1)) and len(parts) == 2` pattern is a Python-3.8-era AI tic.

### Tell #11 — `match` for simple if/elif chains

**AI version:**
```python
match status_code:
    case 200:
        return Result.ok(data)
    case 301 | 302:
        return Result.redirect(location)
    case 404:
        return Result.not_found()
    case 500:
        return Result.server_error()
    case _:
        return Result.unknown()
```
Match for 5 cases where a dict lookup would do.

### Tell #12 — f-strings in logging

**AI version:**
```python
logger.info(f"Processing request {request_id} for user {user.name}")
```
Each `f"..."` is evaluated even when INFO is disabled. Humans who know logging:
```python
logger.info("Processing request %s for user %s", request_id, user.name)
```

### Tell #13 — Print-debugging-friendly verbose variable names

**Real human code (`cpython@3.8.0/Lib/urllib/request.py:130`):**
```python
def request_host(request):
    url = request.full_url
    host = urlparse(url)[1]
    if host == "":
        host = request.get_header("Host", "")
    host = _cut_port_re.sub("", host, 1)
    return host.lower()
```
Three `host` variables. The function's whole job is computing a `host`. Reuses the name because the function is 5 lines.

**AI version:**
```python
def request_host(request):
    original_url = request.full_url
    parsed_url_components = urlparse(original_url)
    initial_host_value = parsed_url_components[1]
    default_host_header_value = request.get_header("Host", "")
    final_host_value_without_port = _cut_port_re.sub("", initial_host_value, 1)
    normalized_host_string = final_host_value_without_port.lower()
    return normalized_host_string
```
Five distinct names for what's effectively the same variable.

### Tell #14 — Triple-nested `is not None` chains

**AI version:**
```python
if user is not None:
    if user.profile is not None:
        if user.profile.avatar is not None:
            if user.profile.avatar.url is not None:
                return user.profile.avatar.url
return DEFAULT_AVATAR_URL
```
Nested 4 levels. A human either trusts the type system or writes:
```python
return (user and user.profile and user.profile.avatar
        and user.profile.avatar.url) or DEFAULT_AVATAR_URL
```

### Tell #15 — `assert` for input validation

**AI version:**
```python
def divide(a: float, b: float) -> float:
    assert b != 0, "Divisor cannot be zero"
    return a / b
```
`assert` is stripped with `python -O`. Humans who know this use `if not b: raise ValueError(...)` for public APIs.

### Tell #16 — Pydantic `BaseModel` for everything

**AI version:**
```python
class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    age: int = Field(ge=0, le=150)

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8)
```
Three Pydantic models for an operation that's "create user, return user, update user." A human with Pydantic would use one model with optional fields.

### Tell #17 — `self.` everywhere when a closure would do

**AI version:**
```python
class Calculator:
    def __init__(self):
        self.history = []

    def add(self, a, b):
        result = a + b
        self.history.append((a, b, result))
        return result
```
A human writes:
```python
history = []

def add(a, b):
    result = a + b
    history.append((a, b, result))
    return result
```
(at module level) until a *reason* to make it a class appears.

## Python — human patterns

### Pattern — Terse variable names in small scopes

**Evidence (`cpython@3.8.0/Lib/collections/__init__.py:444`):**
```python
def _count_elements(mapping, iterable):
    'Tally elements from the iterable.'
    mapping_get = mapping.get
    for elem in iterable:
        mapping[elem] = mapping_get(elem, 0) + 1
```
`elem`, `mapping_get`, `mapping`. In-function locals get the shortest reasonable names.

### Pattern — Comments that explain *why*

**Evidence (`cpython@3.8.0/Lib/urllib/request.py:191`):**
```python
# Strictly (according to RFC 2616), 301 or 302 in response to
# a POST MUST NOT cause a redirection without confirmation
# from the user (of urllib.request, in this case).  In practice,
# essentially all clients do redirect in this case, so we do
# the same.
```
The author weighed RFC compliance against practice and chose practice. "essentially all clients do redirect, so we do too" is a judgment call.

### Pattern — Local imports to break circular dependencies

**Evidence (`cpython@3.8.0/Lib/urllib/request.py:1079`):**
```python
class HTTPCookieProcessor(BaseHandler):
    def __init__(self, cookiejar=None):
        import http.cookiejar
        if cookiejar is None:
            cookiejar = http.cookiejar.CookieJar()
        self.cookiejar = cookiejar
```
The `import http.cookiejar` is *inside* `__init__` to avoid a circular import.

### Pattern — `__slots__` in performance-sensitive classes

**Evidence (`cpython@3.8.0/Lib/collections/__init__.py:96`):**
```python
class _Link(object):
    __slots__ = 'prev', 'next', 'key', '__weakref__'
```
A `__slots__` declaration in a doubly-linked-list node. Performance-critical data structure.

### Pattern — Generator expressions for memory efficiency

**Evidence (`cpython@3.8.0/Lib/collections/__init__.py:391`):**
```python
def __len__(self):
    return len(set().union(*self.maps))     # reuses stored hash values if possible
```
The author didn't write `sum(len(m) for m in self.maps)`. The comment explains the *performance reasoning* (reusing hash values).

### Pattern — `XXX` and `FIXME` markers

**Evidence (`cpython@3.8.0/Lib/urllib/request.py:69`):**
```python
# XXX issues:
# If an authentication error handler that tries to perform
# authentication for some reason but fails, how should the error be
# signalled?
# ftp errors aren't handled cleanly
# check digest against correct (i.e. non-apache) implementation
```
The author left *known* debt in comments, with the tag `XXX`. AI doesn't write "not sure what exactly was meant by this" — that requires acknowledging uncertainty.

### Pattern — Test names like `test_raises_on_empty_input`

**Human-style:**
```python
def test_raises_on_empty_input():
    with pytest.raises(ValueError):
        parse_config("")

def test_returns_empty_dict_for_missing_file(tmp_path):
    result = load_config(tmp_path / "nonexistent.yaml")
    assert result == {}

def test_handles_unicode_in_url():
    url = "https://example.com/π/λ"
    assert normalize(url) == "https://example.com/%CF%80/%CE%BB"
```

**AI-style:**
```python
def test_url_normalization_behavior():
    """Test the URL normalization function."""
    url = "https://example.com/π/λ"
    expected = "https://example.com/%CF%80/%CE%BB"
    result = normalize_url(url)
    assert result == expected
    assert isinstance(result, str)
    assert len(result) > 0
```
The name describes the *function*, not the *case*. The docstring is redundant. The 3-assert pile is testing implementation, not behavior.

## JavaScript / TypeScript

### Tells

| Tell | Human | AI |
|---|---|---|
| `var` vs `const`/`let` | `var` in pre-2020 code | `const`/`let` in 2023+ AI output |
| TS `any` vs `unknown` | Often `any` (laziness) in pre-2020 code; `unknown` in 2023+ | Almost always `unknown` |
| `interface` vs `type` | Inconsistent; both | Prefers `interface` |
| Optional chaining `?.` | Common after 2020 | Over-used: `a?.b?.c?.d` when none can be undefined |
| Nullish coalescing `??` | Common after 2020 | Used even when `\|\|` would do |
| `async/await` for sequential ops | Yes | Over-applies to single-promise cases |
| JSDoc `@deprecated` everywhere | Rare | Common (LLM-trained to "inform") |
| Default exports | Mixed | Prefers named exports |

### Real human JS — Express's application.js

```javascript
var finalhandler = require('finalhandler');
var Router = require('./router');
var methods = require('methods');
var middleware = require('./middleware/init');
var query = require('./middleware/query');
var debug = require('debug')('express:application');
var View = require('./view');
var http = require('http');
```
`var` throughout. CommonJS. No TypeScript. No JSDoc types. Express depends on its own modules and a couple of micro-deps (`debug`, `depd`, `array-flatten`, `utils-merge`, `setprototypeof`). The author refused to depend on `lodash`.

### Strict equality

**Real human code (`express@4.16.0/lib/application.js:46`):**
```javascript
if (env === 'production') {
    this.enable('view cache');
}
```
Strict equality. Humans use `===` reflexively in JS after one bug.

### Overloaded functions

**Real human code (`express@4.16.0/lib/application.js:172`):**
```javascript
app.set = function set(setting, val) {
  if (arguments.length === 1) {
    // app.get(setting)
    return this.settings[setting];
  }
  ...
};
```
`set` is a getter if you call it with one arg. A human overloads existing functions to reduce API surface. AI adds a separate `get` method.

## Go

### Tells

| Tell | Human | AI |
|---|---|---|
| Wrapped errors `fmt.Errorf("...: %w", err)` | Common but unformatted in early Go | Always uses `%w` in 2023+ AI |
| `context.Context` as first arg | Common in 1.7+ | Universal in AI output, even when no cancellation needed |
| Custom error types | Reserved for cross-package use | AI creates one for every error case |
| Sentinel `ErrXxx` vars | Common | Common, but AI makes them unexported (`errFoo`) |
| `sync.Mutex` vs `sync.RWMutex` | Pick one and stick with it | Always `sync.RWMutex` "for performance" |
| Comments on exported funcs | Required by `golint` | Always present, sometimes redundant |
| Receiver name | Inconsistent across stdlib (`c *conn`, `srv *Server`) | AI picks `s` for short |

### Real human Go — net/http server.go

```go
type conn struct {
    // server is the server on which the connection arrived.
    // Immutable; never nil.
    server *Server

    // cancelCtx cancels the connection-level context.
    cancelCtx context.CancelFunc
    ...
}
```
The first line of every field comment is the *what*, but the second line is the *invariant* (`Immutable; never nil`). That's a human who knew the field would be touched by other goroutines.

### Real human Go — error messages

```go
return nil, badRequestError("unsupported protocol version")
```
Direct, lowercase, no period. Compare:
```go
return nil, fmt.Errorf("unsupported protocol version: please check your request format and try again")
```
The "please check your request format and try again" suffix is the AI tell.

### Real human Go — early returns

```go
func (c *conn) readRequest(ctx context.Context) (w *response, err error) {
    if c.hijacked() {
        return nil, ErrHijacked
    }
    ...
    if !http1ServerSupportsRequest(req) {
        return nil, badRequestError("unsupported protocol version")
    }
    ...
}
```
Each guard is an early return. No nested-else blocks.

### Real human Go — comments that cite real-world failure modes

```go
// Fortunately, almost nothing uses HTTP/1.x pipelining.
// Unfortunately, apt-get does, or sometimes does.
// New Go 1.11 behavior: don't fire CloseNotify or cancel
// contexts on pipelined requests. Shouldn't affect people, but
// fixes cases like Issue 23921.
```
"apt-get does" is a real-world observation. AI doesn't make calls like that.

## Rust

### Tells

| Tell | Human | AI |
|---|---|---|
| `.unwrap()` count | High in scripts, low in libs | Higher in libs (LLM defaults to unsafe) |
| `#[derive(Debug, Clone, ...)]` overload | Minimal (usually `Debug, Clone, PartialEq, Eq`) | Includes every derive that doesn't fail to compile |
| `impl Default for ...` | When truly needed | Even for trivial newtypes |
| `unsafe` block size | Small, commented | Either absent (paranoia) or oversized (cargo-cult) |
| `.clone()` everywhere | Avoided where borrow works | Used as "just in case" |
| `pub` vs `pub(crate)` | Defaults to `pub` for libs | Over-restricts to `pub(crate)` |
| `String` vs `&str` | `String` in public APIs, `&str` in fn args | Inconsistent or always `String` |
| `std::error::Error` impl | Manual | Uses `thiserror::Error` macro every time |
| `.iter().map().collect()` chains | Idiomatic | Often 3-deep, hard to read |

### Human vs AI Rust — error handling

**Human:**
```rust
fn read_file(path: &Path) -> Result<String, io::Error> {
    let mut s = String::new();
    File::open(path)?.read_to_string(&mut s)?;
    Ok(s)
}
```

**AI:**
```rust
fn read_file(path: &Path) -> Result<String, Box<dyn std::error::Error>> {
    let content: String = std::fs::read_to_string(path)?;
    Ok(content)
}
```
The human version *opens* then *reads*, allowing for more granular error handling and stream operations. The AI version is fine but is the "easy way."

### Human vs AI Rust — error messages

**Human:** `"failed to open %s: %s"` (printf style)
**AI:** `"Failed to open file. Reason: {}"` (sentence case, period)

## C

### Real human C — Linux kernel style

From `linux/Documentation/process/coding-style.rst`:

**Tabs are 8 characters:**
> Tabs are 8 characters, and thus indentations are also 8 characters. There are heretic movements that try to make indentations 4 (or even 2!) characters deep, and that is akin to trying to define the value of PI to be 3.

**K&R braces, but special case for functions:**
```c
if (x is true) {
        we do y
}
```
…but for functions:
```c
int function(int x)
{
        body of function
}
```

**Pointer `*` belongs to the name:**
```c
char *linux_banner;
unsigned long long memparse(char *ptr, char **retptr);
```
Not `char* linux_banner`. The pointer attaches to the variable.

**Don't typedef structs and pointers:**
> Please don't use things like `vps_t`. It's a **mistake** to use typedef for structures and pointers. When you see a `vps_t a;` in the source, what does it mean? In contrast, if it says `struct virtual_container *a;` you can actually tell what `a` is.

**Spartan naming:**
> Unlike Modula-2 and Pascal programmers, C programmers do not use cute names like ThisVariableIsATemporaryCounter. A C programmer would call that variable `tmp`.

**No Hungarian notation:**
> Encoding the type of a function into the name (so-called Hungarian notation) is asinine - the compiler knows the types anyway and can check those, and it only confuses the programmer.

**The multi-line comment style:**
```c
/*
 * This is the preferred style for multi-line
 * comments in the Linux kernel source code.
 * Please use it consistently.
 *
 * Description:  A column of asterisks on the left side,
 * with beginning and ending almost-blank lines.
 */
```

**`goto` for centralized cleanup:**
```c
        int result = 0;
        char *buffer;

        buffer = kmalloc(SIZE, GFP_KERNEL);
        if (!buffer)
                return -ENOMEM;

        if (condition1) {
                while (loop1) {
                        ...
                }
                result = 1;
                goto out_free_buffer;
        }
        ...
out_free_buffer:
        kfree(buffer);
        return result;
```
The label is *named for what it does* (`out_free_buffer:`), not `err1:` or `err2:`.

**Error messages — no period:**
> Kernel messages do not have to be terminated with a period. Printing numbers in parentheses (%d) adds no value and should be avoided.

## The Test of Humanity — 50-question checklist

A self-check. Answer yes/no. **Yes leans human. No leans AI.**

### Comments and naming
1. Do comments explain *why* rather than *what*?
2. Are variable names shorter for short-lived locals than for module-level state?
3. Is the same name reused across transformations of one concept?
4. Are there `XXX`, `FIXME`, or `TODO` markers where the author was honest about debt?
5. Is the comment density low overall (1 comment per 10–20 lines, not 1 per 3 lines)?
6. Are there `# oops`-style admissions of mistakes?

### Type hints and types
7. Is the type-hint density moderate (0–2 per function for public APIs)?
8. Is `from __future__ import annotations` used only when needed?
9. Is `Optional[X]` / `X | None` used consistently (not mixed within a file)?
10. Are dataclasses reserved for actual data carriers, not 2-field trivial structs?
11. Is `**kwargs` reserved for the few cases that genuinely need it?

### Error handling
12. Are `try/except` clauses targeted (specific exceptions, not bare `except:`)?
13. Are error messages one line, lowercase, and including the actual value?
14. Is `assert` used only for internal invariants, never for input validation?
15. Is `raise` from `except` used without apologetic comment?

### Style consistency
16. Is one docstring style used throughout the file (not mixed)?
17. Are imports at the top *unless* there's a documented reason?
18. Are public APIs annotated but internals not?
19. Is there any commented-out code, dead `print` statement, or `XXX` marker?
20. Is there at least one minor inconsistency in quoting or formatting?

### Function and class design
21. Are functions short (≤ 30 lines)?
22. Are classes small (≤ 5 public methods)?
23. Is the test name describing the *case* (e.g., `test_raises_on_empty_input`)?
24. Is the test name describing the *function* (e.g., `test_function_behavior`)?
25. Are docstrings one line, in imperative voice, summarizing the function?
26. Is `if __name__ == "__main__":` used only for big scripts?
27. Are early returns used instead of nested if-else?
28. Are class attributes used for module-level constants (lowercase, inline)?

### README / docs
29. Does the README open with a one-sentence factual definition?
30. Are there zero emoji in section headers?
31. Are there ≤ 8 badges at the top?
32. Is the README ≤ 100 lines for a library, ≤ 300 for a framework?
33. Is there no "Why X?" sales section?
34. Is there a "Why shouldn't I use X?" or "When NOT to use X" section?
35. Are there zero "Happy coding!" / "Let's dive in!" closings?

### Commit / changelog
36. Is the commit subject in imperative mood, ≤ 72 chars, no period?
37. Is the commit body wrapped at 75 columns?
38. Does each changelog entry reference a PR/issue number?
39. Are changelog categories stable across releases (Security, Bugfixes, Improvements, Deprecations)?
40. Are changelog entries short, factual, and free of marketing language?

### Project structure
41. Is there a hand-written CHANGELOG/HISTORY (not auto-generated)?
42. Is the project description ≤ 12 words, in 1 sentence?
43. Are there zero pre-filled issue templates in `.github/ISSUE_TEMPLATE/`?
44. Is there no `.github/dependabot.yml` unless the project has many deps?
45. Is the LICENSE file customized with the project's name and year?

### Tone and voice
46. Is there at least one specific real-world detail (issue #, RFC cite, "apt-get does this")?
47. Is there at least one opinion or stance (not all "considered and rejected" hedging)?
48. Is there at least one minor typo or grammatical inconsistency?
49. Are contractions (`don't`, `won't`, `it's`) used naturally?
50. Does the project's voice sound like a *specific* person, not a generic "we"?

A score of 40+ "yes" is human. 30–40 is mixed (could be either). Below 30 is AI.

## The transformation table (compact)

| AI-slop code | Human code |
|---|---|
| 4-line docstring paraphrasing 1-line body | 1-line docstring in imperative, or no docstring |
| `Optional[Any]` on every parameter | no annotation on internal helpers |
| `assert user_input is not None, "..."` | `if user_input is None: raise ValueError(...)` |
| `try: ... except (A, B, C, D): ...` | `try: ... except A: ...` |
| 4-level `if x is not None: if y is not None: ...` | early return with single guard |
| `f"Processing {x}"` in `logger.info` | `"Processing %s", x` in `logger.info` |
| `(parts := x.split(...)) and len(parts) == 2` | `parts = x.split(...); if len(parts) == 2:` |
| `match status: case 200: ... case 301 \| 302: ...` | `{200: ..., 301: ..., 302: ...}.get(status, default)` |
| `def main(): ...; if __name__ == "__main__": main()` | top-level code in scripts < 50 lines |
| `original_url, parsed_url_components, initial_host_value, ...` | `url, host` reused across transformations |
| `'''Calculates the total price of the given items with tax applied...'''` | (no docstring, function name says it) |
| `user.profile.avatar.url or DEFAULT` chained 4 times | one early return, or a single `getattr` chain |
| `**kwargs` forwarding preemptively | add `**kwargs` when a real second caller needs it |
| `@dataclass` for a 2-field struct | plain class with `__init__` |
| 5 `logger.info` calls in one function | zero, unless something is actually informative |
| `metadata: Dict[str, Any] = field(default_factory=dict)` | (delete) |
