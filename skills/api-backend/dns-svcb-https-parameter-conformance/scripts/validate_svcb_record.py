#!/usr/bin/env python3
"""
RFC 9460 SVCB and HTTPS Resource Record Conformance Validator.

Validates:
1. Presentation format and parsing
2. Mode rules: AliasMode (priority 0) vs ServiceMode (priority > 0)
3. TargetName compression and wire rules
4. SvcParamKey parsing (named vs keyNNNNN) and canonical wire sorting (ascending, unique)
5. Parameter-specific wire validation:
   - mandatory (0): cannot be empty, cannot list 0, must refer to present keys
   - alpn (1): length-prefixed protocol IDs, non-empty, valid lengths
   - no-default-alpn (2): wire length MUST be 0
   - port (3): 2 bytes big-endian, range 0-65535
   - ipv4hint (4): multiple of 4 bytes, valid IPv4 addresses
   - ech (5): ECHConfigList format / opaque octets
   - ipv6hint (6): multiple of 16 bytes, valid IPv6 addresses
6. Wire encoding serialization / deserialization fidelity.
"""

import sys
import os
import re
import socket
import struct
import json
from typing import Dict, Any, List, Tuple, Optional

# Well-known SvcParamKey registry (RFC 9460 Section 14.3.2)
SVC_PARAM_KEYS = {
    "mandatory": 0,
    "alpn": 1,
    "no-default-alpn": 2,
    "port": 3,
    "ipv4hint": 4,
    "ech": 5,
    "ipv6hint": 6,
}

KEY_TO_NAME = {v: k for k, v in SVC_PARAM_KEYS.items()}


def parse_svc_param_key(key_str: str) -> int:
    """Parse key string into integer key id. Accepts registered names or keyNNNNN."""
    key_lower = key_str.lower()
    if key_lower in SVC_PARAM_KEYS:
        return SVC_PARAM_KEYS[key_lower]
    if key_lower.startswith("key"):
        suffix = key_lower[3:]
        if suffix.isdigit():
            val = int(suffix)
            if 0 <= val <= 65535:
                return val
    raise ValueError(f"Unknown or invalid SvcParamKey: '{key_str}'")


def format_svc_param_key(key_num: int) -> str:
    """Format key integer to canonical name or keyNNNNN."""
    return KEY_TO_NAME.get(key_num, f"key{key_num}")


def parse_alpn_presentation(value_str: str) -> bytes:
    """Parse comma-separated ALPN presentation string into RFC 9460 wire format."""
    # Wire format: sequence of 1-octet length + alpn ID
    parts = [p.strip() for p in value_str.split(",") if p.strip()]
    if not parts:
        raise ValueError("alpn parameter cannot have empty list of identifiers")
    out = bytearray()
    for p in parts:
        p_bytes = p.encode("ascii")
        if len(p_bytes) == 0 or len(p_bytes) > 255:
            raise ValueError(f"ALPN protocol identifier '{p}' invalid length: {len(p_bytes)}")
        out.append(len(p_bytes))
        out.extend(p_bytes)
    return bytes(out)


def parse_ipv4hint_presentation(value_str: str) -> bytes:
    """Parse comma-separated IPv4 hints into wire format (4 bytes each)."""
    parts = [p.strip() for p in value_str.split(",") if p.strip()]
    if not parts:
        raise ValueError("ipv4hint cannot be empty")
    out = bytearray()
    for p in parts:
        try:
            packed = socket.inet_pton(socket.AF_INET, p)
            out.extend(packed)
        except OSError:
            raise ValueError(f"Invalid IPv4 address in ipv4hint: '{p}'")
    return bytes(out)


def parse_ipv6hint_presentation(value_str: str) -> bytes:
    """Parse comma-separated IPv6 hints into wire format (16 bytes each)."""
    parts = [p.strip() for p in value_str.split(",") if p.strip()]
    if not parts:
        raise ValueError("ipv6hint cannot be empty")
    out = bytearray()
    for p in parts:
        try:
            packed = socket.inet_pton(socket.AF_INET6, p)
            out.extend(packed)
        except OSError:
            raise ValueError(f"Invalid IPv6 address in ipv6hint: '{p}'")
    return bytes(out)


def parse_mandatory_presentation(value_str: str) -> Tuple[bytes, List[int]]:
    """Parse comma-separated mandatory parameter keys."""
    parts = [p.strip() for p in value_str.split(",") if p.strip()]
    if not parts:
        raise ValueError("mandatory parameter cannot be empty")
    keys = []
    for p in parts:
        k_num = parse_svc_param_key(p)
        if k_num == 0:
            raise ValueError("mandatory parameter list MUST NOT include 'mandatory' (0)")
        keys.append(k_num)
    # Wire format: sorted list of 2-octet SvcParamKey
    keys = sorted(set(keys))
    out = bytearray()
    for k in keys:
        out.extend(struct.pack("!H", k))
    return bytes(out), keys


def parse_port_presentation(value_str: str) -> bytes:
    """Parse port number into 2-octet big-endian integer."""
    try:
        val = int(value_str)
        if not (0 <= val <= 65535):
            raise ValueError()
    except ValueError:
        raise ValueError(f"Invalid port number: '{value_str}' (must be 0-65535)")
    return struct.pack("!H", val)


def parse_target_name(target_name: str) -> bytes:
    """
    Encode target name into DNS wire format without name compression.
    RFC 9460 Section 2.2: The wire format TargetName MUST NOT be compressed.
    '.' represents the root label (single 0x00 byte).
    """
    clean_target = target_name.strip()
    if clean_target == "." or clean_target == "":
        return b"\x00"
    
    # Strip trailing dot if present for processing
    if clean_target.endswith("."):
        clean_target = clean_target[:-1]
    
    labels = clean_target.split(".")
    out = bytearray()
    for label in labels:
        l_bytes = label.encode("idna")
        if len(l_bytes) == 0 or len(l_bytes) > 63:
            raise ValueError(f"DNS label '{label}' invalid length: {len(l_bytes)}")
        out.append(len(l_bytes))
        out.extend(l_bytes)
    out.append(0x00)
    return bytes(out)


def parse_presentation_tokens(line: str) -> Dict[str, Any]:
    """
    Parse a zone presentation line for SVCB or HTTPS record.
    Expected format:
    [<name>] [<ttl>] [<class>] <TYPE> <SvcPriority> <TargetName> [<SvcParams>...]
    """
    tokens = []
    # Tokenize preserving quoted strings
    pattern = r'\"([^\"]*)\"|(\S+)'
    for match in re.finditer(pattern, line):
        quoted, unquoted = match.groups()
        if quoted is not None:
            tokens.append(quoted)
        else:
            tokens.append(unquoted)

    if not tokens:
        raise ValueError("Empty record line")

    # Find TYPE (SVCB or HTTPS)
    idx = -1
    for i, t in enumerate(tokens):
        if t.upper() in ("SVCB", "HTTPS"):
            idx = i
            break

    if idx == -1:
        raise ValueError("Record type must be SVCB or HTTPS")

    record_type = tokens[idx].upper()
    owner = tokens[0] if idx > 0 else "@"
    
    rem = tokens[idx + 1:]
    if len(rem) < 2:
        raise ValueError(f"Insufficient fields for {record_type}: requires SvcPriority and TargetName")

    try:
        svc_priority = int(rem[0])
        if not (0 <= svc_priority <= 65535):
            raise ValueError()
    except ValueError:
        raise ValueError(f"Invalid SvcPriority: '{rem[0]}' (must be integer 0-65535)")

    target_name = rem[1]
    param_tokens = rem[2:]

    params = {}
    for pt in param_tokens:
        if "=" in pt:
            k, v = pt.split("=", 1)
        else:
            k, v = pt, ""
        k = k.strip()
        v = v.strip().strip('"')
        if k in params:
            raise ValueError(f"Duplicate SvcParam key '{k}' in presentation")
        params[k] = v

    return {
        "owner": owner,
        "type": record_type,
        "priority": svc_priority,
        "target_name": target_name,
        "raw_params": params
    }


def validate_and_serialize_record(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate record invariants per RFC 9460 and construct canonical DNS wire format.
    """
    errors = []
    warnings = []
    priority = parsed["priority"]
    target_name = parsed["target_name"]
    raw_params = parsed["raw_params"]

    # 1. Mode Invariants
    # AliasMode: priority == 0
    # ServiceMode: priority > 0
    is_alias = (priority == 0)
    mode = "AliasMode" if is_alias else "ServiceMode"

    if is_alias:
        if raw_params:
            errors.append("AliasMode (priority 0) MUST NOT contain any SvcParams (RFC 9460 Section 2.4.2)")
        if target_name == ".":
            errors.append("AliasMode TargetName MUST NOT be '.' (RFC 9460 Section 2.4.2)")
    else:
        # ServiceMode
        pass

    # 2. TargetName Wire Validation
    try:
        target_wire = parse_target_name(target_name)
    except Exception as e:
        errors.append(f"TargetName wire encoding error: {str(e)}")
        target_wire = b"\x00"

    # 3. Parameters Wire Validation & Canonical Ordering
    svc_params_wire = []
    parsed_keys = {}
    mandatory_keys = []

    for k_str, v_str in raw_params.items():
        try:
            k_num = parse_svc_param_key(k_str)
        except Exception as e:
            errors.append(str(e))
            continue

        if k_num in parsed_keys:
            errors.append(f"Duplicate SvcParamKey: key id {k_num}")
            continue

        val_wire = b""
        try:
            if k_num == 0:  # mandatory
                val_wire, mandatory_keys = parse_mandatory_presentation(v_str)
            elif k_num == 1:  # alpn
                val_wire = parse_alpn_presentation(v_str)
            elif k_num == 2:  # no-default-alpn
                if v_str != "":
                    errors.append(f"no-default-alpn MUST have empty value in presentation and 0-length in wire format (got '{v_str}')")
                val_wire = b""
            elif k_num == 3:  # port
                val_wire = parse_port_presentation(v_str)
            elif k_num == 4:  # ipv4hint
                val_wire = parse_ipv4hint_presentation(v_str)
            elif k_num == 5:  # ech
                # Raw bytes / hex / base64 or opaque
                try:
                    val_wire = bytes.fromhex(v_str)
                except ValueError:
                    val_wire = v_str.encode("utf-8")
            elif k_num == 6:  # ipv6hint
                val_wire = parse_ipv6hint_presentation(v_str)
            else:
                # Generic key
                val_wire = v_str.encode("utf-8")
        except Exception as e:
            errors.append(f"Parameter '{k_str}' validation failed: {str(e)}")

        parsed_keys[k_num] = {
            "name": format_svc_param_key(k_num),
            "key_num": k_num,
            "raw_val": v_str,
            "wire_val_len": len(val_wire),
            "wire_val_hex": val_wire.hex()
        }
        svc_params_wire.append((k_num, val_wire))

    # 4. Mandatory key cross-reference check
    if mandatory_keys:
        for mk in mandatory_keys:
            if mk not in parsed_keys:
                errors.append(f"Mandatory parameter key {mk} ({format_svc_param_key(mk)}) is declared in 'mandatory' but absent from record")

    # Wire sorting: RFC 9460 Section 2.2:
    # "SvcParams MUST appear in strictly ascending order by SvcParamKey in wire format."
    svc_params_wire.sort(key=lambda item: item[0])

    # Construct RDATA wire format:
    # 2 bytes priority + target_wire + list of (2 bytes key + 2 bytes len + val_wire)
    rdata_wire = bytearray()
    rdata_wire.extend(struct.pack("!H", priority))
    rdata_wire.extend(target_wire)
    for k_num, v_bytes in svc_params_wire:
        rdata_wire.extend(struct.pack("!HH", k_num, len(v_bytes)))
        rdata_wire.extend(v_bytes)

    return {
        "valid": len(errors) == 0,
        "mode": mode,
        "priority": priority,
        "target_name": target_name,
        "errors": errors,
        "warnings": warnings,
        "param_count": len(svc_params_wire),
        "wire_keys": [item[0] for item in svc_params_wire],
        "rdata_len_bytes": len(rdata_wire),
        "rdata_wire_hex": rdata_wire.hex(),
        "parsed_params": parsed_keys
    }


def parse_wire_rdata(rdata_bytes: bytes) -> Dict[str, Any]:
    """Parse and validate raw SVCB/HTTPS RDATA wire format."""
    errors = []
    if len(rdata_bytes) < 3:
        raise ValueError("RDATA too short to contain SvcPriority and TargetName root")

    priority = struct.unpack("!H", rdata_bytes[:2])[0]
    offset = 2

    # Parse uncompressed TargetName
    labels = []
    while offset < len(rdata_bytes):
        length = rdata_bytes[offset]
        offset += 1
        if length == 0:
            break
        if length & 0xC0:
            raise ValueError(f"DNS name compression detected at offset {offset-1}; RFC 9460 Section 2.2 explicitly forbids name compression in SVCB/HTTPS")
        if offset + length > len(rdata_bytes):
            raise ValueError("Truncated target name label in wire format")
        labels.append(rdata_bytes[offset:offset+length].decode("idna", errors="replace"))
        offset += length

    target_name = ".".join(labels) + "." if labels else "."

    is_alias = (priority == 0)
    mode = "AliasMode" if is_alias else "ServiceMode"

    params = []
    seen_keys = set()
    prev_key = -1

    while offset < len(rdata_bytes):
        if offset + 4 > len(rdata_bytes):
            errors.append("Truncated SvcParam header at end of RDATA")
            break
        key_num, val_len = struct.unpack("!HH", rdata_bytes[offset:offset+4])
        offset += 4

        if offset + val_len > len(rdata_bytes):
            errors.append(f"Truncated SvcParam value for key {key_num} (expected {val_len} bytes)")
            break

        val_bytes = rdata_bytes[offset:offset+val_len]
        offset += val_len

        # Check ascending order & uniqueness
        if key_num <= prev_key:
            if key_num == prev_key:
                errors.append(f"Duplicate SvcParamKey {key_num} in wire data (violates RFC 9460 Section 2.2)")
            else:
                errors.append(f"SvcParamKey {key_num} is out of ascending order (previous was {prev_key})")
        prev_key = key_num

        # Invariant checks
        if is_alias:
            errors.append(f"AliasMode wire record contains SvcParamKey {key_num} (forbidden by RFC 9460)")

        if key_num == 2 and val_len != 0:
            errors.append(f"no-default-alpn wire value length MUST be 0 (got {val_len})")

        params.append({
            "key": key_num,
            "name": format_svc_param_key(key_num),
            "length": val_len,
            "val_hex": val_bytes.hex()
        })

    return {
        "valid": len(errors) == 0,
        "mode": mode,
        "priority": priority,
        "target_name": target_name,
        "params": params,
        "errors": errors
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_svcb_record.py [--wire <hex>] | [<record-line> | <input.json>]")
        sys.exit(1)

    arg = sys.argv[1]
    if arg == "--wire":
        if len(sys.argv) < 3:
            print("Error: --wire requires hex string argument")
            sys.exit(1)
        wire_hex = sys.argv[2].strip()
        try:
            res = parse_wire_rdata(bytes.fromhex(wire_hex))
            print(json.dumps(res, indent=2))
            sys.exit(0 if res["valid"] else 2)
        except Exception as e:
            print(json.dumps({"valid": False, "errors": [str(e)]}, indent=2))
            sys.exit(2)

    # Check if arg is a file or a direct line
    if os.path.isfile(arg):
        with open(arg, "r") as f:
            content = f.read().strip()
        if content.startswith("{"):
            data = json.loads(content)
            record_line = data.get("record") or data.get("presentation")
        else:
            record_line = content
    else:
        record_line = " ".join(sys.argv[1:])

    try:
        parsed = parse_presentation_tokens(record_line)
        res = validate_and_serialize_record(parsed)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["valid"] else 2)
    except Exception as e:
        print(json.dumps({"valid": False, "errors": [str(e)]}, indent=2))
        sys.exit(2)


if __name__ == "__main__":
    main()
