#!/usr/bin/env python3
"""Objective 'listening' metrics for every VO take: length, speech span (-40 dBFS gate), sample peak,
clipped samples, RMS, words/s over the speech span, trailing audio after the last aligned word
(v3 artefacts show up there), and the aligned words."""
import glob, json, os, subprocess, sys
import numpy as np
SR = 48000
def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)
rows = []
for mp3 in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "audio-src", "vo", "[HL]*-t*.mp3"))):
    x = load(mp3); j = json.load(open(mp3[:-4] + ".json"))
    env = np.sqrt(np.convolve(x ** 2, np.ones(480) / 480, "same"))
    act = np.where(env > 10 ** (-40 / 20))[0]
    s0, s1 = (act[0] / SR, act[-1] / SR) if len(act) else (0, 0)
    w = j["words"]; we = w[-1][2] if w else 0
    pk = float(np.abs(x).max()); clip = int((np.abs(x) > 0.989).sum())
    rms = 20 * np.log10(np.sqrt(np.mean(x[int(s0*SR):int(s1*SR)] ** 2)) + 1e-9)
    name = os.path.basename(mp3)[:-4]
    print(f"{name:7s} len={len(x)/SR:5.2f} speech={s0:4.2f}-{s1:4.2f} ({s1-s0:4.2f}s) pk={20*np.log10(pk):5.1f}dB clip={clip:3d} rms={rms:5.1f} wps={len(w)/max(s1-s0,.01):4.2f} tail={s1-we:+5.2f} | " + " ".join(f"{a}@{b:.2f}" for a, b, c in w))
