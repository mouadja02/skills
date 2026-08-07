#!/usr/bin/env python3
"""Local-only NO_PROXY conformance probe for curl and Python urllib."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

PROXY_KEYS = {"HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "no_proxy", "all_proxy"}
CLIENTS = {"curl", "python-urllib"}

class TargetHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200); self.end_headers(); self.wfile.write(b"DIRECT")
    def log_message(self, format: str, *args: Any) -> None: pass

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.server.hits += 1  # type: ignore[attr-defined]
        self.send_response(200); self.end_headers(); self.wfile.write(b"PROXY")
    def log_message(self, format: str, *args: Any) -> None: pass

def fail(msg: str) -> int:
    print(f"error: {msg}", file=sys.stderr); return 2

def load_config(path: Path) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant {value}")
    data = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    if not isinstance(data, dict): raise ValueError("root must be an object")
    clients = data.get("clients")
    cases = data.get("cases")
    if not isinstance(clients, list) or not clients or any(not isinstance(x, str) or x not in CLIENTS for x in clients):
        raise ValueError(f"clients must be a non-empty unique-name list drawn from {sorted(CLIENTS)}")
    if len(set(clients)) != len(clients): raise ValueError("clients must not contain duplicates")
    if not isinstance(cases, list) or not cases: raise ValueError("cases must be a non-empty list")
    names: set[str] = set()
    for i, case in enumerate(cases):
        if not isinstance(case, dict): raise ValueError(f"cases[{i}] must be an object")
        name, host, env, expected = case.get("name"), case.get("host"), case.get("environment"), case.get("expected")
        if not isinstance(name, str) or not name or name in names: raise ValueError(f"cases[{i}].name must be non-empty and unique")
        names.add(name)
        if host not in ("localhost", "127.0.0.1"): raise ValueError(f"cases[{i}].host must be localhost or 127.0.0.1")
        if not isinstance(env, dict) or any(k not in PROXY_KEYS or not isinstance(v, str) for k,v in env.items()):
            raise ValueError(f"cases[{i}].environment may contain only string proxy environment variables")
        if not isinstance(expected, dict) or set(expected) != set(clients) or any(v not in ("direct", "proxy") for v in expected.values()):
            raise ValueError(f"cases[{i}].expected must map every selected client to direct or proxy")
    return data

def client_command(client: str, url: str) -> list[str]:
    if client == "curl": return ["curl", "--fail", "--silent", "--show-error", "--max-time", "5", url]
    code = "import sys,urllib.request;sys.stdout.write(urllib.request.urlopen(sys.argv[1],timeout=5).read().decode())"
    return [sys.executable, "-c", code, url]

def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, indent=2, allow_nan=False); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("config", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try: config = load_config(args.config)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as e: return fail(str(e))
    for client in config["clients"]:
        executable = "curl" if client == "curl" else sys.executable
        if not shutil.which(executable): return fail(f"required executable not found: {executable}")
    target = ThreadingHTTPServer(("127.0.0.1", 0), TargetHandler)
    proxy = ThreadingHTTPServer(("127.0.0.1", 0), ProxyHandler); proxy.hits = 0  # type: ignore[attr-defined]
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (target, proxy)]
    for t in threads: t.start()
    rows: list[dict[str, Any]] = []
    try:
        target_port, proxy_port = target.server_port, proxy.server_port
        for case in config["cases"]:
            url = f"http://{case['host']}:{target_port}/sentinel"
            for client in config["clients"]:
                env = os.environ.copy()
                for key in PROXY_KEYS: env.pop(key, None)
                env.update({"HTTP_PROXY": f"http://127.0.0.1:{proxy_port}", "http_proxy": f"http://127.0.0.1:{proxy_port}"})
                env.update(case["environment"])
                before = proxy.hits  # type: ignore[attr-defined]
                run = subprocess.run(client_command(client, url), env=env, text=True, capture_output=True, timeout=8)
                token = run.stdout.strip()
                observed = "proxy" if token == "PROXY" else "direct" if token == "DIRECT" else "error"
                rows.append({"case":case["name"],"client":client,"expected":case["expected"][client],"observed":observed,"passed":observed==case["expected"][client],"exit_code":run.returncode,"proxy_hit":proxy.hits > before})  # type: ignore[attr-defined]
    except (OSError, subprocess.SubprocessError) as e:
        return fail(f"probe failed: {e}")
    finally:
        target.shutdown(); proxy.shutdown(); target.server_close(); proxy.server_close()
    report = {"schema_version":1,"local_only":True,"clients":config["clients"],"rows":rows,"passed":all(r["passed"] for r in rows)}
    try:
        if args.output: atomic_json(args.output, report)
        else: json.dump(report, sys.stdout, indent=2, allow_nan=False); print()
    except (OSError, TypeError, ValueError) as e: return fail(f"cannot write report: {e}")
    return 0 if report["passed"] else 1

if __name__ == "__main__": raise SystemExit(main())
