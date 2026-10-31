#!/usr/bin/env bash
set -euo pipefail
cuty_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$cuty_script_dir/.."
if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt
printf '%s\n' 'Ready. Create a private .env from .env.example, then run .venv/bin/python -m cuty here.'
