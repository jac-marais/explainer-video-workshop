// HyperFrames runs external scripts before the body exists (methods/renderer-traps.md), so nothing here touches the page until startFilm().
window.FilmBrands = window.FilmBrands || {};
window.FilmFigures = window.FilmFigures || {};
window.FilmMotion = window.FilmMotion || {};

window.startFilm = ({ brand, figures, motion } = {}) => {
  const FILM = window.FILM;
  if (!FILM) throw new Error("window.FILM is missing: write data.js with scripts/film/build_data.py");
  const root = document.querySelector("[data-composition-id]");
  if (Number(root.dataset.duration) !== FILM.duration) {
    throw new Error(`root data-duration ${root.dataset.duration} is not data.js duration ${FILM.duration}: rerun build_data.py on this project`);
  }
  const tl = gsap.timeline({ paused: true });

  const lookup = (map, key, what) => {
    if (!(key in map)) {
      const scene = key.split("|")[0];
      const known = Object.keys(map).filter((k) => k.startsWith(`${scene}|`));
      throw new Error(`${what} "${key}" is not in data.js; ${scene} has: ${known.join(", ") || "nothing"}`);
    }
    return map[key];
  };
  const cue = (key) => lookup(FILM.cues, key, "cue");
  const onset = (sentence) => lookup(FILM.caption_onsets, `${sentence.split("-")[0]}|${sentence}`, "caption onset");
  const sceneEnd = (scene) => {
    const ends = FILM.captions.filter((c) => c.scene_id === scene).map((c) => c.end);
    if (!ends.length) throw new Error(`no captions for scene "${scene}" in data.js`);
    return Math.max(...ends);
  };

  const css = getComputedStyle(document.documentElement);
  const token = (name) => {
    const value = css.getPropertyValue(name).trim();
    if (!value) throw new Error(`style token ${name} is not set; copy the brand's Tokens block into tokens.css`);
    return value;
  };
  const px = (name) => parseFloat(token(name));
  const seconds = (name) => {
    const value = token(name);
    return value.endsWith("ms") ? parseFloat(value) / 1000 : parseFloat(value);
  };
  // GSAP's core has no cubic-bezier ease, so solve the token's curve here.
  const ease = (name) => {
    const m = token(name).match(/^cubic-bezier\(([^)]+)\)$/);
    if (!m) throw new Error(`style token ${name} must be a cubic-bezier()`);
    const [x1, y1, x2, y2] = m[1].split(",").map(Number);
    const at = (a, b, t) => 3 * a * (1 - t) ** 2 * t + 3 * b * (1 - t) * t ** 2 + t ** 3;
    return (p) => {
      let lo = 0, hi = 1, t = p;
      for (let i = 0; i < 30; i++) {
        t = (lo + hi) / 2;
        if (at(x1, x2, t) < p) lo = t; else hi = t;
      }
      return at(y1, y2, t);
    };
  };

  const film = {
    FILM, tl, root, cue, onset, sceneEnd, token, px, seconds, ease,
    reveal(target, at, { dur = "--dur-base", easing = "--ease-entrance" } = {}) {
      tl.fromTo(target, { autoAlpha: 0 }, { autoAlpha: 1, duration: seconds(dur), ease: ease(easing), immediateRender: false }, at);
    },
    hide(target, at, { dur = "--dur-fast", easing = "--ease-exit" } = {}) {
      tl.to(target, { autoAlpha: 0, duration: seconds(dur), ease: ease(easing) }, at);
    },
    enterScene(scene, at = onset(`${scene}-01`)) {
      tl.set(`#${scene}`, { autoAlpha: 1 }, at);
    },
    exitScene(scene, at = sceneEnd(scene) + 0.1) {
      film.hide(`#${scene}`, at);
    },
  };
  if (brand) {
    if (!window.FilmBrands[brand]) throw new Error(`brand module "${brand}" is not loaded; add brand-modules/${brand}.js after film.js`);
    window.FilmBrands[brand](film);
  }
  if (figures) {
    if (!window.FilmFigures[figures]) throw new Error(`figure module "${figures}" is not loaded; add figure-modules/${figures}.js after film.js`);
    window.FilmFigures[figures](film);
  }
  if (motion) {
    if (!window.FilmMotion[motion]) throw new Error(`motion module "${motion}" is not loaded; add motion-modules/${motion}.js after film.js`);
    window.FilmMotion[motion](film);
  }

  const band = root.appendChild(document.createElement("div"));
  band.id = "captions";
  for (const c of FILM.captions) {
    const line = band.appendChild(document.createElement("div"));
    line.className = "caption";
    line.appendChild(document.createElement("span")).textContent = c.text;
    tl.set(line, { autoAlpha: 1 }, c.start);
    tl.set(line, { autoAlpha: 0 }, c.end);
  }
  const zone = band.getBoundingClientRect();
  const frame = root.getBoundingClientRect();
  if (zone.top < frame.top || zone.bottom > frame.top + px("--caption-limit") || zone.height <= 0) {
    throw new Error("caption zone is unsafe; follow templates/composition/README.md#caption-layout");
  }
  tl.set({}, {}, FILM.duration);

  for (const face of document.fonts) {
    face.load().catch(() => console.error(`font "${face.family}" ${face.weight} did not load; check fonts/ against tokens.css`));
  }
  document.fonts.ready.then(() => {
    for (const span of band.querySelectorAll("span")) {
      const box = span.getBoundingClientRect();
      if (box.top < zone.top || box.bottom > zone.bottom || box.left < zone.left || box.right > zone.right) {
        console.error(`caption "${span.textContent}" does not fit its zone; shorten or rebreak it`);
      }
    }
  });
  return film;
};
