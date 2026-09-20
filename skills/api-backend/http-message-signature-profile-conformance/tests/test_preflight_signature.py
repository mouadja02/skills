#!/usr/bin/env python3
"""Targeted unit tests for RFC 9421 HTTP Message Signature preflight validator."""

import json
import unittest
from pathlib import Path

# Add script directory to sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from preflight_signature import (
    preflight_http_message_signature,
    parse_inner_list,
    parse_signature_input,
    parse_signature_header,
    parse_legacy_draft_cavage,
    build_signature_base,
    SignatureConformanceError
)


class TestPreflightSignature(unittest.TestCase):
    def test_parse_inner_list(self):
        s = '("@method" "@path" "content-digest");created=1618884473;keyid="test-key-ed25519"'
        items, params = parse_inner_list(s)
        self.assertEqual(items, ['"@method"', '"@path"', '"content-digest"'])
        self.assertEqual(params["created"], 1618884473)
        self.assertEqual(params["keyid"], "test-key-ed25519")

    def test_parse_signature_input_multiple_labels(self):
        s = 'sig1=("@method" "@path");created=1000, sig2=("date");created=2000'
        res = parse_signature_input(s)
        self.assertIn("sig1", res)
        self.assertIn("sig2", res)
        self.assertEqual(res["sig1"][0], ['"@method"', '"@path"'])
        self.assertEqual(res["sig2"][1]["created"], 2000)

    def test_parse_signature_header_bytes(self):
        s = "sig1=:ZT1kooQsEHpZ0I1IjCqtQppOmIqlJPeo7DHR3SoMn0s5JZ1eRGS0A+vyYP9t/LXlh5QMFFQ6cpLt2m0pmj3NDA==:"
        res = parse_signature_header(s)
        self.assertIn("sig1", res)
        self.assertEqual(len(res["sig1"]), 64)

    def test_preflight_normal_rfc9421_success(self):
        payload = {
            "profile": {
                "name": "activitypub-federation",
                "required_components": ["@method", "@path", "@authority", "content-digest"],
                "allowed_algorithms": ["ed25519", "rsa-pss-sha512"],
                "require_created": True,
                "max_signature_age_seconds": 300
            },
            "message": {
                "method": "POST",
                "target_uri": "https://example.com/inbox",
                "headers": {
                    "Host": "example.com",
                    "Content-Digest": "sha-256=:WZDPaVn/7XgHaAy8pmojAkGWoRx2UFChF41A2svX+TaPm+AbwAgBWnrIiYllu7BNNyealdVLvRwEmTHWXvJwew==:",
                    "Signature-Input": 'sig1=("@method" "@path" "@authority" "content-digest");created=1618884473;keyid="test-key-ed25519"',
                    "Signature": "sig1=:ZT1kooQsEHpZ0I1IjCqtQppOmIqlJPeo7DHR3SoMn0s5JZ1eRGS0A+vyYP9t/LXlh5QMFFQ6cpLt2m0pmj3NDA==:"
                }
            },
            "system_clock": 1618884600
        }
        res = preflight_http_message_signature(payload)
        self.assertTrue(res["valid"])
        self.assertEqual(res["envelope_version"], "rfc9421")
        self.assertEqual(len(res["signature_base_lines"]), 5)
        self.assertIn('"@method": POST', res["signature_base_lines"])
        self.assertIn('"@path": /inbox', res["signature_base_lines"])

    def test_preflight_missing_required_component(self):
        payload = {
            "profile": {
                "required_components": ["@method", "@path", "content-digest"]
            },
            "message": {
                "method": "POST",
                "target_uri": "https://example.com/inbox",
                "headers": {
                    "Signature-Input": 'sig1=("@method" "@path");created=1618884473;keyid="key"',
                    "Signature": "sig1=:c2ln:"
                }
            },
            "system_clock": 1618884475
        }
        res = preflight_http_message_signature(payload)
        self.assertFalse(res["valid"])
        self.assertIn("missing_required_covered_component", res["rejected_reason"])

    def test_preflight_disallow_draft_cavage(self):
        payload = {
            "profile": {
                "allow_legacy_draft_cavage": False
            },
            "message": {
                "method": "POST",
                "target_uri": "https://example.com/inbox",
                "headers": {
                    "Signature": 'keyId="alice",algorithm="rsa-sha256",headers="(request-target) host",signature="abc"'
                }
            }
        }
        res = preflight_http_message_signature(payload)
        self.assertFalse(res["valid"])
        self.assertEqual(res["envelope_version"], "draft-cavage")
        self.assertEqual(res["rejected_reason"], "legacy_draft_cavage_disallowed_by_profile")

    def test_preflight_expired_signature(self):
        payload = {
            "profile": {
                "max_signature_age_seconds": 60,
                "allowed_clock_skew_seconds": 0
            },
            "message": {
                "method": "GET",
                "target_uri": "https://example.com/actor",
                "headers": {
                    "Signature-Input": 'sig1=("@method" "@path");created=1000;keyid="key"',
                    "Signature": "sig1=:c2ln:"
                }
            },
            "system_clock": 1200
        }
        res = preflight_http_message_signature(payload)
        self.assertFalse(res["valid"])
        self.assertIn("signature_expired_by_age", res["rejected_reason"])

    def test_preflight_future_created_signature(self):
        payload = {
            "profile": {
                "allowed_clock_skew_seconds": 10
            },
            "message": {
                "method": "GET",
                "target_uri": "https://example.com/actor",
                "headers": {
                    "Signature-Input": 'sig1=("@method" "@path");created=2000;keyid="key"',
                    "Signature": "sig1=:c2ln:"
                }
            },
            "system_clock": 1000
        }
        res = preflight_http_message_signature(payload)
        self.assertFalse(res["valid"])
        self.assertIn("signature_created_in_future", res["rejected_reason"])

    def test_preflight_not_applicable_unsigned(self):
        payload = {
            "profile": {},
            "message": {
                "method": "POST",
                "target_uri": "https://example.com/webhook",
                "headers": {
                    "Authorization": "Bearer 12345"
                }
            }
        }
        res = preflight_http_message_signature(payload)
        self.assertFalse(res["valid"])
        self.assertEqual(res["status"], "not_applicable")


if __name__ == "__main__":
    unittest.main()
