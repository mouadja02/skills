#!/usr/bin/env python3
"""
Targeted tests for RFC 9460 SVCB/HTTPS Conformance Validator.
"""

import unittest
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from validate_svcb_record import (
    parse_presentation_tokens,
    validate_and_serialize_record,
    parse_wire_rdata,
    parse_target_name,
)


class TestSVCBHTTPSConformance(unittest.TestCase):
    def test_valid_servicemode_normal(self):
        line = 'example.com. 7200 IN HTTPS 1 . alpn="h2,h3" port=443'
        parsed = parse_presentation_tokens(line)
        self.assertEqual(parsed["priority"], 1)
        self.assertEqual(parsed["target_name"], ".")
        res = validate_and_serialize_record(parsed)
        self.assertTrue(res["valid"])
        self.assertEqual(res["mode"], "ServiceMode")
        self.assertEqual(res["wire_keys"], [1, 3])  # alpn (1), port (3)
        self.assertFalse(res["errors"])

    def test_valid_aliasmode(self):
        line = 'example.com. 3600 IN HTTPS 0 svc.target.example.net.'
        parsed = parse_presentation_tokens(line)
        self.assertEqual(parsed["priority"], 0)
        res = validate_and_serialize_record(parsed)
        self.assertTrue(res["valid"])
        self.assertEqual(res["mode"], "AliasMode")
        self.assertEqual(res["param_count"], 0)

    def test_invalid_aliasmode_with_params(self):
        # RFC 9460 Section 2.4.2: AliasMode records MUST NOT contain SvcParams
        line = 'example.com. 3600 IN HTTPS 0 target.example.com. alpn="h3"'
        parsed = parse_presentation_tokens(line)
        res = validate_and_serialize_record(parsed)
        self.assertFalse(res["valid"])
        self.assertTrue(any("AliasMode (priority 0) MUST NOT contain any SvcParams" in e for e in res["errors"]))

    def test_invalid_aliasmode_root_target(self):
        # RFC 9460 Section 2.4.2: AliasMode TargetName MUST NOT be "."
        line = 'example.com. 3600 IN HTTPS 0 .'
        parsed = parse_presentation_tokens(line)
        res = validate_and_serialize_record(parsed)
        self.assertFalse(res["valid"])
        self.assertTrue(any("AliasMode TargetName MUST NOT be '.'" in e for e in res["errors"]))

    def test_invalid_no_default_alpn_presentation_value(self):
        # RFC 9460 Section 7.1: no-default-alpn has empty wire value and presentation format
        line = 'example.com. 3600 IN HTTPS 1 . no-default-alpn="true"'
        parsed = parse_presentation_tokens(line)
        res = validate_and_serialize_record(parsed)
        self.assertFalse(res["valid"])
        self.assertTrue(any("no-default-alpn MUST have empty value" in e for e in res["errors"]))

    def test_valid_no_default_alpn_empty_value(self):
        line = 'example.com. 3600 IN HTTPS 1 . alpn="h3" no-default-alpn'
        parsed = parse_presentation_tokens(line)
        res = validate_and_serialize_record(parsed)
        self.assertTrue(res["valid"])
        self.assertIn(2, res["wire_keys"])

    def test_mandatory_keys_validation(self):
        # 1. Mandatory referencing present keys: valid
        line = 'example.com. 3600 IN HTTPS 1 . mandatory=alpn,port alpn="h2" port=8443'
        parsed = parse_presentation_tokens(line)
        res = validate_and_serialize_record(parsed)
        self.assertTrue(res["valid"])
        self.assertEqual(res["wire_keys"], [0, 1, 3])  # mandatory (0), alpn (1), port (3)

        # 2. Mandatory referencing missing key: invalid
        line_missing = 'example.com. 3600 IN HTTPS 1 . mandatory=ipv4hint alpn="h2"'
        parsed_missing = parse_presentation_tokens(line_missing)
        res_missing = validate_and_serialize_record(parsed_missing)
        self.assertFalse(res_missing["valid"])
        self.assertTrue(any("declared in 'mandatory' but absent" in e for e in res_missing["errors"]))

        # 3. Mandatory referencing mandatory (0): invalid
        line_zero = 'example.com. 3600 IN HTTPS 1 . mandatory=mandatory alpn="h2"'
        parsed_zero = parse_presentation_tokens(line_zero)
        res_zero = validate_and_serialize_record(parsed_zero)
        self.assertFalse(res_zero["valid"])
        self.assertTrue(any("MUST NOT include 'mandatory' (0)" in e for e in res_zero["errors"]))

    def test_ip_hints_validation(self):
        line = 'example.com. 3600 IN HTTPS 1 . ipv4hint=192.0.2.1,198.51.100.2 ipv6hint=2001:db8::1'
        parsed = parse_presentation_tokens(line)
        res = validate_and_serialize_record(parsed)
        self.assertTrue(res["valid"])
        self.assertEqual(res["parsed_params"][4]["wire_val_len"], 8)  # 2 IPv4 addresses = 8 bytes
        self.assertEqual(res["parsed_params"][6]["wire_val_len"], 16)  # 1 IPv6 address = 16 bytes

    def test_wire_roundtrip_and_sorting(self):
        # SvcParams must appear in strictly ascending order by SvcParamKey in wire format
        # In presentation, we specify keys out of order: port (3), alpn (1)
        line = 'example.com. 3600 IN HTTPS 1 . port=443 alpn="h2"'
        parsed = parse_presentation_tokens(line)
        res = validate_and_serialize_record(parsed)
        self.assertTrue(res["valid"])
        wire_hex = res["rdata_wire_hex"]

        # Parse wire bytes back
        wire_res = parse_wire_rdata(bytes.fromhex(wire_hex))
        self.assertTrue(wire_res["valid"])
        self.assertEqual([p["key"] for p in wire_res["params"]], [1, 3])

    def test_wire_forbidden_compression(self):
        # Construct RDATA where target name starts with compression pointer 0xC0
        bogus_wire = bytearray()
        bogus_wire.extend(b"\x00\x01")  # priority 1
        bogus_wire.extend(b"\xc0\x0c")  # compression pointer
        with self.assertRaises(ValueError) as ctx:
            parse_wire_rdata(bytes(bogus_wire))
        self.assertIn("name compression detected", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
