#!/usr/bin/env python3
"""ElevenLabs helper. Reads the API key from ~/.claude.json
(mcpServers.elevenlabs.env.ELEVENLABS_API_KEY) at runtime; never prints it.
  eleven.py credits
  eleven.py sfx  OUT.mp3 DURATION "prompt" [prompt_influence]
  eleven.py music OUT.mp3 LENGTH_MS "prompt"
"""
import json, os, sys, urllib.request, urllib.error

def key():
    d = json.load(open(os.path.expanduser("~/.claude.json")))
    return d["mcpServers"]["elevenlabs"]["env"]["ELEVENLABS_API_KEY"]

def call(path, body=None, method="POST"):
    req = urllib.request.Request("https://api.elevenlabs.io" + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"xi-api-key": key(), "Content-Type": "application/json", "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read()[:800].decode(errors='replace')}")

cmd = sys.argv[1]
if cmd == "credits":
    s = json.loads(call("/v1/user/subscription", method="GET"))
    print({k: s.get(k) for k in ("tier", "character_count", "character_limit", "next_character_count_reset_unix")})
elif cmd == "sfx":
    out, dur, prompt = sys.argv[2], float(sys.argv[3]), sys.argv[4]
    infl = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
    data = call("/v1/sound-generation?output_format=mp3_44100_192",
        {"text": prompt, "duration_seconds": dur, "prompt_influence": infl})
    open(out, "wb").write(data)
    print("wrote", out)
elif cmd == "music":
    out, ms, prompt = sys.argv[2], int(sys.argv[3]), sys.argv[4]
    data = call("/v1/music?output_format=mp3_44100_192",
        {"prompt": prompt, "music_length_ms": ms, "force_instrumental": True})
    open(out, "wb").write(data)
    print("wrote", out)
