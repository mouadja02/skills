import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acu_calculator


class PricingURLTests(unittest.TestCase):
    def test_redirects_stay_on_aws_https_origin(self):
        handler = acu_calculator._PricingRedirectHandler()
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

    def test_region_validated_before_fetch(self):
        with patch.object(acu_calculator.urllib.request, "build_opener") as build:
            for region in ("../other", "us-east-1/../../other", "us-east-1?x=1", "us-east-1\n"):
                with self.subTest(region=region), self.assertRaises(ValueError):
                    acu_calculator._fetch_instance_pricing_bulk(region)
            build.assert_not_called()

    def test_valid_region_fetches_expected_endpoint(self):
        response = io.BytesIO(b"SKU,Database Engine\n")
        with patch.object(acu_calculator.urllib.request, "build_opener") as build:
            build.return_value.open.return_value.__enter__.return_value = response
            self.assertEqual(acu_calculator._fetch_instance_pricing_bulk("us-gov-west-1"), {})
            req = build.return_value.open.call_args.args[0]
            self.assertEqual(req.full_url, "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/us-gov-west-1/index.csv")
            self.assertIsInstance(build.call_args.args[0], acu_calculator._PricingRedirectHandler)


if __name__ == "__main__":
    unittest.main()
