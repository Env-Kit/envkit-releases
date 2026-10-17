#!/usr/bin/env python3
"""v3 voiceover: ElevenLabs TTS, one request per line via /with-timestamps (character alignment
-> word timings). Voice + settings: tools/vo_config.json. The API key is read from
~/.claude.json at runtime (tools/eleven.py) and never printed or stored.

Voice id, model and voice_settings come from tools/vo_config.json.
  vo.py gen                  # all takes -> audio-src/vo/<line>-t<k>.mp3 + .json (config model; falls back on error)
  vo.py gen L01 L02          # only some lines
  vo.py gen --model eleven_multilingual_v2 [L..]
  vo.py align                # (re)run forced alignment on every take (gen does this automatically)
Output JSON: {"text", "model", "settings", "seed", "words": [[word, start, end], ...]}"""
import base64, json, os, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "audio-src", "vo")
CFG = json.load(open(os.path.join(HERE, "vo_config.json")))
VOICE = CFG["voice_id"]
sys.path.insert(0, HERE)

# id: (text sent to the model, takes). v3 audio tags in [] steer delivery and are not spoken.
LINES = {
    # Hook (swappable block): three pains, each struck through on the next beat, then the turn.
    "H1": ("[annoyed] Port 80 is already in use.", 3),
    "H2": ("[annoyed] MySQL shut down unexpectedly.", 3),
    "H3": ("[annoyed] Wrong PHP version... again.", 3),
    "H4": ("[calm] What if your stack just fixed itself?", 3),
    "L03": ("[confident] This is EnvKit.", 2),
    "L04": ("[confident] Your whole local stack. One app.", 2),
    "L05": ("Pick a project...", 2),
    "L06": ("[satisfied] and it's live.", 2),
    "L07": ("[confident] Real HTTPS. Real domain. Seconds.", 2),
    "L08": ("Every project gets its own dot test.", 2),
    "L09": ("[energetic] PHP. Node. MySQL. Postgres. Redis.", 2),
    "L10": ("[energetic] All running.", 2),
    "L11": ("[intrigued] Something breaks?", 2),
    "L12": ("[confident] Just ask your AI.", 2),
    "L13": ("[energetic] Cron. Logs. Git. Databases.", 2),
    "L14": ("[energetic] It's all here.", 2),
    "L15": ("[conspiratorial] And the best part?", 3),
    "L16": ("[excited] It's free.", 3),
    "L17": ("[confident] EnvKit. For Windows and Mac.", 2),
}
SETTINGS = CFG["settings"]

def key():
    d = json.load(open(os.path.expanduser("~/.claude.json")))
    return d["mcpServers"]["elevenlabs"]["env"]["ELEVENLABS_API_KEY"]

def strip_tags(t):
    import re
    return re.sub(r"\[[^\]]*\]\s*", "", t)

def words_from(al, text):
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    out, cur, s0, e0, intag = [], "", None, None, False
    for c, s, e in zip(chars, st, en):
        if c == "[": intag = True; continue
        if intag:
            if c == "]": intag = False
            continue
        if c.isspace():
            if cur: out.append([cur, s0, e0]); cur = ""
            continue
        if not cur: s0 = s
        cur += c; e0 = e
    if cur: out.append([cur, s0, e0])
    return out

def gen(model, lid, take, settings=None):
    text, _ = LINES[lid]
    ov = {k: v for k, v in CFG.get("line_overrides", {}).items() if k == lid}.get(lid, {})
    model = ov.get("model", model)
    settings = settings or ov.get("settings") or SETTINGS[model]
    # eleven_v3 tends to cut the last phoneme off at the end of a file; a trailing [pause] tag gives a clean decay.
    if model == "eleven_v3" and not ov.get("no_pause"): text = text + " [pause]"
    if model != "eleven_v3": text = strip_tags(text)
    seed = (2000 if lid[0] == "H" else 1000) + int(lid[1:]) * 10 + take
    body = {"text": text, "model_id": model, "voice_settings": settings, "seed": seed, "language_code": "en"}
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_192",
        data=json.dumps(body).encode(), method="POST", headers={"xi-api-key": key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        return f"{lid}-t{take} HTTP {e.code}: {e.read()[:400].decode(errors='replace')}"
    base = os.path.join(OUT, f"{lid}-t{take}")
    open(base + ".mp3", "wb").write(base64.b64decode(d["audio_base64"]))
    al = d.get("normalized_alignment") or d.get("alignment")
    json.dump({"text": text, "voice": VOICE, "model": model, "settings": settings, "seed": seed, "words": words_from(d["alignment"], text)},
              open(base + ".json", "w"), indent=1)
    return f"{lid}-t{take} ok"

def forced_align(name):
    """ElevenLabs /v1/forced-alignment on one take -> audio-src/vo/<take>.fa.json ({"words": [[w, start, end], ...]}).
    The TTS character alignment of eleven_v3 drifts by up to ~0.5 s; the separate aligner is much closer."""
    import uuid
    j = json.load(open(os.path.join(OUT, name + ".json")))
    text = strip_tags(j["text"]).strip()
    b = uuid.uuid4().hex
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"text\"\r\n\r\n{text}\r\n--{b}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"a.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n").encode() \
        + open(os.path.join(OUT, name + ".mp3"), "rb").read() + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/forced-alignment", data=body, method="POST",
                                 headers={"xi-api-key": key(), "Content-Type": f"multipart/form-data; boundary={b}"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=180).read())
    except urllib.error.HTTPError as e:
        return f"{name} FA HTTP {e.code}"
    ws = [[w["text"], w["start"], w["end"]] for w in d.get("words", []) if w["text"].strip()]
    json.dump({"text": text, "words": ws}, open(os.path.join(OUT, name + ".fa.json"), "w"), indent=1)
    return f"{name} FA ok"

if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "align":
    names = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith(".mp3"))
    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(forced_align, names): print(r)
    sys.exit(0)

if __name__ == "__main__":
    args = sys.argv[2:]
    model = CFG["model"]
    if "--model" in args:
        i = args.index("--model"); model = args[i + 1]; del args[i:i + 2]
    ids = args or list(LINES)
    for f in os.listdir(OUT):  # drop stale takes of the lines being regenerated
        if f.split("-")[0] in ids: os.remove(os.path.join(OUT, f))
    jobs = [(lid, k) for lid in ids for k in range(1, LINES[lid][1] + 1)]
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda j: gen(model, *j), jobs))
    failed = [j for j, r in zip(jobs, res) if not r.endswith(" ok")]
    if failed and model != CFG["fallback_model"]:
        print("falling back to", CFG["fallback_model"], "for", failed)
        res += [gen(CFG["fallback_model"], *j) for j in failed]
    print("\n".join(res))
    names = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith(".mp3") and f.split("-")[0] in ids)
    with ThreadPoolExecutor(4) as ex:
        print("\n".join(ex.map(forced_align, names)))
