#!/usr/bin/env bash
# Verification for the v3 deliverables -> renders/v3/checks/*.txt
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"; export PYTHON="$PY"; C=renders/v3/checks; mkdir -p "$C"
: > "$C/coverage.txt"
for f in index vertical ad15; do echo "== $f.html" >> "$C/coverage.txt"; tools/coverage_debug.sh $f.html >> "$C/coverage.txt" 2>&1 || true; done
: > "$C/loudness.txt"
for f in renders/envkit-promo-v3-master.mp4 renders/envkit-promo-v3-16x9.mp4 renders/envkit-promo-v3-9x16.mp4 renders/envkit-promo-v3-15s.mp4 renders/envkit-demo-v3.mp4; do
  echo "== $f" >> "$C/loudness.txt"
  ffmpeg -hide_banner -nostats -i "$f" -af ebur128=peak=true -f null - 2>&1 | sed -n '/Summary:/,$p' >> "$C/loudness.txt"
done
: > "$C/sync.txt"
"$PY" tools/sync_check.py main renders/v3/main-video.mp4 >> "$C/sync.txt"
"$PY" tools/sync_check.py vertical renders/v3/vertical-video.mp4 >> "$C/sync.txt"
"$PY" tools/sync_check.py ad15 renders/v3/ad15-video.mp4 >> "$C/sync.txt"
"$PY" tools/contact_v3.py renders/envkit-promo-v3-16x9.mp4 renders/contact-v3-16x9.jpg 0.75
"$PY" tools/contact_v3.py renders/envkit-promo-v3-9x16.mp4 renders/contact-v3-9x16.jpg 0.75
"$PY" tools/contact_v3.py renders/envkit-promo-v3-15s.mp4 renders/contact-v3-15s.jpg 0.5
grep -h "magenta check" "$C/coverage.txt"; grep -hE "Integrated|I:|Peak:" "$C/loudness.txt" | head -30; cat "$C/sync.txt" | grep -E "==|: n="
