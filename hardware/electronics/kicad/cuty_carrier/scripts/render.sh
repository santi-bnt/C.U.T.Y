#!/bin/bash
# render.sh OUT.png LAYERS  -> PNG of the board area (white background)
set -e
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
kicad-cli pcb export svg --exclude-drawing-sheet --page-size-mode 2 --layers "$2" -o "$tmp/b.svg" cuty_carrier.kicad_pcb >/dev/null
rsvg-convert -b white -z ${3:-6} "$tmp/b.svg" -o "$1"
rm -rf "$tmp"
