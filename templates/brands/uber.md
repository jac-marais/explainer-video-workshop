# Uber-inspired — video style preset

Status: workshop preset, revision 2 (2026-10-03). This is an original workshop style that borrows the spirit of Uber's public identity: black and white, plain words, and the circle, line and square that JKR describes. It is **not** Uber's brand, it is not endorsed by Uber, and it uses no Uber wordmark, logo, app icon, typeface or trade dress. Name it "Uber-inspired" wherever a viewer can see the name.

This file is self-contained: a video agent can build a 1920×1080 explainer from it alone. The CSS block in "Tokens" is the exact token set. Copy it into the run's `tokens.css` unchanged. The reference implementation is `outputs/explainer-about-explainers-uber/production/` (git-ignored run output): `src/tokens.css`, plus the shape rules in `src/composition.html` (`<style id="brand-layout">`).

Value labels used below: **source** = read on a public page (see Provenance); **observed** = seen in the public login page of Uber's brand portal (implementation values, not guideline text); **adapted** = a workshop choice built on a source or observed value; **workshop** = a workshop choice with no source value; **unverified** = believed true but not confirmed in a source read for this revision.

## Character

- **Feel:** a calm, confident product interface. White canvas, black ink, big bold headlines, light gray panels, one black block per scene. It looks like a well-made app screen, not a poster and not a diagram.
- **Geometry is functional.** Circle, line and square appear only where they carry meaning, at UI scale: a filled circle marks a start, a filled square marks an end, a straight line joins two things that are really connected. Never use them as ornament or as a theme.
- **Avoid:** gradients, shadows, glows, an accent hue, decorative icons, emoji, maps, pins, cars, journey or "route" metaphors in layout or words, outline circles around text, rings around dots, bounce or overshoot, column grids drawn on screen, and any Uber wordmark, logo, app icon or the Uber Move typeface.

## Color

Light theme, black and white. No accent hue: emphasis is black weight, a black fill or a black outline.

| Token | Hex | Role | Basis |
|---|---|---|---|
| `--bg` | `#ffffff` | canvas | workshop (black-and-white character) |
| `--layer` | `#f3f3f3` | panels, cards, tiles, chips: a fill, never a border | workshop |
| `--layer-hi` | `#e8e8e8` | raised or selected layer (defined, not used in the reference video) | observed (portal tertiary button gray) |
| `--line` | `#000000` | connector lines, the terminal's header rule | observed (portal black), adapted role |
| `--line-faint` | `#e8e8e8` | faint rules (defined, not used in the reference video) | observed, adapted role |
| `--text` | `#000000` | primary text | observed (portal body text) |
| `--text-2` | `#545454` | secondary text, labels, step captions | workshop |
| `--text-on-emph` | `#ffffff` | text and ticks on black | observed (portal primary button text) |
| `--emph` | `#000000` | the "selected" outline, the agent's question line (with weight 600) | workshop (no accent hue; the portal's link blue `#276ef1` was used in revision 1 and dropped) |
| `--emph-fill` | `#000000` | the one black block per scene, the start and end markers, the end card | observed (portal primary button fill), adapted role |
| `--ok` | `#05944f` | success tick (always a glyph) | workshop, **unverified** as an Uber value |
| `--warn` | `#ffc043` | warning, only on black (defined, not used in the reference video) | workshop, **unverified** |
| `--err` | `#e11900` | error (defined, not used in the reference video) | workshop, **unverified** |
| `--data-1` … `--data-5` | `#000000`, `#1f5fd9`, `#05944f`, `#7356bf`, `#545454` | identity colors for charts only (defined; the reference video hides card color edges) | workshop |
| `--caption-bg` | `rgba(255, 255, 255, 0.92)` | caption backing (`--bg` at 92 %) | workshop |

Rules:

- **One black block per scene.** `--emph-fill` marks the subject or the chosen item (the skill, the chosen style, the end card). Everything else is a gray fill or plain text.
- **Selected = black outline.** A 4 px black outline around a gray panel marks "current" or "selected", the way a chosen option looks in a product UI. The outline follows the panel's shape and radius.
- **Status needs a glyph.** A tick, cross or word carries the meaning; color only reinforces it.
- **No color on color.** Text sits on `--bg`, `--layer` or black only.

### Contrast (computed)

WCAG 2.x relative-luminance ratios, computed from the hex values above (2026-10-03). Text needs 4.5:1; large text (≥ 24 px at 1080p here) and meaningful graphics need 3:1.

| Foreground | Background | Ratio | Use | Result |
|---|---|---:|---|---|
| `--text` #000000 | `--bg` #ffffff | 21.00 | body, headings | pass |
| `--text` #000000 | `--layer` #f3f3f3 | 18.93 | text in panels, the question line | pass |
| `--text` #000000 | `--layer-hi` #e8e8e8 | 17.14 | text on raised layer | pass |
| `--text` #000000 | caption backing over `--layer` (#fefefe) | 20.82 | captions, worst case | pass |
| `--text-2` #545454 | `--bg` #ffffff | 7.57 | labels, step captions | pass |
| `--text-2` #545454 | `--layer` #f3f3f3 | 6.82 | labels in panels | pass |
| `--text-on-emph` #ffffff | `--emph-fill` #000000 | 21.00 | text on black blocks and the end card | pass |
| `--text-on-emph` #ffffff | end card mid-fade (#262626, black at 85 % when its caption starts) | 15.13 | end-card caption, worst case | pass |
| `--emph` #000000 | `--layer` #f3f3f3 | 18.93 | selected outline | pass (3:1) |
| `--line` #000000 | `--bg` #ffffff | 21.00 | connectors, markers | pass (3:1) |
| `--ok` #05944f | `--layer` #f3f3f3 | 3.53 | tick on a panel | pass (3:1) |
| `--ok` #05944f | `--bg` #ffffff | 3.92 | tick on the canvas | pass (3:1) |
| `--err` #e11900 | `--bg` #ffffff | 4.84 | error glyph | pass |
| `--warn` #ffc043 | `--emph-fill` #000000 | 12.87 | warning glyph, on black only | pass; **never on white (1.63)** |
| `--layer` #f3f3f3 | `--bg` #ffffff | 1.11 | panel fill | **decorative only.** A panel's text names it; the fill is never the only cue |

## Typography

Uber's own typeface, Uber Move, is proprietary (observed as the portal's font; not licensed for this workshop). The substitutes are open:

- **Inter Tight** (SIL OFL 1.1), a tightly spaced neo-grotesque, for all text. It is a substitute chosen for its compact, upright, neutral shapes, not a match.
- **JetBrains Mono** (SIL OFL 1.1) for terminal text and file names only.

Load them from local variable `ttf` files with `@font-face` (weight ranges). Fallbacks are generic `sans-serif` and `monospace` only, so a missing file shows up as an obvious fallback in stills.

| Role | Family | Size at 1080p | Weight | Line height | Tracking | Case | Basis |
|---|---|---:|---:|---:|---:|---|---|
| Display (title, end card) | Inter Tight | 120 px | 700 | 1.05 | −0.03 em | sentence | workshop |
| H1 (scene head, the S01 start/end row) | Inter Tight | 80 px | 700 | 1.05 | −0.03 em | sentence | workshop |
| H2 (step names, box names) | Inter Tight | 48 px | 500 | 1.1 | 0 | sentence | workshop |
| Body (field values, card names) | Inter Tight | 36 px | 500 | 1.4 (1.2–1.3 in tight boxes) | 0 | sentence | workshop |
| Caption | Inter Tight | 36 px | 500 | 1.35 | 0 | sentence | workshop |
| Label / eyebrow | Inter Tight | 30 px | 600 | 1.2 | 0 | sentence | workshop |
| Code / terminal | JetBrains Mono | 32 px | 500 (600 for the agent's question) | 48 px | 0 | as typed | workshop |

Hierarchy comes from size and weight, never color: a small semibold gray eyebrow (`Step 1`), a big bold black headline, then content. Labels are sans, not mono, and never uppercase. Never use italic. Nothing on screen is smaller than 30 px.

## Layout

- Canvas 1920×1080. Base unit `--u` = 30 px; positions and sizes are multiples of 30 px. Side margins 120 px. (All **workshop**; no Uber grid was readable.)
- Caption zone: the bottom band from y = 900 to 1020 px, inset by the margins. No content enters it.
- Scene head at the top left (eyebrow y = 90 px, headline y = 135 px). Content sits between y ≈ 270 and 870 px, left-aligned, read left to right. Center a single row of content on y ≈ 540 px.
- Panels are gray fills with an 8 px radius and no border. Sequences are rows of equal gray cards joined by straight black lines, with no arrowheads.
- A start-to-end statement (topic to video) is one row at H1 size: filled circle + word, a straight line, filled square + word. Markers are 36 px, vertically centered on the word, and the line keeps at least one unit (30 px) of space from each word and marker. Nothing touches.
- Leave space, but do not leave a single small element alone in a large empty area: scale it up to H1 or move it to the optical center.
- The end card is full-bleed black with white type.

## Visual language

- **Circle = start, square = end, line = connection.** Filled black, never outlined, used only in the start-to-end row and nowhere else. Do not repeat them as stops along a process.
- **Shape pairing rules (learned in revision 1):** never put an outline ring around a circle or dot; never let a line run into a circle's edge; never mix an outline circle with a filled square in one row; never draw dots on a branching line. A selection outline goes only around a rectangle with the same radius.
- One black block per scene for the subject. A black outline marks the current card.
- Terminal panels: a gray panel, a sans label bar with a black rule under it, mono text, the agent's question in weight 600.
- Ticks in `--ok` on completed cards.
- No logos, maps, vehicles, pins, photographs, illustrations or icons beyond ticks and the two markers.

## Motion

| Token | Value | Use | Basis |
|---|---|---|---|
| `--ease-standard` | `cubic-bezier(0.65, 0, 0.35, 1)` | lines growing, color changes, fades | workshop (ease-in-out) |
| `--ease-entrance` | `cubic-bezier(0.22, 1, 0.36, 1)` | panels and text arriving | workshop (strong ease-out, no overshoot) |
| `--ease-exit` | `cubic-bezier(0.55, 0, 1, 0.45)` | elements leaving | workshop |
| `--ease-expressive` | `cubic-bezier(0.16, 1, 0.3, 1)` | title and end card only | workshop |
| `--dur-fast` | 200 ms | ticks, outlines, exits | workshop |
| `--dur-base` | 450 ms | panels, cards, the end-card fade | workshop |
| `--dur-slow` | 900 ms | titles, the start-to-end line | workshop |
| `--stagger` | 100 ms | delay between items in a sequence | workshop |

Rules: every element arrives on the narration cue that names it, with a short slide and fade. Lines grow from the thing they leave. The current card gets the black outline; when the sequence moves on, the outline leaves and a tick appears. The end card is one black fade, not a wipe or a column sweep. Nothing loops, bounces, spins or pulses. Each scene fades out over `--dur-fast` before the next begins. Easing and durations are read from these tokens at run time, never typed into scene code. No Uber motion guidance was readable; every motion value is a workshop choice.

## Narration voice

This style talks the way a confident product company talks to a busy person:

- **Plain and direct.** Everyday words ("finds", "gives you", "tests", "checks"). Say what happens and who does it. Second person, present tense.
- **Few words.** One idea per sentence; cut every word that does not change the meaning. No setup phrases ("Let's take a look at…").
- **Confident, not loud.** No hype, superlatives, exclamation marks or rhetorical questions.

Example (reference video, S03): "Then give it a topic and an audience. The prepare skill finds sources, and gives you a sourced script, a scene plan, a renderer choice, and a production prompt."

The reference video used local Kokoro `af_heart` at speed 0.92 (workshop choice) and measured 106 words in 42.7 s including pauses.

## Accessibility

- Burned-in captions on every spoken sentence, in the caption zone, 36 px black on `--caption-bg`; on the black end card, white with no backing. Balanced line breaks, at most two lines; also ship `captions.vtt`.
- All text pairs above pass 4.5:1; the lowest text pair is 6.82:1 (gray labels on a panel).
- Meaning never depends on color alone: status uses ticks, the current card uses an outline, the chosen item is a black block with its name in it.
- Minimum on-screen text 30 px at 1080p. Hold every text element on screen for at least the length of the sentence that introduces it.
- No flashing, looping or strobing motion.

## Tokens

```css
@font-face { font-family: "Inter Tight"; font-weight: 100 900; src: url("fonts/InterTight-VF.ttf") format("truetype"); }
@font-face { font-family: "JetBrains Mono"; font-weight: 100 800; src: url("fonts/JetBrainsMono-VF.ttf") format("truetype"); }
:root {
  /* color: background (white canvas, black ink) */
  --bg: #ffffff;          /* canvas */
  --layer: #f3f3f3;       /* panels, cards, tiles, chips (fill only, no border) */
  --layer-hi: #e8e8e8;    /* raised or selected layer */
  --line: #000000;        /* connector lines */
  --line-faint: #e8e8e8;  /* faint rules */
  /* color: text */
  --text: #000000;        /* primary text */
  --text-2: #545454;      /* secondary text, labels */
  --text-on-emph: #ffffff;
  /* color: emphasis (black; no accent hue) */
  --emph: #000000;        /* selection outline, the agent's question, emphasis text */
  --emph-fill: #000000;   /* the one solid black block per scene, start and end markers, end card */
  /* color: status (always paired with a glyph or word) */
  --ok: #05944f;
  --warn: #ffc043;
  --err: #e11900;
  /* color: data (identity only, never the sole carrier of meaning) */
  --data-1: #000000;
  --data-2: #1f5fd9;
  --data-3: #05944f;
  --data-4: #7356bf;
  --data-5: #545454;
  /* fonts and weights */
  --font-sans: "Inter Tight", sans-serif;
  --font-mono: "JetBrains Mono", monospace;
  --w-light: 400;
  --w-regular: 500;
  --w-strong: 600;
  /* type scale at 1920x1080 */
  --fs-display: 120px;
  --fs-h1: 80px;
  --fs-h2: 48px;
  --fs-body: 36px;
  --fs-label: 30px;
  --fs-code: 32px;
  --fs-caption: 36px;
  --lh-display: 1.05;
  --lh-body: 1.4;
  --ls-display: -0.03em;
  --ls-label: 0em;
  --label-case: none;
  --w-display: 700;
  --w-heading: 700;
  /* grid: 30px unit, 8 columns of 240px, 120px side margins */
  --u: 30px;
  --cols: 8;
  --col: 240px;
  --margin: 120px;
  --gutter: 30px;
  --caption-bottom: 60px;
  --caption-h: 120px;
  /* surface */
  --radius: 8px;
  --stroke: 4px;
  --caption-bg: rgba(255, 255, 255, 0.92);
  /* motion: calm ease-out arrivals, in-out for lines and color changes */
  --ease-standard: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-entrance: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-exit: cubic-bezier(0.55, 0, 1, 0.45);
  --ease-expressive: cubic-bezier(0.16, 1, 0.3, 1);
  --dur-fast: 200ms;
  --dur-base: 450ms;
  --dur-slow: 900ms;
  --stagger: 100ms;
}
```

`--gutter`, `--cols`, `--layer-hi`, `--line-faint`, `--warn`, `--err`, `--data-1`…`--data-5` and `--w-light` are defined for layouts that need them; the reference video uses none of them.

Shape rules (the start circle and end square, hidden arrowheads and column guides, hidden card color edges, sans labels, the outline radius, the black end card) are layout, not tokens. The reference run keeps them in one `<style id="brand-layout">` block in `composition.html` that uses only these tokens.

## Assets and licenses

| Asset | Where to get it | License | Video use |
|---|---|---|---|
| Inter Tight, variable (`InterTight[wght].ttf`) | `github.com/google/fonts`, `ofl/intertight` (fetched 2026-10-03) | SIL OFL 1.1 | allowed; embed or render freely; do not sell the font files alone |
| JetBrains Mono, variable (`JetBrainsMono[wght].ttf`) | `github.com/google/fonts`, `ofl/jetbrainsmono` (fetched 2026-10-03) | SIL OFL 1.1 | as above |

Ship each `OFL.txt` beside the font files. No other assets are needed. No Uber wordmark, logo, app icon, Uber Move font file, photograph or map may be used.

## Provenance

Read on 2026-10-03 (direct `curl` of public pages; text read, not just search results):

- JKR, "Uber" case study (`https://www.jkrglobal.com/work/uber`). Read: "Go Anywhere. Get Anything."; the brand "needed to evolve" so that Uber could "grow beyond delivery into a business that enables all mobility"; "Cue the circle, line, square. We began with three simple icons, that set a world of possibilities in motion. By connecting them in bold, energetic, yet radically straightforward ways, we were able to unify a collection of disparate apps". The page text gives no colors, typefaces, motion or layout values and no year. The year 2024 and the reading "movement, journeys, connections and destinations" come from earlier workshop research and are **unverified** here.
- Uber brand portal (`https://brand.uber.com/`, redirects to `https://assets.uber.com/`, a Frontify site). The guidelines need a login and were **not inspectable**. Only the public login shell's theme settings were seen: font family "Uber Move", black `rgb(0,0,0)` text and primary buttons with white text, link blue `rgb(39,110,241)` (`#276ef1`), tertiary gray `rgb(232,232,232)` (`#e8e8e8`), 8 px button radius. These are **observed** implementation values of the portal page, not documented brand rules.
- Fonts: OFL texts read from the Google Fonts repository folders listed above.

Workshop adaptations, not from any Uber source: the white canvas, every color role, `--layer`, `--text-2`, the status and data colors, the type scale, weights and tracking, the 30 px grid and margins, the caption zone, every easing and duration, the start-to-end row, the black end card, the shape pairing rules, the narration voice and the accessibility rules. The 8 px panel radius follows the portal's observed button radius. Contrast ratios are computed by the workshop from the hex values.

Not checked: Uber's actual brand guidelines (behind a login), its color palette, motion, photography and voice rules, and the Base design system. If you need closer fidelity, get access to the portal, read those first, and revise this file.

Revision history:

- 1 (2026-10-03) first version. Drew every process as a route of stops (outline circles, rings around stops, a square destination), used a blue accent, and worded the narration as a trip ("route", "first stop", "last stop"). The user rejected it: rings on dots looked wrong, the whole felt off, and the trip wording was a pun, not a voice.
- 2 (2026-10-03) circle, line and square limited to one start-to-end row; process scenes became gray cards with a black selection outline; no accent hue; black end card; 8 px radius; a Narration voice section that defines tone and forbids theme puns; shape pairing rules. Reference video `outputs/explainer-about-explainers-uber`.
