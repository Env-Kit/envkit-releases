# EnvKit logo assets

Vector source of truth for the EnvKit logo. See `../BRANDING.md` for the full brand
guide (palette, voice). The mark is the **"Bracketed K"**: a vertical stem + a
terminal-style angle bracket `>` — the "K" of Kit with a developer/terminal feel.

## Files

| File | Use |
|------|-----|
| `envkit-icon.svg` | Icon mark, mint `#2dd4aa` (dark backgrounds), transparent bg |
| `envkit-icon-light.svg` | Icon mark, mint `#0d9488` (light backgrounds) |
| `envkit-app-icon.svg` | App/tray icon — dark rounded square + mint gradient mark (source for `build/icon.*`) |
| `envkit-app-icon-light.svg` | App icon, light variant (off-white square) |
| `envkit-lockup-dark.svg` | Icon + wordmark, dark bg (`Env` light, `Kit` mint) |
| `envkit-lockup-light.svg` | Icon + wordmark, light bg (`Env` ink, `Kit` mint) |
| `envkit-lockup-mono-dark.svg` | Lockup, single light color (no mint) |
| `envkit-lockup-mono-light.svg` | Lockup, single ink color (no mint) |
| `envkit-wordmark.svg` | Wordmark only, for tight spaces |

## Colors

- Primary (mark/accent): `#0d9488` on light, `#2dd4aa` on dark
- Wordmark text: `#0f1729` on light, `#eaf0f6` on dark
- Mark gradient (icon only): `#2dd4aa → #0d9488`

## Notes

- **Wordmark font:** Inter / Geist / Satoshi, weight 800, tracking ≈ -2%. The lockup/
  wordmark SVGs reference these via `font-family`; **outline the text to paths** before
  shipping final art so it renders identically everywhere.
- **Mark is pure paths** (font-independent) — safe to use anywhere as-is.
- Keep clear space ≥ the height of the "E"; icon-only ≥ 16px, full lockup ≥ 96px wide.

## Regenerating the Windows app icon

`build/icon.png` (256×256) and `build/icon.ico` are generated from the mark geometry
(mirrors `envkit-app-icon.svg`) by a pure-Node, dependency-free script:

```bash
npm run icon
```

Edit the geometry/palette in `scripts/gen-icon.mjs` if the mark changes; keep it in sync
with `envkit-app-icon.svg`.
