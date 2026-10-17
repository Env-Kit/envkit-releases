/* EnvKit promo helpers shared by index.html (16:9) and vertical.html (9:16).
 * Everything is a pure function of the timeline position, so any frame can be seeked
 * and rendered in any order (no Date.now, no Math.random, no rAF loops).
 *
 * Screenshots are 2880x1800 PNGs shown in a 1440x900 "logical" space (.cnt).
 * A panel shows a crop of that space; camTo() moves the crop and CLAMPS it to the
 * screenshot bounds, so a zoomed screenshot always covers its panel (the v1 bug was a
 * camera that zoomed past the edge of the window and left half the frame empty). */
(function () {
  const LW = 1440, LH = 900;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  function create({ width, height, duration }) {
    const tl = gsap.timeline({ paused: true });
    const BEAT = 60 / 128, B0 = 0.088;
    const b = (n) => +(B0 + n * BEAT).toFixed(4);

    // Camera inside a panel: crop centred on (cx, cy) with width cw, clamped so the
    // screenshot always covers the whole panel.
    function camVals(P, cx, cy, cw) {
      const sMin = Math.max(P.w / LW, P.h / LH);
      const s = Math.max(P.w / cw, sMin);
      const vw = P.w / s, vh = P.h / s;
      const x0 = clamp(cx - vw / 2, 0, LW - vw);
      const y0 = clamp(cy - vh / 2, 0, LH - vh);
      return { x: -x0 * s, y: -y0 * s, scale: s };
    }

    function panel(sel, { crop, w, left, top, view }) {
      const el = document.querySelector(sel);
      const h = (w * crop[3]) / crop[2];
      el.style.width = w + 'px';
      el.style.height = h + 'px';
      el.style.left = left + 'px';
      el.style.top = top + 'px';
      const P = { el, cnt: el.querySelector('.cnt'), w, h };
      const v = view || [crop[0] + crop[2] / 2, crop[1] + crop[3] / 2, crop[2]];
      gsap.set(P.cnt, { transformOrigin: '0 0', ...camVals(P, v[0], v[1], v[2]) });
      return P;
    }

    function camTo(P, { at, dur, ease, cx, cy, cw }) {
      tl.to(P.cnt, { ...camVals(P, cx, cy, cw), duration: dur, ease }, at);
    }

    function enter(sel, at, { from, to, dur = 0.9 }) {
      tl.fromTo(sel, { ...from, opacity: 0, filter: 'blur(18px)' }, { ...to, opacity: 1, filter: 'blur(0px)', duration: dur, ease: 'expo.out' }, at);
    }

    function ring(sel, r, at) {
      gsap.set(sel, { left: r[0] - 4, top: r[1] - 4, width: r[2] + 8, height: r[3] + 8 });
      tl.fromTo(sel, { opacity: 0, scale: 1.08 }, { opacity: 1, scale: 1, duration: 0.5, ease: 'expo.out' }, at);
    }

    function sweep(sel, at, dur) {
      tl.fromTo(sel, { xPercent: -130, opacity: 1 }, { xPercent: 330, duration: dur, ease: 'power2.inOut' }, at);
    }

    // Split headline/paragraph text into word spans and reveal them with a blur-up.
    function kin(sel, at) {
      const root = document.querySelector(sel);
      root.querySelectorAll('.kin').forEach((node, row) => {
        const ws = node.textContent.trim().split(/\s+/);
        node.textContent = '';
        ws.forEach((w, i) => {
          const s = document.createElement('span');
          s.className = 'w';
          s.textContent = w;
          node.appendChild(s);
          if (i < ws.length - 1) node.appendChild(document.createTextNode(' '));
        });
        const spans = node.querySelectorAll('.w');
        const big = node.tagName === 'H2';
        tl.fromTo(spans, { y: big ? 60 : 24, opacity: 0, filter: `blur(${big ? 14 : 8}px)` },
          { y: 0, opacity: 1, filter: 'blur(0px)', duration: 0.7, ease: 'expo.out', stagger: big ? 0.07 : 0.025 }, at + row * 0.32);
      });
      tl.set(root, { opacity: 1 }, at);
    }

    // Word-by-word "typing" for chat text (one typing tick per word in the mix).
    function words(sel, at, step) {
      gsap.utils.toArray(`${sel} .w`).forEach((w, i) => {
        tl.fromTo(w, { opacity: 0 }, { opacity: 1, duration: 0.08, ease: 'none' }, at + i * step);
      });
    }

    // Character typing: chars are display:none until typed so the caret follows.
    function typeInto(sel, text, at, step) {
      const host = document.querySelector(sel);
      [...text].forEach((ch, i) => {
        const s = document.createElement('span');
        s.textContent = ch;
        s.style.display = 'none';
        host.appendChild(s);
        tl.set(s, { display: 'inline' }, at + i * step);
      });
    }

    // ── Procedural layers, driven through a modifier so they render on every seek ──
    const drawers = [];
    const clock = { t: 0 };
    tl.to(clock, {
      t: duration, duration, ease: 'none',
      modifiers: { t: (v) => { const t = +v; drawers.forEach((d) => d(t)); return v; } },
    }, 0);

    function rng(seed) {
      let s = seed >>> 0;
      return () => ((s = (Math.imul(s, 1664525) + 1013904223) >>> 0) / 4294967296);
    }

    // Mint light trails: thin ribbons of light drifting across the frame.
    function trails(sel, { count = 16, seed = 7 } = {}) {
      const cv = document.querySelector(sel);
      const ctx = cv.getContext('2d');
      const W = cv.width, H = cv.height;
      const R = rng(seed);
      const T = Array.from({ length: count }, () => ({
        y0: H * (0.12 + R() * 0.8), a1: 30 + R() * 110, f1: 0.4 + R() * 0.9, p1: R() * 6.283,
        a2: 6 + R() * 26, f2: 1.6 + R() * 2.4, p2: R() * 6.283, sp: 0.045 + R() * 0.07,
        off: R() * 1.6, len: 0.22 + R() * 0.32, w: 0.6 + R() * 1.7, al: 0.22 + R() * 0.5,
        teal: R() < 0.4, tilt: (R() - 0.5) * H * 0.35,
      }));
      const pt = (tr, u, t) => [
        -0.08 * W + u * 1.16 * W,
        tr.y0 + tr.tilt * (u - 0.5) + tr.a1 * Math.sin(6.283 * tr.f1 * u + tr.p1 + t * 0.35) + tr.a2 * Math.sin(6.283 * tr.f2 * u + tr.p2 + t * 0.8),
      ];
      drawers.push((t) => {
        ctx.clearRect(0, 0, W, H);
        ctx.globalCompositeOperation = 'lighter';
        ctx.lineCap = 'round';
        for (const tr of T) {
          const head = ((t * tr.sp + tr.off) % 1.6) - 0.25;
          const tail = head - tr.len;
          const N = 42;
          const rgb = tr.teal ? '13,148,136' : '45,212,170';
          let prev = pt(tr, tail, t);
          for (let i = 1; i <= N; i++) {
            const u = tail + (tr.len * i) / N;
            const p = pt(tr, u, t);
            const k = (i / N) ** 2;
            ctx.strokeStyle = `rgba(${rgb},${(tr.al * k * 0.09).toFixed(4)})`;
            ctx.lineWidth = tr.w * 9;
            ctx.beginPath(); ctx.moveTo(prev[0], prev[1]); ctx.lineTo(p[0], p[1]); ctx.stroke();
            ctx.strokeStyle = `rgba(${rgb},${(tr.al * k).toFixed(4)})`;
            ctx.lineWidth = tr.w;
            ctx.beginPath(); ctx.moveTo(prev[0], prev[1]); ctx.lineTo(p[0], p[1]); ctx.stroke();
            prev = p;
          }
        }
        ctx.globalCompositeOperation = 'source-over';
      });
    }

    function grain(sel) {
      const el = document.querySelector(sel);
      drawers.push((t) => {
        const f = Math.floor(t * 30);
        el.style.backgroundPosition = `${(f * 73) % 256}px ${(f * 151) % 256}px`;
      });
    }

    function floor(sel) {
      const el = document.querySelector(sel);
      drawers.push((t) => { el.style.backgroundPosition = `0px ${(t * 46).toFixed(2)}px`; });
    }

    drawers.forEach((d) => d(0));
    const api = { b, tl, panel, cam: camVals, camTo, ring, kin, words, typeInto, enter, sweep, trails, grain, floor };
    const _trails = trails, _grain = grain, _floor = floor;
    api.trails = (s, o) => { _trails(s, o); drawers[drawers.length - 1](0); };
    api.grain = (s) => { _grain(s); drawers[drawers.length - 1](0); };
    api.floor = (s) => { _floor(s); drawers[drawers.length - 1](0); };
    return api;
  }

  window.PromoLib = { create };
})();
