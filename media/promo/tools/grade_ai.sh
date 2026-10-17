#!/usr/bin/env bash
# Grade the Higgsfield clips toward the brand (mint/teal on near-black) and re-encode at 30 fps
# with a keyframe every second so HyperFrames can seek them frame-accurately.
set -euo pipefail
cd "$(dirname "$0")/../assets/ai"
G="colorbalance=rs=-0.06:bs=-0.05:rm=-0.05:bm=-0.03:rh=-0.04:bh=-0.02,eq=brightness=-0.03:contrast=1.06:saturation=0.95,fps=30"
X="-c:v libx264 -preset slow -g 30 -keyint_min 30 -pix_fmt yuv420p -an -movflags +faststart"
for f in ribbons-16x9 circuit-16x9 monoliths-16x9; do ffmpeg -v error -y -i $f.mp4 -vf "$G" $X -crf 18 $f-graded.mp4; done
ffmpeg -v error -y -i ribbons-9x16.mp4 -vf "$G" $X -crf 20 ribbons-9x16-graded.mp4
for f in circuit monoliths; do ffmpeg -v error -y -i $f-16x9.mp4 -vf "scale=-2:1920:flags=lanczos,crop=1080:1920,$G" $X -crf 20 $f-9x16-graded.mp4; done
# v3: light-speed tunnel + shockwave (tools/hf_generate_v3.py), 16:9 and a centre crop for 9:16
for f in tunnel shockwave; do
  ffmpeg -v error -y -i $f-16x9.mp4 -vf "$G" $X -crf 19 $f-16x9-graded.mp4
  ffmpeg -v error -y -i $f-16x9.mp4 -vf "scale=-2:1920:flags=lanczos,crop=1080:1920,$G" $X -crf 21 $f-9x16-graded.mp4
done
