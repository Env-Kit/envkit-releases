#!/usr/bin/env bash
# Black-frame regression test for the promo compositions.
# Renders a copy of the composition where the page background, every screenshot panel's own
# background and every tile background are pure magenta. Any magenta in the output means a zoomed
# screenshot did not cover its window (the v1 bug) or the backdrop left part of the frame uncovered.
#   tools/coverage_debug.sh index.html | vertical.html | ad15.html      (FPS=30 checks every frame; default 30)
set -euo pipefail
cd "$(dirname "$0")/.."
SRC="${1:-index.html}"
FPS="${FPS:-30}"
DBG="_coverage-debug-${SRC}"
sed 's|</head>|<style>#root,html,body{background:#f0f!important}.panel,.tile{background:#f0f!important}.panel .sheen{display:none!important}</style></head>|' "$SRC" > "$DBG"
npx --yes hyperframes@0.8.168 render -c "$DBG" -q draft -o "renders/_coverage-${SRC%.html}.mp4" --quiet >/dev/null 2>&1
rm -f "$DBG"
PY="${PYTHON:-python3}"
"$PY" - "renders/_coverage-${SRC%.html}.mp4" "$FPS" <<'PYEOF'
import subprocess, sys, numpy as np
src, fps = sys.argv[1], sys.argv[2]
p = subprocess.run(["ffprobe","-v","error","-select_streams","v","-show_entries","stream=width,height","-of","csv=p=0",src],capture_output=True,text=True).stdout.strip().split(",")
w, h = int(p[0]), int(p[1]); W, H = (480, 270) if w > h else (270, 480)
proc = subprocess.Popen(["ffmpeg","-v","error","-i",src,"-vf",f"fps={fps},scale={W}:{H}","-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
n, bad, mx = 0, [], 0.0
while True:
    buf = proc.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    f = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(int)
    share = ((f[..., 0] > 170) & (f[..., 2] > 170) & (f[..., 1] < 90)).mean()
    mx = max(mx, share)
    if share > 0.001: bad.append((n / float(fps), share))
    n += 1
for t, s in bad[:40]: print(f"t={t:6.2f}s magenta={s*100:.2f}%")
print(f"magenta check: {n} frames @{fps} fps, {len(bad)} with uncovered pixels, max={mx*100:.3f}%")
sys.exit(1 if bad else 0)
PYEOF
