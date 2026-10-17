# EnvKit promo video

Source of `art/envkit-demo.mp4` and `art/envkit-demo.webp`: a [HyperFrames](https://hyperframes.heygen.com)
composition (HTML + a GSAP timeline) built on real EnvKit screenshots from `assets/`.

```bash
npx hyperframes@0.8.168 preview                       # live preview
npx hyperframes@0.8.168 render -f 30 -q high -o renders/master.mp4
```

The README files are re-encoded from the master render:

```bash
# MP4 for README / YouTube / X (H.264, ~7 MB)
ffmpeg -i renders/master.mp4 -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p -movflags +faststart -an envkit-demo.mp4
# Animated WebP for the README (1280 px, 15 fps): extract frames, then encode with Pillow
ffmpeg -i renders/master.mp4 -vf "fps=15,scale=1280:-1:flags=lanczos" frames/f%04d.png
python3 -c "from PIL import Image; import glob; f=[Image.open(p).convert('RGB') for p in sorted(glob.glob('frames/f*.png'))]; f[0].save('envkit-demo.webp', save_all=True, append_images=f[1:], duration=67, loop=0, quality=72, method=4, kmin=4, kmax=8)"
```
