#!/usr/bin/env bash
# v3: soundtrack -> loudness -> mux for the three cuts, plus the README copies.
#   tools/finish_v3.sh            # expects renders/v3/<cut>-video.mp4 (hyperframes -q high renders, see README)
# Loudness: limiter for headroom, then two-pass linear loudnorm to -14 LUFS integrated, -2.0 dBTP target
# (the AAC files are re-measured afterwards; the requirement is <= -1 dBTP).
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
R=renders; V=renders/v3; A=audio-src/v3
mkdir -p "$V"

norm() { # $1 in.wav  $2 out.wav
  ffmpeg -v error -y -i "$1" -af "alimiter=limit=0.7:attack=2:release=50:level=disabled" -c:a pcm_s24le "$2.lim.wav"
  local m; m=$(ffmpeg -hide_banner -i "$2.lim.wav" -af loudnorm=I=-14:TP=-2.0:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  local v; v=$(echo "$m" | "$PY" -c 'import json,sys;d=json.load(sys.stdin);print(d["input_i"],d["input_tp"],d["input_lra"],d["input_thresh"],d["target_offset"])')
  local ii tp lra th off; read -r ii tp lra th off <<<"$v"
  ffmpeg -v error -y -i "$2.lim.wav" -af "loudnorm=I=-14:TP=-2.0:LRA=11:measured_I=$ii:measured_TP=$tp:measured_LRA=$lra:measured_thresh=$th:offset=$off:linear=true,aresample=48000" -c:a pcm_s24le "$2"
  rm -f "$2.lim.wav"
}

for cut in main vertical ad15; do
  "$PY" tools/edit_v3.py "$cut" >/dev/null
  norm "$A/$cut-mix.wav" "$A/$cut-final.wav"
done

# 16:9 master: H.264 CRF 14 from renders/v3/main-video.mp4 (lossless after a hook splice) + AAC 320k; delivery copies H.264 + AAC.
ffmpeg -v error -y -i "$V/main-video.mp4" -i "$A/main-final.wav" -map 0:v -map 1:a -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -c:a aac -b:a 320k -movflags +faststart -shortest "$R/envkit-promo-v3-master.mp4"
ffmpeg -v error -y -i "$V/main-video.mp4" -i "$A/main-final.wav" -map 0:v -map 1:a -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest "$R/envkit-promo-v3-16x9.mp4"
ffmpeg -v error -y -i "$V/vertical-video.mp4" -i "$A/vertical-final.wav" -map 0:v -map 1:a -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest "$R/envkit-promo-v3-9x16.mp4"
ffmpeg -v error -y -i "$V/ad15-video.mp4" -i "$A/ad15-final.wav" -map 0:v -map 1:a -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest "$R/envkit-promo-v3-15s.mp4"
# README copy (< 10 MB): 1600 wide, CRF 27.
ffmpeg -v error -y -i "$V/main-video.mp4" -i "$A/main-final.wav" -map 0:v -map 1:a -vf "scale=1600:-2:flags=lanczos" -c:v libx264 -preset slow -crf 27 -tune film -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart -shortest "$R/envkit-demo-v3.mp4"
ls -la "$R"/envkit-promo-v3-* "$R/envkit-demo-v3.mp4"
