#!/usr/bin/env python3
"""Offline auditor for declared npm platform-optional package families."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

EXIT_FINDINGS = 1
EXIT_INPUT = 2
EXIT_IO = 74
SELECTORS = ("os", "cpu", "libc")


class InputError(ValueError):
    pass


def reject_constant(value: str) -> None:
    raise InputError(f"non-standard JSON constant is not allowed: {value}")


def require_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{path} must be an object")
    return value


def require_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise InputError(f"{path} must be a non-empty string")
    return value


def string_list(value: Any, path: str, *, allow_absent: bool = False) -> list[str] | None:
    if value is None and allow_absent:
        return None
    if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x for x in value):
        raise InputError(f"{path} must be a non-empty array of strings")
    if len(set(value)) != len(value):
        raise InputError(f"{path} must not contain duplicates")
    return value


def selector_contract(obj: dict[str, Any], path: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for key in SELECTORS:
        if key in obj:
            values = string_list(obj[key], f"{path}.{key}")
            assert values is not None
            result[key] = values
    if "os" not in result or "cpu" not in result:
        raise InputError(f"{path} must declare os and cpu")
    return result


def target_matches(contract: dict[str, list[str]], target: dict[str, str]) -> bool:
    for key, allowed in contract.items():
        value = target.get(key)
        if value is None or value not in allowed:
            return False
    return True


def finding(code: str, family: str, package: str | None, detail: str) -> dict[str, Any]:
    return {"code": code, "family": family, "package": package, "detail": detail}


def audit(data: Any) -> tuple[dict[str, Any], bool]:
    root = require_object(data, "$" )
    package_json = require_object(root.get("package_json"), "$.package_json")
    lockfile = require_object(root.get("lockfile"), "$.lockfile")
    lock_version = lockfile.get("lockfileVersion")
    if type(lock_version) is not int or lock_version not in (2, 3):
        raise InputError("$.lockfile.lockfileVersion must be integer 2 or 3")
    packages = require_object(lockfile.get("packages"), "$.lockfile.packages")
    optional = package_json.get("optionalDependencies", {})
    optional = require_object(optional, "$.package_json.optionalDependencies")
    for name, version in optional.items():
        require_string(name, "optional dependency name")
        require_string(version, f"optionalDependencies[{name!r}]")

    families_raw = root.get("families", [])
    targets_raw = root.get("targets", [])
    if not isinstance(families_raw, list) or not isinstance(targets_raw, list):
        raise InputError("$.families and $.targets must be arrays")
    if not families_raw:
        result = {"schema_version": 1, "applicable": False, "classification": "not_applicable", "findings": [], "summary": {"families": 0, "targets": 0, "findings": 0}}
        return result, False
    if not targets_raw:
        raise InputError("$.targets must not be empty when families are declared")

    targets: list[dict[str, str]] = []
    for index, raw in enumerate(targets_raw):
        obj = require_object(raw, f"$.targets[{index}]")
        target = {"os": require_string(obj.get("os"), f"$.targets[{index}].os"), "cpu": require_string(obj.get("cpu"), f"$.targets[{index}].cpu")}
        if "libc" in obj:
            target["libc"] = require_string(obj["libc"], f"$.targets[{index}].libc")
        if set(obj) - set(SELECTORS):
            raise InputError(f"$.targets[{index}] contains unknown keys")
        targets.append(target)

    findings: list[dict[str, Any]] = []
    family_names: set[str] = set()
    package_owners: set[str] = set()
    valid_members: dict[str, list[tuple[str, dict[str, list[str]]]]] = {}

    for fi, raw_family in enumerate(families_raw):
        family_obj = require_object(raw_family, f"$.families[{fi}]")
        family = require_string(family_obj.get("name"), f"$.families[{fi}].name")
        if family in family_names:
            raise InputError(f"duplicate family name: {family}")
        family_names.add(family)
        members = family_obj.get("members")
        if not isinstance(members, list) or not members:
            raise InputError(f"$.families[{fi}].members must be a non-empty array")
        valid_members[family] = []
        for mi, raw_member in enumerate(members):
            path = f"$.families[{fi}].members[{mi}]"
            member = require_object(raw_member, path)
            package = require_string(member.get("package"), f"{path}.package")
            if package in package_owners:
                raise InputError(f"package appears in multiple family members: {package}")
            package_owners.add(package)
            contract = selector_contract(member, path)
            lock_path = f"node_modules/{package}"
            locked_raw = packages.get(lock_path)
            member_ok = True
            if locked_raw is None:
                findings.append(finding("MISSING_LOCK_ENTRY", family, package, f"{lock_path} is absent"))
                member_ok = False
            else:
                locked = require_object(locked_raw, f"$.lockfile.packages[{lock_path!r}]")
                if locked.get("optional") is not True:
                    findings.append(finding("NOT_OPTIONAL", family, package, "lock entry is not marked optional=true"))
                    member_ok = False
                expected_version = optional.get(package)
                if expected_version is None:
                    findings.append(finding("MISSING_ROOT_DECLARATION", family, package, "family member is absent from root optionalDependencies"))
                    member_ok = False
                else:
                    locked_version = locked.get("version")
                    if not isinstance(locked_version, str) or locked_version != expected_version:
                        findings.append(finding("VERSION_MISMATCH", family, package, f"root={expected_version!r}, lock={locked_version!r}"))
                        member_ok = False
                for key in SELECTORS:
                    expected = contract.get(key)
                    actual = locked.get(key)
                    if expected is None:
                        if actual is not None:
                            actual_values = string_list(actual, f"lock entry {package}.{key}")
                            findings.append(finding("SELECTOR_MISMATCH", family, package, f"{key}: expected absent, lock={actual_values}"))
                            member_ok = False
                    else:
                        actual_values = string_list(actual, f"lock entry {package}.{key}", allow_absent=True)
                        if actual_values != expected:
                            findings.append(finding("SELECTOR_MISMATCH", family, package, f"{key}: expected={expected}, lock={actual_values}"))
                            member_ok = False
            if member_ok:
                valid_members[family].append((package, contract))

    for family in sorted(valid_members):
        for target in targets:
            if not any(target_matches(contract, target) for _, contract in valid_members[family]):
                label = "/".join(target.get(k, "-") for k in SELECTORS)
                findings.append(finding("TARGET_UNCOVERED", family, None, f"no valid member covers {label}"))

    findings.sort(key=lambda item: (item["code"], item["family"], item["package"] or "", item["detail"]))
    result = {
        "schema_version": 1,
        "applicable": True,
        "classification": "conformant" if not findings else "nonconformant",
        "findings": findings,
        "summary": {"families": len(family_names), "targets": len(targets), "findings": len(findings)},
    }
    return result, bool(findings)


def load_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle, parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, InputError) as exc:
        raise InputError(f"cannot read valid strict JSON from {path}: {exc}") from exc


def silence_broken_stdout() -> None:
    try:
        fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(fd, sys.stdout.fileno())
        os.close(fd)
    except OSError:
        pass


def write_result(result: dict[str, Any], pretty: bool) -> None:
    try:
        json.dump(result, sys.stdout, indent=2 if pretty else None, sort_keys=True, allow_nan=False)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except (OSError, UnicodeError, ValueError) as exc:
        silence_broken_stdout()
        try:
            print(f"output error: {exc}", file=sys.stderr, flush=True)
        except OSError:
            pass
        raise SystemExit(EXIT_IO) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="strict JSON audit input")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    try:
        result, has_findings = audit(load_json(args.input))
    except InputError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return EXIT_INPUT
    write_result(result, args.pretty)
    return EXIT_FINDINGS if has_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
