# NYCTA-inspired — video style preset

Status: workshop preset, revision 1 (2026-10-03). This is an original workshop style that borrows the method of the 1970 New York City Transit Authority Graphics Standards Manual by Unimark International. It is **not** the MTA's or the NYCTA's brand, it is not endorsed by either, and it uses no MTA logo, no subway route bullet (a colored disc with a line letter or number), no line colors as route identity, and no trademarked symbol. Name it "NYCTA-inspired" wherever a viewer can see the name.

This file is self-contained: a video agent can build a 1920×1080 explainer from it alone. The CSS block in "Tokens" is the exact token set. Copy it into the run's `tokens.css` unchanged. The reference implementation is `outputs/explainer-about-explainers-nycta/production/src/tokens.css` (git-ignored run output).

Value labels used below: **source** = read in the manual scan (see Provenance); **adapted** = a workshop choice built on a source rule or value; **workshop** = a workshop choice with no source value; **unverified** = believed true but not checked against a source in this revision.

## Character

- **Feel:** direct, navigational, and very clear in its hierarchy. Each scene looks like a station sign. White sign plates have a black band on the top edge. Black text uses one medium weight. Heavy black arrows point the way. One orange signal marks "this is the thing to look at".
- **Core rule (source):** "The passenger will be given the information or direction only at the point of decision. Never before. Never after." In video, an item appears on the narration cue that names it. The scene clears before the next scene asks for a new decision.
- **Consistent terms (source: sign glossary):** use one name for each thing in narration, on screen, and in captions. Use positive wording.
- **Avoid:** route bullets or any colored disc with a letter or number, line colors used as identity, MTA marks, gradients, shadows, rounded corners, icons other than arrows and ticks, decoration on the canvas (the manual forbids "painting of tiles, walls"), two-headed or zig-zag arrows (the manual's "how not to use the arrow" page), centered poster layouts, bounce or overshoot.

## Color

Light theme only. The manual specifies black text on a white background for all identification, directional and informational signs, and white letters on colored discs for lines. This preset keeps the black-on-white sign. It does not use discs. One orange (adapted from the PMS 165 swatch) is the only signal color.

| Token | Hex | Role | Basis |
|---|---|---|---|
| `--bg` | `#eeeeea` | canvas (the wall the signs hang on) | workshop |
| `--layer` | `#ffffff` | sign plates: panels, cards, tiles | adapted (source: white sign background) |
| `--layer-hi` | `#e0e0dc` | raised or selected layer (defined, not used in the reference video) | workshop |
| `--line` | `#111111` | plate outline, top band, arrows, connectors | adapted (source: black band, black arrows) |
| `--line-faint` | `#c8c8c4` | faint rules (defined, not used in the reference video) | workshop |
| `--text` | `#111111` | primary text | adapted (source: black text) |
| `--text-2` | `#555555` | secondary text, labels | workshop |
| `--text-on-emph` | `#ffffff` | text on the orange plate and on black bands | workshop |
| `--emph` | `#c03a00` | signal text and the "current" ring | adapted (PMS 165 orange, darkened to pass 4.5:1) |
| `--emph-fill` | `#c03a00` | signal plate (one per scene) | adapted, as above |
| `--ok` | `#00843d` | success tick (always a glyph) | adapted (PMS 354 green, darkened) |
| `--warn` | `#9e6500` | warning glyph (defined, not used) | adapted (PMS 130 yellow, darkened) |
| `--err` | `#a6192e` | error glyph (defined, not used) | adapted (PMS 185 red, darkened) |
| `--data-1` | `#005eb8` | identity edge 1 | adapted (PMS 300 blue, unverified sRGB) |
| `--data-2` | `#b5179e` | identity edge 2 | adapted (PMS 239 magenta, darkened) |
| `--data-3` | `#00843d` | identity edge 3 | adapted (PMS 354 green, darkened) |
| `--data-4` | `#111111` | identity edge 4 | adapted (PMS black) |
| `--data-5` | `#9e6500` | identity edge 5 (defined, not used) | adapted (PMS 130 yellow, darkened) |
| `--caption-bg` | `rgba(17, 17, 17, 0.94)` | caption plate (black) | workshop |
| `--caption-text` | `#ffffff` | caption text | workshop |

The manual names its swatches by PMS number only (PMS 185 red, 312 blue, 239 magenta, 130 yellow, 165 orange, 300 blue, 354 green, black). It gives no sRGB values. The hex values are workshop conversions (**unverified** against Pantone's own sRGB values). Most are darkened so that they pass contrast on white.

Rules:

- **One signal.** Orange means "look here now": one orange plate per scene, an orange ring for the current option, and orange text for the question being asked. Direction is always black.
- **Status needs a glyph.** A tick, cross or word carries the meaning. Color only reinforces it.
- **Identity colors are thin edges, never discs.** Each one sits beside a name. They never carry a line letter or number.
- **No color on color.** Text sits on `--bg`, `--layer`, `--emph-fill` or a black band only.

### Contrast (computed)

WCAG 2.x relative-luminance ratios, computed from the hex values above (2026-10-03). Text needs 4.5:1. Large text (≥ 24 px at 1080p here) and meaningful graphics need 3:1.

| Foreground | Background | Ratio | Use | Result |
|---|---|---:|---|---|
| `--text` #111111 | `--bg` #eeeeea | 16.23 | headings, body | pass |
| `--text` #111111 | `--layer` #ffffff | 18.88 | text on plates | pass |
| `--text` #111111 | `--layer-hi` #e0e0dc | 14.27 | text on raised layer | pass |
| `--caption-text` #ffffff | caption plate over white (#1f1f1f) | 16.48 | captions, worst case | pass |
| `--text-on-emph` #ffffff | `--line` #111111 | 18.88 | label in a black band | pass |
| `--text-2` #555555 | `--bg` #eeeeea | 6.41 | labels | pass |
| `--text-2` #555555 | `--layer` #ffffff | 7.46 | labels on plates | pass |
| `--emph` #c03a00 | `--bg` #eeeeea | 4.69 | signal text | pass |
| `--emph` #c03a00 | `--layer` #ffffff | 5.46 | signal text on plates, ring | pass |
| `--text-on-emph` #ffffff | `--emph-fill` #c03a00 | 5.46 | text on the orange plate | pass |
| `--line` #111111 | `--emph-fill` #c03a00 | 3.46 | black band on the orange plate (graphic) | pass (3:1) |
| `--line` #111111 | `--bg` #eeeeea | 16.23 | plate outline, arrows | pass |
| `--ok` #00843d | `--layer` #ffffff | 4.81 | tick glyph | pass |
| `--warn` #9e6500 | `--bg` #eeeeea | 4.18 | warning glyph (graphic) | pass (3:1) |
| `--warn` #9e6500 | `--layer` #ffffff | 4.87 | warning glyph | pass |
| `--err` #a6192e | `--bg` #eeeeea | 6.45 | error glyph | pass |
| `--data-1` #005eb8 | `--layer` #ffffff | 6.38 | identity edge | pass (3:1) |
| `--data-2` #b5179e | `--layer` #ffffff | 5.86 | identity edge | pass (3:1) |
| `--data-3` #00843d | `--layer` #ffffff | 4.81 | identity edge | pass (3:1) |
| `--line-faint` #c8c8c4 | `--bg` #eeeeea | 1.44 | faint rule | decorative only, never a cue |

## Typography

The manual sets every sign in **Standard Medium** (it gives reproduction alphabets for that face only). Standard Medium and Helvetica are proprietary, so this preset substitutes open fonts:

- **Inter** (SIL OFL 1.1) for everything a sign would carry: headings, body, labels, captions. It is a neo-grotesque that is close in spirit to Standard Medium and Helvetica. It is not a metric or glyph match. Use one weight, 500 Medium, which follows the manual's single weight. Size carries the hierarchy, and weight does not.
- **JetBrains Mono** (SIL OFL 1.1) only for terminal text and file names. The manual has no monospace. This is a workshop addition for code.

Load both from local variable `ttf` files with `@font-face`. Fallbacks are only the generic `sans-serif` and `monospace`, so that a missing file is easy to see in stills.

| Role | Family | Size at 1080p | Weight | Line height | Tracking | Case | Basis |
|---|---|---:|---:|---:|---:|---|---|
| Display (title, end plate) | Inter | 112 px | 500 | 1.08 | −0.02 em | sentence | adapted |
| H1 (scene head) | Inter | 80 px | 500 | 1.08 | −0.02 em | sentence | adapted |
| H2 (plate names, step names) | Inter | 48 px | 500 | 1.1 | 0 | sentence | workshop |
| Body (field values, card names) | Inter | 36 px | 500 | 1.35 | 0 | sentence | workshop |
| Caption | Inter | 36 px | 500 | 1.35 | 0 | sentence | workshop |
| Label / eyebrow | Inter | 30 px | 500 | 1.2 | 0 | sentence | adapted (sign copy is mixed case) |
| Code / terminal | JetBrains Mono | 32 px | 500 | 48 px | 0 | as typed | workshop |

Sign copy in the manual is upper and lower case ("Uptown & The Bronx", "All trains"), so labels are not uppercase. Weight 700 (`--w-strong`) is defined but not used. `--w-light` is mapped to 500 because this style has no light weight. Nothing on screen is smaller than 30 px.

## Layout

- Canvas 1920×1080. Base unit `--u` = 30 px. 8 columns of 240 px. Outer margin `--margin` 120 px. (Workshop grid, shared with the other presets so that scenes stay comparable.)
- **Sign plates (adapted):** every panel, card and tile is a white plate with a 3 px black outline and a 15 px black band (`--band`) across its top edge. In the manual, a black band at the top of each panel is the structural part that holds the plate (the scan reads "1⅝"" on a 1 ft plate). The video keeps the band as a graphic. Content inside a plate starts below the band.
- **Header band (adapted):** each scene head starts with a full-width black band from margin to margin, with the step label under it and the headline below that. Eyebrow at y = 60 px (band), headline at y = 135 px.
- Caption zone: the bottom band from y = 900 to 1020 px, inside the margins. No content goes into it. Captions sit on a black plate with white text.
- Content sits between y ≈ 270 and 870 px. It is left-aligned and reads left to right, in the direction of the arrows.
- The manual's plate proportions (1:1, 2:1, 4:1 and 8:1 ft modules) are not used in this video. Panel sizes follow the shared scene layout.

## Visual language

- White plates with a black top band and a 3 px outline. The radius is 0.
- **Arrows (adapted):** a heavy black shaft (`--arrow-w` 12 px) and a solid triangular head (`--arrow-head` 24 px half-height, `--arrow-len` 36 px). Each arrow points one way, in the direction of travel. Never use two-headed, zig-zag or decorative arrows (source: the "how not to use the arrow" examples). Plain connectors (no head) are 3 px black rules.
- One orange plate per scene marks the subject: the video, the prepare skill, or the chosen style. It keeps the black outline and the black band.
- A 3 px orange ring marks the current option.
- Terminal panels: the black band holds the label in white, mono text below, and the question line in orange.
- Steps are numbered `01`, `02`. Ticks in `--ok` mark completed checks.
- Identity colors only as a thick left edge on a named card.
- No column guides, textures, photos, logos, discs or route-style symbols on the canvas. This follows the manual's rule against extra devices on walls and tiles.

## Motion

| Token | Value | Use | Basis |
|---|---|---|---|
| `--ease-standard` | `cubic-bezier(0.25, 0, 0.25, 1)` | rules growing, color changes, fades | workshop |
| `--ease-entrance` | `cubic-bezier(0.1, 0.6, 0.2, 1)` | plates arriving | workshop |
| `--ease-exit` | `cubic-bezier(0.4, 0, 1, 1)` | plates leaving | workshop |
| `--ease-expressive` | `cubic-bezier(0.1, 0.6, 0.2, 1)` | the same as entrance: this style has no expressive mode | workshop |
| `--dur-fast` | 160 ms | small elements, rings, scene exits | workshop |
| `--dur-base` | 300 ms | plates, cards | workshop |
| `--dur-slow` | 500 ms | titles, long arrows | workshop |
| `--stagger` | 90 ms | delay between items in a sequence | workshop |

The manual is a print and signage standard and says nothing about motion. These rules adapt its principles:

- **Point of decision (adapted):** an element appears on the narration cue that names it, not before. The scene fades out before the next scene begins, so old information never stays on screen.
- **Direction of travel (workshop):** everything enters by sliding from the left (12–36 px) with a fade, the same way the arrows point. Nothing enters from the right, above or below.
- Arrows draw from their origin, then the head lands. Nothing loops, bounces, spins or pulses. There are no wipes or zooms. Motion is short and decisive.
- Easing and durations are read from these tokens at run time, never typed into scene code.

## Narration voice

Like a good sign: direct, positive, and second person ("you"), in the present tense. One instruction or fact in each sentence. Use directional words for sequence ("Next", "then"). Use the same term for the same thing everywhere (source: the glossary policy, "Many different terms have been used in the past, causing confusion and hesitation"). Use positive wording (source: "open 10 am–8 pm instead of closed 8 pm–10 am"). Do not use hype words, rhetorical questions, colons or dashes in spoken text. The reference video used local Kokoro `af_heart` at speed 0.92. It measured about 144 words per minute overall (105 words in 43.8 s, with 1.2 s pauses between scenes).

## Accessibility

- Burned-in captions on every spoken sentence, in the caption zone: 36 px white on a black plate, balanced line breaks, at most two lines. (This adapts the manual's limit of two lines for directional signs.) Also ship `captions.vtt`.
- Informational panels hold at most six lines (source: the manual's limit for informational signs).
- All text pairs above pass 4.5:1. The lowest text pair is 4.69:1 (orange signal text on the canvas).
- Meaning never depends on color alone. Status uses ticks, selection uses an outline ring, and identity colors sit beside names.
- Minimum on-screen text is 30 px at 1080p. Every text element stays on screen for at least the length of the sentence that introduces it.
- No flashing, looping or strobing motion.

## Tokens

```css
@font-face { font-family: "Inter"; font-weight: 100 900; src: url("fonts/Inter-VF.ttf") format("truetype"); }
@font-face { font-family: "JetBrains Mono"; font-weight: 100 800; src: url("fonts/JetBrainsMono-VF.ttf") format("truetype"); }
:root {
  --bg: #eeeeea; --layer: #ffffff; --layer-hi: #e0e0dc; --line: #111111; --line-faint: #c8c8c4;
  --text: #111111; --text-2: #555555; --text-on-emph: #ffffff;
  --emph: #c03a00; --emph-fill: #c03a00;
  --ok: #00843d; --warn: #9e6500; --err: #a6192e;
  --data-1: #005eb8; --data-2: #b5179e; --data-3: #00843d; --data-4: #111111; --data-5: #9e6500;
  --font-sans: "Inter", sans-serif; --font-mono: "JetBrains Mono", monospace; --font-label: var(--font-sans);
  --w-light: 500; --w-regular: 500; --w-strong: 700;
  --fs-display: 112px; --fs-h1: 80px; --fs-h2: 48px; --fs-body: 36px; --fs-label: 30px; --fs-code: 32px; --fs-caption: 36px;
  --lh-display: 1.08; --lh-body: 1.35; --ls-display: -0.02em; --ls-label: 0em; --label-case: none;
  --w-display: var(--w-regular); --w-heading: var(--w-regular);
  --u: 30px; --cols: 8; --col: 240px; --margin: 120px; --gutter: 30px; --caption-bottom: 60px; --caption-h: 120px;
  --radius: 0px; --stroke: 3px; --band: 15px; --arrow-w: 12px; --arrow-head: 24px; --arrow-len: 36px;
  --caption-bg: rgba(17, 17, 17, 0.94); --caption-text: #ffffff;
  --ease-standard: cubic-bezier(0.25, 0, 0.25, 1); --ease-entrance: cubic-bezier(0.1, 0.6, 0.2, 1);
  --ease-exit: cubic-bezier(0.4, 0, 1, 1); --ease-expressive: cubic-bezier(0.1, 0.6, 0.2, 1);
  --dur-fast: 160ms; --dur-base: 300ms; --dur-slow: 500ms; --stagger: 90ms;
}
```

Tokens beyond the IBM preset's shared set: `--font-label` (labels use the sans in this style), `--band` (plate top band), `--arrow-w`, `--arrow-head`, `--arrow-len` (arrow geometry), `--caption-text` (white captions on a black plate). The reference composition reads them in small per-style overrides (see the reference run's `handoff.md`). `--gutter`, `--cols`, `--layer-hi`, `--line-faint`, `--warn`, `--err`, `--data-5` and `--w-strong` are defined but not used in the reference video.

## Assets and licenses

| Asset | Where to get it | License | Video use |
|---|---|---|---|
| Inter variable font `Inter[opsz,wght].ttf`, saved as `Inter-VF.ttf` (sha256 `29160a80…9031`) | `github.com/google/fonts`, `ofl/inter/` | SIL OFL 1.1 | allowed. You can embed it or render with it freely. Do not sell the font files alone |
| JetBrains Mono variable font `JetBrainsMono[wght].ttf`, saved as `JetBrainsMono-VF.ttf` (sha256 `48715a42…feda`) | `github.com/google/fonts`, `ofl/jetbrainsmono/` | SIL OFL 1.1 | as above |

Keep the OFL texts (`OFL-Inter.txt`, `OFL-JetBrainsMono.txt`) beside the font files. No other assets are needed. Do not use any MTA logo, any route bullet, the manual's own arrow artwork, or any photograph of signage. The arrows in this style are drawn with CSS, not traced from the manual.

## Provenance

Read on 2026-10-03 from the third-party scan "New York City Transit Authority Graphic Standards Manual" (Unimark International, 1970) at `https://archive.org/details/nycta-gs-manual`. Sources read: the item metadata, the full OCR text (`NYCTA GS Manual_djvu.txt`), and five page images (Contents; "Diagram of the Information Tree", page 2; a color swatch, page 53; "Examples and combinations of the Arrow", page 60; "Sign plate modulation", page 61). The OCR is noisy, so every quotation was checked against the readable sentence and the page images where possible.

Source rules used, as read:

- Introduction and page 2: information only "at the point of decision. Never before. Never after." There are three sign categories: identification, directional and information.
- Page 5: directional signs have "no more than two lines of text", and informational signs no more than six.
- Page 10: "All word spaces are to equal one-half the height of the capital letter" (not used: the browser sets word spacing).
- Page 11 and the swatch pages: an eight-color line code (PMS 185 red, 312 blue, 239 magenta, 130 yellow, 165 orange, 300 blue, 354 green, black) on discs with white letters. This preset takes some hues as darkened identity colors and does **not** use discs.
- Pages 56–60: the arrow points in a set of fixed directions. There is a blank module between two directions on one sign. The page shows examples of how not to use the arrow (two-headed, zig-zag).
- Pages 61–62: modular plates of 1, 2, 4 and 8 ft by 1 ft. A black band at the top of the panel is the structural part that holds the plate. Text is black on a white background. Painting tiles or walls breaks the standard.
- Page 171: glossary and semantics. Use consistent terms and positive language.
- Contents and the reproduction pages: the typeface is Standard Medium.

Workshop adaptations, not from the manual: the canvas color, every hex value (the manual gives PMS numbers only), orange as the single signal, white-on-black captions, the type sizes, the choice of Inter and JetBrains Mono, the shared 30 px grid and margins, the header band, the band thickness in pixels, all motion (the manual covers no motion), the narration voice details, and the accessibility rules. The contrast ratios were computed by the workshop from the hex values.

Not checked: the manual's construction drawing for the arrow (only the use examples were viewed), the exact Standard Medium letter-spacing tables, the later 1980s–present MTA sign practice (white on black), and any MTA brand rules. The Pantone-to-sRGB conversions are **unverified**.

Revision history: 1 (2026-10-03). First version, written with the reference video `outputs/explainer-about-explainers-nycta`.
