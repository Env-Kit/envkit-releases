#!/usr/bin/env python3
"""Contact sheet: one frame every STEP seconds with its timestamp.
  contact_v3.py in.mp4 out.jpg [STEP=1]"""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]; step = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip().split(","))
tw = 480 if w > h else 240; th = round(tw * h / w); cols = 6 if w > h else 8
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps=1/{step},scale={tw}:{th}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
n = len(raw) // (tw * th * 3); rows = (n + cols - 1) // cols
sheet = Image.new("RGB", (cols * (tw + 4) + 4, rows * (th + 4) + 4), (17, 17, 17))
try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 16)
except OSError: font = ImageFont.load_default()
for i in range(n):
    im = Image.frombytes("RGB", (tw, th), raw[i * tw * th * 3:(i + 1) * tw * th * 3])
    d = ImageDraw.Draw(im); t = f"{i * step:.1f}s"; d.rectangle([4, 4, 12 + 9 * len(t), 24], fill=(0, 0, 0)); d.text((8, 6), t, fill=(255, 255, 255), font=font)
    sheet.paste(im, (4 + (i % cols) * (tw + 4), 4 + (i // cols) * (th + 4)))
sheet.save(out, quality=85); print(out, n, "frames")
