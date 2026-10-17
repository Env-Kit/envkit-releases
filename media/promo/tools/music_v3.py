#!/usr/bin/env python3
"""v3 music bed: ElevenLabs /v1/music with a composition plan (140 BPM, sections sized in whole bars:
1 bar = 1714 ms). The edit later re-splices it on bar lines (tools/edit_v3.py), so the hard cut to
silence before "Stop." and the drop-out under "And the best part?" are made in the mix, exactly.
  music_v3.py OUT.mp3 SEED"""
import json, os, sys, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(__file__))
from vo import key
BAR = 1714
G_POS = ["energetic modern electronic trailer hybrid", "140 BPM", "4/4", "instrumental", "punchy cinematic drums",
         "distorted analog sub bass", "bright supersaw stabs", "tight modern mix", "premium tech launch trailer", "confident, driving"]
G_NEG = ["vocals", "vocal chops", "choir", "spoken word", "lo-fi", "acoustic guitar", "swing", "tempo changes"]
SECTIONS = [
    ("Hook build", 2, ["tense pulsing 16th-note synth", "glitchy stutter edits", "ticking hi-hats", "rising white-noise riser", "snare roll building", "ends on a sharp cut"], ["drop", "kick"]),
    ("Hard drop", 8, ["massive hard drop on the first beat", "huge sub impact", "four-on-the-floor punchy kick", "driving distorted bass", "big supersaw stabs on the off-beats", "full energy"], ["build-up", "riser"]),
    ("Drive", 6, ["driving groove continues", "pulsing arpeggio", "tight claps", "slightly leaner mix leaving room for a voiceover", "steady energy"], ["breakdown"]),
    ("Montage build", 2, ["energy rises fast", "snare build", "rising riser", "faster hats", "tension"], ["drop"]),
    ("Breakdown", 2, ["everything drops out", "only a soft filtered pad and a low sub swell", "sparse", "suspense", "near silence"], ["drums", "kick", "bass line"]),
    ("Final drop", 4, ["biggest hit on the first beat", "massive impact", "full drums and bass", "triumphant supersaw chords", "maximum energy"], ["breakdown"]),
    ("Ending", 2, ["one final huge hit on the first beat", "then a clean cinematic reverb tail that fully decays", "no drums after the hit"], ["fade in", "new melody"]),
]
plan = {"positive_global_styles": G_POS, "negative_global_styles": G_NEG,
        "sections": [{"section_name": n, "positive_local_styles": p, "negative_local_styles": ng, "duration_ms": bars * BAR, "lines": []}
                     for n, bars, p, ng in SECTIONS]}
if __name__ == "__main__":
    out, seed = sys.argv[1], int(sys.argv[2])
    body = {"composition_plan": plan, "model_id": "music_v1", "seed": seed}
    req = urllib.request.Request("https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192", data=json.dumps(body).encode(),
        method="POST", headers={"xi-api-key": key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            open(out, "wb").write(r.read())
        print("wrote", out)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read()[:800].decode(errors='replace')}")
