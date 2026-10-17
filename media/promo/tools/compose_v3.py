#!/usr/bin/env python3
"""Write the three v3 compositions from the edit marks (audio-src/v3/timing-<cut>.json):
  index.html     main 16:9 (1920x1080)
  vertical.html  9:16 (1080x1920)
  ad15.html      16:9 15 s ad cut
Only the clip timings that HyperFrames needs as static attributes (root duration, backdrop videos)
are written here; all animation lives in assets/v3.js and reads assets/timing-<cut>.js at runtime.
  compose_v3.py [main|vertical|ad15 ...]"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FILES = {"main": "index.html", "vertical": "vertical.html", "ad15": "ad15.html"}

LOGO = """<svg class="mark" viewBox="6 4 384 285" aria-hidden="true">
  <path class="bar" d="M30.17,20.83 Q33.00,18.00 37.00,17.98 L244.00,17.02 Q248.00,17.00 245.51,20.13 L204.49,71.87 Q202.00,75.00 198.00,75.00 L86.00,75.00 Q82.00,75.00 79.88,78.39 L79.12,79.61 Q77.00,83.00 73.00,82.93 L23.00,82.07 Q19.00,82.00 19.08,78.00 L19.92,35.00 Q20.00,31.00 22.83,28.17 Z" />
  <path class="bar" d="M19.00,120.00 Q19.00,116.00 23.00,116.00 L171.00,116.00 Q175.00,116.00 172.54,119.15 L152.46,144.85 Q150.00,148.00 152.22,151.33 L165.78,171.67 Q168.00,175.00 164.00,175.00 L86.91,175.00 Q83.00,175.00 80.50,178.00 L80.50,178.00 Q78.00,181.00 74.09,181.00 L23.00,181.00 Q19.00,181.00 19.00,177.00 Z" />
  <path class="bar" d="M19.09,223.00 Q19.00,219.00 23.00,219.00 L196.00,219.00 Q200.00,219.00 202.37,222.22 L239.63,272.78 Q242.00,276.00 238.00,276.00 L38.00,276.00 Q34.00,276.00 31.07,273.28 L22.93,265.72 Q20.00,263.00 19.91,259.00 Z" />
  <path class="k" d="M292.11,19.33 Q294.00,17.00 297.00,17.00 L372.00,17.00 Q375.00,17.00 373.10,19.33 L270.90,144.67 Q269.00,147.00 270.87,149.34 L370.13,273.66 Q372.00,276.00 369.00,276.00 L285.00,276.00 Q282.00,276.00 280.11,273.67 L184.89,156.33 Q183.00,154.00 184.89,151.67 Z" />
</svg>
<div class="word">EnvKit</div>"""

OK = '<svg class="ok" viewBox="0 0 22 22"><circle cx="11" cy="11" r="10" fill="rgba(45,212,170,0.15)" stroke="#2dd4aa" stroke-width="1.5" /><path d="M6.5 11.5 L9.6 14.4 L15.5 8" fill="none" stroke="#2dd4aa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>'
def tool(cls, name, args, res):
    return (f'<div class="tool {cls}"><div class="ic"><div class="spin"></div>{OK}</div>'
            f'<div><div class="name"><em>envkit ·</em> {name} <em>{args}</em></div><div class="res">{res}</div></div></div>')
USER = "Redis stopped and the shop queue is failing. Can you fix it?"
CHAT = ('<div id="chat"><div class="hd"><span class="live"></span><b>AI assistant</b><span class="sep">·</span>connected to EnvKit over MCP</div>'
        '<div class="bd"><div class="msg-user">' + " ".join(f'<span class="w">{w}</span>' for w in USER.split()) + '</div>'
        + tool("t1", "diagnose_service", '{ "name": "redis" }', "stopped · port 6379 is free · config OK")
        + tool("t2", "start_service", '{ "name": "redis" }', "<b>running</b> · 127.0.0.1:6379")
        + tool("t3", "restart_site_queue_worker", '{ "name": "shop" }', "worker <b>default</b> restarted")
        + '<div class="msg-ai">Redis is back on <code>:6379</code> and the shop queue worker restarted. Jobs are processing again.</div></div></div>')

PORTRAIT_CSS = """
      #bg .glow { top: 30%; }
      .lockup { gap: 30px; } .lockup .mark { width: 140px; } .lockup .word { font-size: 120px; }
      .endcard .lockup.sm .mark { width: 130px; } .endcard .lockup.sm .word { font-size: 116px; }
      .endcard .tag { font-size: 46px; padding: 0 60px; }
      .ctarow { flex-direction: column; gap: 34px; } .ctarow .free { font-size: 42px; } .ctarow .btn { font-size: 44px; padding: 26px 56px; }
      #chat .hd { font-size: 27px; } .msg-user { font-size: 31px; max-width: 820px; }
      .tool .name { font-size: 24px; } .tool .res { font-size: 23px; } .msg-ai { font-size: 31px; } .msg-ai code { font-size: 27px; }
      .chiprow .chip { font-size: 36px; }
      .dlg { width: 600px; font-size: 28px; } .dlg b { font-size: 34px; }"""
LAND_CSS = """
      .ctarow .btn { font-size: 34px; padding: 20px 44px; }
      #chat .hd { font-size: 23px; } .msg-user { font-size: 26px; max-width: 700px; } .tool .name { font-size: 22px; } .tool .res { font-size: 20px; } .msg-ai { font-size: 26px; }"""

def b2s(T, k, off=0.0): return round((T["marks"][k] + off) * T["beat"], 3)

def videos(cut, T):
    """Backdrop clips (graded Higgsfield footage, always under the UI). (file, start, end, media_start, peak, zoom)"""
    sfx = "16x9" if cut != "vertical" else "9x16"
    M = T["marks"]; L = T["length"]
    v = [("ribbons", 0, b2s(T, "x3") + 0.2, 0.0, 0.45, 1.12)]
    # the tunnel starts at beat 8 in every cut (the v3 launch edit); keeping it fixed keeps every frame after the
    # slam identical when only the hook is re-cut, so a new hook can be spliced onto the existing render
    tun_from = round(8 * T["beat"], 3)
    v.append(("tunnel", tun_from, min(b2s(T, "slam") + 1.6, tun_from + 7.5), 0.4, 0.75 if "h4e" in M else 0.85, 1.25))
    mid0 = b2s(T, "slam") + 1.6
    mid1 = b2s(T, "bd")
    t = mid0
    for name in ["circuit", "monoliths", "ribbons", "circuit"]:   # quiet light under the UI, 8 s clips back to back
        if t >= mid1 - 0.5: break
        e = min(t + 7.6, mid1)
        v.append((name, t, e, 0.2, 0.3, 1.08)); t = e - 0.4
    v.append(("shockwave", b2s(T, "free") - 0.15, b2s(T, "card") + 0.1, 0.5, 0.6, 1.0))
    v.append(("monoliths", b2s(T, "card") - 0.2, L, 0.0, 0.55, 1.1))
    out = []
    for i, (n, s, e, ms, pk, zm) in enumerate(v):
        d = round(min(e - s, 8.0 - ms - 0.05), 3)
        ramp = f' data-ramp="{b2s(T, "slam")}"' if n == "tunnel" else ""
        out.append(f'      <video class="clip bgv vid" id="v{i}" src="assets/ai/{n}-{sfx}-graded.mp4" data-start="{round(s, 3)}" data-duration="{d}" '
                   f'data-media-start="{ms}" data-peak="{pk}" data-zoom="{zm}"{ramp} data-track-index="1" muted playsinline></video>')
    return "\n".join(out)

def splice_frame(T, fps=30):
    """First frame that is identical with or without the hook: the turn text is gone 0.25 s after the slam."""
    import math
    return math.ceil((T["marks"]["slam"] * T["beat"] + 0.25) * fps)

def compose(cut, hook=False):
    T = json.load(open(os.path.join(ROOT, "audio-src", "v3", f"timing-{cut}.json")))
    W, H = (1080, 1920) if cut == "vertical" else (1920, 1080)
    L = T["length"]
    full = ""
    if hook:   # hook-only render: same timeline maths (data-full-duration), only the first frames are rendered
        full = f' data-full-duration="{L}"'
        L = round(splice_frame(T) / 30 + 0.3, 3)
    cid = {"main": "main", "vertical": "vertical", "ad15": "ad15"}[cut]
    html = f"""<!doctype html>
<html lang="en" data-resolution="{'portrait' if H > W else 'landscape'}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <!-- EnvKit promo v3 ({cut}, {W}x{H}, {L} s). Generated by tools/compose_v3.py from audio-src/v3/timing-{cut}.json;
         the animation is assets/v3.js, timed by assets/timing-{cut}.js (140 BPM grid + measured voiceover).
         Every UI surface is a real EnvKit screenshot; every word on screen is HTML. -->
    <script src="assets/gsap.min.js"></script>
    <link rel="stylesheet" href="assets/promo.css" />
    <link rel="stylesheet" href="assets/v3.css" />
    <style>
      #root {{ width: {W}px; height: {H}px; }}{PORTRAIT_CSS if H > W else LAND_CSS}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="{cid}" data-start="0" data-duration="{L}"{full} data-width="{W}" data-height="{H}">
      <div class="clip layer" id="bg" data-start="0" data-duration="{L}" data-track-index="0"><div class="base"></div><div class="glow" id="glow"></div></div>
{videos(cut, T)}
      <div class="clip layer" id="fx" data-start="0" data-duration="{L}" data-track-index="2"><div id="floor"></div><canvas id="trails" width="{W}" height="{H}"></canvas></div>
      <div class="clip layer" id="world" data-start="0" data-duration="{L}" data-track-index="10"></div>
      <div class="clip layer" id="caps" data-start="0" data-duration="{L}" data-track-index="20"></div>
      <div class="clip layer" id="finish" data-start="0" data-duration="{L}" data-track-index="30"><div id="vignette"></div><div id="grain"></div></div>
    </div>
    <template id="logo-tpl">{LOGO}</template>
    <template id="chat-tpl">{CHAT}</template>
    <script src="assets/promo-lib.js"></script>
    <script src="assets/timing-{cut}.js"></script>
    <script src="assets/v3.js"></script>
  </body>
</html>
"""
    out = ("_hook-" if hook else "") + FILES[cut]
    open(os.path.join(ROOT, out), "w").write(html)
    print("wrote", out, L, "s", f"(splice frame {splice_frame(T)})" if hook else "")

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--hook"]
    for c in (args or ["main", "vertical", "ad15"]): compose(c, hook="--hook" in sys.argv)
