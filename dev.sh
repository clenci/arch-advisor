#!/usr/bin/env bash
# Load arch-advisor from local source — edits reflected immediately, no install needed.
# Usage: ./dev.sh [any claude arguments]
exec claude --plugin-dir "$(dirname "$0")/arch-advisor" "$@"
