#!/usr/bin/env bash
# v3 additions (music + new SFX). The v2 effects in tools/eleven_generate.sh are reused.
# Voiceover: tools/vo.py (voice + settings in tools/vo_config.json).
set -euo pipefail
cd "$(dirname "$0")/.."
E="python3 tools/eleven.py"; A=audio-src
if [ "${1:-}" = "music" ]; then
  python3 tools/music_v3.py $A/music-v3-a.mp3 140   # the one used (hard drop at 6.85 s)
  exit 0
fi
$E sfx $A/glitch1.mp3 0.6 "Short harsh digital glitch hit, data corruption stutter burst, crunchy bit-crushed error sound, punchy, no music" 0.7 &
$E sfx $A/glitch2.mp3 0.5 "Very short electronic glitch zap with a buzzy distorted click, broken signal, punchy transient, no music" 0.7 &
$E sfx $A/slam.mp3 2.5 "Massive cinematic trailer slam impact, deep sub boom with a sharp metallic crack transient and a long dark tail, huge logo hit, no music" 0.65 &
$E sfx $A/tapestop.mp3 0.7 "Abrupt tape stop power-down effect, audio slowing down and cutting out, short, no music" 0.6 &
wait
$E sfx $A/strike.mp3 0.5 "Fast sharp marker swipe slash sound, quick strike-through swish, crisp, very short, no music" 0.7 &
$E sfx $A/reverse.mp3 1.2 "Reverse cymbal swell rising into a sudden stop, airy suction riser, short, no music" 0.6 &
$E sfx $A/subdrop.mp3 2.0 "Deep sub bass drop boom, a single powerful 808 sub hit falling in pitch, clean, cinematic, no music" 0.6 &
$E sfx $A/pop.mp3 0.5 "Tiny crisp UI pop, soft bubbly click for a chip appearing, short and clean, no music" 0.7 &
wait
