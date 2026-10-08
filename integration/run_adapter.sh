#!/bin/bash
# Usage: integration/run_adapter.sh <event-slug>
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$REPO_ROOT/adapters/polymarket_adapter.py" "$@"
