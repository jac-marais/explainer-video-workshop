# Starter composition

A HyperFrames composition to copy into a run, so the run writes only its scenes. It holds the paused timeline, the narration audio, the burned-in captions and the lookups that read audio-bound times from `data.js`. A brand module adds a style's signature motion.

## Files

| File | Job | A run edits it |
|---|---|---|
| `index.html` | the root, the scenes and the scene script | yes; replace the example scene |
| `film.js` | `startFilm()`: timeline, FILM lookups, token helpers, captions | no |
| `film.css` | base layout read from the tokens: scene, beat, eyebrow, headline, caption band | no |
| `tokens.css` | neutral placeholder tokens | replace it with the brand's tokens |
| `example-script.md` | the invented script that cues the example scene | no; a run uses its own script |
| `brand-modules/<brand>.js`, `.css` | a brand's signature motion | no |

## Set up a run

1. Copy the folder: `mkdir -p outputs/<topic>/project && cp -R templates/composition/. outputs/<topic>/project/`.
2. Replace `tokens.css` with the `css` block under "Tokens" in the chosen `brands/<brand>.md`, unchanged. Copy the font files that its "Assets and licenses" table names into `fonts/`, with their OFL texts. The workshop does not ship them, because each brand file owns its faces and their sources. Keep the placeholder only for the neutral default.
3. Put GSAP in `vendor/gsap.min.js`. Install it beside the HyperFrames CLI with `npm install gsap@3.14.2` and copy `node_modules/gsap/dist/gsap.min.js`. GSAP's own license (`gsap.com/standard-license`) covers that file, so the workshop does not ship it.
4. Build `data.js` with `scripts/film/build_data.py`, `--estimate` for a silent preview or `--audio` after M1. It also writes the root's `data-duration`, which `startFilm()` checks against `data.js`.
5. Before a voice exists, write a silent `audio/narration.wav` as long as the estimate, because the lint fails on a missing audio file: `ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t SECONDS -c:a pcm_s16le audio/narration.wav`. `narrate_film.py` replaces it.

A brand with other token names, such as `brands/mozilla.md`, needs the base names (`--bg`, `--text`, `--ease-entrance`, `--dur-base` and the others in `tokens.css`) mapped to its own in a `:root` block in `index.html`. `token()` throws on a missing name, but CSS skips one silently, so map them all.

## Write a scene

Each scene is a `<section class="scene" id="sNN">` whose elements carry `beat`, so they stay hidden until the timeline reveals them. Lay them out in the `<style>` block of `index.html` from tokens and the `--u` unit.

In the scene script, call `startFilm()` once, register its `tl` under the root's `data-composition-id` in `index.html` (the lint reads the key there), and then add each beat at a time from `data.js`:

- `cue("s01|quoted words")` or `cue("s01|s01-02+0.4")` gives a Visual cue's start. `scripts/README.md` defines both cue forms.
- `onset("s01-02")` gives the start of a sentence's first caption, for a hard cut on it.
- `sceneEnd("s01")` gives the end of a scene's last caption.
- `reveal(target, at, {dur, easing})` and `hide(target, at, {dur, easing})` fade by tokens. A brand module may replace `reveal` with its signature entrance.
- `enterScene("s01")` shows the section at its first caption, and `exitScene("s01")` hides it 0.1 s after its last.
- `token`, `px`, `seconds` and `ease` read a token as a string, pixels, seconds and a GSAP ease.

A lookup with a missing key throws and lists that scene's keys, so a renamed quote fails `hyperframes check` instead of drawing at second 0. Never write a second for an audio-bound event. Plan the beats under the beat rule in step 4 of `methods/prepare-explainer-video.md`.

## Caption layout

This section owns the caption geometry contract for every brand and the neutral starter; each preset's Layout and Tokens sections supply its values. In the 1920×1080 canvas, `film.css` derives `--caption-top = 1080px - --caption-bottom - --caption-h` and `--content-bottom = --caption-top - --u`. The complete zone must end at or before `--caption-limit` (990 px), with a margin before the renderer's blank strip. The [renderer traps](../../methods/renderer-traps.md) explain that strip.

Keep all foreground content above `--content-bottom`, including grids, panel fills, title and end-card groups, marks, shadows and the furthest point of entrance motion. Canvas backgrounds and transitions may fill the frame behind captions. The band clips painted overflow as a final guard; clipping text is a layout failure. Measure the complete caption span, including padding, against the zone, and keep it to two lines. `film.js` rejects an unsafe band or a span that does not fit when the film starts.

The captions come from `FILM.captions` and switch on and off hard, because `check_film.py` looks for the change at each caption edge. Pass the brand's caption font and size to `captions.py`, so its line breaks fit. Pass font files from the project's `fonts/`, the same faces the composition's `@font-face` rules load, never operating-system fonts: system faces differ between macOS and Linux, so the measured breaks would not match the rendered captions on the other platform. For Han, Hangul or Devanagari captions, add an OFL face such as Noto Sans SC, KR or Devanagari, with its license, and list it in the same fallback order in the CSS and in the repeated `--font` options. The `--caption-pad` token supplies padding when a brand defines it. `check_film.py --help` owns the default inspection crop and its resolution scaling; use the preset's entire zone for a different brand crop.

## Brand modules

A module registers `window.FilmBrands["<brand>"] = (film) => { ... }` and loads after `film.js`. `startFilm({ brand: "<brand>" })` calls it before any scene code, and fails when it is not loaded. It takes durations, easings, sizes and colors from the tokens, and fixed timings from the brand file. Add a module only for a brand whose film needs one.

`mit-media-lab` follows "Motion" in `brands/mit-media-lab.md`:

- `reveal` becomes the column-module reveal.
- `film.mark({s01: rows, s02: rows})` adds the one 7×7 mark. Each shape is 7 strings of 7 characters: `.` empty, `#` a black cell, `*` the one magenta accent cell.
- `mark.intro("s01")` assembles it at the film start and moves it to the corner.
- `const at = mark.change("s01", "s02")` morphs it at the center between the scenes and returns the time it settles in the corner, when the next scene's content may start.
- `mark.hide(at)` fades it out.

The preset's Layout section owns the mark positions and bounds.

`change` throws when the pause before the next scene is too short for the morph. Write `[pause]` before each later scene's first sentence. The estimate's scene gap can pass where measured narration's does not, so only the measured `data.js` proves it.

## Check

Run `hyperframes check`, then render and check the MP4 as M5 of `templates/production-prompt.md` says, under the HyperFrames preflight traps in `methods/renderer-traps.md`.
