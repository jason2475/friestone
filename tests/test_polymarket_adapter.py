import io
import json
import os
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "adapters"))
import polymarket_adapter as adapter  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "gamma_event.json")


def fake_opener(payload):
    def opener(url, timeout):
        return io.BytesIO(payload.encode())
    return opener


class FetchEventTest(unittest.TestCase):
    def test_returns_first_event(self):
        with open(FIXTURE) as f:
            event = adapter.fetch_event("sample-event", opener=fake_opener(f.read()))
        self.assertEqual(event["slug"], "sample-event")

    def test_returns_none_when_no_event(self):
        self.assertIsNone(adapter.fetch_event("missing", opener=fake_opener("[]")))

    @mock.patch.object(adapter.time, "sleep")
    def test_raises_after_retries(self, sleep):
        def failing(url, timeout):
            raise urllib.error.URLError("blocked")
        with self.assertRaises(RuntimeError):
            adapter.fetch_event("x", opener=failing)
        self.assertEqual(sleep.call_count, adapter.MAX_ATTEMPTS - 1)


class NormalizeEventTest(unittest.TestCase):
    def setUp(self):
        with open(FIXTURE) as f:
            self.result = adapter.normalize_event(json.load(f)[0])

    def test_parses_outcome_prices(self):
        market = self.result["markets"][0]
        self.assertEqual(market["outcomes"], {"Yes": 0.62, "No": 0.38})
        self.assertEqual(market["best_bid"], 0.61)
        self.assertEqual(market["volume"], 15000.5)

    def test_tolerates_missing_fields(self):
        market = self.result["markets"][1]
        self.assertEqual(market["outcomes"], {})
        self.assertIsNone(market["best_ask"])


if __name__ == "__main__":
    unittest.main()
