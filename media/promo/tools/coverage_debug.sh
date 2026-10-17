#!/usr/bin/env bash
# Black-frame regression test for the promo compositions.
# Renders a copy of the composition where every screenshot panel's own background and the
# page background are pure magenta. Any magenta in the output means a zoomed screenshot did
# not cover its window (the v1 bug) or the backdrop left the frame uncovered.
#   tools/coverage_debug.sh index.html   |   tools/coverage_debug.sh vertical.html
set -euo pipefail
cd "$(dirname "$0")/.."
SRC="${1:-index.html}"
DBG="_coverage-debug-${SRC}"
sed 's|</head>|<style>#root,html,body{background:#f0f!important}.panel{background:#f0f!important}.panel .sheen{display:none!important}</style></head>|' "$SRC" > "$DBG"
npx --yes hyperframes@0.8.168 render -c "$DBG" -q draft -o "renders/_coverage-${SRC%.html}.mp4" --quiet >/dev/null 2>&1
rm -f "$DBG"
PY="${PYTHON:-python3}"
"$PY" - "renders/_coverage-${SRC%.html}.mp4" <<'PYEOF'
import subprocess, sys, numpy as np
src = sys.argv[1]; W, H = 480, 270
p = subprocess.run(["ffprobe","-v","error","-select_streams","v","-show_entries","stream=width,height","-of","csv=p=0",src],capture_output=True,text=True).stdout.strip().split(",")
w, h = int(p[0]), int(p[1]); W, H = (480, 270) if w > h else (270, 480)
raw = subprocess.run(["ffmpeg","-v","error","-i",src,"-vf",f"fps=4,scale={W}:{H}","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True,check=True).stdout
f = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(int)
mag = (f[..., 0] > 170) & (f[..., 2] > 170) & (f[..., 1] < 90)
share = mag.reshape(len(f), -1).mean(1)
bad = [(i / 4, s) for i, s in enumerate(share) if s > 0.001]
for t, s in bad: print(f"t={t:6.2f}s magenta={s*100:.2f}%")
print(f"magenta check: {len(f)} frames @0.25s, {len(bad)} with uncovered pixels, max={share.max()*100:.3f}%")
sys.exit(1 if bad else 0)
PYEOF
