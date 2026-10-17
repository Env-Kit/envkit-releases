#!/usr/bin/env bash
# Re-cut only the hook: render the hook-only compositions (tools/compose_v3.py --hook -> _hook-*.html) and splice
# them onto the existing full renders at the first frame that does not depend on the hook (compose_v3.splice_frame).
#   tools/splice_hook_v3.sh      # needs renders/v3/hook/<file>.mp4 and renders/v3/<cut>-video.mp4
# Output: renders/v3/<cut>-video.mp4 (lossless H.264 intermediate; the previous render is kept as <cut>-video-prev.mp4)
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
for pair in "index main" "vertical vertical" "ad15 ad15"; do
  set -- $pair; f=$1; cut=$2
  SP=$("$PY" -c "import json,sys; sys.path.insert(0,'tools'); from compose_v3 import splice_frame; print(splice_frame(json.load(open('audio-src/v3/timing-$cut.json'))))")
  [ -f "renders/v3/$cut-video-prev.mp4" ] || mv "renders/v3/$cut-video.mp4" "renders/v3/$cut-video-prev.mp4"
  ffmpeg -v error -y -i "renders/v3/hook/$f.mp4" -i "renders/v3/$cut-video-prev.mp4" -filter_complex \
    "[0:v]trim=end_frame=$SP,setpts=PTS-STARTPTS[a];[1:v]trim=start_frame=$SP,setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0[v]" \
    -map "[v]" -c:v libx264 -preset ultrafast -qp 0 -pix_fmt yuv420p -r 30 "renders/v3/$cut-video.mp4"
  echo "$cut spliced at frame $SP: $(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 renders/v3/$cut-video.mp4) frames"
done
