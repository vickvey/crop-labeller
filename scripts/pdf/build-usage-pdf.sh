#!/bin/sh
# Regenerate USAGE-GUIDELINES.pdf from USAGE-GUIDELINES.md, and fail loudly if it
# wasn't actually rewritten.
#   scripts/pdf/build-usage-pdf.sh
# Uses an installed Chrome if $PUPPETEER_EXECUTABLE_PATH is unset and one is found.
set -e
cd "$(dirname "$0")/../.."
if [ -z "$PUPPETEER_EXECUTABLE_PATH" ]; then
  for c in google-chrome google-chrome-stable chromium chromium-browser; do
    if command -v "$c" >/dev/null 2>&1; then export PUPPETEER_EXECUTABLE_PATH="$(command -v "$c")"; break; fi
  done
fi
marker=$(mktemp)
# </dev/null: md-to-pdf reads stdin first. From a pipe or a non-interactive shell it
# either hangs or converts stdin to stdout instead of writing the file.
npx --yes md-to-pdf --config-file scripts/pdf/md-to-pdf.config.cjs USAGE-GUIDELINES.md </dev/null
if [ ! USAGE-GUIDELINES.pdf -nt "$marker" ]; then
  rm -f "$marker"; echo "ERROR: USAGE-GUIDELINES.pdf was not regenerated" >&2; exit 1
fi
rm -f "$marker"
echo "Wrote USAGE-GUIDELINES.pdf"
