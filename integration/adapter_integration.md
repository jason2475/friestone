Adapter integration for polymarket-data-scraper

The adapter now lives in this repository: adapters/polymarket_adapter.py
(standard library only, no external dependencies).

Run:
    integration/run_adapter.sh <event-slug>

Output: normalized event JSON on stdout (event id/slug/title, and per market:
question, outcome prices, best bid/ask, volume, active/closed, end date).
Exit codes: 0 ok, 1 API failure after 3 retries, 2 bad usage, 3 slug not found.

Tests (offline, no network needed):
    python3 -m unittest discover -s tests
