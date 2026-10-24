// Hairline figures: isometric line drawings of rounded solids, drawn from the paused timeline.
// Geometry and motion constants are ported from @lucasmarkes/hairline 0.5.1 (MIT); see HAIRLINE-LICENSE.txt.
// The package animates on requestAnimationFrame, which a seeking renderer cannot follow, so every moving value
// here is a plain property that GSAP tweens, and setting it redraws its part at once.
// startFilm({ figures: "hairline" }) calls this with the film's helpers before any scene code runs.
window.FilmFigures = window.FilmFigures || {};
window.FilmFigures.hairline = (film) => {
  const { tl } = film;
  const NS = "http://www.w3.org/2000/svg";
  const W = 400, H = 320;
  const rad = (d) => (d * Math.PI) / 180;
  const r2 = (n) => Math.round(n * 100) / 100;
  const poly = (pts) => "M" + pts.map((p) => r2(p[0]) + " " + r2(p[1])).join("L") + "Z";
  const open = (pts) => (pts.length < 2 ? "" : "M" + pts.map((p) => r2(p[0]) + " " + r2(p[1])).join("L"));
  const mk = (tag, attrs, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs || {}) e.setAttribute(k, String(attrs[k]));
    if (parent) parent.appendChild(e);
    return e;
  };

  // A rounded rectangle sampled four steps per corner, each sample with its outward normal.
  const rrect = (u0, v0, u1, v1, r, n = 4) => {
    r = Math.max(0, Math.min(r, (u1 - u0) / 2, (v1 - v0) / 2));
    const out = [];
    for (const [cu, cv, a0] of [[u1 - r, v1 - r, 0], [u0 + r, v1 - r, 90], [u0 + r, v0 + r, 180], [u1 - r, v0 + r, 270]])
      for (let k = 0; k <= n; k++) {
        const a = rad(a0 + (90 * k) / n), ca = Math.cos(a), sa = Math.sin(a);
        out.push({ u: cu + r * ca, v: cv + r * sa, nu: ca, nv: sa });
      }
    return out;
  };
  const hull = (input) => {
    const pts = input.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const x = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const lo = [], up = [];
    for (const p of pts) { while (lo.length > 1 && x(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); }
    for (let i = pts.length - 1; i >= 0; i--) { const p = pts[i]; while (up.length > 1 && x(up[up.length - 2], up[up.length - 1], p) <= 0) up.pop(); up.push(p); }
    lo.pop(); up.pop();
    return lo.concat(up);
  };
  // The one cyclic run of samples that face the camera, in ring order.
  const run = (ring, keep) => {
    const n = ring.length;
    let s = -1;
    for (let i = 0; i < n; i++) if (keep(ring[i]) && !keep(ring[(i + n - 1) % n])) { s = i; break; }
    if (s < 0) return keep(ring[0]) ? ring.slice() : [];
    const out = [];
    for (let k = 0; k < n && keep(ring[(s + k) % n]); k++) out.push(ring[(s + k) % n]);
    return out;
  };

  // Hairline's two clocks: a 700 ms lift for a discrete change, and its k 100 · c 18 · m 1 spring for a follow.
  const bezier = (x1, y1, x2, y2) => {
    const at = (a, b, t) => 3 * a * (1 - t) ** 2 * t + 3 * b * (1 - t) * t ** 2 + t ** 3;
    return (p) => {
      let lo = 0, hi = 1, t = p;
      for (let i = 0; i < 30; i++) { t = (lo + hi) / 2; if (at(x1, x2, t) < p) lo = t; else hi = t; }
      return at(y1, y2, t);
    };
  };
  const zeta = 18 / (2 * Math.sqrt(100)), w0 = Math.sqrt(100), wd = w0 * Math.sqrt(1 - zeta * zeta);
  const step = (t) => 1 - Math.exp(-zeta * w0 * t) * (Math.cos(wd * t) + (zeta / Math.sqrt(1 - zeta * zeta)) * Math.sin(wd * t));
  const SPRING_T = 0.6;
  const ease = { lift: bezier(0.32, 0.72, 0, 1), spring: (p) => (p >= 1 ? 1 : step(p * SPRING_T) / step(SPRING_T)) };
  const dur = { lift: 0.7, spring: SPRING_T };

  // A figure is a 400 × 320 drawing in a 2:1 orthographic view, scaled to the width of its element.
  const figure = (target, { S = 1.6, az = 45, k = 0.5 } = {}) => {
    const host = typeof target === "string" ? document.querySelector(target) : target;
    if (!host) throw new Error(`hairline figure: no element matches ${target}`);
    host.classList.add("hl-figure");
    const svg = mk("svg", { viewBox: `0 0 ${W} ${H}`, "aria-hidden": "true" }, host);
    const ground = mk("g", {}, svg), links = mk("g", {}, svg), solids = mk("g", {}, svg);
    const C = { az: rad(az), k, S, ox: 0, oy: 0 };
    const c = Math.cos(C.az), s = Math.sin(C.az), zf = Math.sqrt(1 - k * k);
    const P = (x, y, z) => [C.ox + C.S * (x * c - y * s), C.oy + C.S * ((x * s + y * c) * C.k - z * zf)];
    const front = (q) => q.nu * s + q.nv * c >= -1e-6;
    const depth = (x, y) => r2(x * s + y * c);
    const parts = [];

    // Plates are filled with the ground colour and painted back to front, so a nearer part covers a farther one.
    // Parts on the same centre paint bottom up, so a stack draws right whatever order it was built in.
    const sort = () => {
      const order = parts.filter((p) => !p.ground).sort((a, b) => a.depth - b.depth || a.z() - b.z());
      if (order.some((p, i) => solids.children[i] !== p.g)) order.forEach((p) => solids.appendChild(p.g));
    };

    // A rounded solid with its foot at (x, y, z). A `ground` part, such as a plinth, stays under every link and part.
    const box = ({ x, y, w, d, h, z = 0, r = 2.6, bevel = 0.9, ground: low = false }) => {
      const state = { x, y, z, h, hi: 0, opacity: 1 };
      const g = mk("g", {}, low ? ground : solids);
      const sil = mk("path", { class: "sil" }, g), crease = mk("path", { class: "crease" }, g);
      const dots = [];
      const part = { g, ground: low, depth: depth(x + w / 2, y + d / 2), links: [] };
      const outline = () => {
        const ring = rrect(state.x, state.y, state.x + w, state.y + d, r), top = state.z + Math.max(0.6, state.h);
        return hull(ring.map((q) => P(q.u, q.v, top)).concat(ring.map((q) => P(q.u, q.v, state.z))));
      };
      const draw = () => {
        const inner = rrect(state.x + bevel, state.y + bevel, state.x + w - bevel, state.y + d - bevel, r > 0 ? Math.max(0.3, r - bevel) : 0);
        const top = state.z + Math.max(0.6, state.h);
        sil.setAttribute("d", poly(outline()));
        crease.setAttribute("d", open(run(inner, front).map((q) => P(q.u, q.v, top))));
        sil.classList.toggle("hi", state.hi >= 0.5);
        g.setAttribute("opacity", r2(state.opacity));
        for (const dot of dots) dot.draw();
        for (const link of part.links) link.draw();
      };
      part.draw = draw;
      part.outline = outline;
      part.center = () => [state.x + w / 2, state.y + d / 2, state.z];
      part.lid = () => state.z + Math.max(0.6, state.h);
      part.z = () => state.z;
      // The handle's x, y, z, h, hi and opacity are GSAP-tweenable; every set redraws this part.
      const handle = { part };
      for (const key of Object.keys(state)) {
        Object.defineProperty(handle, key, {
          enumerable: true,
          get: () => state[key],
          set: (v) => {
            state[key] = v;
            draw();
            if (key === "x" || key === "y") part.depth = depth(state.x + w / 2, state.y + d / 2);
            if (key === "x" || key === "y" || key === "z") sort();
          },
        });
      }
      // A flat dot riding the lid at (u, v) from the centre: Hairline's way to number a part without a word.
      handle.dot = (u = 0, v = 0, { r: dr = 1.2 } = {}) => {
        const el = mk("ellipse", { class: "dot" }, g);
        const dot = {};
        let on = 0;
        Object.defineProperty(dot, "on", { enumerable: true, get: () => on, set: (val) => { on = val; draw1(); } });
        const draw1 = () => {
          const [cx, cy] = part.center(), q = P(cx + u, cy + v, part.lid());
          el.setAttribute("cx", r2(q[0])); el.setAttribute("cy", r2(q[1]));
          el.setAttribute("rx", r2(dr * C.S)); el.setAttribute("ry", r2(dr * C.S * C.k));
          el.classList.toggle("on", on >= 0.5);
        };
        dots.push({ draw: draw1 });
        draw1();
        return dot;
      };
      parts.push(part);
      draw();
      sort();
      return handle;
    };

    // A link on the ground between two parts' centres, dashed until it is lit.
    const link = (a, b, { dash = true } = {}) => {
      const el = mk("path", { class: dash ? "link dash" : "link" }, links);
      const lk = {};
      let hi = 0;
      Object.defineProperty(lk, "hi", { enumerable: true, get: () => hi, set: (v) => { hi = v; draw(); } });
      const draw = () => {
        const [ax, ay] = a.part.center(), [bx, by] = b.part.center();
        el.setAttribute("d", open([P(ax, ay, 0), P(bx, by, 0)]));
        el.classList.toggle("hi", hi >= 0.5);
        el.classList.toggle("dash", dash && hi < 0.5);
      };
      a.part.links.push(lk); b.part.links.push(lk);
      lk.draw = draw;
      draw();
      return lk;
    };

    // Centres the parts' rest bounds, plus any world points of the most extreme pose, on (cx, cy); call it once after the parts.
    // It moves the drawing but never scales it, so it fails when the extent cannot fit the viewBox.
    const fit = (cx = 200, cy = 166, points = []) => {
      C.ox = 0; C.oy = 0;
      let a = Infinity, b = -Infinity, t = Infinity, u = -Infinity;
      const screen = parts.flatMap((p) => p.outline()).concat(points.map(([x, y, z]) => P(x, y, z)));
      for (const [px, py] of screen) {
        a = Math.min(a, px); b = Math.max(b, px); t = Math.min(t, py); u = Math.max(u, py);
      }
      if (a === Infinity) throw new Error("hairline fit: add parts to the figure before calling fit()");
      if (b - a > W || u - t > H) {
        throw new Error(`hairline fit: the figure spans ${Math.round(b - a)} × ${Math.round(u - t)} of a ${W} × ${H} viewBox; lower S or the motion`);
      }
      C.ox = cx - (a + b) / 2; C.oy = cy - (t + u) / 2;
      parts.forEach((p) => p.draw());
    };

    return { svg, box, link, fit };
  };

  // Stagger by distance: each part starts |i − from| × step after `at`, so the motion spreads out from one part.
  // `vars` are the GSAP values to tween to; a function value gets (index, handle) when the scene is built, not at play.
  const ripple = (handles, at, { from = 0, step = 0.045, clock = "lift", ...vars } = {}) => {
    if (!handles.length) throw new Error("hairline ripple: pass at least one box");
    if (!ease[clock]) throw new Error(`hairline ripple: clock must be "lift" or "spring", not "${clock}"`);
    handles.forEach((h, i) => {
      const values = Object.fromEntries(Object.entries(vars).map(([key, v]) => [key, typeof v === "function" ? v(i, h) : v]));
      tl.to(h, { ...values, duration: dur[clock], ease: ease[clock] }, at + Math.abs(i - from) * step);
    });
    return at + dur[clock] + Math.max(...handles.map((_, i) => Math.abs(i - from))) * step;
  };

  // The stroke is the only highlight: light a part or a link with a hard switch on the timeline.
  const light = (target, at, on = true) => tl.set(target, { hi: on ? 1 : 0 }, at);

  film.hairline = { figure, ripple, light, ease, dur };
};
