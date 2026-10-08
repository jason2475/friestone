#!/usr/bin/env python3
"""Polymarket event adapter.

Fetches one event from the Polymarket Gamma API by slug and prints its
markets as normalized JSON on stdout. Standard library only.

Usage:
    python3 adapters/polymarket_adapter.py <event-slug>
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

GAMMA_API_BASE_URL = "https://gamma-api.polymarket.com"
TIMEOUT_SECONDS = 10
MAX_ATTEMPTS = 3


def fetch_event(slug, opener=urllib.request.urlopen):
    """Return the first event matching slug, or None if none exists."""
    query = urllib.parse.urlencode({"slug": slug, "archived": "false"})
    url = f"{GAMMA_API_BASE_URL}/events?{query}"
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with opener(url, timeout=TIMEOUT_SECONDS) as response:
                events = json.load(response)
            return events[0] if events else None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_error = e
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Gamma API request failed after {MAX_ATTEMPTS} attempts: {last_error}")


def _parse_list(value):
    # Gamma returns outcomes/outcomePrices as JSON-encoded strings.
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return []
    return value if isinstance(value, list) else []


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_event(event):
    """Reduce a raw Gamma event to the fields the pipeline uses."""
    markets = []
    for market in event.get("markets", []):
        outcomes = _parse_list(market.get("outcomes"))
        prices = [_to_float(p) for p in _parse_list(market.get("outcomePrices"))]
        markets.append({
            "id": market.get("id"),
            "slug": market.get("slug"),
            "question": market.get("question"),
            "outcomes": dict(zip(outcomes, prices)),
            "best_bid": _to_float(market.get("bestBid")),
            "best_ask": _to_float(market.get("bestAsk")),
            "volume": _to_float(market.get("volume")),
            "active": market.get("active"),
            "closed": market.get("closed"),
            "end_date": market.get("endDate"),
        })
    return {
        "event_id": event.get("id"),
        "slug": event.get("slug"),
        "title": event.get("title"),
        "markets": markets,
    }


def main(argv):
    if len(argv) != 2:
        print("usage: polymarket_adapter.py <event-slug>", file=sys.stderr)
        return 2
    try:
        event = fetch_event(argv[1])
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 1
    if event is None:
        print(f"No event found with slug: {argv[1]}", file=sys.stderr)
        return 3
    json.dump(normalize_event(event), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
