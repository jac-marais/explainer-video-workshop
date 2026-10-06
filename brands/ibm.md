# IBM-inspired — video style preset

Status: workshop preset, revision 1 (2026-10-03). This is an original workshop style that borrows the look of IBM's public design language. It is **not** IBM's brand, it is not endorsed by IBM, and it uses no IBM logo, mark or trade dress beyond the openly licensed IBM Plex typefaces. Name it "IBM-inspired" wherever a viewer can see the name.

This file is self-contained: a video agent can build a 1920×1080 explainer from it alone. The CSS block in "Tokens" is the exact token set. Copy it into the run's `tokens.css` unchanged. The reference implementation is `outputs/explainer-about-explainers/production/src/tokens.css` (git-ignored run output).

Value labels used below: **source** = read on a public IBM or Carbon page (see Provenance); **adapted** = a workshop choice built on a source value; **workshop** = a workshop choice with no source value; **unverified** = believed true but not checked against a source in this revision.

## Character

- **Feel:** engineered, calm, precise. Dark canvas, flat rectangles, one blue, light large type, monospace labels. Diagrams look like system drawings: boxes, straight rules, right angles.
- **Avoid:** gradients, shadows, glows, rounded corners, emoji, decorative icons, stock imagery, more than one accent meaning, centered "poster" layouts, playful bounce or overshoot, text on top of busy fills, any IBM logo or 8-bar mark.

## Color

Dark theme only. Every hex below is used as given; no tints are derived except the caption backing (alpha).

| Token | Hex | Role | Basis |
|---|---|---|---|
| `--bg` | `#161616` | canvas | source value, adapted role |
| `--layer` | `#262626` | panels, cards, tiles | source value, adapted role |
| `--layer-hi` | `#393939` | raised or selected layer (defined, not used in the reference video) | source value, adapted role |
| `--line` | `#525252` | panel borders, connectors, rules | source value, adapted role |
| `--line-faint` | `#393939` | column guides | source value, adapted role |
| `--text` | `#f4f4f4` | primary text | source value, adapted role |
| `--text-2` | `#c6c6c6` | secondary text, labels | source value, adapted role |
| `--text-on-emph` | `#ffffff` | text on the emphasis fill | workshop |
| `--emph` | `#78a9ff` | emphasis text, active rings, active connectors and arrowheads | source value, adapted role |
| `--emph-fill` | `#0f62fe` | emphasis fill (the one solid blue block per scene) | source value, adapted role |
| `--ok` | `#42be65` | success tick (always a glyph, never color alone) | source value, adapted role |
| `--warn` | `#f1c21b` | warning (defined, not used in the reference video) | source value, adapted role |
| `--err` | `#fa4d56` | error (defined, not used in the reference video) | source value, adapted role |
| `--data-1` | `#78a9ff` | identity color 1 (card edge) | source value, adapted role |
| `--data-2` | `#3ddbd9` | identity color 2 | source value, adapted role |
| `--data-3` | `#be95ff` | identity color 3 | source value, adapted role |
| `--data-4` | `#ff7eb6` | identity color 4 | source value, adapted role |
| `--data-5` | `#c6c6c6` | identity color 5 (defined, not used in the reference video) | source value, adapted role |
| `--caption-bg` | `rgba(22, 22, 22, 0.92)` | caption backing (`--bg` at 92 %) | workshop |

Rules:

- **One meaning for blue.** `--emph`/`--emph-fill` mean "look here now". Use one filled blue block per scene at most.
- **Status needs a glyph.** A tick, cross or word carries the meaning; color only reinforces it.
- **Data colors identify, never rank.** Use them as a thin edge or swatch, not as text color for body copy, and never as the only way to tell items apart.
- **No color on color.** Text sits on `--bg`, `--layer` or `--emph-fill` only.

### Contrast (computed)

WCAG 2.x relative-luminance ratios, computed from the hex values above (2026-10-03). Text needs 4.5:1; large text (≥ 24 px at 1080p here) and meaningful graphics need 3:1.

| Foreground | Background | Ratio | Use | Result |
|---|---|---:|---|---|
| `--text` #f4f4f4 | `--bg` #161616 | 16.45 | body, headings | pass |
| `--text` #f4f4f4 | `--layer` #262626 | 13.76 | text in panels | pass |
| `--text` #f4f4f4 | `--layer-hi` #393939 | 10.50 | text on raised layer | pass |
| `--text` #f4f4f4 | caption backing over `--layer` (#171717) | 16.30 | captions, worst case | pass |
| `--text-2` #c6c6c6 | `--bg` #161616 | 10.59 | labels | pass |
| `--text-2` #c6c6c6 | `--layer` #262626 | 8.86 | labels in panels | pass |
| `--emph` #78a9ff | `--bg` #161616 | 7.68 | emphasis text, rules | pass |
| `--emph` #78a9ff | `--layer` #262626 | 6.43 | emphasis text in panels | pass |
| `--text-on-emph` #ffffff | `--emph-fill` #0f62fe | 5.00 | text on the blue block | pass |
| `--emph-fill` #0f62fe | `--bg` #161616 | 3.62 | blue block edge (graphic) | pass (3:1) |
| `--ok` #42be65 | `--layer` #262626 | 6.33 | tick glyph | pass |
| `--warn` #f1c21b | `--bg` #161616 | 10.75 | warning glyph | pass |
| `--err` #fa4d56 | `--bg` #161616 | 5.40 | error glyph | pass |
| `--data-2` #3ddbd9 | `--layer` #262626 | 8.89 | identity edge | pass (3:1) |
| `--data-3` #be95ff | `--layer` #262626 | 6.44 | identity edge | pass (3:1) |
| `--data-4` #ff7eb6 | `--layer` #262626 | 6.42 | identity edge | pass (3:1) |
| `--line` #525252 | `--bg` #161616 | 2.32 | panel border | **below 3:1: decorative only.** A border must never be the only cue; the panel's text names it |
| `--line-faint` #393939 | `--bg` #161616 | 1.57 | column guides | decorative only |

## Typography

Families: **IBM Plex Sans** and **IBM Plex Mono**, SIL Open Font License 1.1 (Reserved Font Name "Plex"). Load them from local `woff2` files with `@font-face`; do not rely on system fonts. Fallbacks are generic `sans-serif` and `monospace` only, so a missing file shows up as an obvious fallback in stills.

| Role | Family | Size at 1080p | Weight | Line height | Tracking | Case | Basis |
|---|---|---:|---:|---:|---:|---|---|
| Display (title, end card) | Sans | 108 px | 300 Light | 1.1 | −0.01 em | sentence | adapted |
| H1 (scene head) | Sans | 72 px | 400 | 1.1 | −0.01 em | sentence | adapted |
| H2 (box names, step names) | Sans | 48 px | 400 | 1.1 | 0 | sentence | workshop |
| Body (field values, card names) | Sans | 36 px | 400 | 1.4 (1.2–1.3 in tight boxes) | 0 | sentence | workshop |
| Caption | Sans | 36 px | 400 | 1.35 | 0 | sentence | workshop |
| Label / eyebrow | Mono | 30 px | 400 | 1.2 | +0.04 em | UPPERCASE | workshop |
| Code / terminal | Mono | 32 px | 400 | 48 px | 0 | as typed | workshop |

Hierarchy: an eyebrow label (`STEP 1`) over a light or regular headline, then content. Size and weight carry hierarchy; color does not. Weight 600 (Sans SemiBold) and Mono 500 are loaded for rare strong emphasis; the reference video does not use them. Never use italic, all-caps Sans, or weights above 600. Nothing on screen is smaller than 30 px.

## Layout

The video grid adapts IBM's "2x Grid for video".

- Canvas 1920×1080. Base unit `--u` = 30 px; every position and size is a multiple of 30 px (a half unit, 15 px, only for optical centring). Source: the 2x Grid page gives a 7.5 px mini unit, 30 px increments and 8 columns for 1920×1080.
- 8 columns of 240 px over the full canvas (source: 8 columns; adapted: no gutters, which the page allows as optional).
- Outer margin `--margin` 120 px (half a column) on left and right (**workshop**: the source page gives no video margin).
- Caption zone: the bottom band from y = 900 to 1020 px (`--caption-bottom` 60 px, `--caption-h` 120 px), inset by the margins. No content enters it.
- Scene head at the top left: eyebrow at y = 90 px, headline at y = 135 px. Content sits between y ≈ 270 and 870 px, left-aligned to the margin; it reads left to right.
- Asymmetric and left-aligned. Do not center titles. Leave the right side empty rather than stretching content to fill it.

## Visual language

- Flat rectangles with a 3 px `--line` border on `--layer`; 0 radius.
- Straight 3 px rules for connections; the active path is `--emph` and ends in a solid triangular arrowhead.
- One filled `--emph-fill` block per scene marks the subject (the product, the active step, the chosen option).
- A 3 px `--emph` outline ring marks "current" or "selected".
- Column guides (2 px, `--line-faint`) may fade in on title and end cards to show the grid; never behind dense content.
- Terminal panels: a mono label bar, mono text, prompt lines in `--emph`.
- Numbers as mono labels (`01`, `02`) for steps; ticks in `--ok` for completed checks.
- No logos, photographs, illustrations or icons beyond ticks and arrowheads.

## Motion

| Token | Value | Use | Basis |
|---|---|---|---|
| `--ease-standard` | `cubic-bezier(0.2, 0, 0.38, 0.9)` | rules growing, color changes, fades | source (Carbon productive standard) |
| `--ease-entrance` | `cubic-bezier(0, 0, 0.38, 0.9)` | elements entering | source (Carbon productive entrance) |
| `--ease-exit` | `cubic-bezier(0.2, 0, 1, 0.9)` | elements leaving | source (Carbon productive exit) |
| `--ease-expressive` | `cubic-bezier(0, 0, 0.3, 1)` | title and end card only | source (Carbon expressive entrance) |
| `--dur-fast` | 240 ms | small elements, rings, exits | source (Carbon moderate-02) |
| `--dur-base` | 400 ms | panels, cards | source (Carbon slow-01) |
| `--dur-slow` | 700 ms | titles, long rules | source (Carbon slow-02) |
| `--stagger` | 120 ms | delay between items in a sequence | workshop |

Rules: every element enters on the narration cue that names it (sequential reveal), with a 12–36 px slide toward its resting place plus a fade. Connectors draw from their origin. Items in a list stagger. Nothing loops, bounces, spins or pulses. Each scene fades out over `--dur-fast` with `--ease-exit` just before the next one begins; there are no wipes or zooms. Easing and durations are read from these tokens at run time, never typed into scene code.

## Narration voice

Plain, confident, second person ("you"), present tense. Short declarative sentences, one idea each. No hype words, no rhetorical questions, no colons or dashes in spoken text, no "X, not Y" constructions. Name the thing, then show it. The reference video used local Kokoro `af_heart` at speed 0.92 (workshop choice; any calm neutral voice fits). The reference measured about 148 words per minute overall (105 words in 42.7 s, including a 1.2 s pause between scenes); aim for 140–150.

## Accessibility

- Burned-in captions on every spoken sentence, in the caption zone, 36 px, on `--caption-bg`, balanced line breaks, at most two lines; also ship `captions.vtt`.
- All text-on-background pairs above pass 4.5:1; the lowest text pair is 5.00:1 (white on the blue block).
- Meaning never depends on color alone: status uses ticks, selection uses an outline ring, identity colors are paired with names.
- Minimum on-screen text 30 px at 1080p. Hold every text element on screen for at least the length of the sentence that introduces it.
- No flashing, looping or strobing motion.

## Tokens

```css
@font-face { font-family: "IBM Plex Sans"; font-weight: 300; src: url("fonts/IBMPlexSans-Light.woff2") format("woff2"); }
@font-face { font-family: "IBM Plex Sans"; font-weight: 400; src: url("fonts/IBMPlexSans-Regular.woff2") format("woff2"); }
@font-face { font-family: "IBM Plex Sans"; font-weight: 600; src: url("fonts/IBMPlexSans-SemiBold.woff2") format("woff2"); }
@font-face { font-family: "IBM Plex Mono"; font-weight: 400; src: url("fonts/IBMPlexMono-Regular.woff2") format("woff2"); }
@font-face { font-family: "IBM Plex Mono"; font-weight: 500; src: url("fonts/IBMPlexMono-Medium.woff2") format("woff2"); }
:root {
  --bg: #161616; --layer: #262626; --layer-hi: #393939; --line: #525252; --line-faint: #393939;
  --text: #f4f4f4; --text-2: #c6c6c6; --text-on-emph: #ffffff;
  --emph: #78a9ff; --emph-fill: #0f62fe;
  --ok: #42be65; --warn: #f1c21b; --err: #fa4d56;
  --data-1: #78a9ff; --data-2: #3ddbd9; --data-3: #be95ff; --data-4: #ff7eb6; --data-5: #c6c6c6;
  --font-sans: "IBM Plex Sans", sans-serif; --font-mono: "IBM Plex Mono", monospace;
  --w-light: 300; --w-regular: 400; --w-strong: 600;
  --fs-display: 108px; --fs-h1: 72px; --fs-h2: 48px; --fs-body: 36px; --fs-label: 30px; --fs-code: 32px; --fs-caption: 36px;
  --lh-display: 1.1; --lh-body: 1.4; --ls-display: -0.01em; --ls-label: 0.04em; --label-case: uppercase;
  --w-display: var(--w-light); --w-heading: var(--w-regular);
  --u: 30px; --cols: 8; --col: 240px; --margin: 120px; --gutter: 30px; --caption-bottom: 60px; --caption-h: 120px;
  --radius: 0px; --stroke: 3px; --caption-bg: rgba(22, 22, 22, 0.92);
  --ease-standard: cubic-bezier(0.2, 0, 0.38, 0.9); --ease-entrance: cubic-bezier(0, 0, 0.38, 0.9);
  --ease-exit: cubic-bezier(0.2, 0, 1, 0.9); --ease-expressive: cubic-bezier(0, 0, 0.3, 1);
  --dur-fast: 240ms; --dur-base: 400ms; --dur-slow: 700ms; --stagger: 120ms;
}
```

`--gutter` and `--cols` are defined for layouts that need them; the reference video uses neither.

## Assets and licenses

| Asset | Where to get it | License | Video use |
|---|---|---|---|
| IBM Plex Sans Light, Regular, SemiBold (`woff2`) | npm `@ibm/plex-sans` 1.1.0 | SIL OFL 1.1, Reserved Font Name "Plex" | allowed; embed or render freely; do not sell the font files alone; a modified font may not be called "Plex" |
| IBM Plex Mono Regular, Medium (`woff2`) | npm `@ibm/plex-mono` 2.5.0 | SIL OFL 1.1, Reserved Font Name "Plex" | as above |

Ship the OFL text beside the font files. No other assets are needed. No IBM logo, 8-bar mark, pictogram or photograph may be used.

## Provenance

Read on 2026-10-03 (direct `curl` of the public pages; text read, not just search results):

- [IBM Design Language, "2x Grid"](https://www.ibm.com/design/language/2x-grid/), section "2x Grid for video": 1920×1080, 7.5 px mini unit, 30 px increments, 8 columns "sufficient for most layouts", 16 optional, snap to 30 px. Gives no video margin.
- [Carbon Design System, "Motion overview"](https://carbondesignsystem.com/elements/motion/overview/): all six productive/expressive curves and the duration set 70/110/150/240/400/700 ms appear on the page.
- [IBM Design Language, "Color"](https://www.ibm.com/design/language/color/): all 14 palette hex values in this file appear in the page source. Note: they were found as values in the page's CSS (observed implementation), so the hex values are confirmed but their palette names (for example "Gray 100" for `#161616`) are **unverified** here and deliberately not used.
- [Carbon "Color tokens"](https://carbondesignsystem.com/elements/color/tokens/): 12 of the 14 values appear; `#262626` and `#3ddbd9` do not appear in the fetched page. (An earlier draft note claimed all appeared there; that was wrong.)
- Fonts: OFL texts read from the npm packages.

Workshop adaptations, not from any IBM source: every color **role**, the type scale and tracking, the 120 px margin, the caption zone, the 120 ms stagger, the choice of which Carbon duration maps to fast/base/slow, the scene fade-out, the "one blue block per scene" rule, the narration voice, and the accessibility rules. Contrast ratios are computed by the workshop from the hex values.

Not checked: IBM's own brand rules for video or motion (the IBM `/design/language/animation/` URL returned 404), IBM's voice and tone guidance, and Carbon's type-scale tokens. If you need closer fidelity, read those first and revise this file.

Revision history: 1 (2026-10-03) first version, written with the reference video `outputs/explainer-about-explainers`.
