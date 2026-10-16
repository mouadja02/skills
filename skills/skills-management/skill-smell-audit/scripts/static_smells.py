#!/usr/bin/env python3
"""Deterministic skill-smell checks for SKILL.md files.

Covers the smells that need no judgment (Hong, Imani & Ahmed 2026, arXiv:2607.01456):
Lengthy Skill Name/Description/Body, XML Included Description, Backslash Path, plus
loading problems (frontmatter, name/folder mismatch, broken references) and cheap
proxies for Confusing/Non-Third-Person descriptions and Time Sensitive content.
The remaining smells need a reader; see references/smell-catalog.md.

Usage:
    python3 static_smells.py PATH [PATH ...] [--json]

PATH may be a SKILL.md file, a skill folder, or a directory searched recursively.
Exit status is 1 when any finding has severity "error", else 0. Standard library only.
"""

import json
import os
import re
import sys

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FENCE_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})[^\n]*\n.*?^\1\2[^\n]*$", re.M | re.S)
INLINE_CODE_RE = re.compile(r"(`+)[^`\n]*?\1")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BUNDLED_RE = re.compile(
    r"(?<![\w./-])((?:\./)?(?:references|scripts|assets|templates|examples|agents|resources|rules)"
    r"/[\w./-]*?[\w-]\.(?:md|py|sh|js|mjs|ts|json|yaml|yml|txt|html|csv|sql|toml))(?![\w])"
)
BACKSLASH_RE = re.compile(r"(?<![\\\w])(?:[A-Za-z]:\\|\.{1,2}\\|[\w.-]+\\[\w.-]+\\?)[\w.\\-]*")
XML_TAG_RE = re.compile(r"</?[A-Za-z][\w:-]*(?:\s[^<>]*)?/?>")
TIME_RE = re.compile(
    r"\b(?:as of (?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.? )?20\d\d"
    r"|(?:new|added|released|introduced) in 20\d\d"
    r"|this (?:year|quarter|month)"
    r"|(?:the )?latest (?:version|release|model)s?\b"
    r"|until (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* 20\d\d)",
    re.I,
)
TRIGGER_RE = re.compile(r"\b(use (?:when|for|to|this|it|whenever)|when (?:the|a|an|you|user)|trigger|activate|invoke)", re.I)
FIRST_PERSON_RE = re.compile(r"^(?:i|we|you)\b|\b(?:i can|i will|i'll|you can|you should|let me)\b", re.I)
PLAIN_UNSAFE_RE = re.compile(r"^[@`*&!%|>\[{]|: |\s#")
# Documentation placeholders, not references to resolve.
PLACEHOLDER_RE = re.compile(r"[<>{}*]|\.\.\.|path/to/|(?:^|/)(?:path|url|link)(?:/|$)|\byour[-_]", re.I)


def find_skill_files(paths):
    for path in paths:
        if os.path.isfile(path):
            yield path
        elif os.path.isfile(os.path.join(path, "SKILL.md")) and not os.path.isdir(os.path.join(path, "skills")):
            yield os.path.join(path, "SKILL.md")
        else:
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", "__pycache__"}]
                if "SKILL.md" in files:
                    yield os.path.join(root, "SKILL.md")


def split_frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---[ \t]*(?:\n|$)", text, re.S)
    if not match:
        return None, text
    return match.group(1), text[match.end():]


def parse_frontmatter(block):
    """Reads top-level scalar keys. Returns (fields, problems)."""
    fields, problems = {}, []
    lines = block.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^([A-Za-z0-9_-]+):(?:\s(.*)|$)", line)
        if not match:
            i += 1
            continue
        key, value = match.group(1), (match.group(2) or "").strip()
        i += 1
        if value in {">", "|", ">-", "|-", ">+", "|+"}:
            parts = []
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                parts.append(lines[i].strip())
                i += 1
            fields[key] = " ".join(p for p in parts if p).strip()
            continue
        if value[:1] in {'"', "'"}:
            quote = value[0]
            while not (len(value) > 1 and value.endswith(quote)) and i < len(lines):
                value += " " + lines[i].strip()
                i += 1
            fields[key] = value[1:-1]
            continue
        continuation = []
        while i < len(lines) and lines[i].startswith((" ", "\t")) and lines[i].strip():
            continuation.append(lines[i].strip())
            i += 1
        if value and PLAIN_UNSAFE_RE.search(value) and key in {"name", "description"}:
            problems.append(f"'{key}' is an unquoted plain scalar containing YAML syntax; quote it or use '>-'")
        fields[key] = " ".join([value] + continuation).strip()
    return fields, problems


def strip_code(markdown, inline=True):
    out = FENCE_RE.sub("", markdown)
    return INLINE_CODE_RE.sub("", out) if inline else out


def resolves(skill_dir, target):
    current = skill_dir
    for _ in range(4):
        if os.path.exists(os.path.join(current, target)):
            return True
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return False


def check(path):
    findings = []

    def add(smell, severity, message):
        findings.append({"smell": smell, "severity": severity, "message": message})

    with open(path, encoding="utf-8") as handle:
        raw = handle.read()
    if raw.startswith("﻿"):
        add("loading", "error", "file starts with a UTF-8 BOM")
    text = raw.lstrip("﻿").replace("\r\n", "\n")
    block, body = split_frontmatter(text)
    skill_dir = os.path.dirname(os.path.abspath(path))
    if block is None:
        add("loading", "error", "no YAML frontmatter block (--- ... ---) at the top")
        return findings
    fields, problems = parse_frontmatter(block)
    for problem in problems:
        add("loading", "error", problem)

    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name:
        add("loading", "error", "frontmatter has no 'name'")
    else:
        if len(name) > 64:
            add("LSN", "error", f"name is {len(name)} characters (limit 64)")
        if not NAME_RE.match(name):
            add("loading", "error", f"name '{name}' is not lowercase kebab-case")
        if re.search(r"anthropic|claude", name):
            add("loading", "warning", f"name '{name}' contains a reserved word ('anthropic'/'claude'); claude.ai and the Claude API reject it")
        if name != os.path.basename(skill_dir):
            add("loading", "warning", f"name '{name}' differs from folder '{os.path.basename(skill_dir)}'")
    if not description:
        add("loading", "error", "frontmatter has no 'description'")
    else:
        if len(description) > 1024:
            add("LSD", "error", f"description is {len(description)} characters (limit 1024)")
        if XML_TAG_RE.search(description):
            add("XID", "error", "description contains an XML/HTML tag")
        if len(description) < 60:
            add("CSD", "warning", f"description is only {len(description)} characters; say what it does and when to use it")
        elif not TRIGGER_RE.search(description):
            add("CSD", "warning", "description names no trigger ('Use when ...'); clients route on it")
        if FIRST_PERSON_RE.search(description):
            add("NTPD", "warning", "description is not written in the third person")

    words = len(re.findall(r"\S+", body))
    lines = body.count("\n") + 1
    if words > 5000:
        add("LSB", "error", f"body is {words} words (limit 5000); move detail into references/")
    elif lines > 500:
        add("UD", "info", f"body is {lines} lines; consider moving detail into references/ (aim for under 500)")

    prose = strip_code(body)
    for match in BACKSLASH_RE.finditer(prose):
        token = match.group(0).rstrip(".,;:")
        if "\\" in token and not re.fullmatch(r"\\+[nrt0]?", token):
            add("BP", "warning", f"backslash path '{token}'; use forward slashes")
            break

    seen = set()
    for link in LINK_RE.findall(prose):
        if "://" in link or link.startswith(("#", "mailto:")):
            continue
        target = link.split("#")[0]
        if not target or target in seen or PLACEHOLDER_RE.search(target):
            continue
        seen.add(target)
        if target.startswith("/"):
            add("loading", "error", f"absolute link '{target}' will not resolve once installed")
        elif not resolves(skill_dir, target):
            add("loading", "error", f"broken relative link '{target}'")
    for ref in sorted(set(BUNDLED_RE.findall(strip_code(body, inline=False)))):
        if ref not in seen and not resolves(skill_dir, ref):
            add("loading", "warning", f"mentions bundled file '{ref}', which the skill does not ship")

    hits = sorted({m.group(0).lower() for m in TIME_RE.finditer(prose)})
    if hits:
        add("TSS", "info", "time-sensitive wording: " + ", ".join(hits[:5]))

    if not re.search(r"^#{1,4}\s.*(example|sample|template|output format)", body, re.I | re.M) and "```" not in body:
        add("ME", "info", "no example, template, or code block; confirm the skill does not need one")
    return findings


def main(argv):
    as_json = "--json" in argv
    paths = [a for a in argv if a != "--json"]
    if not paths:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    report = []
    for skill_file in sorted(set(find_skill_files(paths))):
        report.append({"file": skill_file.replace(os.sep, "/"), "findings": check(skill_file)})
    errors = sum(1 for r in report for f in r["findings"] if f["severity"] == "error")
    if as_json:
        print(json.dumps({"skills": len(report), "errors": errors, "results": report}, indent=2))
    else:
        for entry in report:
            if not entry["findings"]:
                continue
            print(entry["file"])
            for f in entry["findings"]:
                print(f"  {f['severity']:<7} {f['smell']:<7} {f['message']}")
        print(f"{len(report)} skill(s) checked, {errors} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
