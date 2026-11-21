#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.cargo/bin:/opt/homebrew/bin:$PATH"
python3 "${SCRIPT_DIR}/scripts/build_vyron_iso.py"
