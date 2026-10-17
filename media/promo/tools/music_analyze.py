#!/usr/bin/env python3
"""Tempo + beat phase + per-bar loudness of a music file (numpy only).
  music_analyze.py FILE"""
import subprocess, sys
import numpy as np
SR = 22050
def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)
x = load(sys.argv[1]); hop = 256; fr = SR / hop
n = len(x) // hop
frames = x[:n * hop].reshape(n, hop)
# spectral-flux onset envelope (low band weighted for kicks)
win = 1024
spec = []
for i in range(0, len(x) - win, hop):
    spec.append(np.abs(np.fft.rfft(x[i:i + win] * np.hanning(win))))
S = np.log1p(np.array(spec))
flux = np.maximum(0, np.diff(S, axis=0)).sum(1)
lowflux = np.maximum(0, np.diff(S[:, :24], axis=0)).sum(1)
o = flux - np.convolve(flux, np.ones(16) / 16, "same"); o = np.maximum(o, 0)
best = None
for bpm in np.arange(120, 160.01, 0.05):
    per = fr * 60 / bpm
    for ph in np.arange(0, per, 0.5):
        idx = (ph + per * np.arange(int((len(o) - ph) / per))).astype(int)
        sc = o[idx].mean()
        if best is None or sc > best[0]: best = (sc, bpm, ph / fr)
sc, bpm, ph = best
beat = 60 / bpm
print(f"len={len(x)/SR:.2f}s bpm={bpm:.2f} first beat={ph:.3f}s")
# downbeat: choose beat offset 0..3 with most low-band flux
lf = lowflux
def at(t): return lf[min(int(t * fr), len(lf) - 1)]
scores = [np.mean([at(ph + (k + 4 * m) * beat) for m in range(int(len(x) / SR / beat / 4) - 1)]) for k in range(4)]
db = ph + int(np.argmax(scores)) * beat
print("downbeat offset", db, scores)
bar = 4 * beat
t = db % bar
print("bar  start  rmsdB  lowflux")
k = 0
while t < len(x) / SR:
    seg = x[int(t * SR):int((t + bar) * SR)]
    if len(seg) < 100: break
    print(f"{k:3d} {t:6.2f} {20*np.log10(np.sqrt(np.mean(seg**2))+1e-9):6.1f} {np.mean(lf[int(t*fr):int((t+bar)*fr)]):6.1f}")
    t += bar; k += 1
