#!/usr/bin/env python3
"""Frame-coverage check: samples a video every STEP seconds and flags frames
where any half or quadrant is a large flat dark region (uncovered frame).
usage: coverage_check.py video.mp4 [step=0.25]"""
import subprocess, sys, numpy as np
src = sys.argv[1]; step = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
W, H = 192, 108
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps={1/step},scale={W}:{H},format=gray",
                      "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(float)
regions = {"L": (slice(None), slice(0, W//2)), "R": (slice(None), slice(W//2, W)),
           "T": (slice(0, H//2), slice(None)), "B": (slice(H//2, H), slice(None)),
           "TL": (slice(0, H//2), slice(0, W//2)), "TR": (slice(0, H//2), slice(W//2, W)),
           "BL": (slice(H//2, H), slice(0, W//2)), "BR": (slice(H//2, H), slice(W//2, W))}
bad = 0
for i, f in enumerate(frames):
    flags = []
    for k, (ys, xs) in regions.items():
        r = f[ys, xs]
        dark = (r < 12).mean()          # share of near-pure-black pixels
        if dark > 0.85 or (r.mean() < 14 and r.std() < 2.0):
            flags.append(f"{k}:mean={r.mean():.1f},std={r.std():.1f},dark={dark:.2f}")
    if flags:
        bad += 1
        print(f"t={i*step:6.2f}s  " + "  ".join(flags))
print(f"checked {len(frames)} frames @ {step}s, flagged {bad}")
sys.exit(1 if bad else 0)
