#!/usr/bin/env python3
"""EnvKit promo v3: the edit decision list for the soundtrack and the captions.

One place defines, for each cut (main 16:9, vertical 9:16, ad15 16:9 15 s):
  * where each voiceover line (or each word group of a line) lands on the 140 BPM grid,
  * how the ElevenLabs music track is re-spliced on its beats (riser under the hook, hard cut to
    silence for "What if your dev stack... just worked?", the drop on the logo slam, the drop-out under
    "And the best part?", the hit on "It's free."),
  * every sound effect, placed so its transient lands on the frame the picture uses.

  edit_v3.py CUT        -> audio-src/v3/<cut>-{vo,music,sfx,mix}.wav
                           assets/timing-<cut>.js  (word timings for the captions + the picture)
                           renders/envkit-promo-v3-<cut>.srt  (main cut also: renders/envkit-promo-v3-16x9.srt)

The picture (index.html / vertical.html / ad15.html) reads assets/timing-<cut>.js, so a new voice
(tools/vo.py + tools/vo_config.json) re-times the captions and the mix without touching the HTML.
Lines are laid out one after another on the 140 BPM grid from their measured length (a different voice
gives different marks; the picture follows the marks). Edit time 0 is on a beat; beat n is at n * 60/140 s."""
import json, os, subprocess, sys
import numpy as np

SR = 48000
BEAT = 60 / 140
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
A = os.path.join(ROOT, "audio-src")
VO_DIR = os.path.join(A, "vo")
OUT = os.path.join(A, "v3")
CFG = json.load(open(os.path.join(HERE, "vo_config.json")))
def n(x): return x * BEAT

# Music: audio-src/music-v3-a.mp3 (ElevenLabs music_v1, tools/music_v3.py seed 140). Measured: 140.00 BPM,
# beat k transient at 0.445 + k * BEAT. k 0-14 build/riser, k 15 = hard drop, k 77-78 built-in filter
# break, k 79-94 sub-only section, k 95 final hit + tail (file ends at 44.6 s).
SB0 = 0.445
def sb(k): return SB0 + k * BEAT

def ffload(path, mono=False):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1" if mono else "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    return x.copy() if mono else x.reshape(-1, 2).copy()

def envelope(x, win=0.005):
    m = x if x.ndim == 1 else x.mean(1)
    k = max(1, int(win * SR))
    return np.sqrt(np.convolve(m ** 2, np.ones(k) / k, "same"))

# ── Voiceover takes ──────────────────────────────────────────────────────────────
def load_take(name):
    x = ffload(os.path.join(VO_DIR, name + ".mp3"), mono=True)
    j = json.load(open(os.path.join(VO_DIR, name + ".json")))
    return x, j

def take_metrics(name):
    x, j = load_take(name)
    env = envelope(x, 0.01)
    pk = env.max()
    act = np.where(env > pk * 10 ** (-32 / 20))[0]
    s0, s1 = act[0] / SR, act[-1] / SR
    w = j["words"]
    clip = int((np.abs(x) > 0.989).sum())
    tail = s1 - (w[-1][2] if w else s1)
    lead = (w[0][1] if w else s0) - s0
    rms = 20 * np.log10(np.sqrt(np.mean(x[int(s0 * SR):int(s1 * SR)] ** 2)) + 1e-9)
    # pitch range (semitones, p10..p90) from frame autocorrelation: more range = livelier read
    f0 = []
    fl = int(0.04 * SR)
    for i in range(int(s0 * SR), int(s1 * SR) - fl, fl // 2):
        f = x[i:i + fl]
        if np.sqrt(np.mean(f ** 2)) < pk * 0.25: continue
        ac = np.correlate(f, f, "full")[fl - 1:]
        lo, hi = int(SR / 300), int(SR / 60)
        lag = lo + int(np.argmax(ac[lo:hi]))
        if ac[lag] > 0.35 * ac[0]: f0.append(SR / lag)
    e5 = envelope(x, 0.005)
    isl = islands_of(e5, e5.max())
    trunc = float(isl[-1][1] > len(x) / SR - 0.02)   # last spoken island runs into the end of the file
    nisl = len(isl)
    rng = 12 * np.log2(np.percentile(f0, 90) / np.percentile(f0, 10)) if len(f0) > 4 else 0
    return dict(name=name, trunc=trunc, nisl=nisl, nwords=len(w), clip=clip, tail=tail, lead=lead, span=s1 - s0, wps=len(w) / max(s1 - s0, 0.1), rms=rms, range=rng)

STACCATO = {"L09", "L13"}
KEY_LINES = {"H1", "H2", "H3", "H4", "L16"}
def pick(line):
    if line in CFG.get("picks", {}): return CFG["picks"][line]
    takes = sorted(f[:-4] for f in os.listdir(VO_DIR) if f.startswith(line + "-t") and f.endswith(".mp3"))
    ms = [take_metrics(t) for t in takes]
    med = np.median([m["rms"] for m in ms])
    def score(m):
        s = 10 * (m["clip"] > 0) + 10 * m["trunc"] + (4 * (m["nisl"] != m["nwords"]) if line in STACCATO else 0) + 5 * max(0, m["tail"] - 0.35) + 2 * max(0, m["lead"] - 0.35) + 0.05 * abs(m["rms"] - med)
        if line not in STACCATO: s += 0.6 * abs(m["wps"] - 2.6)
        s -= (0.12 if line in KEY_LINES else 0.04) * min(m["range"], 12)
        return s
    best = min(ms, key=score)
    return best["name"]

PUNCT = tuple(".,?!…:;")
def islands_of(env, pk, thr_db=-38, bridge=0.12, minlen=0.1):
    on = env > pk * 10 ** (thr_db / 20)
    idx = np.flatnonzero(np.diff(np.concatenate([[0], on.astype(int), [0]])))
    runs = [[s / SR, e / SR] for s, e in zip(idx[::2], idx[1::2])]
    out = []
    for r in runs:
        if out and r[0] - out[-1][1] < bridge: out[-1][1] = r[1]
        else: out.append(r)
    out = [r for r in out if r[1] - r[0] >= minlen]
    # drop breaths/clicks: islands whose loudest point stays 20 dB under the take's peak
    loud = [r for r in out if env[int(r[0] * SR):int(r[1] * SR)].max() > pk * 10 ** (-20 / 20)]
    return loud or out

class Line:
    """One VO take. ElevenLabs' character alignment can be several hundred ms off for eleven_v3, so word
    onsets are re-anchored on the audio itself: words that follow a pause (sentence starts, every word of a
    staccato line) snap to the start of a speech island; words inside connected speech are interpolated."""
    def __init__(self, lid):
        self.id = lid
        self.take = pick(lid)
        self.x, j = load_take(self.take)
        self.text, self.model, self.settings = j["text"], j["model"], j["settings"]
        self.words = [list(w) for w in j["words"]]
        self.env = envelope(self.x, 0.005)
        self.pk = self.env.max()
        self.sil = self.pk * 10 ** (-38 / 20)
        self.isl = islands_of(self.env, self.pk)
        W = self.words
        isl = self.isl
        fa_path = os.path.join(VO_DIR, self.take + ".fa.json")
        fa = json.load(open(fa_path))["words"] if os.path.exists(fa_path) else None
        if fa and len(fa) == len(W):
            est = [w[1] for w in fa]          # ElevenLabs forced alignment (separate aligner)
            self.est_src = "forced-alignment"
        else:                                 # fall back to the TTS alignment, shifted onto the speech islands
            off = isl[0][0] - W[0][1]
            est = [w[1] + off for w in W]
            self.est_src = "tts-alignment"
        self.est = est
        # Boundaries the ear hears: starts of speech islands (after a pause) and the rise after an energy dip
        # (>= 6 dB under both neighbouring peaks). Words are matched to them by a monotone DP around the
        # aligner's estimate; a word with no boundary nearby keeps the estimate.
        e20 = 20 * np.log10(envelope(self.x, 0.010) / self.pk + 1e-9)
        hop = int(0.005 * SR); ev = e20[::hop]; tv = np.arange(len(ev)) * hop / SR
        cands = [(s0, 40.0) for s0, _ in isl]
        for k in range(3, len(ev) - 3):
            if ev[k] <= ev[k - 1] and ev[k] < ev[k + 1] and ev[k] > -60:
                lpk = ev[max(0, k - 24):k].max(); rpk = ev[k + 1:k + 25].max()
                depth = min(lpk, rpk) - ev[k]
                if depth >= 6:
                    rise = k
                    while rise < len(ev) - 1 and ev[rise] < ev[k] + 0.55 * (rpk - ev[k]): rise += 1
                    cands.append((tv[rise], depth))
        cands.sort()
        nW, nC = len(W), len(cands)
        INF = 1e9
        D = np.full((nW + 1, nC + 1), INF); D[0, :] = 0; P = {}
        for i in range(1, nW + 1):
            for j in range(nC + 1):
                best = (D[i - 1, j] + 1.5, (i - 1, j, None))
                if j > 0:
                    c = cands[j - 1]; d = abs(c[0] - est[i - 1])
                    if d < 0.25:
                        kb = int(np.argmin(D[i - 1, :j])); v = D[i - 1, kb] + d / 0.1 - min(c[1], 30) / 30
                        if v < best[0]: best = (v, (i - 1, kb, j - 1))
                if j > 0 and D[i, j - 1] < best[0]: best = (D[i, j - 1], (i, j - 1, "skip"))
                D[i, j] = best[0]; P[(i, j)] = best[1]
        self.onsets = list(est)
        i, j = nW, int(np.argmin(D[nW]))
        while i > 0:
            pi, pj, m = P[(i, j)]
            if m not in (None, "skip"): self.onsets[i - 1] = float(cands[m][0])
            i, j = pi, pj
        if self.onsets[0] > isl[0][0] + 0.15 or self.onsets[0] < isl[0][0] - 0.05: self.onsets[0] = isl[0][0]
        # sentence starts (after punctuation) that follow a pause are the "flagged" words used for splicing
        self.flagged = [0] + [i for i in range(1, nW) if any(abs(s0 - self.onsets[i]) < 0.03 for s0, _ in isl[1:])]
        for i in range(1, len(W)):  # keep monotone
            self.onsets[i] = max(self.onsets[i], self.onsets[i - 1] + 0.04)

    def island_end_before(self, t):
        ends = [e for s, e in self.isl if e <= t + 1e-6]
        return ends[-1] if ends else t

    def cut_before(self, i):
        if i == 0:
            return max(0.0, self.onsets[0] - 0.04)
        on = self.onsets[i]
        if i in self.flagged:
            pe = self.island_end_before(on)
            return max(pe + 0.03, (pe + on) / 2) if on - pe > 0.08 else on - 0.02
        a, b = max(0, int((on - 0.05) * SR)), int((on + 0.02) * SR)
        return (a + int(np.argmin(self.env[a:b]))) / SR

    def end_of(self, i):
        """End of word i including its natural decay."""
        if i + 1 < len(self.words) and (i + 1) not in self.flagged:
            return self.cut_before(i + 1)
        lim = self.onsets[i + 1] if i + 1 < len(self.words) else len(self.x) / SR
        if i + 1 == len(self.words):
            return min(self.isl[-1][1] + 0.12, lim)
        e = self.island_end_before(lim - 0.001)
        return min(e + 0.07, lim - 0.01)

def compress(x, t0, maxgap, sil):
    """Shorten pauses longer than maxgap inside a slice. Returns audio and a time map f(local_t)->new_t."""
    if maxgap is None: return x, (lambda t: t)
    env = envelope(x, 0.01)
    q = env < sil
    runs, i = [], 0
    while i < len(q):
        if q[i]:
            j = i
            while j < len(q) and q[j]: j += 1
            if (j - i) / SR > maxgap and i > 0 and j < len(q): runs.append((i, j))
            i = j
        else: i += 1
    if not runs: return x, (lambda t: t)
    parts, cuts, last = [], [], 0
    for i, j in runs:
        keep = int(maxgap * SR)
        mid0 = i + keep // 2; mid1 = j - keep // 2
        parts.append(x[last:mid0]); cuts.append((mid0 / SR, (mid1 - mid0) / SR)); last = mid1
    parts.append(x[last:])
    xf = int(0.006 * SR)
    out = parts[0]
    for p in parts[1:]:
        r = np.linspace(0, 1, xf)
        if len(out) > xf and len(p) > xf:
            mix = out[-xf:] * (1 - r) + p[:xf] * r
            out = np.concatenate([out[:-xf], mix, p[xf:]])
        else: out = np.concatenate([out, p])
    def f(t):
        s = 0
        for c, d in cuts:
            if t >= c + d: s += d
            elif t > c: s += t - c
        return t - s
    return out, f

def fade(x, fi=0.004, fo=0.025):
    x = x.copy(); a, b = int(fi * SR), int(fo * SR)
    if len(x) > a + b:
        x[:a] *= np.linspace(0, 1, a); x[-b:] *= np.linspace(1, 0, b)
    return x

TARGET_RMS = -17.0   # dBFS, speech-active RMS each line is levelled to (before the final loudnorm)
LINE_GAIN = {"L15": -2.5, "H4": -1.0}   # the two quiet turns stay intimate
_LINES = {}
def line(lid):
    if lid not in _LINES: _LINES[lid] = Line(lid)
    return _LINES[lid]

def tempo(x, r):
    if abs(r - 1) < 1e-3: return x
    out = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", f"atempo={r}",
                          "-f", "f32le", "-"], input=x.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(out, np.float32).copy()

def group_audio(L, a, b, maxgap=None, speed=1.0):
    """Audio of words a..b-1 of a line, pauses capped, optional pitch-preserving speed-up.
    Returns (audio, [local onset per word], local end)."""
    c0 = L.cut_before(a)
    c1 = min(L.cut_before(b), L.end_of(b - 1)) if b < len(L.words) else L.end_of(b - 1)
    x = fade(L.x[int(c0 * SR):int(c1 * SR)])
    x, f = compress(x, c0, maxgap, L.sil)
    x = tempo(x, speed)
    ons = [f(L.onsets[i] - c0) / speed for i in range(a, b)]
    end = f(min(L.end_of(b - 1), c1) - c0) / speed
    group_audio.fa = [f(max(L.est[i] - c0, 0)) / speed for i in range(a, b)]   # aligner times, same mapping
    return x, ons, end

def snap(t, grid):
    """Next grid point (in beats) at or after time t (seconds)."""
    if not grid: return t
    g = grid * BEAT
    return np.ceil(t / g - 1e-6) * g

def layout(seq, marks, speed=1.0):
    """seq: items placed one after another. Item keys:
       id      VO line id
       split   word indices that start a new group (default [0]); groups follow each other with ggap beats
       groups  explicit [a, b) word ranges instead of split (lets a short cut use a subset of a line)
       key     word index (absolute) whose onset is snapped to the grid for the first group (default first word)
       at      absolute beat for the key word (else: previous end + gap, snapped to grid)
       gap     minimum silence before the item, beats (default 0.5)
       ggap    minimum silence between groups, beats (default 0.35)
       grid    beat grid for snapping (default 0.5); staccato lines use split=all words
       maxgap  pause cap inside a group (s); speed: pitch-preserving tempo factor
       mark    name -> beat of the key word onset;  endmark name -> beat of the item end
       hold    extra beats reserved after the item for the picture"""
    placed, cur = [], 0.0
    for it in seq:
        L = line(it["id"])
        split = it.get("split", [0]); bounds = split + [len(L.words)]
        ranges = it.get("groups") or [(bounds[g], bounds[g + 1]) for g in range(len(split))]
        for gi, (a, b) in enumerate(ranges):
            x, ons, end = group_audio(L, a, b, it.get("maxgap"), it.get("speed", speed))
            key = it.get("key", a) if gi == 0 else a
            kof = ons[key - a] - ons[0]
            if gi == 0 and "at" in it:
                t_key = n(it["at"])
            else:
                gap = it.get("gap", 0.5) if gi == 0 else it.get("ggap", 0.35)
                t0 = max(cur + n(gap), n(it.get("after", -99)))
                t_key = snap(t0 + kof, it.get("grid", 0.5))
            off = t_key - ons[key - a]
            placed.append((L, a, b, x, ons, end, off, group_audio.fa))
            if gi == 0 and "mark" in it: marks[it["mark"]] = round(t_key / BEAT, 3)
            cur = off + end
        cur += n(it.get("hold", 0))
        if "endmark" in it: marks[it["endmark"]] = round(cur / BEAT, 3)
    return placed, cur

def render_vo(placed, length):
    vo = np.zeros(int(length * SR), np.float32)
    words, info = [], []
    for L, a, b, x, ons, end, off, fa in placed:
        seg_rms = 20 * np.log10(np.sqrt(np.mean(L.x[(L.env > L.sil * 4)] ** 2)) + 1e-9)
        g = 10 ** ((TARGET_RMS - seg_rms + LINE_GAIN.get(L.id, 0)) / 20)
        i0 = int(round(off * SR)); s = max(0, -i0); m = min(len(x) - s, len(vo) - max(i0, 0))
        if m > 0: vo[max(i0, 0):max(i0, 0) + m] += x[s:s + m] * g
        for k, i in enumerate(range(a, b)):
            e = off + (ons[k + 1] if k + 1 < len(ons) else end)
            words.append({"line": L.id, "i": i, "w": L.words[i][0], "t": round(off + ons[k], 3), "e": round(e, 3),
                          "fa": round(off + fa[k], 3)})
        info.append({"line": L.id, "take": L.take, "model": L.model, "t0": round(off + ons[0], 3), "t1": round(off + end, 3)})
    words.sort(key=lambda w: w["t"])
    return vo, words, info

# ── Captions (display text per line; tokens map to the spoken words) ───────────────
DISPLAY = {"L08": [["Every", 0], ["project", 1], ["gets", 2], ["its", 3], ["own", 4], [".test", 5]]}
HERO = {"H1", "H2", "H3", "H4", "L09", "L13", "L15", "L16"}   # these lines are the big kinetic type itself (no lower-third duplicate)
def captions(words):
    by = {}
    for w in words: by.setdefault(w["line"], []).append(w)
    cards = []
    for lid, ws in by.items():
        ws = sorted(ws, key=lambda w: w["i"])
        disp = DISPLAY.get(lid)
        if disp: toks = [{"w": d, "t": next(w["t"] for w in ws if w["i"] == i)} for d, i in disp]
        else: toks = [{"w": w["w"].replace("...", "…"), "t": w["t"]} for w in ws]
        for k, tk in enumerate(toks):
            tk["e"] = round(toks[k + 1]["t"] if k + 1 < len(toks) else ws[-1]["e"], 3)
        cards.append({"line": lid, "hero": lid in HERO, "t0": toks[0]["t"], "t1": round(ws[-1]["e"], 3), "toks": toks})
    cards.sort(key=lambda c: c["t0"])
    return cards

# ── Music ────────────────────────────────────────────────────────────────────────
_MUSIC = None
def music_track(segments, length):
    """segments: (src_k0, src_k1, dst_beat, env) — src beats k0..k1 of music-v3-a placed so beat k0's transient
    lands on edit beat dst. env: optional list of (t_rel_seconds, gain_db) breakpoints."""
    global _MUSIC
    if _MUSIC is None: _MUSIC = ffload(os.path.join(A, "music-v3-a.mp3")) * 10 ** (-5 / 20)
    m = _MUSIC
    out = np.zeros((int(length * SR), 2), np.float32)
    pre = 0.012
    for k0, k1, dstb, *rest in segments:
        dst = n(dstb)
        s0 = sb(k0) - pre; s1 = (sb(k1) - pre) if k1 is not None else len(m) / SR
        seg = m[int(s0 * SR):int(s1 * SR)].copy()
        seg[:int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))[:, None]
        tail = int(0.008 * SR) if k1 is not None else int(0.4 * SR)
        seg[-tail:] *= np.linspace(1, 0, tail)[:, None]
        if rest and rest[0]:
            pts = rest[0]; tt = np.arange(len(seg)) / SR
            db = np.interp(tt, [p[0] for p in pts], [p[1] for p in pts])
            seg *= (10 ** (db / 20))[:, None]
        i0 = int(round((dst - pre) * SR)); s = max(0, -i0); i0 = max(0, i0)
        k = min(len(seg) - s, len(out) - i0)
        if k > 0: out[i0:i0 + k] += seg[s:s + k]
    return out

def groove(from_beat, to_beat):
    """Continuous drop groove from the hard drop (src beat 15) between two edit beats; loops on bar lines
    (back to src beat 23) if it would run into the built-in break at src beat 77."""
    segs, cur, k = [], from_beat, 15
    while cur < to_beat - 1e-6:
        room = 76 - k
        take = min(room, to_beat - cur)
        segs.append((k, k + take, cur)); cur += take; k = 23
    return segs

def duck(music, vo, depth_db=-8.0):
    """Sidechain: music down depth_db while the VO speaks (40 ms look-ahead, 20 ms attack, 280 ms release)."""
    e = envelope(vo, 0.01)
    ds = 48  # 1 kHz control rate
    c = e[::ds]
    act = np.clip((20 * np.log10(c + 1e-9) + 48) / 12, 0, 1)   # 0 below -48 dBFS, 1 above -36 dBFS
    look = 40
    act = np.concatenate([act[look:], np.zeros(look)])
    g = np.zeros_like(act); v = 0.0
    a_up, a_dn = 1 - np.exp(-1 / 20), 1 - np.exp(-1 / 280)
    for i, x in enumerate(act):
        v += (x - v) * (a_up if x > v else a_dn); g[i] = v
    gain = 10 ** (depth_db * g / 20)
    gain = np.repeat(gain, ds)[:len(music)]
    if len(gain) < len(music): gain = np.pad(gain, (0, len(music) - len(gain)), constant_values=1)
    return music * gain[:, None]

# ── Sound effects ────────────────────────────────────────────────────────────────
_SFX = {}
def sfx(name):
    if name not in _SFX:
        x = ffload(os.path.join(A, name + ".mp3"))
        e = np.convolve(np.abs(x).mean(1), np.ones(240) / 240, "same")
        _SFX[name] = (x, int(np.argmax(e)))
    return _SFX[name]

def sfx_track(cues, length):
    out = np.zeros((int(length * SR), 2), np.float32)
    log = []
    for cue in cues:
        name, t, db = cue[:3]
        rate = cue[3] if len(cue) > 3 else 1.0
        x, pk = sfx(name)
        if rate != 1.0:
            idx = np.linspace(0, len(x) - 1, int(len(x) / rate))
            x = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], 1).astype(np.float32)
            pk = int(pk / rate)
        i0 = int(round(t * SR)) - pk; s = max(0, -i0); i0 = max(0, i0)
        k = min(len(x) - s, len(out) - i0)
        if k > 0: out[i0:i0 + k] += x[s:s + k] * 10 ** (db / 20)
        log.append({"sfx": name, "t": round(t, 3), "db": db})
    return out, log

# ── Shared blocks ────────────────────────────────────────────────────────────────
HOOK_SPEED = 1.0   # the pains are generated at native speed 1.15 (eleven_multilingual_v2), see vo_config.json
SPEED = {"main": 1.1, "vertical": 1.12, "ad15": 1.12}   # pitch-preserving tempo for the VO after the hook
def hook_seq(turn=True):
    """The swappable hook: three pains on a 2-beat grid (each struck through as the next one slams in), the music
    cuts out on the third strike, and the turn starts right there; the logo slams on "worked".
    Marks: h1 h2 h3 (line onsets), x1..x3 (strikes; x3 = music cut), h4, slam."""
    seq = [
        {"id": "H1", "at": 0.25, "mark": "h1", "maxgap": 0.08, "speed": HOOK_SPEED},
        {"id": "H2", "gap": -0.3, "grid": 0.5, "mark": "h2", "maxgap": 0.08, "speed": HOOK_SPEED},
        {"id": "H3", "gap": -0.3, "grid": 0.5, "mark": "h3", "maxgap": 0.08, "speed": HOOK_SPEED, "endmark": "h3e"},
    ]
    if turn:   # "What if your dev stack… just worked?" — key word "worked?" (index 6) lands on the slam beat
        seq.append({"id": "H4", "key": 6, "gap": 0.0, "grid": 0.5, "mark": "slam", "maxgap": 0.3, "speed": 1.0, "endmark": "h4e"})
    return seq

def hook_marks(M):
    M["x1"] = M["h2"]; M["x2"] = M["h3"]
    M["x3"] = float(np.ceil((M["h3e"] + 0.1) * 2) / 2)    # last strike + music cut (half-beat grid)
    if "h4e" not in M:
        M["slam"] = M["x3"] + 1.5                         # no turn: 1.5 beats of silence, then the slam

def hook_music(M):
    # riser (src beats 5..14 build into the drop) runs under the three pains and stops dead on x3
    k_end = 15; k_start = k_end - int(M["x3"])
    segs = [(max(k_start, 0), k_end, max(0, -k_start) * 0 + (M["x3"] - (k_end - max(k_start, 0))))]
    # a low sub swell under the turn (src sub-only section), fading in, cut on the slam
    sw = M["slam"] - M["x3"]
    if sw > 0.5:
        segs.append((79, 79 + int(np.ceil(sw)), M["x3"], [(0, -40), (n(sw) * 0.7, -20), (n(sw), -15)]))
    return segs

def hook_sfx(M):
    c = []
    for k, (h, x) in enumerate((("h1", "x1"), ("h2", "x2"), ("h3", "x3"))):
        c += [("slam" if k == 0 else "impact", n(M[h]), -10 if k == 0 else -9), ("glitch1", n(M[h]), -11, 1.0 + 0.08 * k)]
        c += [("strike", n(M[x]) - 0.06, -9), ("glitch2", n(M[x]), -8, 0.95 + 0.07 * k)]
        c += [("glitch2", n(M[h]) + n(0.75) + 0.03 * j, -19, 1.1 + 0.05 * j) for j in range(2)]  # stutter
    c += [("tapestop", n(M["x3"]) + 0.05, -16)]
    c += [("reverse", n(M["slam"]) - 0.02, -9)]
    c += [("slam", n(M["slam"]), -2), ("impact", n(M["slam"]), -8), ("shimmer", n(M["slam"]) + 0.1, -12)]
    return c

BD_ENV = [(0, -3), (0.8, -6), (1.35, -14), (1.48, -60), (30, -60)]

def build(cut):
    M = {}
    if cut == "main":
        seq = hook_seq() + [
            {"id": "L03", "gap": 1.25, "grid": 0.5, "mark": "tag", "maxgap": 0.1},
            {"id": "L04", "split": [0, 4], "gap": 0.25, "ggap": 0.35, "maxgap": 0.1, "mark": "stack"},
            {"id": "L05", "gap": 0.75, "grid": 1.0, "mark": "pick", "maxgap": 0.1},
            {"id": "L06", "key": 2, "gap": 1.0, "grid": 1.0, "mark": "live", "maxgap": 0.08},
            {"id": "L07", "split": [0, 2, 4], "gap": 0.35, "ggap": 0.25, "grid": 0.5, "maxgap": 0.1, "mark": "https"},
            {"id": "L08", "gap": 0.5, "grid": 1.0, "mark": "sites", "maxgap": 0.1},
            {"id": "L09", "split": [0, 1, 2, 3, 4], "gap": 0.5, "ggap": 0.05, "grid": 0.5, "mark": "svc", "speed": 1.15},
            {"id": "L10", "gap": 0.25, "grid": 0.5, "mark": "run", "maxgap": 0.1},
            {"id": "L11", "gap": 0.75, "grid": 1.0, "mark": "ai", "maxgap": 0.1},
            {"id": "L12", "gap": 0.25, "grid": 0.5, "mark": "ask", "maxgap": 0.1, "hold": 2.75},
            {"id": "L13", "split": [0, 1, 2, 3], "gap": 0.5, "ggap": 0.05, "grid": 0.5, "mark": "mont", "speed": 1.15},
            {"id": "L14", "gap": 0.25, "grid": 0.5, "mark": "here", "maxgap": 0.1, "endmark": "here_e"},
            {"id": "L15", "gap": 1.0, "grid": 1.0, "mark": "best", "maxgap": 0.1, "endmark": "best_e"},
            {"id": "L16", "key": 1, "gap": 0.6, "grid": 1.0, "mark": "free", "maxgap": 0.1, "hold": 0},
            {"id": "L17", "split": [0, 1], "gap": 2.5, "ggap": 0.5, "grid": 1.0, "mark": "env", "maxgap": 0.12, "endmark": "env_e"},
        ]
        hold_end = 2.0
    elif cut == "vertical":
        seq = hook_seq() + [
            {"id": "L03", "gap": 1.25, "grid": 0.5, "mark": "tag", "maxgap": 0.1},
            {"id": "L05", "gap": 0.75, "grid": 1.0, "mark": "pick", "maxgap": 0.1, "speed": 1.05},
            {"id": "L06", "key": 2, "gap": 1.0, "grid": 1.0, "mark": "live", "maxgap": 0.08, "speed": 1.05},
            {"id": "L09", "split": [0, 1, 2, 3, 4], "gap": 0.75, "ggap": 0.05, "grid": 0.5, "mark": "svc", "speed": 1.15},
            {"id": "L11", "gap": 0.75, "grid": 1.0, "mark": "ai", "maxgap": 0.1, "speed": 1.05},
            {"id": "L12", "gap": 0.25, "grid": 0.5, "mark": "ask", "maxgap": 0.1, "speed": 1.05, "hold": 3.0},
            {"id": "L15", "gap": 1.0, "grid": 1.0, "mark": "best", "maxgap": 0.1, "endmark": "best_e"},
            {"id": "L16", "key": 1, "gap": 0.6, "grid": 1.0, "mark": "free", "maxgap": 0.1},
            {"id": "L17", "split": [0, 1], "gap": 2.0, "ggap": 0.5, "grid": 1.0, "mark": "env", "maxgap": 0.12, "endmark": "env_e"},
        ]
        hold_end = 1.5
    else:  # ad15
        seq = hook_seq(turn=False) + [
            {"id": "L05", "gap": 2.25, "grid": 1.0, "mark": "pick", "maxgap": 0.1, "speed": 1.12},
            {"id": "L06", "key": 2, "gap": 0.6, "grid": 1.0, "mark": "live", "maxgap": 0.08, "speed": 1.12},
            {"id": "L09", "groups": [[0, 1], [2, 3], [4, 5]], "gap": 0.5, "ggap": 0.0, "grid": 0.5, "mark": "svc", "speed": 1.15, "endmark": "svc_e"},
            {"id": "L16", "key": 1, "gap": 0.75, "grid": 1.0, "mark": "free", "maxgap": 0.1, "hold": 1.0},
            {"id": "L17", "split": [0, 1], "gap": 0.4, "ggap": 0.2, "grid": 0.5, "mark": "env", "maxgap": 0.08, "endmark": "env_e"},
        ]
        hold_end = 0.3
    placed, end = layout(seq, M, SPEED[cut])
    hook_marks(M)
    for it in seq:
        if it["id"] == "H4": it["after"] = M["x3"]
    M2 = {}
    placed, end = layout(seq, M2, SPEED[cut])
    M.update(M2); hook_marks(M)
    post = seq[len([x for x in seq if x["id"].startswith("H")])]
    post["at"] = M["slam"] + post.pop("gap", 1.0) if "at" not in post else post["at"]
    M2 = {}
    placed, end = layout(seq, M2, SPEED[cut])
    M.update(M2); hook_marks(M)
    # picture marks derived from the VO
    if "live" in M: M["click"] = M["live"] - 2.0 if cut != "ad15" else M["live"] - 1.5
    M["pickin"] = max(M["pick"] - 1, M["slam"] + 1.25)
    if "free" in M: M["bd"] = M["best"] - 1.0 if "best" in M else M["free"] - 1.5
    M["card"] = float(np.floor(M["env"] - 0.75))
    M["end"] = float(np.ceil((end + hold_end) / BEAT * 2) / 2)
    length = round(n(M["end"]), 3)
    vo, words, info = render_vo(placed, length)
    W = {}
    for w in words: W.setdefault(w["line"], []).append(w)
    for k in W: W[k].sort(key=lambda w: w["i"])
    # music
    mus = hook_music(M)
    mus += groove(M["slam"], M["bd"])
    mus.append((77, 85, M["bd"], BD_ENV if "best" in M else [(0, -4), (0.5, -10), (0.62, -60), (30, -60)]))
    mus += [(15, 15 + int(M["card"] - M["free"]), M["free"]), (95, None, M["card"])]
    music = duck(music_track(mus, length), vo)
    cues = hook_sfx(M) + cut_sfx(cut, M, W)
    fx, cue_log = sfx_track(cues, length)
    return length, M, vo, words, info, music, fx, cue_log, mus

def cut_sfx(cut, M, W):
    c = []
    B = lambda k: n(M[k])
    if "tag" in M:
        c += [("whoosh2", B("tag") - 0.1, -12)]
    if "stack" in M:
        c += [("pop", B("stack") + n(k * 0.5), -17, 0.94 + 0.03 * (k % 4)) for k in range(9)]
    c += [("whoosh1", B("pick") - n(0.5), -10), ("click", B("click"), -3)]
    c += [("tick", B("click") + 0.12 + i * 0.07, -13, 0.95 + 0.03 * (i % 4)) for i in range(8)]
    c += [("chime", B("live"), -5), ("shimmer", B("live") + 0.08, -14)]
    if "https" in M:
        hs = [w for w in W["L07"] if w["i"] in (0, 2, 4)]
        c += [("whoosh1", hs[0]["t"] - 0.04, -13), ("whoosh1", hs[1]["t"] - 0.04, -13), ("impact", hs[2]["t"], -13)]
    if "sites" in M:
        c += [("whoosh2", B("sites") - 0.08, -10), ("blip", B("sites") + n(4), -17)]
    for w in W.get("L09", []): c += [("pop", w["t"], -9), ("whoosh1", w["t"] - 0.05, -18)]
    if "run" in M: c += [("blip", B("run"), -11), ("shimmer", B("run"), -15)]
    if "ai" in M:
        c += [("glitch1", B("ai"), -13), ("whoosh2", B("ask") - 0.1, -11)]
        c += [("tick", B("ask") + 0.3 + i * 0.06, -16, 0.95 + 0.025 * (i % 5)) for i in range(10)]
        a = M["ask"] + 2.5
        for k in range(3): c += [("click", n(a + 1.5 * k), -10), ("blip", n(a + 1.5 * k + 1.0), -11)]
    for w in W.get("L13", []): c += [("whoosh1", w["t"] - 0.04, -10)]
    if "here" in M: c += [("impact", B("here"), -12)]
    c += [("reverse", B("free") - 0.03, -9), ("slam", B("free"), -2), ("subdrop", B("free"), -6), ("shimmer", B("free") + 0.1, -11)]
    c += [("whoosh2", B("card"), -10), ("impact", B("card"), -9), ("shimmer", B("card") + n(6), -13)]
    return c

def write_wav(path, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2" if x.ndim == 2 else "1", "-i", "-",
                    "-c:a", "pcm_s24le", path], input=x.astype(np.float32).tobytes(), check=True)

def srt(cards, path):
    def ts(t):
        ms = int(round(max(t, 0) * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w") as f:
        for i, c in enumerate(cards, 1):
            nxt = cards[i]["t0"] - 0.07 if i < len(cards) else c["t1"] + 0.4
            f.write(f"{i}\n{ts(c['t0'] - 0.05)} --> {ts(min(c['t1'] + 0.35, nxt))}\n{' '.join(t['w'] for t in c['toks'])}\n\n")

if __name__ == "__main__":
    cut = sys.argv[1] if len(sys.argv) > 1 else "main"
    os.makedirs(OUT, exist_ok=True)
    length, M, vo, words, info, music, fx, cue_log, mus = build(cut)
    voS = np.stack([vo, vo], 1)
    mix = music + fx * 0.9 + voS
    fo = int(0.2 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    pk = np.abs(mix).max()
    if pk > 0.98: mix *= 0.98 / pk
    for name, x in (("vo", voS), ("music", music), ("sfx", fx), ("mix", mix)):
        write_wav(os.path.join(OUT, f"{cut}-{name}.wav"), x)
    cards = captions(words)
    timing = {"cut": cut, "beat": BEAT, "length": length, "voice": CFG["voice_id"], "marks": M,
              "words": words, "cards": cards, "segments": info}
    with open(os.path.join(ROOT, "assets", f"timing-{cut}.js"), "w") as f:
        f.write("/* generated by tools/edit_v3.py — do not edit */\nwindow.TIMING = " + json.dumps(timing) + ";\n")
    json.dump({**timing, "music": mus, "sfx": cue_log}, open(os.path.join(OUT, f"timing-{cut}.json"), "w"), indent=1)
    if cut == "main":
        os.makedirs(os.path.join(ROOT, "renders"), exist_ok=True)
        srt(cards, os.path.join(ROOT, "renders", "envkit-promo-v3-16x9.srt"))
    segs = sorted(info, key=lambda s: s["t0"])
    for p, q in zip(segs, segs[1:]):
        if q["t0"] < p["t1"] - 0.01: print("WARN overlap", p, q)
    for s_ in segs: print(f"  {s_['line']} {s_['take']:6s} {s_['t0']:6.2f}-{s_['t1']:6.2f}")
    print("marks", {k: round(v, 2) for k, v in M.items()})
    print("ok", cut, f"length={length}s", len(words), "words", len(cards), "cards")
