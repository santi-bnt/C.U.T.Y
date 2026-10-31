#!/usr/bin/env bash
set -euo pipefail
cuty_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$cuty_root/raspberry/touchscreen/install.sh" "$@"
