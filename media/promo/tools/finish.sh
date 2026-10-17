#!/usr/bin/env bash
# Mix, loudness-normalise and mux the promo deliverables.
#   tools/finish.sh          # 16:9 + 9:16 (expects the silent video renders to exist)
# Inputs : renders/envkit-promo-master-video.mp4, renders/envkit-promo-9x16-video.mp4 (hyperframes -q high)
# Outputs: renders/envkit-promo-master.mp4 (video stream-copied from the render + AAC 320k), renders/envkit-promo-16x9.mp4,
#          renders/envkit-promo-9x16.mp4, renders/envkit-demo.mp4 (README copy), renders/envkit-demo.webp
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"

norm() { # $1 in.wav  $2 out.wav  — limiter for headroom, then two-pass linear loudnorm to -16 LUFS / -1.5 dBTP
  ffmpeg -v error -y -i "$1" -af "alimiter=limit=0.6:attack=3:release=60:level=disabled" -c:a pcm_s24le "$2.lim.wav"
  local m; m=$(ffmpeg -hide_banner -i "$2.lim.wav" -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  local ii tp lra th off
  ii=$(echo "$m" | "$PY" -c 'import json,sys;d=json.load(sys.stdin);print(d["input_i"],d["input_tp"],d["input_lra"],d["input_thresh"],d["target_offset"])')
  read -r ii tp lra th off <<<"$ii"
  ffmpeg -v error -y -i "$2.lim.wav" -af "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=$ii:measured_TP=$tp:measured_LRA=$lra:measured_thresh=$th:offset=$off:linear=true,aresample=48000" -c:a pcm_s24le "$2"
  rm -f "$2.lim.wav"
}

(cd tools && "$PY" mix.py main && "$PY" mix.py vertical)
norm audio-src/mix-16x9.wav audio-src/final-16x9.wav
norm audio-src/mix-9x16.wav audio-src/final-9x16.wav

V=renders/envkit-promo-master-video.mp4
VV=renders/envkit-promo-9x16-video.mp4
# Master: the high-quality HyperFrames render stream-copied (no re-encode) + AAC 320k.
ffmpeg -v error -y -i "$V" -i audio-src/final-16x9.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -movflags +faststart -shortest renders/envkit-promo-master.mp4
# Delivery 16:9 (< 25 MB) and the README copy (< 10 MB).
ffmpeg -v error -y -i "$V" -i audio-src/final-16x9.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest renders/envkit-promo-16x9.mp4
ffmpeg -v error -y -i "$V" -i audio-src/final-16x9.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 26 -tune film -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart -shortest renders/envkit-demo.mp4
if [ -f "$VV" ]; then
  ffmpeg -v error -y -i "$VV" -i audio-src/final-9x16.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest renders/envkit-promo-9x16.mp4
fi
ls -la renders/*.mp4
