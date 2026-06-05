#!/usr/bin/env bash
#
# banner-png.sh — regenerate assets/banner.png from assets/banner.svg.
#
# PyPI does not render SVG in the long description, so the README serves the SVG
# to GitHub (via a <picture><source>) and this PNG to PyPI (the <img> fallback).
# Re-run this whenever assets/banner.svg changes, and commit the updated PNG.
#
# Needs a faithful SVG engine (gradients + feGaussianBlur + fonts):
#   - rsvg-convert  (brew install librsvg)            ← preferred
#   - cairosvg      (brew install cairo; uvx cairosvg) ← fallback
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SVG="$ROOT/assets/banner.svg"
PNG="$ROOT/assets/banner.png"
SCALE="${SCALE:-2}"   # 2x → crisp on retina / PyPI

[ -f "$SVG" ] || { echo "error: $SVG not found" >&2; exit 1; }

if command -v rsvg-convert >/dev/null 2>&1; then
  echo ">> rsvg-convert --zoom $SCALE"
  rsvg-convert --zoom "$SCALE" "$SVG" -o "$PNG"
elif command -v cairosvg >/dev/null 2>&1 || uvx --from cairosvg cairosvg --help >/dev/null 2>&1; then
  W=$(( 1280 * SCALE )); H=$(( 320 * SCALE ))
  echo ">> cairosvg ${W}x${H}"
  uvx --from cairosvg cairosvg "$SVG" -o "$PNG" --output-width "$W" --output-height "$H"
else
  echo "error: no SVG converter found. Install one:" >&2
  echo "  brew install librsvg   # provides rsvg-convert (preferred)" >&2
  echo "  brew install cairo     # lets 'uvx cairosvg' work" >&2
  exit 1
fi

echo ">> wrote $PNG ($(du -h "$PNG" | cut -f1))"
