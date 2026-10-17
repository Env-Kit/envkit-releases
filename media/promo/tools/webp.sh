#!/usr/bin/env bash
# Silent looping WebP for the README: 1280 wide, 15 fps, from the 16:9 master render.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
rm -rf renders/_webp && mkdir -p renders/_webp
ffmpeg -v error -i renders/envkit-promo-master-video.mp4 -vf "fps=15,scale=1280:-1:flags=lanczos" renders/_webp/f%04d.png
"$PY" - <<'PYEOF'
import glob
from PIL import Image
paths = sorted(glob.glob("renders/_webp/f*.png"))
frames = [Image.open(p).convert("RGB") for p in paths]
frames[0].save("renders/envkit-demo.webp", save_all=True, append_images=frames[1:], duration=67, loop=0,
               quality=46, method=4, kmin=4, kmax=8)
print(len(frames), "frames")
PYEOF
rm -rf renders/_webp
ls -la renders/envkit-demo.webp
