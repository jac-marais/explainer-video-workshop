// The stage: a seekable motion engine for scenes drawn as SVG, with a camera, cuts, motion helpers, a character
// rig and a few props. startFilm({ motion: "stage" }) calls this and puts the helpers on film.stage.
// Every moving value is a segment on a channel, rendered from one clock tween, so any seek gives the same frame.
window.FilmMotion = window.FilmMotion || {};
window.FilmMotion.stage = (startedFilm) => {
  const S = (() => {
    // Filled by init() from the captions, in film order, so a film can have any number of scenes.
    const SCENES = [];
    const FLOOR = 22;
    const SFX_NAMES = new Set(["key", "thump", "thud", "slam", "pop", "whoosh", "swish", "ding", "click", "tick", "spring", "note", "riser"]);
    // Hue names map to stage.css classes, which read the brand tokens.
    const HUES = ["emph", "text", "dim", "good", "bad", "wait"];
    window.SFX = window.SFX || [];
    let film = null;

    const node = (target) => {
      if (typeof target !== "string") return target;
      const found = document.getElementById(target);
      if (!found) throw new Error(`stage: no element #${target}`);
      return found;
    };
    const num = (v) => +(+v).toFixed(2);
    const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    const floor = (size) => {
      if (size < FLOOR) throw new Error(`stage: text size ${size} px is under the ${FLOOR} px floor`);
      return size;
    };
    const hue = (h) => {
      if (!HUES.includes(h)) throw new Error(`stage: hue "${h}" must be one of ${HUES.join(", ")}`);
      return h;
    };
    const hidden = (yes) => (yes ? ' class="beat"' : "");
    // The stage's one outline, as attributes that sit beside a fill class; its colour is --stage-ink.
    const INK = (w = 4) => `style="stroke: var(--stage-ink, var(--line))" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"`;
    // A hue stroke (stage.css .h-<hue>); fill stays separate.
    const HUE = (h = "emph", w = 3) => `class="h-${hue(h)}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"`;
    const posStr = (v) => `translate(${num(v.x)} ${num(v.y)})${v.k !== 1 ? ` scale(${+(+v.k).toFixed(4)})` : ""}${v.r ? ` rotate(${num(v.r)})` : ""}`;
    // A placed thing: `<id>-at` holds the position (x, y, scale k, rotation r), `<id>` the body (see README, Ids).
    const placed = (id, x, y, body, { hide = false, cls = "", k = 1, r = 0 } = {}) =>
      `<g id="${id}-at" transform="${posStr({ x, y, k, r })}"><g id="${id}"${hide || cls ? ` class="${[hide ? "beat" : "", cls].join(" ").trim()}"` : ""}>${body}</g></g>`;
    // Each prop's centre in its own drawing, so S.hold can put that point in a hand.
    const CENTRES = new Map();

    const S = {
      W: 1920, H: 1080, SCENES, FLOOR, HUES,
      // No foreground below S.LIMIT on screen, the top of the caption zone less one unit; S.GROUND is the floor line.
      LIMIT: 840, GROUND: 660,

      init(f) {
        film = f;
        S.film = f;
        S.LIMIT = 1080 - f.px("--caption-bottom") - f.px("--caption-h") - f.px("--u");
        SCENES.splice(0, SCENES.length, ...new Set((f.FILM.captions || []).map((c) => c.scene_id)));
        const clock = { t: 0 }, length = f.FILM.duration;
        f.tl.fromTo(clock, { t: 0 }, { t: length, duration: length, ease: "none", immediateRender: false, onUpdate: () => S.render(clock.t) }, 0);
      // Pivots are measured on the whole drawing, so typed or swapped text shows its authored string meanwhile.
      document.fonts.ready.then(() => { atRest(); for (const measure of pivots) measure(); S.render(S.time || 0); });
        return S;
      },
      // Sorts the sound events and draws frame 0; the page calls it once, after every scene.
      finish() {
        for (const fn of S.core.finishers) fn();
        window.SFX.sort((a, b) => a.t - b.t || a.name.localeCompare(b.name));
        S.render(0);
      },
      cues: (scene) => (words) => film.cue(`${scene}|${words}`),
      onset: (sentence) => film.onset(sentence),
      sceneEnd: (scene) => film.sceneEnd(scene),

      // ------------------------------------------------------------------ drawing
      svg(scene) {
        const found = document.querySelector(`#${scene} > svg.plate`);
        if (!found) throw new Error(`stage: scene ${scene} has no svg.plate`);
        return found;
      },
      // Appends markup to a layer of the plate (back, content, top inside the camera; sky and screen fixed), or into
      // the element with id `layer` when no such layer exists; returns the last new node.
      mount(svg, markup, layer = "content") {
        const host = svg.querySelector(`g[data-layer="${layer}"]`) || node(layer);
        host.insertAdjacentHTML("beforeend", markup);
        return host.lastElementChild;
      },
      // The plate: a fixed sky in --bg, then the camera with back/content/top layers, then a fixed screen layer.
      // `floor` draws a floor line at `ground` in the back layer. Ids: <p>-land (landing lens), <p>-shake, <p>-cam
      // (camera), <p>-floor.
      plate(svg, { id = svg.parentElement.id, floor: withFloor = true, ground = S.GROUND } = {}) {
        svg.innerHTML = `<g data-layer="sky"><rect width="1920" height="1080" class="f-bg"/></g>
          <g id="${id}-land"><g id="${id}-shake"><g id="${id}-cam"><g data-layer="back">${withFloor ? S.floor(`${id}-floor`, { y: ground }) : ""}</g>
          <g data-layer="content"></g><g data-layer="top"></g></g></g></g><g data-layer="screen"></g>`;
        return svg;
      },
      // The floor: one line at y, wider than the plate so a camera move never finds its end.
      floor(id, { y = S.GROUND, hide = false } = {}) {
        return `<g id="${id}"${hidden(hide)}><line x1="-2000" y1="${y}" x2="3920" y2="${y}" ${INK(3)}/></g>`;
      },

      // Text: `font` sans, mono or display, from the brand's font tokens; `fill` is "bg" or a hue. Every size is
      // checked against the 22 px floor, and text is escaped.
      text(x, y, s, { size = 28, font = "sans", weight = 400, anchor = "start", fill = "text", id = null, cls = "", spacing = 0, hide = false } = {}) {
        floor(size);
        const fam = { sans: "var(--font-sans)", mono: "var(--font-mono)", display: "var(--font-display, var(--font-sans))" }[font];
        if (!fam) throw new Error(`S.text: font ${font} must be sans, mono or display`);
        if (fill !== "bg") hue(fill);
        const classes = [`t-${fill}`, hide ? "beat" : "", cls].filter(Boolean).join(" ");
        return `<text${id ? ` id="${id}"` : ""} x="${num(x)}" y="${num(y)}" class="${classes}" style="font-family:${fam};font-size:${size}px;font-weight:${weight}${spacing ? `;letter-spacing:${spacing}px` : ""}" text-anchor="${anchor}">${esc(s)}</text>`;
      },
      mono: (x, y, s, o = {}) => S.text(x, y, s, { font: "mono", size: 24, ...o }),
      caps: (x, y, s, o = {}) => S.text(x, y, String(s).toUpperCase(), { font: "mono", size: 22, weight: 500, spacing: 2, fill: "dim", ...o }),
      display: (x, y, s, o = {}) => S.text(x, y, s, { font: "display", size: 84, ...o }),
      // Estimated advance widths, for laying out cards before they are on the page.
      monoWidth: (s, size = 24) => String(s).length * size * 0.6,
      sansWidth: (s, size = 28) => String(s).length * size * 0.54,
      setLit: (id, on = true) => node(id).classList.toggle("lit", on),

      // ------------------------------------------------------------------ timeline
      // Every helper adds a segment to a channel (one property of one element). One clock tween calls render(time),
      // which computes each channel from its own segments, so a seek in any order draws the same frame.
      render(time) {
        S.time = time;
        for (const [el, map] of channels) for (const c of map.values()) c.apply(el, valueAt(c, time));
      },
      sfx(name, at, gain = 0.5, pitch = 0) {
        if (!SFX_NAMES.has(name)) throw new Error(`S.sfx: "${name}" is not one of ${[...SFX_NAMES].join(", ")}`);
        if (!(at >= 0)) throw new Error(`S.sfx: bad time ${at} for ${name}`);
        window.SFX.push({ name, t: num(at), gain: num(gain), pitch });
      },
      // Opacity: hard on and off by default, or a fade; a node with class "beat" starts at 0.
      show(target, at, { dur = 0, sfx = null } = {}) {
        segment(opacity(node(target)), at, dur, (p, prev) => prev + (1 - prev) * p);
        if (sfx) S.sfx(sfx, at, 0.35);
        return at + dur;
      },
      hide(target, at, { dur = 0 } = {}) {
        segment(opacity(node(target)), at, dur, (p, prev) => prev * (1 - p));
        return at + dur;
      },
      fade(target, at, to, dur = 0.25) {
        segment(opacity(node(target)), at, dur, (p, prev) => prev + (to - prev) * p, "power1.inOut");
        return at + dur;
      },
      // Adds (or removes) the class .lit at `at`; a tick sounds when it lights unless sfx is null.
      light(id, at, on = true, { sfx = on ? "tick" : null, gain = 0.3, pitch = 0 } = {}) {
        S.cls(id, at, "lit", on);
        if (sfx) S.sfx(sfx, at, gain, pitch);
        return at;
      },
      // Any class on or off at `at` (states such as "bad", "pass", "fail", "on").
      cls(id, at, name, on = true) {
        const el = node(id);
        segment(channel(el, `cls:${name}`, (e, v) => e.classList.toggle(name, v), () => el.classList.contains(name)), at, 0, () => on);
        return at;
      },
      // Lights ids in order, evenly from t0 to t1, with a tick on every `every`th one.
      lightRun(ids, t0, t1, { every = 3, on = true } = {}) {
        ids.forEach((id, i) => {
          const at = ids.length > 1 ? t0 + ((t1 - t0) * i) / (ids.length - 1) : t0;
          S.light(id, at, on, { sfx: on && every && i % every === 0 ? "tick" : null, gain: 0.2, pitch: i % 5 });
        });
        return t1;
      },
      // Swaps a <text> node's string at `at` (a counter, a status label).
      setText(target, at, value) {
        const el = node(target);
        segment(channel(el, "text", (e, v) => { if (e.textContent !== v) e.textContent = v; }, () => el.textContent), at, 0, () => String(value));
        return at;
      },
      // Where a placed thing's `<id>-at` is at `time`, from the segments added so far: {x, y, k, r}.
      at: (id, time) => ({ ...valueAt(position(node(`${id}-at`)), time) }),
      // Moves `<id>-at` along points between t0 and t1 at constant speed; `k` and `r` tween the scale and rotation
      // to new values, and `arc` lifts the middle of the trip that many px (a hop or a toss).
      ride(id, points, t0, t1, { ease = "power2.inOut", sfx = "swish", k = null, r = null, arc = 0 } = {}) {
        const el = node(`${id}-at`);
        const start = valueAt(position(el), t0);
        const pts = points.length === 1 ? [[start.x, start.y], points[0]] : points;
        if (pts.every(([x, y]) => x === pts[0][0] && y === pts[0][1])) throw new Error(`S.ride ${id}: the road has no length; use S.place`);
        segment(position(el), t0, t1 - t0, (p, prev) => {
          const [x, y] = along(pts, p);
          return { x, y: y - arc * 4 * p * (1 - p), k: k == null ? prev.k : start.k + (k - start.k) * p, r: r == null ? prev.r : start.r + (r - start.r) * p };
        }, ease);
        if (sfx) S.sfx(sfx, t0, 0.25);
        return t1;
      },
      // Puts `<id>-at` at a point (and optionally a scale and rotation) at `at`: a jump, such as a reset.
      place(id, at, [x, y], { k = null, r = null } = {}) {
        segment(position(node(`${id}-at`)), at, 0, (p, prev) => ({ x, y, k: k ?? prev.k, r: r ?? prev.r }));
        return at;
      },
      // Falls from dy above and lands with a squash. The target must have no transform attribute of its own.
      drop(target, at, { dy = -140, dur = 0.3, sfx = "thump", gain = 0.45 } = {}) {
        const el = node(target), tf = transform(el, "bottom");
        segment(opacity(el), at, dur * 0.3, (p, prev) => prev + (1 - prev) * p);
        segment(tf, at, dur, (p) => ({ y: dy * (1 - p), sy: 1, sx: 1 }), "power3.in");
        segment(tf, at + dur, 0.18, (p) => ({ sy: 0.86 + 0.14 * p, sx: 1.08 - 0.08 * p }), "power2.out");
        if (sfx) S.sfx(sfx, at + dur, gain);
        return at + dur + 0.18;
      },
      // Slides in from (dx, dy) with a firm stop.
      slide(target, at, { dx = 0, dy = 160, dur = 0.32, sfx = "swish" } = {}) {
        const el = node(target);
        segment(opacity(el), at, dur * 0.4, (p, prev) => prev + (1 - prev) * p);
        segment(transform(el), at, dur, (p) => ({ x: dx * (1 - p), y: dy * (1 - p) }), "power3.out");
        if (sfx) S.sfx(sfx, at, 0.3);
        return at + dur;
      },
      // Leaves toward (dx, dy) and fades out.
      slideOut(target, at, { dx = 0, dy = 160, dur = 0.3, sfx = "swish" } = {}) {
        const el = node(target);
        segment(transform(el), at, dur, (p, prev) => ({ x: prev.x + dx * p, y: prev.y + dy * p }), "power2.in");
        segment(opacity(el), at + dur * 0.5, dur * 0.5, (p, prev) => prev * (1 - p));
        if (sfx) S.sfx(sfx, at, 0.25);
        return at + dur;
      },
      // Moves a node to the offset (dx, dy) from its drawn place.
      move(target, at, dx, dy, { dur = 0.4, ease = "power2.inOut" } = {}) {
        segment(transform(node(target)), at, dur, (p, prev) => ({ x: prev.x + (dx - prev.x) * p, y: prev.y + (dy - prev.y) * p }), ease);
        return at + dur;
      },
      // A rubber stamp: scales down from `from` onto the page with a thud.
      stamp(target, at, { from = 1.9, dur = 0.16, sfx = "thud", gain = 0.5 } = {}) {
        const el = node(target);
        segment(opacity(el), at, dur * 0.5, (p, prev) => prev + (1 - prev) * p);
        segment(transform(el, "center"), at, dur, (p) => ({ sx: from + (1 - from) * p, sy: from + (1 - from) * p }), "power4.in");
        if (sfx) S.sfx(sfx, at + dur, gain);
        return at + dur;
      },
      // Pops in from nothing with an overshoot (icons, chips, glyphs).
      popIn(target, at, { dur = 0.3, sfx = "pop", gain = 0.35, origin = "center" } = {}) {
        const el = node(target);
        segment(opacity(el), at, 0.05, (p, prev) => prev + (1 - prev) * p);
        segment(transform(el, origin), at, dur, (p) => ({ sx: p, sy: p }), "back.out(2.2)");
        if (sfx) S.sfx(sfx, at, gain);
        return at + dur;
      },
      // Shrinks to nothing and hides.
      popOut(target, at, { dur = 0.2 } = {}) {
        const el = node(target);
        segment(transform(el), at, dur, (p, prev) => ({ sx: prev.sx * (1 - p), sy: prev.sy * (1 - p) }), "back.in(1.6)");
        segment(opacity(el), at + dur, 0, () => 0);
        return at + dur;
      },
      // One quick swell and settle, to point at a thing without moving it.
      pulse(target, at, { to = 1.12, dur = 0.36, origin = "center" } = {}) {
        segment(transform(node(target), origin), at, dur, (p, prev) => { const s = 1 + (to - 1) * Math.sin(p * Math.PI); return { sx: s, sy: s }; }, "none");
        return at + dur;
      },
      // A squash on landing, about the node's bottom.
      squash(target, at, { amt = 0.82, dur = 0.3 } = {}) {
        segment(transform(node(target), "bottom"), at, dur, (p) => { const w = Math.sin(p * Math.PI) * (1 - p * 0.4); return { sy: 1 - (1 - amt) * w, sx: 1 + (1 - amt) * 0.6 * w }; });
        return at + dur;
      },
      // Rocks a node side to side `times` times (a no, a jam, a rattle).
      wobble(target, at, { deg = 8, times = 3, dur = 0.45, origin = "bottom" } = {}) {
        segment(transform(node(target), origin), at, dur, (p) => ({ r: deg * Math.sin(p * Math.PI * 2 * times) * (1 - p) }));
        return at + dur;
      },
      // Rotates a node to `deg` (about `origin`).
      turn(target, at, deg, { dur = 0.3, ease = "power2.inOut", origin = "center" } = {}) {
        segment(transform(node(target), origin), at, dur, (p, prev) => ({ r: prev.r + (deg - prev.r) * p }), ease);
        return at + dur;
      },
      // Spins a node (gears) from t0 to t1 at `rps` turns a second; `dir` -1 turns it backwards.
      spin(target, t0, t1, { rps = 0.5, dir = 1, origin = "center" } = {}) {
        segment(transform(node(target), origin), t0, t1 - t0, (p, prev) => ({ r: prev.r + dir * 360 * rps * (t1 - t0) * p }));
        return t1;
      },
      // Scales a node (both axes, or "x" / "y") to `to`, about `origin` ("center", "bottom", "top", "left" or a
      // local [x, y]; the first helper to move a node fixes its origin).
      scale(target, at, to, { dur = 0.2, axis = "both", origin = "center", ease = "power2.out" } = {}) {
        segment(transform(node(target), origin), at, dur, (p, prev) => ({
          sx: axis === "y" ? prev.sx : prev.sx + (to - prev.sx) * p,
          sy: axis === "x" ? prev.sy : prev.sy + (to - prev.sy) * p,
        }), ease);
        return at + dur;
      },
      // Tweens a numeric attribute, such as a line's x2 or a rect's width.
      attr(target, name, at, dur, to, { ease = "none" } = {}) {
        const el = node(target);
        segment(channel(el, `attr:${name}`, (e, v) => e.setAttribute(name, num(v)), () => +el.getAttribute(name)), at, dur, (p, prev) => prev + (to - prev) * p, ease);
        return at + dur;
      },
      // Types a <text> node's own string out from empty, at `cps` characters a second, with sparse key clicks.
      type(target, at, { cps = 24, sfx = "key" } = {}) {
        const el = node(target), textNode = el.tagName === "text" ? el : el.querySelector("text");
        const full = textNode.textContent, dur = full.length / cps;
        segment(channel(textNode, "text", (e, v) => { if (e.textContent !== v) e.textContent = v; }, () => ""), at, dur, (p) => full.slice(0, Math.round(p * full.length)));
        if (sfx) for (let s = 0; s < Math.min(8, Math.ceil(dur / 0.11)); s++) S.sfx(sfx, at + s * 0.11, 0.18, s % 3);
        return at + dur;
      },
      // Draws a node on from one side with a clip; it is clipped away until `at`.
      draw(target, at, dur = 0.5, { from = "left", sfx = null } = {}) {
        const el = node(target), side = { left: 1, right: 3, top: 2, bottom: 0 }[from];
        const inset = (p) => { const v = [-30, -30, -30, -30]; v[side] = 100 - 130 * p; return `inset(${v.map((n) => `${num(n)}%`).join(" ")})`; };
        segment(channel(el, "clip", (e, v) => { e.style.clipPath = v; }, () => inset(0)), at, dur, inset, "power2.inOut");
        if (sfx) S.sfx(sfx, at, 0.3);
        return at + dur;
      },
      // Traces a <path> (or the first path in a group) along its length, like a pen; it is invisible until `at`.
      trace(target, at, dur = 0.6, { ease = "power1.inOut", sfx = null } = {}) {
        const el = node(target), paths = el.tagName === "path" ? [el] : [...el.querySelectorAll("path")];
        for (const p of paths) {
          const len = Math.ceil(p.getTotalLength()) + 2;
          p.setAttribute("stroke-dasharray", `${len} ${len}`);
          segment(channel(p, "trace", (e, v) => e.setAttribute("stroke-dashoffset", num(v)), () => len), at, dur, (q) => len * (1 - q), ease);
        }
        if (sfx) S.sfx(sfx, at, 0.25);
        return at + dur;
      },
      // Flashes off and on `times`, and ends on (or off with end: "off").
      blink(target, at, { times = 2, period = 0.3, end = "on" } = {}) {
        const c = opacity(node(target));
        for (let i = 0; i < times; i++) {
          segment(c, at + i * period, 0, () => 0.15);
          segment(c, at + i * period + period / 2, 0, () => 1);
        }
        if (end === "off") segment(c, at + times * period, 0.1, (p) => 1 - p);
        return at + times * period;
      },
      // Shakes the whole scene picture (never the captions) for `dur`, with a thud.
      shake(scene, at, { amp = 10, dur = 0.35, sfx = "thud", gain = 0.5 } = {}) {
        const el = node(`${scene}-shake`);
        segment(channel(el, "shake", (e, v) => { if (v.x || v.y) e.setAttribute("transform", `translate(${num(v.x)} ${num(v.y)})`); else e.removeAttribute("transform"); }, () => ({ x: 0, y: 0 })),
          at, dur, (p) => (p >= 1 ? { x: 0, y: 0 } : { x: amp * (1 - p) * Math.sin(p * 47), y: amp * 0.7 * (1 - p) * Math.cos(p * 61) }));
        if (sfx) S.sfx(sfx, at, gain);
        return at + dur;
      },
      // A looping value from t0 to t1: apply(el, localTime) poses the node; schedule every custom loop with it (S.idle has its own). It holds its first
      // frame before t0 and its last after t1, so every seek agrees. Loops on one node apply in the order they were added.
      loop(target, t0, t1, apply) {
        segment(channel(node(target), `loop:${++loops}`, apply, () => 0), t0, t1 - t0, (p) => p * (t1 - t0));
        return t1;
      },

      // ------------------------------------------------------------------ camera and cuts
      // Reframes the scene's camera onto a plate region {x, y, w} (16:9) or "wide". dur 0 is a snap with a click,
      // dur > 0 a push or a pull, and via "land" snaps and settles in from closer. Returns when the framing rests.
      cam(scene, at, frame, { dur = 0, ease = "power2.inOut", via = null } = {}) {
        if (via && via !== "land") throw new Error(`S.cam: via "${via}" must be "land" or nothing`);
        const f = frame === "wide" ? { x: 0, y: 0, w: 1920 } : frame, h = (f.w * 9) / 16;
        if (!(f.w <= 1920 && f.w >= 640)) throw new Error(`S.cam: width ${f.w} must be 640..1920`);
        if (f.x < 0 || f.y < 0 || f.x + f.w > 1920 + 1e-6 || f.y + h > 1080 + 1e-6) throw new Error(`S.cam: frame ${JSON.stringify(f)} leaves the plate`);
        const el = node(`${scene}-cam`);
        const c = channel(el, "cam", (e, v) => { const k = 1920 / v.w; e.setAttribute("transform", `translate(${num(-v.x * k)} ${num(-v.y * k)}) scale(${+k.toFixed(4)})`); },
          () => ({ x: 0, y: 0, w: 1920 }));
        segment(c, at, via ? 0 : dur, (p, prev) => ({ x: prev.x + (f.x - prev.x) * p, y: prev.y + (f.y - prev.y) * p, w: prev.w + (f.w - prev.w) * p }), ease);
        if (via) return S.land(scene, at);
        if (dur <= 0.12) S.sfx("click", at, 0.25);
        return at + dur;
      },
      // Plate y that sits on screen y S.LIMIT under a camera frame: keep foreground above it in that frame.
      limitIn: (frame) => (frame === "wide" ? S.LIMIT : frame.y + (S.LIMIT * frame.w) / 1920),
      // The landing settle: from `at`, the picture starts `zoom` times closer about `focus` and eases out.
      land(scene, at, { zoom = LAND.zoom, dur = LAND.dur, focus = [960, 460], sfx = "whoosh" } = {}) {
        segment(lens(scene), at, dur, (p) => ({ z: zoom + (1 - zoom) * p, f: focus }), LAND.ease);
        if (sfx) S.sfx(sfx, at, 0.4);
        return at + dur;
      },
      // The cut into a scene, by default 0.45 s before its first caption (clamped at 0): a hard cut where the new plate
      // lands and the previous scene leaves at once. `cut: false` only shows it. Returns when the plate rests.
      enter(scene, { at = film.onset(`${scene}-01`) - 0.45, cut = true, zoom = LAND.zoom, focus } = {}) {
        at = Math.max(0, at);
        const prev = SCENES[SCENES.indexOf(scene) - 1];
        film.enterScene(scene, at);
        // GSAP never renders a set at exactly 0 on the first seek to 0, so a scene that opens the film shows statically.
        if (at === 0) Object.assign(node(scene).style, { visibility: "inherit", opacity: "1" });
        if (!cut) return at;
        if (prev && document.getElementById(prev)) {
          // The previous scene fades down after its last line, so the gap shows the sky.
          const el = node(prev), fadeAt = Math.max(0, Math.min(film.sceneEnd(prev) + 0.2, at - EXIT_FADE));
          segment(channel(el, "exit", (e, v) => { e.style.filter = v >= 1 ? "" : `opacity(${num(v)})`; }, () => 1), fadeAt, EXIT_FADE, (p) => 1 - p, "power2.in");
          segment(transform(el), at, 0, () => ({ x: -2400 }));
        }
        return S.land(scene, at, { zoom, ...(focus ? { focus } : {}) });
      },
    };

    // ------------------------------------------------------------------ cuts
    const LAND = { zoom: 1.4, dur: 0.4, ease: "power3.out" };
    const EXIT_FADE = 0.3;
    function lens(scene) {
      const el = node(`${scene}-land`);
      return channel(el, "land", (e, v) => {
        if (v.z === 1) { e.removeAttribute("transform"); return; }
        e.setAttribute("transform", `translate(${num(v.f[0])} ${num(v.f[1])}) scale(${+v.z.toFixed(4)}) translate(${num(-v.f[0])} ${num(-v.f[1])})`);
      }, () => ({ z: 1, f: [960, 460] }));
    }
    // A point a fraction p of the way along a polyline, by length.
    function along(points, p) {
      const lens = [];
      let total = 0;
      for (let i = 1; i < points.length; i++) { const l = Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]); lens.push(l); total += l; }
      let d = p * total;
      for (let i = 0; i < lens.length; i++) {
        if (d <= lens[i] || i === lens.length - 1) {
          const q = lens[i] ? Math.min(1, d / lens[i]) : 1;
          return [points[i][0] + (points[i + 1][0] - points[i][0]) * q, points[i][1] + (points[i + 1][1] - points[i][1]) * q];
        }
        d -= lens[i];
      }
      return points[points.length - 1];
    }

    // ------------------------------------------------------------------ channels
    const channels = new Map();
    const pivots = [];
    // Puts every channel at its value before any segment, with text at its authored string.
    const atRest = () => { for (const [el, map] of channels) for (const c of map.values()) c.apply(el, c.authored ?? c.initial); };
    let loops = 0;
    function channel(el, key, apply, initial) {
      if (!channels.has(el)) channels.set(el, new Map());
      const map = channels.get(el);
      if (!map.has(key)) map.set(key, { apply, initial: initial(), authored: key === "text" ? el.textContent : undefined, segments: [], merge: false });
      return map.get(key);
    }
    // Adds a segment; segments apply in start order, each from the value the earlier ones left (`prev`).
    function segment(c, t0, dur, fn, ease = "none") {
      if (!(t0 >= 0)) throw new Error(`stage: bad segment time ${t0}`);
      const s = { t0, t1: t0 + Math.max(0, dur), fn, ease: typeof ease === "function" ? ease : gsap.parseEase(ease) };
      let i = c.segments.length;
      while (i > 0 && c.segments[i - 1].t0 > t0) i--;
      c.segments.splice(i, 0, s);
    }
    function valueAt(c, time) {
      let v = c.initial;
      for (const s of c.segments) {
        if (time < s.t0) break;
        const p = time >= s.t1 ? 1 : s.ease((time - s.t0) / (s.t1 - s.t0));
        const out = s.fn(p, v);
        v = c.merge ? { ...v, ...out } : out;
      }
      return v;
    }
    function opacity(el) {
      return channel(el, "opacity", (e, v) => { e.style.opacity = num(v); e.style.visibility = v > 0.001 ? "visible" : "hidden"; },
        () => (el.classList.contains("beat") ? 0 : 1));
    }
    const parsePos = (s) => {
      const t = /translate\(([-\d.]+)[ ,]+([-\d.]+)\)/.exec(s || ""), k = /scale\(([-\d.]+)\)/.exec(s || ""), r = /rotate\(([-\d.]+)\)/.exec(s || "");
      if (!t) throw new Error(`stage: no position in transform "${s}"`);
      return { x: +t[1], y: +t[2], k: k ? +k[1] : 1, r: r ? +r[1] : 0 };
    };
    function position(el) {
      const c = channel(el, "position", (e, v) => e.setAttribute("transform", posStr(v)), () => parsePos(el.getAttribute("transform")));
      c.merge = true;
      return c;
    }
    // x, y, sx, sy, r about an origin fixed when the channel is made. SVG nodes get a transform attribute (so they
    // must not have one of their own), HTML nodes a CSS transform.
    function transform(el, origin = "center") {
      const svgNode = el instanceof SVGElement;
      if (svgNode && !(channels.get(el)?.has("transform")) && el.hasAttribute("transform")) {
        throw new Error(`stage: #${el.id} has its own transform; move an inner group instead`);
      }
      let o = [0, 0];
      if (svgNode && !(channels.get(el)?.has("transform"))) {
        const measure = () => {
          const b = el.getBBox();
          o = Array.isArray(origin) ? origin : [
            origin === "left" ? b.x : b.x + b.width / 2,
            origin === "bottom" ? b.y + b.height : origin === "top" ? b.y : b.y + b.height / 2,
          ];
        };
        measure();
        // Text bounds change when the brand fonts arrive, so init() measures again then.
        if (!Array.isArray(origin)) pivots.push(measure);
      }
      const c = channel(el, "transform", svgNode
        ? (e, v) => e.setAttribute("transform", `translate(${num(v.x + o[0])} ${num(v.y + o[1])})${v.r ? ` rotate(${num(v.r)})` : ""} scale(${+v.sx.toFixed(4)} ${+v.sy.toFixed(4)}) translate(${num(-o[0])} ${num(-o[1])})`)
        : (e, v) => { e.style.transform = `translate(${num(v.x)}px, ${num(v.y)}px)`; },
        () => ({ x: 0, y: 0, sx: 1, sy: 1, r: 0 }));
      c.merge = true;
      // The first call on a node fixes its pivot; later calls reuse that channel.
      c.origin ??= () => o;
      return c;
    }
    // Internals for the character and props below; scenes use the helpers above.
    S.core = { node, num, esc, floor, hue, hidden, INK, HUE, placed, posStr, segment, channel, valueAt, channels, opacity, position, transform, along, CENTRES, finishers: [] };
    return S;
  })();
    // ------------------------------------------------------------------ the cast
    // A character is a drawing with named parts plus one "rig" channel that holds its whole pose, so every action is
    // a segment on that channel and a seek poses it the same way. figure() is the one built-in character; draw
    // another with the same parts and rig keys to replace it.
    const { node, num, placed, segment, channel, valueAt, channels, position, CENTRES, finishers, INK } = S.core;
    const FIGURES = new Map();
    const TAU = Math.PI * 2;
    const SHOULDER = 30, SHOULDER_Y = -176, ARM = 68, HIP_Y = -96;
    const REST = { bob: 0, sq: 1, lean: 0, head: 0, headY: 0, aL: 0, aR: 0, legL: 0, legR: 0, look: 0, eyes: "open",
      dir: 1, gait: 0, phase: 0, idleT: null, amp: 1 };

    // Draws the figure with its feet at (x, y), `scale` times its 300 px height. Parts: <id>-rig, -legL/R, -armL/R,
    // -head, -eyes.
    S.figure = (id, x, y, { scale = 1, dir = 1, hide = false } = {}) => {
      const leg = (s) => `<g id="${id}-leg${s < 0 ? "L" : "R"}"><path d="M${14 * s} ${HIP_Y} V0" class="f-none" ${INK(4)}/></g>`;
      const arm = (s) => `<g id="${id}-arm${s < 0 ? "L" : "R"}"><path d="M${SHOULDER * s} ${SHOULDER_Y} L${(SHOULDER + 16) * s} ${SHOULDER_Y + ARM - 2}" class="f-none" ${INK(4)}/></g>`;
      const body = `<g id="${id}-rig">${leg(-1)}${leg(1)}
        <rect x="-40" y="-200" width="80" height="110" rx="34" class="f-layer" ${INK(4)}/>${arm(-1)}${arm(1)}
        <g id="${id}-head"><circle cx="0" cy="-250" r="44" class="f-layer" ${INK(4)}/>
          <g id="${id}-eyes"><circle cx="-14" cy="-254" r="6" class="f-ink"/><circle cx="14" cy="-254" r="6" class="f-ink"/></g></g></g>`;
      FIGURES.set(id, { start: { ...REST, dir } });
      CENTRES.set(id, [0, -150]);
      return placed(id, x, y, body, { hide, k: scale });
    };

    // The pose as drawn: what render applies and what hand() measures, from one calculation.
    function drawn(v) {
      let breath = 0, blink = false;
      if (v.idleT != null) {
        breath = Math.sin((v.idleT * TAU) / 2.6) * v.amp;
        blink = v.amp > 0.5 && v.idleT % 3.9 > 3.76;
      }
      const g = v.gait, s = Math.sin(v.phase);
      return { breath, blink, bob: v.bob + 2 * breath + 6 * Math.abs(s) * g, lean: v.lean + 3 * g,
        sx: v.dir * (1 + (1 - v.sq) * 0.7), sy: v.sq, armL: -v.aL - 16 * s * g, armR: -v.aR + 16 * s * g };
    }
    const turn = ([x, y], deg, [cx, cy] = [0, 0]) => {
      const a = (deg * Math.PI) / 180, c = Math.cos(a), sn = Math.sin(a);
      return [cx + (x - cx) * c - (y - cy) * sn, cy + (x - cx) * sn + (y - cy) * c];
    };
    function rig(id) {
      if (!FIGURES.has(id)) throw new Error(`stage: #${id} is not a stage.figure`);
      const el = node(id), parts = {};
      for (const p of ["rig", "legL", "legR", "armL", "armR", "head", "eyes"]) parts[p] = node(`${id}-${p}`);
      const c = channel(el, "rig", (e, v) => {
        const d = drawn(v), g = v.gait, s = Math.sin(v.phase);
        parts.rig.setAttribute("transform", `translate(0 ${num(-d.bob)}) rotate(${num(d.lean)}) scale(${num(d.sx)} ${num(d.sy)})`);
        parts.legL.setAttribute("transform", `rotate(${num(v.legL + 18 * s * g)} -14 ${HIP_Y})`);
        parts.legR.setAttribute("transform", `rotate(${num(v.legR - 18 * s * g)} 14 ${HIP_Y})`);
        parts.armL.setAttribute("transform", `rotate(${num(d.armL)} ${-SHOULDER} ${SHOULDER_Y})`);
        parts.armR.setAttribute("transform", `rotate(${num(d.armR)} ${SHOULDER} ${SHOULDER_Y})`);
        parts.head.setAttribute("transform", `translate(0 ${num(v.headY - d.breath)}) rotate(${num(v.head)} 0 -206)`);
        // The eyes slide toward the look and squash shut for a blink or the "closed" state.
        const shut = d.blink || v.eyes === "closed";
        parts.eyes.setAttribute("transform", `translate(${num(v.look * 8)} 0)${shut ? " translate(0 -254) scale(1 0.2) translate(0 254)" : ""}`);
      }, () => ({ ...FIGURES.get(id).start }));
      c.merge = true;
      return c;
    }
    finishers.push(() => { for (const id of FIGURES.keys()) rig(id); });
    const state = (id, at) => valueAt(rig(id), at);

    // Tweens any rig keys (bob, sq, lean, head, headY, aL, aR, legL, legR, look) over `dur`. An arm angle is degrees
    // toward the facing side from hanging down, so aR: 70 reaches the front arm out ahead.
    S.pose = (id, at, target, { dur = 0.25, ease = "power2.inOut" } = {}) => {
      const keys = Object.keys(target);
      segment(rig(id), at, dur, (p, prev) => Object.fromEntries(keys.map((k) => [k, typeof target[k] === "number" ? prev[k] + (target[k] - prev[k]) * p : target[k]])), ease);
      return at + dur;
    };
    S.rest = (id, at, { dur = 0.25 } = {}) => S.pose(id, at, { aL: 0, aR: 0, lean: 0, head: 0, headY: 0, sq: 1, bob: 0, legL: 0, legR: 0, look: 0 }, { dur });
    // Eyes "open" or "closed" from `at`.
    S.eyes = (id, at, eyes) => {
      if (eyes !== "open" && eyes !== "closed") throw new Error(`stage.eyes: "${eyes}" must be open or closed`);
      segment(rig(id), at, 0, () => ({ eyes }));
      return at;
    };
    // Eyes toward the facing side (dx > 0) or away, -1..1.
    S.look = (id, at, dx, { dur = 0.15 } = {}) => S.pose(id, at, { look: dx }, { dur });
    // Faces right (1) or left (-1).
    S.face = (id, at, dir) => { segment(rig(id), at, 0, () => ({ dir })); return at; };
    // The breathing idle from t0 to t1, with a blink every 3.9 s: the one loop a scene may run for a whole shot.
    S.idle = (id, t0, t1) => { segment(rig(id), t0, t1 - t0, (p) => ({ idleT: p >= 1 ? null : p * (t1 - t0) })); return t1; };
    // Walks along points from t0 to t1, facing the way it goes, with `stride` px a step and the legs at rest after.
    S.walk = (id, points, t0, t1, { stride = 34, sfx = "tick", ease = "power1.inOut" } = {}) => {
      const start = S.at(id, t0), pts = [[start.x, start.y], ...points];
      let dist = 0;
      for (let i = 1; i < pts.length; i++) dist += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      // An even step count ends the stride with both legs down.
      const steps = 2 * Math.max(1, Math.round(dist / (2 * stride * start.k))), dir = pts[pts.length - 1][0] >= start.x ? 1 : -1;
      S.ride(id, pts, t0, t1, { ease, sfx: null });
      segment(rig(id), t0, t1 - t0, (p) => ({ phase: p * steps * Math.PI, gait: p >= 1 ? 0 : Math.min(1, p * 10, (1 - p) * 10), dir }));
      if (sfx) for (let i = 1; i < steps; i += 2) S.sfx(sfx, t0 + ((t1 - t0) * i) / steps, 0.1, i % 4);
      return t1;
    };
    // Where a hand is at `at`, in plate px: the arm on the facing side ("front") or the other one ("back"). It runs
    // the drawing's own transforms, so a held prop stays in the hand.
    S.hand = (id, at, side = "front") => {
      const v = state(id, at), d = drawn(v), p = S.at(id, at), s = side === "front" ? 1 : -1;
      let pt = turn([(SHOULDER + 16) * s, SHOULDER_Y + ARM - 2], s > 0 ? d.armR : d.armL, [SHOULDER * s, SHOULDER_Y]);
      pt = turn([pt[0] * d.sx, pt[1] * d.sy], d.lean);
      pt = [pt[0], pt[1] - d.bob];
      // A move, turn or squash on the body itself sits between the rig and the placed group.
      const body = channels.get(node(id))?.get("transform");
      if (body) {
        const b = valueAt(body, at), [ox, oy] = body.origin();
        pt = turn([(pt[0] - ox) * b.sx, (pt[1] - oy) * b.sy], b.r);
        pt = [pt[0] + ox + b.x, pt[1] + oy + b.y];
      }
      pt = turn(pt, p.r);
      return [p.x + pt[0] * p.k, p.y + pt[1] * p.k];
    };
    // Keeps a placed prop centred on a hand from t0 to t1, frame by frame, whatever the figure does meanwhile.
    S.hold = (id, prop, t0, t1, { side = "front" } = {}) => {
      const [cx, cy] = CENTRES.get(prop) || [0, 0];
      segment(position(node(`${prop}-at`)), t0, t1 - t0, (q, prev) => {
        const [x, y] = S.hand(id, t0 + q * (t1 - t0), side), [dx, dy] = turn([cx * prev.k, cy * prev.k], prev.r);
        return { x: x - dx, y: y - dy };
      });
      return t1;
    };
    // Walks along points from t0 to t1 with a prop held in the front hand.
    S.carry = (id, prop, points, t0, t1, o = {}) => {
      S.walk(id, points, t0, t1, o);
      return S.hold(id, prop, t0, t1);
    };

    // ------------------------------------------------------------------ props
    // A prop is a placed drawing (<id>-at holds its position) with its centre in CENTRES, so S.hold can carry it.
    const prop = (id, x, y, w, h, body, hide) => { CENTRES.set(id, [w / 2, h / 2]); return placed(id, x, y, body, { hide }); };
    // A parcel with its tape, its top left at (x, y).
    S.parcel = (id, x, y, { w = 80, h = 60, hide = false } = {}) =>
      prop(id, x, y, w, h, `<rect width="${w}" height="${h}" rx="6" class="f-layer" ${INK(4)}/><path d="M${w / 2} 0 V${h}" class="f-none" ${INK(4)}/>`, hide);
    // An envelope with its flap, its top left at (x, y).
    S.envelope = (id, x, y, { w = 96, h = 64, hide = false } = {}) =>
      prop(id, x, y, w, h, `<rect width="${w}" height="${h}" rx="6" class="f-layer" ${INK(4)}/><path d="M4 6 L${w / 2} ${h * 0.6} L${w - 4} 6" class="f-none" ${INK(4)}/>`, hide);
    // A card of mono lines, such as a field and its value; each line is <id>-l<i>, for stage.type or stage.setText.
    S.card = (id, x, y, lines, { w = null, size = 26, hide = false } = {}) => {
      const lh = size * 1.5, width = w || Math.max(...lines.map((l) => S.monoWidth(l, size))) + 48, h = lines.length * lh + 32;
      const body = `<rect width="${num(width)}" height="${num(h)}" rx="12" class="f-layer" ${INK(4)}/>` +
        lines.map((l, i) => S.mono(24, 16 + lh * (i + 0.72), l, { size, id: `${id}-l${i}` })).join("");
      return prop(id, x, y, width, h, body, hide);
    };
    // A verdict stamp: a word in a tilted frame of one hue, centred on (x, y); animate it in with stage.stamp(id, at).
    S.verdict = (id, x, y, word, { hue = "good", size = 40, hide = true } = {}) => {
      const w = S.monoWidth(word, size) + 48, h = size * 1.7;
      const body = `<g transform="rotate(-8)"><rect x="${num(-w / 2)}" y="${num(-h / 2)}" width="${num(w)}" height="${num(h)}" rx="10" class="f-none" ${S.core.HUE(hue, 5)}/>` +
        S.text(0, size * 0.36, word.toUpperCase(), { font: "mono", size, weight: 700, anchor: "middle", fill: hue }) + "</g>";
      CENTRES.set(id, [0, 0]);
      return placed(id, x, y, body, { hide });
    };
  startedFilm.stage = S.init(startedFilm);
};
