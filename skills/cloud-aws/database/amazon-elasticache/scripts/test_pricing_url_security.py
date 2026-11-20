import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pricing


class PricingURLTests(unittest.TestCase):
    def test_redirects_stay_on_aws_https_origin(self):
        handler = pricing._PricingRedirectHandler()
        req = Request("https://pricing.us-east-1.amazonaws.com/start")
        for target in ("http://pricing.us-east-1.amazonaws.com/path",
                       "https://example.com/path",
                       "https://pricing.us-east-1.amazonaws.com@example.com/path",
                       "file:///tmp/pricing"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                handler.redirect_request(req, None, 302, "Found", {}, target)
        redirected = handler.redirect_request(
            req, None, 302, "Found", {},
            "https://pricing.us-east-1.amazonaws.com/other")
        self.assertEqual(redirected.full_url, "https://pricing.us-east-1.amazonaws.com/other")

    def test_fetch_uses_expected_endpoint(self):
        import tempfile
        response = io.BytesIO(b'{"products": {}, "terms": {}}')
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(pricing, "_CACHE_DIR", tmp), \
             patch.object(pricing, "_CACHE_FILE", str(Path(tmp) / "cache.json")), \
             patch.object(pricing.urllib.request, "build_opener") as build:
            build.return_value.open.return_value.__enter__.return_value = response
            self.assertIn("fetched_at", pricing._fetch_and_cache())
            req = build.return_value.open.call_args.args[0]
            self.assertEqual(req.full_url, pricing.BULK_PRICING_URL)
            self.assertIsInstance(build.call_args.args[0], pricing._PricingRedirectHandler)


if __name__ == "__main__":
    unittest.main()
