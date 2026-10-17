#!/usr/bin/env python3
"""Mix the promo soundtrack: ElevenLabs music bed + ElevenLabs SFX placed on the edit's beat grid.

  mix.py main      -> audio-src/mix-16x9.wav   (48 s, matches index.html)
  mix.py vertical  -> audio-src/mix-9x16.wav   (matches vertical.html)

SFX are positioned so their transient (measured peak) lands exactly on the cue time.
Loudness normalisation (-16 LUFS, -1.5 dBTP) happens afterwards in ffmpeg (see render.sh)."""
import subprocess, sys, json, os
import numpy as np

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "..", "audio-src")
B0, BEAT = 0.088, 60 / 128
def b(n): return B0 + n * BEAT

def load(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(A, name), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

def peak_time(x):
    env = np.convolve(np.abs(x).mean(1), np.ones(240) / 240, "same")
    return int(np.argmax(env))

SFX = {k: load(k + ".mp3") for k in ["impact", "whoosh1", "whoosh2", "click", "tick", "chime", "shimmer", "blip"]}
PEAK = {k: peak_time(v) for k, v in SFX.items()}

def varied(x, rate):  # tiny pitch/length variation for repeated ticks (deterministic)
    n = int(len(x) / rate)
    idx = np.linspace(0, len(x) - 1, n)
    return np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], 1).astype(np.float32)

def cues_main():
    c = []
    c += [("impact", b(2), -2), ("shimmer", b(2) + 0.12, -13)]
    c += [("tick", b(12 + i * 0.5), -15, 0.94 + 0.03 * (i % 4)) for i in range(8)]
    c += [("whoosh2", b(16), -7)]
    c += [("click", b(22), -2)]
    c += [("whoosh1", b(28), -9)]
    c += [("tick", b(28.6) + i * 0.1, -9, 0.95 + 0.025 * (i % 5)) for i in range(10)]
    c += [("chime", b(32), -5), ("shimmer", b(32) + 0.1, -14)]
    c += [("blip", b(33), -17)]
    for n in (40, 48, 56, 64):
        c += [("whoosh2", b(n), -10)]
    c += [("blip", b(43), -18), ("blip", b(51), -18), ("blip", b(59), -18)]
    c += [("tick", b(66) + i * 0.115, -15, 0.95 + 0.025 * (i % 5)) for i in range(12)]
    for start, done in ((68, 69.5), (70.5, 72), (73, 74.5)):
        c += [("click", b(start), -8), ("blip", b(done), -11)]
    for n in (80, 82, 84, 86):
        c += [("whoosh1", b(n), -11)]
    c += [("whoosh2", b(88), -9), ("impact", b(88), -9)]
    c += [("shimmer", b(96), -12)]
    return c

def render(cues, music_segments, length, fade_out):
    """music_segments: list of (src_start, src_end, dst_start) in seconds, crossfaded 30 ms."""
    out = np.zeros((int(length * SR), 2), np.float32)
    music = load("music-a.mp3") * 10 ** (-6 / 20)
    xf = int(0.03 * SR)
    for s0, s1, d0 in music_segments:
        seg = music[int(s0 * SR):int(s1 * SR)].copy()
        ramp = np.linspace(0, 1, xf)[:, None]
        seg[:xf] *= ramp; seg[-xf:] *= ramp[::-1]
        i0 = int(d0 * SR) - xf // 2
        i0c = max(i0, 0)
        seg = seg[i0c - i0:]
        n = min(len(seg), len(out) - i0c)
        out[i0c:i0c + n] += seg[:n]
    fo = int(fade_out * SR)
    out[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
    log = []
    for cue in cues:
        name, t, db = cue[:3]
        x = SFX[name] if len(cue) < 4 else varied(SFX[name], cue[3])
        pk = PEAK[name] if len(cue) < 4 else int(PEAK[name] / cue[3])
        i0 = int(round(t * SR)) - pk
        g = 10 ** (db / 20)
        s = max(0, -i0); i0 = max(0, i0)
        n = min(len(x) - s, len(out) - i0)
        if n > 0:
            out[i0:i0 + n] += x[s:s + n] * g
        log.append({"sfx": name, "t": round(t, 3), "db": db})
    return out, log

def write(path, x):
    pk = np.abs(x).max()
    if pk > 0.98:  # keep headroom before loudnorm; ffmpeg does the final level
        x = x * (0.98 / pk)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_s24le", path],
                   input=x.astype(np.float32).tobytes(), check=True)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "main"
    if which == "main":
        out, log = render(cues_main(), [(0, 48, 0)], 48, 1.1)
        write(os.path.join(A, "mix-16x9.wav"), out)
        json.dump(log, open(os.path.join(A, "cues-16x9.json"), "w"), indent=1)
    else:
        from vertical_cues import cues_vertical, segments_vertical, LENGTH
        out, log = render(cues_vertical(b), segments_vertical(b), LENGTH, 1.0)
        write(os.path.join(A, "mix-9x16.wav"), out)
        json.dump(log, open(os.path.join(A, "cues-9x16.json"), "w"), indent=1)
    print("ok", which, len(log), "cues")
