# EnvKit promo video (v3)

Source of `art/envkit-demo.mp4` and `art/envkit-demo.webp` in the README, plus the full 16:9 promo,
a 9:16 cut for Reels / Shorts / TikTok and a 15 s 16:9 ad cut. It is a [HyperFrames](https://hyperframes.heygen.com)
project: plain HTML + one GSAP timeline per composition, rendered frame by frame in headless Chrome.

| File | What |
| --- | --- |
| `index.html` | 16:9, 1920x1080 @ 30 fps, 44.1 s (main cut) |
| `vertical.html` | 9:16, 1080x1920 @ 30 fps, 27.2 s |
| `ad15.html` | 16:9 ad cut, 14.8 s |
| `assets/v3.js`, `assets/v3.css` | the scenes, shared by all three cuts |
| `assets/timing-<cut>.js` | generated: beat marks, voiceover word timings, caption cards |
| `assets/promo-lib.js`, `assets/promo.css` | panels, clamped camera, light trails, grain (from v2) |
| `assets/*.png` | real EnvKit screenshots (2880x1800), the only UI shown in the video |
| `assets/ai/` | abstract backdrop clips (not in git, see below) |
| `audio-src/` | ElevenLabs music bed, sound effects and every voiceover take (small mp3s, in git) |
| `tools/` | edit, mix, compose, checks, ElevenLabs and Higgsfield helpers |

The three HTML files are written by `tools/compose_v3.py`; edit `assets/v3.js` / `tools/edit_v3.py`, not the HTML.

## Honest by construction

- Every app surface is a real screenshot. Every word on screen is HTML text (nothing is AI-generated text).
  The AI chat window is drawn in HTML and uses EnvKit's real MCP tool names and arguments
  (`diagnose_service {"name":"redis"}` → `start_service` → `restart_site_queue_worker {"name":"shop"}`).
- The hook is styled as generic error messages (monospaced, red/amber); its background "nods" (port-80 error
  dialogs, database crash lines, a version mismatch) are generic, brand-free HTML, blurred so they read as mood.
  No competitor names or logos anywhere.
- The AI-generated clips are abstract light only (no text, no UI) and sit under the screenshots.

## The edit (140 BPM)

`tools/edit_v3.py` is the edit decision list. It lays every voiceover line out on the 140 BPM grid from its
measured length, re-splices the music on its beats, places the sound effects so their transients land on the
frames the picture uses, side-chains the music under the voice (−8 dB) and writes `assets/timing-<cut>.js`.
The picture reads only those marks, so a different voice re-times everything without touching the HTML.

- Hook (0–4.9 s): "Port 80 in use." / "MySQL crashed." / "Wrong PHP version." slam in as error messages over the
  riser, each struck through in mint (glitch hit) as the next lands. On the third strike (beat 8, 3.43 s) the music
  cuts dead; "Now it fixes itself." plays over near-black and a light-speed tunnel, and the logo slams on "itself"
  with the drop (beat 11.5, 4.93 s; the 15 s cut has no turn line and slams at 4.07 s).
- Then: This is EnvKit → stack chips → the dashboard ("One app.") → onboarding click on the beat → "Your site is
  live" + chime → three camera punches (Real HTTPS / Real domain / Seconds) → sites → services staccato (one hard
  cut + chip per word) → All running → Redis breaks → the AI chat fixes it with the real tool calls → montage
  (Cron / Logs / Git / Databases, one cut per word, punch-in on the off-beat) → wall of screens → everything
  drops out for "And the best part?" → "It's free." on the drop again → end card (envkit.net, Download).
- Captions: every VO word is on screen at its onset. 16:9 uses an elegant lower third (whole line dim,
  spoken word lit in mint); 9:16 uses big centred captions; hook, "What if…", the staccato words and
  "It's free." are the big kinetic type itself.

Music: one ElevenLabs `music_v1` generation (`tools/music_v3.py`, seed 140, composition plan). Measured:
exactly 140.00 BPM, beat k at 0.445 + k·60/140 s; beats 0–14 build/riser, 15 hard drop, 77–78 filter break,
79–94 sub-only, 95 final hit + tail. Loudness: −14 LUFS integrated, true peak ≤ −1.6 dBTP after AAC.

## Voiceover

Voice "Hale" (`dXtC3XhB9GtPusIpNtQx`). `tools/vo_config.json` holds the voice, model and voice settings:
`eleven_v3` (stability 0.5, similarity 0.8, style 0.45, speaker boost) for the script. The hook is spoken at natural
pace (no speed-up anywhere in the hook): each hook line has three `eleven_v3` takes and three
`eleven_multilingual_v2` takes at speed 1.0 (`hook_compare` in the config), and `picks` holds the most natural take
that fits the beat grid. The other lines have 2–3 takes; `edit_v3.py` picks one by objective metrics (no clipping, no
truncated ending, natural pace, pitch range). v3 tends to cut the last phoneme, so its lines get a trailing
`[pause]` tag. Word timings come from ElevenLabs forced alignment (`/v1/forced-alignment`, `*.fa.json`) snapped
to the audible boundaries (speech-island starts and energy dips) of each take.

Change the voice: edit `tools/vo_config.json`, then `tools/build_v3.sh vo` (regenerates every take, aligns,
re-times captions, mix and picture, renders, checks).

## Re-cutting only the hook

The slam (beat 11.5; 9.5 in the 15 s cut) and the music cut (beat 8) are fixed in `tools/edit_v3.py`, and the
tunnel clip always starts at beat 8, so every frame from 0.25 s after the slam onward is identical whatever the
hook says. To change the hook: edit the `H1`–`H4` lines in `tools/vo.py`, `python3 tools/vo.py gen H1 H2 H3 H4`,
`tools/edit_v3.py <cut>` for each cut, `tools/compose_v3.py && tools/compose_v3.py --hook`, render the three
`_hook-*.html` (5 s each, in parallel), `tools/splice_hook_v3.sh`, then `tools/finish_v3.sh` and `tools/webp_v3.sh`.

## Checks (`tools/check_v3.sh` → `renders/v3/checks/`)

- `tools/coverage_debug.sh <file>.html` renders a copy where the page, every panel and every tile background
  are magenta and fails if any magenta pixel shows, checking **every frame** (30 fps). v3: 0 of 1325 / 817 / 444
  frames uncovered. `tools/coverage_check.py <video>` is the luminance heuristic from v2.
- `tools/sync_check.py <cut> <video>`: caption time vs the measured onset of every word that follows a pause
  (median 3–4 ms), vs the forced-alignment start of every word (median 33–40 ms), and the frame where each
  rendered caption word turns mint vs its VO time (all words within 48 ms, i.e. frame rounding).
- ebur128 loudness and true peak of every deliverable.

## Build

```bash
# everything (PYTHON = a python with numpy + Pillow; HyperFrames pinned to 0.8.168)
PYTHON=/path/to/python tools/build_v3.sh        # add "vo" to regenerate the voiceover first
```

Steps it runs: `tools/edit_v3.py main|vertical|ad15` → `tools/compose_v3.py` → `hyperframes render -q high` ×3 →
`tools/finish_v3.sh` (limiter, two-pass loudnorm, mux) → `tools/webp_v3.sh` (README WebP, 1280 wide, 12 fps,
captions burned in) → `tools/check_v3.sh`.

## Regenerating the generated media

- Music and SFX (ElevenLabs): `tools/music_v3.py` (music, composition plan in the file), `tools/eleven_generate_v3.sh`
  (the eight v3 effects) and `tools/eleven_generate.sh` (the v2 effects that are reused). `tools/eleven.py` and
  `tools/vo.py` read the API key at runtime from `~/.claude.json` (`mcpServers.elevenlabs.env.ELEVENLABS_API_KEY`)
  and never print or store it.
- Backdrop clips (Higgsfield, Kling 3.0 pro, 8 s, silent, 14 credits each): `tools/hf_generate.py` (v2: ribbons,
  circuit, monoliths) and `tools/hf_generate_v3.py` (v3: light-speed tunnel `8aa1b924-811b-403c-b5ee-0d4c53e3253e`,
  shockwave `a01f6f8b-be3e-4a08-b885-dcaa2602de76`); `tools/hf_fetch.py` downloads the jobs listed in it. They are
  graded and re-encoded with a keyframe every second (`*-graded.mp4`, 9:16 versions are centre crops) by
  `tools/grade_ai.sh`. The originals (10–36 MB each) live in the maintainer's working copy at
  `marketing/promo-video/assets/ai/` and are not committed.
