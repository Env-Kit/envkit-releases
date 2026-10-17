#!/usr/bin/env python3
"""VO <-> caption sync check for a v3 cut.
  sync_check.py CUT VIDEO     (CUT = main | vertical | ad15; VIDEO = the rendered picture of that cut)

A. Audio: for every caption word that follows a pause in the voiceover stem (audio-src/v3/<cut>-vo.wav),
   the audible onset is measured (first 2 ms-envelope crossing of -30 dB re. the word's own peak after
   >= 60 ms below -45 dB) and compared with the caption time from assets/timing-<cut>.js.
B. Picture: in the render, the frame where each lower-third / 9:16 caption word turns mint is detected
   (largest jump of mint pixels in the caption band within +-0.2 s of the word, never reaching a neighbouring word) and compared with the
   word's VO onset. Frame quantisation is 33 ms at 30 fps."""
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
cut, video = sys.argv[1], sys.argv[2]
T = json.load(open(os.path.join(ROOT, "audio-src", "v3", f"timing-{cut}.json")))
SR = 48000
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(ROOT, "audio-src", "v3", f"{cut}-vo.wav"), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32)
env = np.sqrt(np.convolve(x ** 2, np.ones(96) / 96, "same"))
pk_all = env.max()

toks = [(c["line"], tk["w"], tk["t"], c["hero"]) for c in T["cards"] for tk in c["toks"]]
# A. audio onsets
errA = []
for line, w, t, hero in toks:
    a, b = int((t - 0.3) * SR), int((t + 0.3) * SR)
    seg = env[max(a, 0):b]
    if len(seg) < 100: continue
    quiet = seg < pk_all * 10 ** (-45 / 20)
    # last >= 60 ms quiet run that ends within +-0.3 s of t
    runs, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if (j - i) / SR >= 0.06: runs.append((i, j))
            i = j
        else: i += 1
    if not runs: continue
    j = min(runs, key=lambda r: abs((max(a, 0) + r[1]) / SR - t))[1]
    if abs((max(a, 0) + j) / SR - t) > 0.15: continue   # no pause right before this word
    wpk = seg[j:j + int(0.25 * SR)].max(initial=0)
    if wpk <= 0: continue
    up = np.where(seg[j:] > wpk * 10 ** (-30 / 20))[0]
    if not len(up): continue
    onset = (max(a, 0) + j + up[0]) / SR
    errA.append((line, w, t, onset, (t - onset) * 1000))

# B. picture: mint caption word activation
p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip().split(",")
w, h = int(p[0]), int(p[1]); fps = 30
portrait = h > w
y0, y1 = (1380, 1660) if portrait else (900, 1045)
S = 2  # downscale
cmd = ["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},crop={w}:{y1 - y0}:0:{y0},scale={w // S}:{(y1 - y0) // S}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
fr = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.uint8).reshape(-1, (y1 - y0) // S, w // S, 3).astype(int)
r, g, b_ = fr[..., 0], fr[..., 1], fr[..., 2]
mint = (g > 150) & (r < 110) & (b_ > 120) & (b_ < 215) & (g - r > 90)
errB = []
allt = sorted(t for _, _, t, _ in toks)
for line, word, t, hero in toks:
    if hero: continue
    gap = min([abs(u - t) for u in allt if abs(u - t) > 1e-6] + [0.5])
    r = min(0.2, gap / 2)          # never let the window reach the neighbouring word's own activation
    k0, k1 = int(round((t - r) * fps)), int(round((t + r) * fps)) + 1
    k0 = max(k0, 1); k1 = min(k1, len(mint) - 1)
    jumps = [(np.logical_and(mint[k], ~mint[k - 1]).sum(), k) for k in range(k0, k1)]
    if not jumps: continue
    v, k = max(jumps)
    if v < 40: continue
    errB.append((line, word, t, k / fps, (k / fps - t) * 1000))

def summary(name, e):
    if not e: print(name, "no samples"); return
    d = np.array([x[-1] for x in e])
    print(f"{name}: n={len(d)} mean={d.mean():+.0f} ms  median abs={np.median(np.abs(d)):.0f} ms  max abs={np.abs(d).max():.0f} ms  within 80 ms: {(np.abs(d) <= 80).sum()}/{len(d)}")
# C. caption time vs the forced-alignment timestamp of the same word (ElevenLabs aligner, mapped through the edit)
fa = {(w["line"], w["t"]): w["fa"] for w in T["words"]}
errC = [(l, w, t, fa[(l, t)], (t - fa[(l, t)]) * 1000) for l, w, t, h in toks if (l, t) in fa]
print(f"== {cut}: {len(toks)} caption words")
summary("C  caption time vs forced-alignment word start (all words)", errC)
summary("A  caption time vs measured VO onset (words after a pause)", errA)
summary("B  rendered caption word turns mint vs VO caption time (frame-accurate)", errB)
for e in errC:
    if abs(e[-1]) > 80: print("  C >80ms:", e)
for e in errA:
    if abs(e[-1]) > 80: print("  A >80ms:", e)
for e in errB:
    if abs(e[-1]) > 80: print("  B >80ms:", e)
