#!/usr/bin/env python3
"""Submit the abstract backdrop clips to Higgsfield (Kling 3.0 pro, 8 s, silent).

Needs a Higgsfield MCP client at ~/.config/envkit/higgsfield/hf.py (wraps
`npx mcp-remote https://mcp.higgsfield.ai/mcp` with cached OAuth). Prints the job ids;
put them in tools/hf_fetch.py and run it to download into assets/ai/.
Cost when made (2026-10-17): 14 credits per clip (4 clips = 56 credits).

  hf_generate.py            # submit all four
  hf_generate.py --cost     # preflight only, nothing is generated"""
import json, os, subprocess, sys

HF = os.path.expanduser("~/.config/envkit/higgsfield/hf.py")
STYLE = (" Pure abstract imagery only: absolutely no text, no letters, no numbers, no logos, no user interface, no screens,"
         " no people, no hands. Color palette strictly near-black (#06090d) with mint (#2dd4aa) and teal (#0d9488) light as"
         " the only light source; no other hues, no purple, no orange. Calm, premium, high-end tech brand film look, shallow"
         " depth of field, fine film grain, smooth slow camera motion, seamless and elegant.")
CLIPS = [
    ("ribbons-16x9", "16:9", "Macro cinematic shot: thin ribbons of mint-green light flowing slowly through layers of dark smoked glass, refracting and splitting into soft caustics, camera slowly dollies forward through the glass sheets, deep black background with gentle volumetric haze."),
    ("circuit-16x9", "16:9", "Extreme macro of glowing mint circuit-like lines drawing themselves across a dark glossy black surface, lines branch and connect at right angles like traces on a circuit board, light pulses travel along them, slow lateral camera slide, very shallow depth of field with bokeh."),
    ("monoliths-16x9", "16:9", "Abstract architectural space made of light: long dark corridor of tall black glass monoliths like an abstract server room, thin vertical mint light lines glow and softly pulse inside the monoliths, polished reflective floor, slow steady forward dolly, atmospheric haze, symmetrical composition."),
    ("ribbons-9x16", "9:16", "Macro cinematic vertical shot: thin ribbons of mint-green light flowing slowly upward through layers of dark smoked glass, refracting into soft caustics, camera slowly rises, deep black background with gentle volumetric haze."),
]

def params(ar, prompt, cost=False):
    p = {"model": "kling3_0", "prompt": prompt + STYLE, "aspect_ratio": ar, "duration": 8, "mode": "pro", "sound": "off"}
    if cost:
        p["get_cost"] = True
    return p

if "--cost" in sys.argv:
    for name, ar, prompt in CLIPS:
        r = subprocess.run(["python3", HF, "call", "generate_video", json.dumps({"params": params(ar, prompt, True)})], capture_output=True, text=True)
        print(name, json.loads(r.stdout)["content"][0]["text"])
    sys.exit(0)

body = {"requests": [{"index": i, "params": params(ar, prompt)} for i, (_, ar, prompt) in enumerate(CLIPS)]}
r = subprocess.run(["python3", HF, "call", "generate_video_batch", json.dumps(body)], capture_output=True, text=True)
for job in json.loads(r.stdout).get("structuredContent", {}).get("jobs", []):
    print(CLIPS[job["index"]][0], job["job_id"], job["status"])
