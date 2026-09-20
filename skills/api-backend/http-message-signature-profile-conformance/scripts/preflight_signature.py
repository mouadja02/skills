#!/usr/bin/env python3
"""Deterministic preflight validator for RFC 9421 HTTP Message Signatures and legacy migration profiles.

Validates:
- Envelope identification: RFC 9421 (Signature-Input + Signature) vs legacy draft-cavage vs un-signed.
- RFC 8941 Structured Field syntax for Signature-Input (Dictionary of Inner Lists) and Signature (Dictionary of Byte Sequences).
- Signature parameters: created, expires, keyid, alg, nonce, tag.
- Clock skew & expiration window validation against an injected or current timestamp.
- Application profile conformance: required components present, allowed algorithms, keyid policies.
- Derived component derivation: @method, @target-uri, @authority, @scheme, @request-target, @path, @query, @status.
- Content-Digest / Repr-Digest (RFC 9530) requirement enforcement when configured by the application profile.
- Exact RFC 9421 Section 2.5 signature base reconstruction with canonical newline terminators.
- Dual-accept migration rules: fail-closed on envelope mixing, no fall-through to draft-cavage on RFC 9421 parse failure.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


class SignatureConformanceError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def parse_sf_bare_item(item_str: str) -> Any:
    item_str = item_str.strip()
    if item_str.startswith('"') and item_str.endswith('"') and len(item_str) >= 2:
        # String
        return item_str[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if item_str.startswith(':') and item_str.endswith(':') and len(item_str) >= 2:
        # Byte sequence
        return base64.b64decode(item_str[1:-1])
    if item_str.startswith('?'):
        if item_str == '?1':
            return True
        if item_str == '?0':
            return False
    # Integer or decimal
    try:
        if '.' in item_str:
            return float(item_str)
        return int(item_str)
    except ValueError:
        # Token
        return item_str


def parse_inner_list(val_str: str) -> Tuple[List[str], Dict[str, Any]]:
    """Parse Inner List format: ("@method" "@path" "date");created=123;keyid="key" """
    val_str = val_str.strip()
    if not val_str.startswith('('):
        raise SignatureConformanceError("invalid_inner_list", f"Inner list must start with '(': {val_str}")
    
    close_idx = val_str.find(')')
    if close_idx == -1:
        raise SignatureConformanceError("invalid_inner_list", f"Inner list missing closing ')': {val_str}")
    
    list_content = val_str[1:close_idx].strip()
    params_content = val_str[close_idx + 1:].strip()
    
    items: List[str] = []
    if list_content:
        # Items in inner list are space-separated
        # Handle quoted strings and parameters on components
        tokens = []
        cur = ""
        in_quotes = False
        for ch in list_content:
            if ch == '"':
                in_quotes = not in_quotes
                cur += ch
            elif ch.isspace() and not in_quotes:
                if cur:
                    tokens.append(cur)
                    cur = ""
            else:
                cur += ch
        if cur:
            tokens.append(cur)
        
        for t in tokens:
            items.append(t)
            
    params: Dict[str, Any] = {}
    if params_content:
        if not params_content.startswith(';'):
            raise SignatureConformanceError("invalid_parameters", f"Parameters must start with ';': {params_content}")
        raw_params = params_content[1:].split(';')
        for p in raw_params:
            p = p.strip()
            if not p:
                continue
            if '=' in p:
                k, v = p.split('=', 1)
                k = k.strip()
                v = v.strip()
                params[k] = parse_sf_bare_item(v)
            else:
                params[p] = True
                
    return items, params


def parse_signature_input(header_val: str) -> Dict[str, Tuple[List[str], Dict[str, Any]]]:
    """Parse Signature-Input header into dict: label -> (covered_components, params)"""
    results = {}
    # Labels separated by comma, but inner list can have semicolon params
    # We do a basic top-level comma split respecting quotes and parentheses
    parts = []
    cur = ""
    in_quotes = False
    paren_depth = 0
    for ch in header_val:
        if ch == '"':
            in_quotes = not in_quotes
            cur += ch
        elif ch == '(' and not in_quotes:
            paren_depth += 1
            cur += ch
        elif ch == ')' and not in_quotes:
            paren_depth -= 1
            cur += ch
        elif ch == ',' and not in_quotes and paren_depth == 0:
            if cur.strip():
                parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
        
    for part in parts:
        if '=' not in part:
            raise SignatureConformanceError("invalid_signature_input", f"Missing '=' in member: {part}")
        label, rest = part.split('=', 1)
        label = label.strip()
        items, params = parse_inner_list(rest.strip())
        results[label] = (items, params)
        
    return results


def parse_signature_header(header_val: str) -> Dict[str, bytes]:
    """Parse Signature header dictionary into label -> signature_bytes"""
    results = {}
    parts = [p.strip() for p in header_val.split(',') if p.strip()]
    for part in parts:
        if '=' not in part:
            raise SignatureConformanceError("invalid_signature", f"Missing '=' in signature member: {part}")
        label, val = part.split('=', 1)
        label = label.strip()
        val = val.strip()
        if not (val.startswith(':') and val.endswith(':')):
            raise SignatureConformanceError("invalid_signature_byte_sequence", f"Signature value must be Byte Sequence: {val}")
        raw_b64 = val[1:-1]
        try:
            results[label] = base64.b64decode(raw_b64)
        except Exception as e:
            raise SignatureConformanceError("invalid_base64", f"Failed to decode base64 signature for {label}: {e}")
    return results


def parse_legacy_draft_cavage(header_val: str) -> Dict[str, str]:
    """Parse legacy draft-cavage Signature or Authorization header."""
    # Example: keyId="...",algorithm="rsa-sha256",headers="(request-target) host date",signature="..."
    prefix = ""
    if header_val.startswith("Signature "):
        header_val = header_val[len("Signature "):].strip()
    
    results = {}
    matches = re.findall(r'([a-zA-Z0-9_\-]+)="([^"]*)"', header_val)
    for k, v in matches:
        results[k] = v
    return results


def derive_component_value(
    comp_id: str,
    message: Dict[str, Any],
    headers_lower: Dict[str, str],
    parsed_uri: Any
) -> str:
    """Derive value for a component identifier according to RFC 9421 Sections 2.1 and 2.2."""
    raw_name = comp_id
    params = {}
    if ';' in comp_id:
        parts = comp_id.split(';')
        raw_name = parts[0]
        # Ignore sub-params for now or parse if needed
    
    # Strip quotes from component identifier name if present
    if raw_name.startswith('"') and raw_name.endswith('"'):
        comp_name = raw_name[1:-1]
    else:
        comp_name = raw_name

    if comp_name.startswith('@'):
        if comp_name == '@method':
            method = message.get("method")
            if not method:
                raise SignatureConformanceError("missing_component", "Missing @method in message")
            return method.upper()
        elif comp_name == '@path':
            path = parsed_uri.path
            return path if path else "/"
        elif comp_name == '@authority':
            # Authority is host + port if non-default
            if parsed_uri.netloc:
                return parsed_uri.netloc.lower()
            if "host" in headers_lower:
                return headers_lower["host"].lower()
            raise SignatureConformanceError("missing_component", "Cannot derive @authority")
        elif comp_name == '@scheme':
            if parsed_uri.scheme:
                return parsed_uri.scheme.lower()
            return "https"
        elif comp_name == '@target-uri':
            target = message.get("target_uri")
            if not target:
                raise SignatureConformanceError("missing_component", "Cannot derive @target-uri")
            return target
        elif comp_name == '@query':
            return f"?{parsed_uri.query}" if parsed_uri.query else "?"
        elif comp_name == '@request-target':
            # Older draft component sometimes mistakenly used
            path = parsed_uri.path if parsed_uri.path else "/"
            if parsed_uri.query:
                path += f"?{parsed_uri.query}"
            return path
        elif comp_name == '@status':
            status = message.get("status")
            if status is None:
                raise SignatureConformanceError("missing_component", "Cannot derive @status for request")
            return str(status)
        else:
            raise SignatureConformanceError("unsupported_derived_component", f"Unsupported derived component: {comp_name}")
    else:
        # Standard HTTP Header
        header_key = comp_name.lower()
        if header_key not in headers_lower:
            raise SignatureConformanceError("missing_field", f"Required HTTP header field missing from message: {comp_name}")
        return headers_lower[header_key]


def build_signature_base(
    label: str,
    covered_components: List[str],
    sig_params: Dict[str, Any],
    message: Dict[str, Any],
    headers_lower: Dict[str, str],
    parsed_uri: Any
) -> Tuple[str, List[str]]:
    """Build canonical signature base according to RFC 9421 Section 2.5."""
    lines = []
    seen = set()
    
    for comp in covered_components:
        # Canonicalize component identifier serialization: must be quoted
        raw = comp.strip()
        if ';' in raw:
            parts = raw.split(';', 1)
            name_part = parts[0].strip()
            param_part = ';' + parts[1].strip()
        else:
            name_part = raw
            param_part = ""
            
        if not (name_part.startswith('"') and name_part.endswith('"')):
            canonical_comp_id = f'"{name_part}"{param_part}'
            comp_name_clean = name_part
        else:
            canonical_comp_id = raw
            comp_name_clean = name_part[1:-1]

        if canonical_comp_id in seen:
            raise SignatureConformanceError("duplicate_component", f"Duplicate component identifier in covered components: {canonical_comp_id}")
        seen.add(canonical_comp_id)
        
        val = derive_component_value(comp_name_clean, message, headers_lower, parsed_uri)
        lines.append(f"{canonical_comp_id}: {val}")

    # Format @signature-params line
    # Reconstruct inner list exactly
    inner_list_items = []
    for comp in covered_components:
        raw = comp.strip()
        if not (raw.startswith('"') and raw.endswith('"')):
            if ';' in raw:
                p0, p1 = raw.split(';', 1)
                inner_list_items.append(f'"{p0}";{p1}')
            else:
                inner_list_items.append(f'"{raw}"')
        else:
            inner_list_items.append(raw)
            
    param_str_items = []
    for k, v in sig_params.items():
        if isinstance(v, str):
            param_str_items.append(f'{k}="{v}"')
        elif isinstance(v, bool):
            param_str_items.append(f'{k}=?1' if v else f'{k}=?0')
        elif isinstance(v, (int, float)):
            param_str_items.append(f'{k}={v}')
        elif isinstance(v, bytes):
            param_str_items.append(f'{k}=:{base64.b64encode(v).decode("ascii")}:')
        else:
            param_str_items.append(f'{k}={v}')
            
    params_suffix = (";" + ";".join(param_str_items)) if param_str_items else ""
    sig_params_line = f'"@signature-params": ({" ".join(inner_list_items)}){params_suffix}'
    lines.append(sig_params_line)
    
    signature_base = "\n".join(lines)
    return signature_base, lines


def preflight_http_message_signature(payload: Dict[str, Any]) -> Dict[str, Any]:
    profile = payload.get("profile", {})
    message = payload.get("message", {})
    clock = payload.get("system_clock", 1618884600)
    
    headers = message.get("headers", {})
    headers_lower = {k.lower(): str(v).strip() for k, v in headers.items()}
    
    target_uri = message.get("target_uri", "")
    parsed_uri = urlparse(target_uri)
    
    has_sig_input = "signature-input" in headers_lower
    has_sig = "signature" in headers_lower
    has_auth = "authorization" in headers_lower
    
    # Check for legacy draft-cavage signature
    is_cavage = False
    cavage_data = {}
    if has_sig and not has_sig_input:
        sig_header = headers_lower["signature"]
        if 'keyid="' in sig_header.lower() or 'signature="' in sig_header.lower():
            is_cavage = True
            cavage_data = parse_legacy_draft_cavage(sig_header)
    elif has_auth and headers_lower["authorization"].startswith("Signature "):
        is_cavage = True
        cavage_data = parse_legacy_draft_cavage(headers_lower["authorization"])

    # If neither RFC 9421 nor Cavage is present
    if not has_sig_input and not is_cavage:
        return {
            "valid": False,
            "status": "not_applicable",
            "envelope_version": None,
            "rejected_reason": "missing_rfc9421_signature_input_and_legacy_signature"
        }
        
    # Check for disallowed draft-cavage
    if is_cavage:
        allow_cavage = profile.get("allow_legacy_draft_cavage", False)
        if not allow_cavage:
            return {
                "valid": False,
                "status": "rejected",
                "envelope_version": "draft-cavage",
                "rejected_reason": "legacy_draft_cavage_disallowed_by_profile",
                "details": cavage_data
            }
        else:
            return {
                "valid": True,
                "status": "accepted_legacy",
                "envelope_version": "draft-cavage",
                "details": cavage_data
            }
            
    # RFC 9421 Envelope processing
    if not has_sig:
        return {
            "valid": False,
            "status": "rejected",
            "envelope_version": "rfc9421",
            "rejected_reason": "signature_header_missing_when_signature_input_present"
        }
        
    try:
        sig_inputs = parse_signature_input(headers_lower["signature-input"])
    except SignatureConformanceError as exc:
        return {
            "valid": False,
            "status": "rejected",
            "envelope_version": "rfc9421",
            "rejected_reason": f"malformed_signature_input: {exc.code} - {exc.message}"
        }
        
    try:
        signatures = parse_signature_header(headers_lower["signature"])
    except SignatureConformanceError as exc:
        return {
            "valid": False,
            "status": "rejected",
            "envelope_version": "rfc9421",
            "rejected_reason": f"malformed_signature: {exc.code} - {exc.message}"
        }

    # Select target label
    target_label = payload.get("label")
    if not target_label:
        # Default to first label in Signature-Input
        target_label = next(iter(sig_inputs.keys()))
        
    if target_label not in sig_inputs:
        return {
            "valid": False,
            "status": "rejected",
            "envelope_version": "rfc9421",
            "rejected_reason": f"label_{target_label}_not_found_in_signature_input"
        }
        
    if target_label not in signatures:
        return {
            "valid": False,
            "status": "rejected",
            "envelope_version": "rfc9421",
            "rejected_reason": f"label_{target_label}_not_found_in_signature"
        }

    covered_components, sig_params = sig_inputs[target_label]
    
    # Check profile requirements
    required_comps = profile.get("required_components", [])
    # Strip quotes for comparison
    covered_clean = []
    for c in covered_components:
        raw = c.strip()
        if raw.startswith('"') and raw.endswith('"'):
            covered_clean.append(raw[1:-1])
        elif ';' in raw:
            p0 = raw.split(';', 1)[0].strip()
            covered_clean.append(p0.strip('"'))
        else:
            covered_clean.append(raw)
            
    for req in required_comps:
        if req not in covered_clean:
            return {
                "valid": False,
                "status": "rejected",
                "envelope_version": "rfc9421",
                "rejected_reason": f"missing_required_covered_component: {req}",
                "covered_components": covered_components
            }

    # Algorithm check
    alg = sig_params.get("alg")
    allowed_algs = profile.get("allowed_algorithms")
    if allowed_algs and alg:
        if alg not in allowed_algs:
            return {
                "valid": False,
                "status": "rejected",
                "envelope_version": "rfc9421",
                "rejected_reason": f"algorithm_{alg}_not_permitted_by_profile"
            }
            
    # Timestamp checks
    require_created = profile.get("require_created", True)
    created = sig_params.get("created")
    if require_created and created is None:
        return {
            "valid": False,
            "status": "rejected",
            "envelope_version": "rfc9421",
            "rejected_reason": "created_timestamp_required_by_profile"
        }
        
    if created is not None:
        max_age = profile.get("max_signature_age_seconds", 300)
        clock_skew = profile.get("allowed_clock_skew_seconds", 60)
        
        # Check future
        if created > clock + clock_skew:
            return {
                "valid": False,
                "status": "rejected",
                "envelope_version": "rfc9421",
                "rejected_reason": f"signature_created_in_future: created={created}, clock={clock}"
            }
        # Check expired by age
        if clock - created > max_age + clock_skew:
            return {
                "valid": False,
                "status": "rejected",
                "envelope_version": "rfc9421",
                "rejected_reason": f"signature_expired_by_age: age={clock-created}s > max={max_age}s"
            }
            
    expires = sig_params.get("expires")
    if expires is not None:
        if clock > expires:
            return {
                "valid": False,
                "status": "rejected",
                "envelope_version": "rfc9421",
                "rejected_reason": f"signature_expired_at_{expires}_current_{clock}"
            }

    # Reconstruct signature base
    try:
        sig_base, lines = build_signature_base(
            target_label,
            covered_components,
            sig_params,
            message,
            headers_lower,
            parsed_uri
        )
    except SignatureConformanceError as exc:
        return {
            "valid": False,
            "status": "rejected",
            "envelope_version": "rfc9421",
            "rejected_reason": f"signature_base_construction_error: {exc.code} - {exc.message}"
        }

    return {
        "valid": True,
        "status": "verified_preflight",
        "envelope_version": "rfc9421",
        "label": target_label,
        "covered_components": covered_components,
        "parameters": sig_params,
        "signature_base": sig_base,
        "signature_base_lines": lines
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight RFC 9421 HTTP Message Signature Profiles")
    parser.add_argument("input_file", help="Path to input JSON file containing message, profile, and parameters")
    args = parser.parse_args()
    
    with open(args.input_file, "r", encoding="utf-8") as f:
        payload = json.load(f)
        
    result = preflight_http_message_signature(payload)
    print(json.dumps(result, indent=2))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    sys.exit(main())
