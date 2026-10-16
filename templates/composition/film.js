// Shared plumbing for a HyperFrames explainer: one paused timeline, FILM lookups, style tokens and burned-in captions.
// HyperFrames 0.8.57 runs external scripts from <head> before the body exists, so nothing here touches the page
// until the scene script in index.html calls startFilm().
window.FilmBrands = window.FilmBrands || {};

window.startFilm = ({ brand } = {}) => {
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
  // cue("s01|quoted words") or cue("s01|s01-02+0.4"): the start of a Visual cue from the script.
  const cue = (key) => lookup(FILM.cues, key, "cue");
  // onset("s01-02"): the start of that sentence's first caption, for hard cuts on a sentence.
  const onset = (sentence) => lookup(FILM.caption_onsets, `${sentence.split("-")[0]}|${sentence}`, "caption onset");
  // sceneEnd("s01"): the end of the scene's last caption, that is, its last spoken line.
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
    // A brand module may replace reveal with its signature entrance; scenes call it the same way.
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

  const band = root.appendChild(document.createElement("div"));
  band.id = "captions";
  for (const c of FILM.captions) {
    const line = band.appendChild(document.createElement("div"));
    line.className = "caption";
    line.appendChild(document.createElement("span")).textContent = c.text;
    // Hard on and off, because check_film.py expects the band to change within one frame of each caption edge.
    tl.set(line, { autoAlpha: 1 }, c.start);
    tl.set(line, { autoAlpha: 0 }, c.end);
  }
  tl.set({}, {}, FILM.duration);

  for (const face of document.fonts) {
    face.load().catch(() => console.error(`font "${face.family}" ${face.weight} did not load; check fonts/ against tokens.css`));
  }
  return film;
};
