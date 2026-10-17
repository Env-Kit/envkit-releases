# EnvKit promo video (v2)

Source of `art/envkit-demo.mp4` and `art/envkit-demo.webp` in the README, plus the full-length
16:9 promo and a 9:16 cut for Reels / Shorts / TikTok. It is a [HyperFrames](https://hyperframes.heygen.com)
project: plain HTML + one GSAP timeline per composition, rendered frame by frame in headless Chrome.

| File | What |
| --- | --- |
| `index.html` | 16:9, 1920x1080 @ 30 fps, 48 s |
| `vertical.html` | 9:16, 1080x1920 @ 30 fps, 29.25 s |
| `assets/promo.css`, `assets/promo-lib.js` | shared look and helpers (panels, clamped camera, kinetic type, light trails, grain) |
| `assets/*.png` | real EnvKit screenshots (2880x1800), the only UI shown in the video |
| `assets/ai/` | abstract backdrop clips (not in git, see below) |
| `audio-src/` | ElevenLabs music bed + sound effects (small mp3s, in git) |
| `tools/` | mix, loudness, coverage checks, ElevenLabs and Higgsfield helpers |

## Honest by construction

- Every app surface is a real screenshot. Every word on screen is HTML text. The AI chat window is
  drawn in HTML and uses EnvKit's real MCP tool names and arguments (`diagnose_service`,
  `start_service`, `restart_site_queue_worker`).
- The AI-generated clips are abstract light only (no text, no UI) and sit under the screenshots.

## The edit is cut to the music

The track is 128 BPM; beat `n` lands at `0.088 + n * 0.46875` s (`b(n)` in `assets/promo-lib.js`
and `tools/mix.py`). Scene changes sit on bar lines, the 2-bar break in the track is where the URL
types itself, and the drop is "Your site is live". `tools/mix.py` places each sound effect so its
measured transient lands on the same beat the picture uses.

## No uncovered frames (the v1 bug)

v1 zoomed the app window with a free camera, so on some zooms the window slid off and half the
frame showed the empty page. In v2:

- a full-frame backdrop (graded footage, light trails, floor grid, glow) is always under everything;
- screenshots live in panels, and `camTo()` clamps the crop to the screenshot bounds, so a zoomed
  screenshot always covers its panel.

`tools/coverage_debug.sh index.html` (or `vertical.html`) renders a copy where the page and every
panel background are magenta and fails if any magenta pixel shows (sampled every 0.25 s).
`tools/coverage_check.py <video>` measures luminance per half and quadrant every 0.25 s and lists
large flat dark regions. As a control, the magenta test flags 128 of 148 frames of v1.

## Build

```bash
# 1. picture (HyperFrames pinned to 0.8.168)
npx --yes hyperframes@0.8.168 render -q high -o renders/envkit-promo-master-video.mp4
npx --yes hyperframes@0.8.168 render -c vertical.html -q high -o renders/envkit-promo-9x16-video.mp4
# 2. sound + mux: mix -> limiter -> two-pass loudnorm (-16 LUFS, -1.5 dBTP) -> ProRes master + H.264/AAC
PYTHON=/path/to/python-with-numpy tools/finish.sh
# 3. README WebP (silent, 1280 wide, 15 fps)
PYTHON=/path/to/python-with-numpy-and-pillow tools/webp.sh
```

## Regenerating the generated media

- Music and SFX (ElevenLabs): `tools/eleven_generate.sh` has the exact prompts for the one 50 s
  music generation (`music-a.mp3`) and the eight effects. `tools/eleven.py` reads the API key at
  runtime from `~/.claude.json` (`mcpServers.elevenlabs.env.ELEVENLABS_API_KEY`) and never prints or
  stores it.
- Backdrop clips (Higgsfield, Kling 3.0 pro, 8 s, silent, ~14 credits each): `tools/hf_generate.py`
  holds the prompts; `tools/hf_fetch.py` downloads finished jobs. The clips used here are jobs
  `a5358fbd-a7cb-4245-854f-56ed492c3958` (ribbons 16:9), `7d8a2be8-9b1e-4b28-bc51-d26458ef50c0`
  (circuit 16:9), `a421ebb1-152b-4bcc-94f9-8df2c6157a27` (monoliths 16:9) and
  `965c59e0-294a-488d-8836-d09ae7d81fb0` (ribbons 9:16). They are graded and re-encoded with a
  keyframe every second (`*-graded.mp4`) before use; the commands are in `tools/grade_ai.sh`.
  The originals (10–15 MB each) live in the maintainer's working copy at
  `marketing/promo-video/assets/ai/` and are not committed.
