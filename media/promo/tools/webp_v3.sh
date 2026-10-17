#!/usr/bin/env bash
# Silent looping WebP for the README (captions are burned into the picture): 1280 wide, 12 fps, from the 16:9 render.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"; FPS="${FPS:-12}"; Q="${Q:-44}"
rm -rf renders/_webp && mkdir -p renders/_webp
ffmpeg -v error -i renders/v3/main-video.mp4 -vf "fps=$FPS,scale=1280:-1:flags=lanczos" renders/_webp/f%04d.png
"$PY" - "$FPS" "$Q" <<'PYEOF'
import glob, sys
from PIL import Image
fps, q = int(sys.argv[1]), int(sys.argv[2])
paths = sorted(glob.glob("renders/_webp/f*.png"))
frames = [Image.open(p).convert("RGB") for p in paths]
frames[0].save("renders/envkit-demo-v3.webp", save_all=True, append_images=frames[1:], duration=round(1000 / fps), loop=0,
               quality=q, method=4, kmin=4, kmax=8)
print(len(frames), "frames")
PYEOF
rm -rf renders/_webp
ls -la renders/envkit-demo-v3.webp
