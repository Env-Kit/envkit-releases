#!/usr/bin/env python3
"""v3: two high-energy abstract clips (Kling 3.0 pro, 8 s, silent, 16:9; the 9:16 cut uses a centre crop).

  hf_generate_v3.py --cost   # preflight, nothing generated
  hf_generate_v3.py          # submit both, prints job ids (download with tools/hf_fetch.py)"""
import json, os, subprocess, sys

HF = os.path.expanduser("~/.config/envkit/higgsfield/hf.py")
STYLE = (" Pure abstract imagery only: absolutely no text, no letters, no numbers, no logos, no user interface, no screens,"
         " no people, no hands. Color palette strictly near-black (#06090d) with mint (#2dd4aa) and teal (#0d9488) light as"
         " the only light source; no other hues, no purple, no orange, no blue. Premium high-end tech brand launch trailer look,"
         " crisp, high contrast, fine film grain.")
CLIPS = [
    ("tunnel-16x9", "16:9", "Hyper-fast forward flight through a tunnel made of streaking mint-green light lines, light-speed warp effect, streaks stretch from the centre vanishing point to the edges, camera accelerates forward continuously, intense motion blur, deep black between the streaks, energetic and powerful."),
    ("shockwave-16x9", "16:9", "A single bright mint-green energy shockwave bursts outward from the centre of a pitch-black void, an expanding ring of light with fine glowing particles and a soft lens flare, the ring sweeps past the camera, then a second smaller pulse, slow motion, cinematic, powerful impact moment."),
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
print(r.stdout[:3000])
for job in json.loads(r.stdout).get("structuredContent", {}).get("jobs", []):
    print(CLIPS[job["index"]][0], job["job_id"], job["status"])
