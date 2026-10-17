#!/usr/bin/env bash
# The exact ElevenLabs generations used for the soundtrack (2026-10-17, ~790 credits in total).
# The API key is read by tools/eleven.py from ~/.claude.json at runtime; it is never printed or stored.
# ElevenLabs allows 5 concurrent requests on the Creator plan, so effects run in two waves.
set -euo pipefail
cd "$(dirname "$0")/.."
E="python3 tools/eleven.py"; A=audio-src
$E music $A/music-a.mp3 50000 "Instrumental product launch track for a calm, premium developer tool. Modern minimal electronic, 120 BPM, 4/4, confident and focused, no vocals. Structure: 0-4s soft airy pad swell with a deep sub hit at 4s; 4-20s tight kick, crisp closed hats, muted plucked synth arpeggio, warm sub bass; 20-36s fuller groove with a subtle lift, glassy synth chords; 36-44s builds energy; 44s final hit then a clean, short reverb-tail ending that resolves fully by 50s. Polished mix, restrained, no risers longer than 2 seconds, no drops, no vocal chops."
# (The result came back at 128 BPM with a 2-bar break at 13.2 s; the edit is cut to what came back.)
$E sfx $A/impact.mp3 2.5 "Deep cinematic low sub-bass impact hit, short clean boom with a soft dark tail, modern trailer logo hit, no music" 0.6 &
$E sfx $A/whoosh1.mp3 0.8 "Fast clean airy swoosh, modern motion graphics UI transition whoosh, short, no music" 0.6 &
$E sfx $A/whoosh2.mp3 1.0 "Smooth deep air whoosh pass-by, soft cinematic transition swish, clean, no music" 0.6 &
$E sfx $A/click.mp3 0.5 "Single soft subtle mouse click, modern trackpad tap, short and clean, no reverb" 0.7 &
wait
$E sfx $A/tick.mp3 0.5 "Single quiet soft keyboard key tap, one keystroke, short, close mic, no reverb" 0.7 &
$E sfx $A/chime.mp3 2.0 "Gentle bright success chime, two soft glassy bell notes rising, modern app notification, clean, airy tail" 0.6 &
$E sfx $A/shimmer.mp3 1.5 "Subtle airy glass shimmer swell, soft sparkling light sweep, delicate, no music" 0.5 &
$E sfx $A/blip.mp3 0.5 "Soft short digital confirmation blip, UI success tick sound, clean and quiet" 0.7 &
wait
