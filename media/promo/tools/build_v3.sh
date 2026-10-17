#!/usr/bin/env bash
# One command for the whole v3 build. PYTHON must have numpy + Pillow.
#   tools/build_v3.sh vo      # regenerate every VO take (voice/settings from tools/vo_config.json) + forced alignment, then build
#   tools/build_v3.sh         # build from the existing takes
# Steps: edit (VO placement, captions, music splice, SFX, ducking) -> compositions -> HyperFrames renders (-q high)
#        -> loudness + mux -> README WebP -> checks (magenta coverage, sync, loudness) -> contact sheets
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"; export PYTHON="$PY"
HF="npx --yes hyperframes@0.8.168"
[ "${1:-}" = "vo" ] && python3 tools/vo.py gen
for c in main vertical ad15; do "$PY" tools/edit_v3.py "$c" | tail -1; done
python3 tools/compose_v3.py
mkdir -p renders/v3/checks
$HF render -c index.html -q high -o renders/v3/main-video.mp4 --quiet >/dev/null 2>&1
$HF render -c vertical.html -q high -o renders/v3/vertical-video.mp4 --quiet >/dev/null 2>&1
$HF render -c ad15.html -q high -o renders/v3/ad15-video.mp4 --quiet >/dev/null 2>&1
tools/finish_v3.sh
tools/webp_v3.sh
tools/check_v3.sh
