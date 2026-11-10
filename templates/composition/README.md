# Starter composition

Copy this HyperFrames starter into a run and write its scenes. The shared files handle the film's setup.

## Files

| File | Job | A run edits it |
|---|---|---|
| `index.html` | It holds the root, scenes, scene script and narration audio. | Replace the example scene. |
| `film.js` | `startFilm()` supplies the paused timeline, FILM lookups, token helpers and burned-in captions. | Keep it unchanged. |
| `film.css` | It lays out scenes, beats, eyebrows, headlines and the caption band from tokens. | Keep it unchanged. |
| `tokens.css` | It supplies neutral placeholder tokens. | Follow [Set up a run](#set-up-a-run). |
| `example-script.md` | It cues the invented example scene. | Use the run's own script. |
| `brand-modules/<brand>.js`, `.css` | See [Brand modules](#brand-modules). | Keep them unchanged. |
| `figure-modules/hairline.js`, `.css`, `HAIRLINE-LICENSE.txt` | See [Figure modules](#figure-modules). | Keep them unchanged. |
| `motion-modules/stage.js`, `.css` | See [Motion modules](#motion-modules). | Keep them unchanged. |
| `stage-example.html` | It supplies a stage scene to adapt. | Follow [Motion modules](#motion-modules). |

Link each optional module's `.css` in `<head>` and load its `.js` after `film.js`. `startFilm()` applies brand, figure and motion modules in that order, before scene code. [film.js](film.js) owns missing-module errors.

## Set up a run

1. Copy the folder with `mkdir -p outputs/<topic>/project && cp -R templates/composition/. outputs/<topic>/project/`.
2. Replace `tokens.css` with the unchanged `css` block under "Tokens" in the chosen `brands/<brand>.md`. Copy the fonts named in its "Assets and licenses" table under the [caption font contract](#caption-layout). Each brand file owns its faces and sources, so the workshop does not ship them. Keep the placeholder for the neutral default.
3. Put GSAP in `vendor/gsap.min.js`. Install it beside the HyperFrames CLI with `npm install gsap@3.14.2` and copy `node_modules/gsap/dist/gsap.min.js`. GSAP's own license (`gsap.com/standard-license`) covers that file, so the workshop does not ship it.
4. See [scripts/film/build_data.py](../../scripts/film/build_data.py) for `data.js`, `--estimate` and `--audio`. [M1](../production-prompt.md) supplies the measured inputs.
5. Before a voice exists, write a silent `audio/narration.wav` as long as the estimate, because lint fails on a missing audio file. Run `ffmpeg -f lavfi -i anullsrc=r=48000:cl=mono -t SECONDS -c:a pcm_s16le audio/narration.wav`. `narrate_film.py` replaces it.

A brand with other token names, such as `brands/mozilla.md`, needs the base names (`--bg`, `--text`, `--ease-entrance`, `--dur-base` and the others in `tokens.css`) mapped to its own in a `:root` block in `index.html`. CSS silently skips a missing token. [film.js](film.js) owns the helper checks.

## Write a scene

For a composition split into `scenes/sNN.js` fragments, assemble its page with [build_scenes.py](../../scripts/film/build_scenes.py). Pass that composition's own template; the starter `index.html` is a complete example page.

Use a `<section class="scene" id="sNN">` for each scene and mark reveal targets with `beat` so they stay hidden until the timeline reveals them. Lay them out in the `<style>` block of `index.html` from tokens and the `--u` unit.

Call `startFilm()` once in the scene script and register its `tl` in `index.html` under the [HyperFrames preflight contract](../../methods/renderer-traps.md#hyperframes-preflight-traps). Plan the beats under [step 4 of methods/prepare-explainer-video.md](../../methods/prepare-explainer-video.md#4-convert-the-narrative-into-a-scene-and-shot-sequence), then use these helpers to place them.

- Use `cue("s01|quoted words")` or `cue("s01|s01-02+0.4")` with the forms in [scripts/README.md](../../scripts/README.md#sentence-cues-and-translations).
- Use `onset("s01-02")` to read `FILM.caption_onsets` for the [cut timing rules](../../scripts/README.md#sentence-cues-and-translations).
- Use `sceneEnd("s01")` to read the end of a scene's last caption.
- Use `reveal(target, at, {dur, easing})` and `hide(target, at, {dur, easing})` for token-based fades. A brand module can supply its signature entrance through `reveal`.
- Use `enterScene("s01")` and `exitScene("s01")` to show and hide the section. [film.js](film.js) defines their timing and missing-key errors.
- Use `token`, `px`, `seconds` and `ease` to read a token as a string, pixels, seconds and a GSAP ease.

## Draw a cast

Use the example scene's worker as the SVG drawing pattern. Draw each character and prop as one SVG group with named child groups for moving parts, such as legs, arms, head and eyes. Set each part's pivot with `svgOrigin` so it turns around its joint. Use [the cast rule](../../methods/prepare-explainer-video.md#cast) for the shared world and camera plan. [Motion modules](#motion-modules) describes the optional implementation.

Joints bend the way a body bends, and held things sit in the hands. Props keep their true scale beside the character, and carried props paint in front of it. Keep things level unless a beat calls for a tilt. Keep the character whole inside the frame at its most extreme pose.

## Caption layout

This section owns the caption geometry contract for every brand and the neutral starter. Each preset's Layout and Tokens sections supply its values. In the 1920×1080 canvas, `film.css` derives `--caption-top = 1080px - --caption-bottom - --caption-h` and `--content-bottom = --caption-top - --u`. The complete zone ends at or before `--caption-limit` (990 px), leaving a margin before the blank strip explained in [renderer traps](../../methods/renderer-traps.md).

Keep all foreground content above `--content-bottom`, including grids, panel fills, title and end-card groups, marks, shadows and the furthest point of entrance motion. Canvas backgrounds and transitions can fill the frame behind captions. Measure the complete caption span, including padding, against the zone and keep it to two lines. The band clips painted overflow, so clipped text is a layout failure. [film.js](film.js) owns the startup geometry checks.

Captions from `FILM.captions` switch on and off hard because `check_film.py` inspects each caption edge. Give `captions.py` the brand's caption font and size. Copy the chosen brand's font files into `fonts/` and use those files in both `@font-face` and `captions.py`, because system faces can change the measured breaks across platforms. For Han, Hangul or Devanagari captions, add an OFL face such as Noto Sans SC, KR or Devanagari. Copy each face's license text into `fonts/`, including every fallback face, and use the same fallback order in CSS and the repeated `--font` options. `--caption-pad` supplies padding when the brand defines it. `check_film.py --help` owns the inspection crop and resolution scaling. Use the preset's entire zone for a different brand crop.

## Brand modules

A brand module adds a style's signature motion. Register it as `window.FilmBrands["<brand>"] = (film) => { ... }` and select it with `startFilm({ brand: "<brand>" })`. It takes durations, easings, sizes and colors from tokens and fixed timings from the brand file. Add one when the brand's film needs it.

The `mit-media-lab` module implements "Motion" in `brands/mit-media-lab.md`. Its [source](brand-modules/mit-media-lab.js) defines the mark's shape encoding and transition checks. Use these calls to schedule it.

- `film.mark({s01: rows, s02: rows})` creates the mark.
- `mark.intro("s01")` assembles it at the film start and moves it to the corner.
- `const at = mark.change("s01", "s02")` morphs it at the center between scenes and returns when it settles in the corner, ready for the next scene's content.
- `mark.hide(at)` fades it out.

The preset's Layout section owns mark positions and bounds. Write `[pause]` before each later scene's first sentence to leave room for the morph. An estimated scene gap can fit when measured narration does not, so verify it with measured `data.js`.

## Figure modules

A figure module adds a drawing style that works with any brand. Register it as `window.FilmFigures["<name>"] = (film) => { ... }` and select it with `startFilm({ figures: "<name>" })`.

See [License](../../README.md#license) for Hairline provenance (S-HL-001), and keep `HAIRLINE-LICENSE.txt` beside the module. [hairline.js](figure-modules/hairline.js) owns its seek implementation.

- `const fig = film.hairline.figure("#s02-fig", { S })` draws into an element of class `abs` that has a width. [hairline.js](figure-modules/hairline.js) defines the viewBox, `S` scale, defaults and fit guards.
- `fig.box({ x, y, w, d, h, z, r, bevel, ground })` places a solid's foot at `(x, y, z)`. Follow rule 09 for its drawing and rule 06 for `ground: true`.
- `fig.link(a, b)` adds a dashed ground line between two boxes' centres. `box.dot(u, v)` adds a flat lid dot at an offset from its centre.
- Use `fig.fit(cx, cy, points)` under rule 03 for placement and fit failures.
- Tween a box's `x`, `y`, `z`, `h`, `hi` and `opacity` with plain `tl.to`, a link's `hi`, or a dot's `on`.
- `film.hairline.ripple(boxes, at, { from, step, clock, ...values })` schedules the spread under rules 02 and 08 and returns when the last box lands. Use `clock: "lift"` or `"spring"` as those rules specify.
- `film.hairline.light(target, at, on)` switches the bright stroke under rule 04.

Follow [Brand guidelines](../../README.md#brand-guidelines) for the figure palette. Plates fill with `--bg`, the lit stroke uses `--emph`, and other strokes mix `--text` into `--bg` at `--stroke` width. Set `--hairline-plate`, `--hairline-hi`, `--hairline-edge`, `--hairline-mid`, `--hairline-lo` or `--hairline-stroke` to override them. A brand that forbids tints sets all four strokes. Set the plate to the panel colour for a figure on a panel.

### Design a Hairline figure

Choose an object that could sit on a desk and carry the scene's idea, such as a rack of blades, a stack of trays or a hub with its tiles. Name and draw the two or three features that make each kind of part recognizable. Let motion show the one number or choice the narration turns on. Write the object, its motion cue and its rest pose in the shot's Visual line.

Rework a concept that is dead at rest, needs a word to be understood, holds two ideas, reduces to boxes joined by arrows or depends on colour. Apply the rest, accent and label constraints in [Hairline rules](#hairline-rules).

### Hairline rules

These are Hairline's ten rules (S-HL-001), adapted for a seeked film. Rule 01 (hit areas) and rule 07 (loops sleep offscreen) govern the pointer and frame loop that the timeline replaces.

- **02 Order.** `ripple` delays each box by `|i − from| × step`, so order the boxes by their distance from the source. Use a `step` of 0.03 to 0.06 s and keep `max(|i − from|) × step` under the clock's duration, so the last box starts before the first lands. For a long row, lower the step or ripple from the middle.
- **03 Reach.** Clamp every lift, gap and lean to keep the extreme pose composed inside the figure's box. Follow [hairline.js](figure-modules/hairline.js) for the `fit(cx, cy, points)` contract and fit remedies. Inspect the extreme pose's still because placement away from the box centre can still cross an edge.
- **04 Accent.** Use the bright stroke as the only highlight. Leave out glows, shadows and colours of the figure's own. One bright mark draws attention at rest and moves to the part a beat selects. The previous mark goes dim, so only one place is bright at a time. A highlight can cover several parts of one thing while marking one place.
- **05 Rest.** Compose the pose the viewer sees first with varied, deliberate values. Avoid zeroed, uniform poses and regular grids.
- **06 Honesty.** Opaque plates paint back to front by their centres, and parts on one centre paint bottom up, so far edges stay behind near solids. Links paint under parts, and a plinth uses `ground`. Intersections or a large part among small ones need `ground` or a split.
- **08 Clocks.** Use the 700 ms lift for a change of state and the spring for a follow. Keep their constants unless the scene has a reason you can state.
- **09 Radius.** Round every corner. Draw a solid as its silhouette, one dim crease and at most a few marks the object would have. Omit vertical corner lines.
- **10 Quiet.** Keep words, digits, arrows and icons outside the figure. Number parts with lid dots and place labels beside it.
- **The frame.** Make the object and its features readable at 480 px, a quarter of the frame's width. Past about a hundred solids, or with parts under ten viewBox units, it will not read.

[Choose a figure style](../../methods/brand-explainer-video.md#figure-styles-are-not-brands) owns conflicts between brand and figure rules, including exceptions. For a brand with no rounded corners, pass `r: 0` to every box to apply its rule instead of rule 09.

### Check a Hairline figure

Inspect the scene's stills at rest and at each beat's landed pose against rules 02, 03, 04, 05, 06, 10 and "The frame" in [Hairline rules](#hairline-rules). Record yes or no for each listed rule, point to the object's visible features and fix every no.

A small lift can fall below `check_film.py`'s frozen-picture threshold. Repair quiet stretches under the [beat rule in step 4](../../methods/prepare-explainer-video.md#4-convert-the-narrative-into-a-scene-and-shot-sequence). In 0.8.145, `hyperframes check` can warn `connector_detached` when a link's ends sit under a part. Read a still before accepting or fixing that warning.

## Motion modules

Register a motion module as `window.FilmMotion["<name>"] = (film) => { ... }` and select it with `startFilm({ motion: "<name>" })`.

The optional stage suits a cast moving through one world under a camera. The plain GSAP `index.html` stays the default. To choose the stage, copy `stage-example.html` over `index.html`, keep its links to `motion-modules/stage.css` and `stage.js`, and replace its scene. `startFilm({ motion: "stage" })` exposes the helpers as `film.stage`, called `S` in the example. See [stage.js](motion-modules/stage.js) for the finish constraint.

Draw each scene in one `<svg class="plate">` in a 1920 × 1080 plate space. [stage.js](motion-modules/stage.js) owns the seek contract, helper arguments, return values, timings and guards. Read that contract before adding motion. [stage.css](motion-modules/stage.css) owns drawing classes and token overrides.

- Use `S.plate(S.svg("s01"), { ground })` to build the scene layers and `S.mount(svg, markup, layer)` to add drawings. `S.core.INK(w)` supplies outlines. See the stylesheet for `f-*`, `h-*` and `t-*`, the hues `emph`, `text`, `dim`, `good`, `bad` and `wait`, and `--stage-ink`, `--stage-good`, `--stage-bad` and `--stage-wait`.
- Use `S.text`, `S.mono`, `S.caps` and `S.display` to draw text, `S.type` to type it and `S.setText` to replace it.
- Use `S.ride` to move a placed figure or prop along points, `S.place` to jump it and `S.at(id, t)` to query its position. The source defines the `<id>-at` and `<id>` groups.
- Use `show`, `hide`, `fade`, `drop`, `slide`, `slideOut`, `move`, `stamp`, `popIn`, `popOut`, `pulse`, `squash`, `wobble`, `turn`, `spin`, `scale`, `attr`, `draw`, `trace`, `blink`, `light`, `lightRun` and `cls` for individual motion and state changes.
- Use `S.cam(scene, at, { x, y, w })` or `"wide"` to reframe the camera. `S.limitIn(frame)` applies [Caption layout](#caption-layout) to that framing. `S.enter(scene)` handles cuts and `S.shake` moves the picture. See the source for `S.loop` intervals and the cast's `S.idle`.
- Use `S.figure(id, x, y)` for the built-in character and `S.pose`, `S.rest`, `S.look`, `S.face`, `S.eyes`, `S.walk`, `S.hand(id, at)` and `S.carry(id, prop, points, t0, t1)` to act it out. For another character, copy `S.figure` and its rig in `stage.js` and redraw the body while keeping its part IDs and joints.
- Use `S.parcel`, `S.envelope`, `S.card` and `S.verdict` for props. See the source for prop IDs and hand placement.
- Use `S.sfx(name, at)` for explicit sound cues. [scripts/README.md](../../scripts/README.md#audio) lists the capture and synthesis tools.

## Check

Run `hyperframes check`, then follow [M5 of templates/production-prompt.md](../production-prompt.md) for rendering and checking the MP4 under the HyperFrames preflight traps in [methods/renderer-traps.md](../../methods/renderer-traps.md).
