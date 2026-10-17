#!/usr/bin/env python3
"""Rough tempo + beat grid + loudness envelope of an audio file (numpy only)."""
import subprocess, sys, numpy as np
src = sys.argv[1]; sr = 22050
x = np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",src,"-ac","1","-ar",str(sr),"-f","f32le","-"],
    capture_output=True, check=True).stdout, np.float32)
hop = 256; n = 1024
frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n)
S = np.abs(np.fft.rfft(frames, axis=1))
low = S[:, :12].sum(1)  # < ~250Hz kick band
flux = np.maximum(0, np.diff(np.log1p(S), axis=0)).sum(1)
fr = sr / hop
ac = np.correlate(flux - flux.mean(), flux - flux.mean(), "full")[len(flux)-1:]
lags = np.arange(len(ac)) / fr; m = (lags > 60/180) & (lags < 60/70)
lag = lags[m][np.argmax(ac[m])]; bpm = 60 / lag
# phase: best offset for comb over flux
period = lag * fr; best = max(range(int(period)), key=lambda o: flux[np.round(np.arange(o, len(flux), period)).astype(int)].sum())
t0 = best / fr
print(f"bpm~{bpm:.2f} beat={lag:.4f}s first_beat={t0:.3f}s")
rms = np.sqrt(np.convolve(x**2, np.ones(sr//2)/(sr//2), "same"))
for s in range(0, int(len(x)/sr)):
    seg = x[s*sr:(s+1)*sr]; db = 20*np.log10(np.sqrt((seg**2).mean())+1e-9)
    lowseg = low[int(s*fr):int((s+1)*fr)]
    print(f"{s:3d}s {db:6.1f} dB  {'#'*max(0,int((db+40)))}  kick_peaks={np.round(np.argsort(lowseg)[-2:]/fr+s,2).tolist()}")
