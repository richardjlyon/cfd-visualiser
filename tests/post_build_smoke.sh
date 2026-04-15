#!/usr/bin/env bash
# Post-build smoke test for Phase 01.1 dist/ artefacts.
#
# Asserts the built site has:
#   - landing page with id="shock-numeral"
#   - 4 chart detail pages (scissors + 3 placeholders)
#   - 4 chart PNGs under assets/charts/
#   - tailwind.css bundle > 1KB
#   - NO pico CSS leak (Phase 01 stylesheet must be gone)
#   - glossary.json reachable for the tooltip client fetch
#
# Exit codes:
#   0   pass
#   1   fail (with FAIL: message)
#   2   skip (dist/ does not exist — build not run yet)
set -euo pipefail

DIST=${DIST:-dist}

fail() { echo "FAIL: $*" >&2; exit 1; }

[ -d "$DIST" ] || { echo "SKIP: $DIST/ missing — run 'npm run build' first" >&2; exit 2; }

# Landing page
[ -f "$DIST/index.html" ] || fail "index.html missing"
grep -q 'id="shock-numeral"' "$DIST/index.html" || fail "shock-numeral missing from landing"

# 4 chart detail pages (Framework may nest as /slug/index.html or /slug.html)
for slug in scissors co2-avoided cumulative-subsidy generation-heatmap; do
  if [ ! -f "$DIST/charts/$slug/index.html" ] && [ ! -f "$DIST/charts/$slug.html" ]; then
    fail "chart page $slug missing (neither charts/$slug/index.html nor charts/$slug.html)"
  fi
done

# Per-chart PNGs
for png in chart-3c.png chart-co2-avoided-placeholder.png \
           chart-cumulative-subsidy-placeholder.png chart-heatmap-placeholder.png; do
  [ -f "$DIST/assets/charts/$png" ] || fail "PNG $png missing from assets/charts/"
done

# Tailwind bundle
TW="$DIST/assets/tailwind.css"
[ -f "$TW" ] || fail "assets/tailwind.css missing"
SIZE=$(wc -c < "$TW")
[ "$SIZE" -gt 1024 ] || fail "assets/tailwind.css suspiciously small (${SIZE} bytes)"

# Pico must not leak (reference Phase 01 stylesheet)
if find "$DIST" -name '*.css' -print0 | xargs -0 grep -l 'pico' 2>/dev/null | grep -q .; then
  fail "pico CSS leaked into dist"
fi

# Glossary JSON reachable (fetched by client)
[ -f "$DIST/content/glossary.json" ] || [ -f "$DIST/_file/content/glossary.json" ] \
  || find "$DIST/_file/content" -name 'glossary.*.json' 2>/dev/null | grep -q . \
  || fail "glossary.json not in dist/ (tooltip will 404)"

echo "ok: post-build smoke passed"
