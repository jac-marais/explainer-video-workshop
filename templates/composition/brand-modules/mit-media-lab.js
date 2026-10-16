// MIT Media Lab-inspired signature system: column-module reveals and one morphing 7x7 mark.
// brands/mit-media-lab.md owns the rules; every duration and easing here is read from its tokens.
// startFilm({ brand: "mit-media-lab" }) calls this with the film's helpers before any scene code runs.
window.FilmBrands = window.FilmBrands || {};
window.FilmBrands["mit-media-lab"] = (film) => {
  const { tl, root, token, px, seconds, ease, onset, sceneEnd } = film;
  const fast = seconds("--dur-fast"), base = seconds("--dur-base"), slow = seconds("--dur-slow");

  // Reveals come from the grid: 7 column modules over 1.5x the element's duration token.
  film.reveal = (target, at, { dur = "--dur-base", easing = "--ease-standard" } = {}) => {
    gsap.utils.toArray(target).forEach((el) => el.classList.add("modules"));
    tl.set(target, { autoAlpha: 1 }, at);
    tl.fromTo(target, { "--p": 0 }, { "--p": 1, duration: 1.5 * seconds(dur), ease: ease(easing), immediateRender: false }, at);
  };

  // A shape is 7 strings of 7 characters: "." empty, "#" a black cell, "*" the one magenta accent cell.
  const parse = (name, rows) => {
    const cells = rows.join("");
    if (rows.length !== 7 || rows.some((r) => r.length !== 7) || /[^.#*]/.test(cells)) {
      throw new Error(`mark ${name}: write 7 rows of 7 characters from ".#*"`);
    }
    if (cells.split("*").length !== 2) throw new Error(`mark ${name}: needs exactly one "*" accent cell`);
    return [...cells];
  };

  // mark({s01: rows, s02: rows, ...}) adds the film's one mark; call intro, then change between scenes.
  film.mark = (shapes) => {
    const parsed = Object.fromEntries(Object.entries(shapes).map(([name, rows]) => [name, parse(name, rows)]));
    const shape = (name) => {
      if (!parsed[name]) throw new Error(`no mark shape for "${name}"`);
      return parsed[name];
    };
    const el = root.appendChild(document.createElement("div"));
    el.className = "ml-mark";
    const cells = Array.from({ length: 49 }, (_, k) => {
      const cell = el.appendChild(document.createElement("i"));
      cell.style.left = `calc(var(--cell-lg) * ${k % 7})`;
      cell.style.top = `calc(var(--cell-lg) * ${Math.floor(k / 7)})`;
      return cell;
    });
    const fill = { "#": token("--text"), "*": token("--emph") };
    let shown = Array(49).fill(".");

    const u = px("--u"), size = 7 * px("--cell-lg"), width = Number(root.dataset.width);
    const spot = {
      corner: { x: 0, y: -8 * u, scale: px("--cell") / px("--cell-lg") },
      center: { x: (width + size) / 2 - (width - px("--margin")), y: -2 * u, scale: 1 },
    };
    const move = (where, at, duration = base) => tl.to(el, { ...spot[where], duration, ease: ease("--ease-standard") }, at);

    // Leaving cells start over the first --dur-fast and arriving cells over the next, so the two shapes barely overlap.
    const draw = (next, at, order, spread, gap) => {
      next.forEach((kind, k) => {
        if (shown[k] === kind) return;
        if (shown[k] !== ".") tl.to(cells[k], { scale: 0, duration: fast, ease: ease("--ease-exit") }, at + order(k) * spread);
        if (kind !== ".") {
          const t = at + gap + order(k) * spread;
          tl.set(cells[k], { backgroundColor: fill[kind] }, t);
          tl.fromTo(cells[k], { scale: 0 }, { scale: 1, duration: fast, ease: ease("--ease-entrance"), immediateRender: false }, t);
        }
      });
      shown = next;
    };
    const diagonal = (k) => ((k % 7) + Math.floor(k / 7)) / 12;
    const scattered = (k) => ((k * 29) % 49) / 48;

    return {
      // The first scene's mark assembles large over 1.0 s, then settles in the corner over --dur-slow.
      intro(name, at = 0) {
        draw(shape(name), at, scattered, 1.0 - fast, 0);
        move("corner", at + 1.0, slow);
      },
      // In the pause between scenes: to the center, morph along the diagonal, back to the corner as the next scene starts.
      // Returns the time the mark settles, which is when the next scene's content may start to build.
      change(from, to) {
        const leave = sceneEnd(from) + 0.1 + fast, morph = leave + base, back = onset(`${to}-01`) + 0.15;
        if (morph + 3 * fast > back) {
          throw new Error(`mark change ${from} to ${to} needs ${(morph + 3 * fast - back).toFixed(2)} s more pause` +
            ` before ${to}'s first sentence than the narration has; put [pause] there in the script`);
        }
        move("center", leave);
        draw(shape(to), morph, diagonal, fast, fast);
        move("corner", back);
        return back + base;
      },
      hide(at) {
        tl.to(el, { autoAlpha: 0, duration: fast, ease: ease("--ease-exit") }, at);
      },
    };
  };
};
