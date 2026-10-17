"""Soundtrack edit + SFX cues for vertical.html (9:16, 29.25 s).

The vertical cut reuses the 16:9 track, re-edited on bar lines (every cut joins two
sections with the same texture): beats are numbered on the vertical timeline (v),
and `b` converts a beat number to seconds on the shared 128 BPM grid."""

LENGTH = 29.25

def segments_vertical(b):
    # (source start, source end, destination start) in seconds
    return [
        (0.0, b(8), 0.0),        # intro: logo hit + tagline
        (b(24), b(40), b(8)),    # riser, the break, the drop (onboarding -> URL -> live)
        (b(40), b(52), b(24)),   # groove: sites, services, databases
        (b(68), b(80), b(36)),   # groove: AI over MCP
        (b(88), 48.0, b(48)),    # end section + final hit + tail
    ]

def cues_vertical(b):
    c = [("impact", b(2), -2), ("shimmer", b(2) + 0.12, -13)]
    c += [("whoosh2", b(8), -8), ("click", b(10), -2)]
    c += [("whoosh1", b(12), -9)]
    c += [("tick", b(12.6) + i * 0.1, -9, 0.95 + 0.025 * (i % 5)) for i in range(10)]
    c += [("chime", b(16), -5), ("shimmer", b(16) + 0.1, -14), ("blip", b(17), -17)]
    for n in (24, 28, 32, 36):
        c += [("whoosh2", b(n), -10)]
    for n in (25.5, 29.5, 33.5):
        c += [("blip", b(n), -18)]
    c += [("tick", b(37.5) + i * 0.08, -16, 0.95 + 0.025 * (i % 5)) for i in range(12)]
    for start, done in ((39.5, 40.5), (41, 42), (42.5, 43.5)):
        c += [("click", b(start), -8), ("blip", b(done), -11)]
    c += [("whoosh2", b(48), -9), ("impact", b(48), -9), ("shimmer", b(56), -12)]
    return c
