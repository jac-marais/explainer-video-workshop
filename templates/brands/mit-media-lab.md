# MIT Media Lab-inspired: video style preset

Status: workshop preset, revision 2 (2026-10-03). This is an original workshop style that borrows the look of the MIT Media Lab's public brand portal and Pentagram's 2014 identity. It is **not** the Media Lab's brand, it is not endorsed by MIT or the Media Lab, and it uses no Media Lab logo, ML monogram glyph, group glyph, wordmark or MIT mark. Its 7×7 marks are original abstract shapes built for this workshop. Name it "MIT Media Lab-inspired" wherever a viewer can see the name.

This file is self-contained: a video agent can build a 1920×1080 explainer from it alone. The CSS block in "Tokens" is the exact token set. Copy it into the run's `tokens.css` unchanged. The reference implementation is `outputs/explainer-about-explainers-mit-media-lab/production/src/tokens.css` (git-ignored run output).

Value labels used below: **source** = read on the Media Lab brand portal or the Pentagram project page (see Provenance); **adapted** = a workshop choice built on a source value or rule; **workshop** = a workshop choice with no source value; **unverified** = believed true but not checked against a source in this revision.

## Character

- **Feel:** modular, geometric, research-oriented. A white canvas, black type and thin black outlines, so the content leads. One secondary color (magenta) appears sparingly as a signal. Large tight Grotesk headlines, left-aligned. A 7×7 grid generates a family of related marks. One mark is on screen at a time, and it changes shape cell by cell from scene to scene: it opens the film large, rests in the corner while a scene plays, and comes to the center to become the next scene's mark. The end card shows the whole family.
- **Avoid:** two secondary colors in one frame, color as decoration, gradients, shadows, rounded corners, photographs behind text, emoji, icons beyond ticks and arrowheads, centered layouts, bounce or overshoot, added letter spacing, and anything that copies the Media Lab's ML monogram, group glyphs, wordmark or lockups. Marks must never spell letters or initials.

## Color

The Media Lab's primary colors are black, white and grey; secondary colors are used one at a time with black and white (source). This preset uses the primary set plus one secondary, magenta.

| Token | Hex | Role | Basis |
|---|---|---|---|
| `--bg` | `#ffffff` | canvas | source (primary "FFFFFF"), adapted role |
| `--layer` | `#ffffff` | panels, cards, tiles (outlined, not filled) | source value, adapted role |
| `--layer-hi` | `#000000` | raised or selected layer: solid black (defined, not used in the reference video) | source value, adapted role |
| `--line` | `#000000` | panel borders, connectors, card bars | source (primary "000000"), adapted role |
| `--line-faint` | `#969696` | faint guides (defined, not used in the reference video) | source (primary grey "969696", PMS Cool Grey 6), adapted role |
| `--text` | `#000000` | primary text, mark cells, ticks | source value, adapted role |
| `--text-2` | `#595959` | secondary text, labels | **workshop.** The source grey `#969696` is only 2.96:1 on white, too low for text, so labels use a darker grey |
| `--text-on-emph` | `#ffffff` | text on the black block | source value, adapted role |
| `--emph` | `#e5178f` | rings, active connectors, arrowheads, the one accent cell per mark, the prompt line, the end-card label | source (secondary "E5178F"), adapted role |
| `--emph-fill` | `#000000` | the selected block (Video, Skill node, picked tile) | source value, adapted role |
| `--ok` | `#000000` | completed tick (a glyph) | workshop: black keeps to one secondary color |
| `--warn` | `#000000` | warning (defined, not used); pair with a "!" glyph or the word | workshop |
| `--err` | `#e54500` | error glyph (defined, not used) | source (secondary "E54500"), adapted role |
| `--data-1` | `#e5178f` | secondary color 1 (one hue per composition) | source |
| `--data-2` | `#07aef5` | secondary color 2; use on black only | source |
| `--data-3` | `#9477ff` | secondary color 3 | source |
| `--data-4` | `#2fa85e` | secondary color 4 | source |
| `--data-5` | `#e54500` | secondary color 5 | source |
| `--caption-bg` | `#000000` | caption bar | workshop |
| `--caption-fg` | `#ffffff` | caption text | workshop |

The sixth secondary color, `#D9D900` (yellow), is in the source palette but not in the tokens: it is 1.50:1 on white and works only on black.

Rules:

- **One secondary at a time.** A frame uses black, white, grey and at most one secondary color (source rule). This video uses only magenta. Do not tell items apart by color; use names, numbers or a mark. The data tokens exist for a chart that needs a single hue; pick one.
- **Black is the emphasis fill.** The selected thing becomes a solid black block with white text. Magenta marks what is active now (ring, connector, arrowhead).
- **Status needs a glyph.** Ticks carry the meaning; they are black.
- **No color on color.** Text sits on white or black only.

### Contrast (computed)

WCAG 2.x relative-luminance ratios, computed from the hex values above (2026-10-03). Text needs 4.5:1; large text (≥ 24 px at 1080p) and meaningful graphics need 3:1.

| Foreground | Background | Ratio | Use | Result |
|---|---|---:|---|---|
| `--text` #000000 | `--bg` #ffffff | 21.00 | body, headings, ticks, mark cells | pass |
| `--text-2` #595959 | `--bg` #ffffff | 7.00 | labels | pass |
| `--text-on-emph` #ffffff | `--emph-fill` #000000 | 21.00 | text on the black block | pass |
| `--caption-fg` #ffffff | `--caption-bg` #000000 | 21.00 | captions | pass |
| `--emph` #e5178f | `--bg` #ffffff | 4.33 | rings, connectors, arrowheads; 30–32 px text only | pass (3:1 large text and graphics). **Never use it for text under 24 px** |
| `--emph` #e5178f | `--emph-fill` #000000 | 4.85 | accent cell beside black cells | pass (3:1) |
| `--line` #000000 | `--bg` #ffffff | 21.00 | panel borders, connectors | pass |
| `--line-faint` #969696 | `--bg` #ffffff | 2.96 | faint guides | decorative only |
| `--err` #e54500 | `--bg` #ffffff | 4.05 | error glyph | pass (3:1) |
| `--data-2` #07aef5 | `--bg` #ffffff | 2.51 | — | **fails on white;** on black 8.38 |
| `--data-3` #9477ff | `--bg` #ffffff | 3.31 | graphic | pass (3:1); on black 6.34 |
| `--data-4` #2fa85e | `--bg` #ffffff | 3.05 | graphic | pass (3:1); on black 6.88 |
| `--data-5` #e54500 | `--bg` #ffffff | 4.05 | graphic | pass (3:1); on black 5.18 |

## Typography

The Media Lab's primary typeface is Neue Haas Grotesk (NHG), in Display (above 20 px digital) and Text (20 px and below) cuts (source). NHG is a commercial font licensed to the MIT community through Adobe Fonts; it may not be used here. **Substitute: Inter Display** (Inter 4.1, SIL OFL 1.1), an open neo-grotesque with a separate Display optical cut, which mirrors NHG's Display/Text split. Because nothing on screen is smaller than 30 px, only the Display cut is needed. The source names Helvetica or Arial as fallbacks for NHG; neither is openly licensed for embedding, so they are not used. The brand names no monospace face; **JetBrains Mono** (SIL OFL 1.1) is a workshop choice for the terminal and file names only.

Fallbacks are generic `sans-serif` and `monospace` only, so a missing file shows up as an obvious fallback in stills.

| Role | Family | Size at 1080p | Weight | Line height | Tracking | Case | Basis |
|---|---|---:|---:|---:|---:|---|---|
| Display (title, end card) | Inter Display | 112 px | 500 | 0.95 | −0.02 em | sentence | adapted: tight leading of 85–100 % and up to −20 units tracking for NHG Display headlines (source) |
| H1 (scene head) | Inter Display | 80 px | 500 | 0.95 | −0.02 em | sentence | adapted (as above) |
| H2 (box names, step names) | Inter Display | 48 px | 400 | 1.1 | 0 | sentence | workshop |
| Body (field values, card names) | Inter Display | 36 px | 400 | 1.25 (1.2–1.3 in tight boxes) | 0 | sentence | adapted: body leading 100–125 %, tracking 0 (source, for NHG Text) |
| Caption | Inter Display | 36 px | 400 | 1.35 | 0 | sentence | workshop |
| Label / eyebrow | Inter Display | 30 px | 500 | 1.2 | 0 | sentence | workshop; no added tracking (source: "Never add additional tracking") |
| Code / terminal | JetBrains Mono | 32 px | 400 | 48 px | 0 | as typed | workshop |

Hierarchy comes from size and weight: a small grey label (`Step 1`) over a large black headline. Bold (700) is loaded for rare strong emphasis; the reference video does not use it. Never add tracking, never use italic, never set all caps.

## Layout

- Canvas 1920×1080. Base unit `--u` = 30 px; positions are multiples of 30 px. Outer margin 120 px left and right (workshop).
- **7×7 module.** Marks are 7×7 grids of square cells, `--cell` = 16 px (112 px square) in the corner. The large mark uses `--cell-lg` = 60 px (420 px square); it is the same element, scaled. The Media Lab's own monogram was built on a 7×7, 49-unit grid, and Pentagram used the same grid to generate a family of group glyphs (source). This preset keeps the method and invents its own shapes (workshop).
- **Mark positions.** Corner: right edge on the margin, top at y = 90 px, level with the eyebrow; it scales from its top-right corner. Intro: large, right edge on the margin, top at y = 330 px, beside the title. Transition: large, centered horizontally, top at y = 270 px, on an empty frame. Below about 100 px a 7×7 mark stops reading as a shape, so keep the corner mark at 16 px cells or larger.
- Scene head at the top left: eyebrow at y = 90 px, headline at y = 135 px. Content between y ≈ 270 and 870 px, left-aligned.
- Caption zone: the bottom band from y = 900 to 1020 px, inset by the margins. Captions sit in a black bar; no content enters the band.
- Asymmetric and left-aligned. Do not center titles. Leave white space empty.

## Visual language

- Outlined rectangles: white fill, 2 px black border, 0 radius. The selected item is a solid black block with white text.
- Straight 2 px rules; active connectors are magenta and end in a solid magenta triangle.
- A 2 px magenta outline ring marks "current" or "selected".
- Cards carry a 12 px black left bar; items are told apart by name, never by hue.
- **7×7 marks (original).** One per scene, each a tiny diagram of what the scene says, abstract and never a letter: S01 an arrow (topic to video, accent at the tip); S02 four hollow squares, the accent in the centre of one (options, one picked); S03 an input cell, a 3×3 node and four outputs in a column (one input, four outputs, accent on the last); S04 four rising bars (steps that build up, accent on top of the tallest); S05 a tick (check, accent at its end). Each mark has exactly one magenta accent cell. Neighbouring marks should differ in most cells, so the morph reads as a change of idea. The end card shows all five in a row, 30 px apart: the family. To make a new mark, fill cells of a 7×7 grid, then check it at corner size and ask "does this read as a letter?"; if yes, redraw it. Keep it abstract and do not imitate the Media Lab's monogram or group glyphs.
- Terminal: outlined panel with a label bar, mono text, prompt line in magenta.
- No logos, photographs, illustrations or icons beyond ticks, arrowheads and the marks.

## Motion

The brand portal gives no motion rules; all motion values are **workshop** choices that express "modular".

| Token | Value | Use |
|---|---|---|
| `--ease-standard` | `cubic-bezier(0.65, 0, 0.35, 1)` | rules drawing, color changes, fades |
| `--ease-entrance` | `cubic-bezier(0.22, 1, 0.36, 1)` | cells arriving |
| `--ease-exit` | `cubic-bezier(0.55, 0, 1, 0.45)` | scene exits, cells leaving |
| `--ease-expressive` | `cubic-bezier(0.83, 0, 0.17, 1)` | title, Video block and end card reveals |
| `--dur-fast` | 200 ms | each cell, rings, scene exits |
| `--dur-base` | 360 ms | panels, cards, lines of text; each mark move |
| `--dur-slow` | 640 ms | titles, long rules |
| `--stagger` | 80 ms | delay between items in a list |
| `--cell-stagger` | 18 ms | delay between cells of an end-card mark |

Rules:

- **Reveals come from the grid.** Each element enters on the narration cue that names it, revealed as **7 column modules**, left to right: a mask splits the element into 7 equal columns, and each column fades in over 45 % of the reveal, one after another. The reveal lasts 1.5× the element's duration token. No sliding, no flat single wipe.
- **The mark morphs between scenes.** One 7×7 mark element is on screen from the first frame to the end card.
  - Intro (0–1.5 s): the S01 mark assembles large at the intro position, its cells arriving in a scattered order over 1.0 s, then it moves to the corner over `--dur-slow`.
  - Scene change: when the last narration line of a scene ends, the scene's content fades out over `--dur-fast` (0.1 s after the line ends). The mark then moves to the center over `--dur-base`, morphs into the next scene's mark, and returns to the corner 0.15 s after the next scene starts, before its content builds.
  - Morph: cells change along the diagonal, top left first, and each cell takes `--dur-fast`. Leaving cells (scaling down) start over the first 0.2 s and arriving cells (scaling up from their centers) over the next 0.2 s, so few old and new cells share a frame. Starting both together showed both shapes at once, which read as a blob.
  - Within a scene the corner mark does not move.
  - End card: the mark fades out with the S05 content, and the five family marks build cell by cell, `--cell-stagger` apart.
- **Nothing moves behind text people are reading.** The mark only moves on an empty frame, inside the pause between scenes.
- Connectors draw from their origin. Nothing loops, bounces, spins or pulses. Easing and durations are read from these tokens at run time, never typed into scene code.
- **Explore signature motion before the full render.** Render 2–3 short motion options (a contiguous intro and one scene change each), let the user pick, then pilot a span that holds both the intro and a scene change. Stills alone cannot judge motion.

## Narration voice

Precise, curious and plain, like a lab explaining its method: second person, present tense, short declarative sentences, one idea each, with plain sequence words ("Next", "then"). No hype, no rhetorical questions, no colons or dashes in spoken text. The reference video used local Kokoro `af_heart` at speed 0.92 (workshop choice).

## Accessibility

- Burned-in captions on every spoken sentence, in a black bar with white 36 px text (21:1), balanced line breaks, at most two lines; also ship `captions.vtt`.
- All text pairs pass 4.5:1 except magenta, which is used only for text of 30 px or more (large text, 4.33:1) and for graphics.
- Meaning never depends on color alone: status uses ticks, selection uses a black block or an outline ring, items have names.
- Minimum on-screen text 30 px at 1080p. Hold every text element for at least the sentence that introduces it.
- No flashing, looping or strobing motion. A morph lasts 0.6 s. The intro mark is in the corner by 2.2 s.

## Tokens

```css
@font-face { font-family: "Inter Display"; font-weight: 400; src: url("fonts/InterDisplay-Regular.woff2") format("woff2"); }
@font-face { font-family: "Inter Display"; font-weight: 500; src: url("fonts/InterDisplay-Medium.woff2") format("woff2"); }
@font-face { font-family: "Inter Display"; font-weight: 700; src: url("fonts/InterDisplay-Bold.woff2") format("woff2"); }
@font-face { font-family: "JetBrains Mono"; font-weight: 400; src: url("fonts/JetBrainsMono-Regular.woff2") format("woff2"); }
@font-face { font-family: "JetBrains Mono"; font-weight: 500; src: url("fonts/JetBrainsMono-Medium.woff2") format("woff2"); }
:root {
  /* color: background (primary palette: white, black, grey) */
  --bg: #ffffff;          /* canvas */
  --layer: #ffffff;       /* panels, cards, tiles (outlined, not filled) */
  --layer-hi: #000000;    /* raised or selected layer: solid black */
  --line: #000000;        /* borders, connectors */
  --line-faint: #969696;  /* faint guides (not used in the reference video) */
  /* color: text */
  --text: #000000;        /* primary text */
  --text-2: #595959;      /* secondary text, labels */
  --text-on-emph: #ffffff;
  /* color: emphasis (the one secondary color, used sparingly) */
  --emph: #e5178f;        /* rings, active connectors, arrowheads, accent cell */
  --emph-fill: #000000;   /* the selected block is black */
  /* color: status (always paired with a glyph or word) */
  --ok: #000000;
  --warn: #000000;
  --err: #e54500;
  /* color: data (secondary palette; one hue per composition, never two together) */
  --data-1: #e5178f;
  --data-2: #07aef5;
  --data-3: #9477ff;
  --data-4: #2fa85e;
  --data-5: #e54500;
  /* fonts and weights */
  --font-sans: "Inter Display", sans-serif;
  --font-mono: "JetBrains Mono", monospace;
  --font-label: var(--font-sans);
  --w-light: 400;
  --w-regular: 400;
  --w-strong: 700;
  /* type scale at 1920x1080 */
  --fs-display: 112px;
  --fs-h1: 80px;
  --fs-h2: 48px;
  --fs-body: 36px;
  --fs-label: 30px;
  --fs-code: 32px;
  --fs-caption: 36px;
  --lh-display: 0.95;
  --lh-body: 1.25;
  --ls-display: -0.02em;
  --ls-label: 0em;
  --label-case: none;
  --w-display: 500;
  --w-heading: 500;
  --w-label: 500;
  /* grid: 30px unit; 7x7 module for marks */
  --u: 30px;
  --cols: 7;
  --col: 240px;
  --margin: 120px;
  --gutter: 30px;
  --caption-bottom: 60px;
  --caption-h: 120px;
  --cell: 16px;           /* corner mark cell (7 cells = 112px) */
  --cell-lg: 60px;        /* intro and transition mark cell (7 cells = 420px) */
  /* surface */
  --radius: 0px;
  --stroke: 2px;
  --caption-bg: #000000;
  --caption-fg: #ffffff;
  /* motion: column-module reveals and cell-by-cell morphs; no slide, no bounce */
  --ease-standard: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-entrance: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-exit: cubic-bezier(0.55, 0, 1, 0.45);
  --ease-expressive: cubic-bezier(0.83, 0, 0.17, 1);
  --dur-fast: 200ms;
  --dur-base: 360ms;
  --dur-slow: 640ms;
  --stagger: 80ms;
  --cell-stagger: 18ms;
}
```

`--cols`, `--col`, `--gutter`, `--layer-hi`, `--warn`, `--err`, the data colors, `--w-light`, `--w-strong` and the Mono 500 face are defined for layouts that need them; the reference video does not use them. `--font-label`, `--w-label`, `--caption-fg`, `--cell`, `--cell-lg` and `--cell-stagger` are additions to the IBM-inspired token set.

## Assets and licenses

| Asset | Where to get it | License | Video use |
|---|---|---|---|
| Inter Display Regular, Medium, Bold (`woff2`) | Inter 4.1 release, `github.com/rsms/inter/releases/tag/v4.1` (`web/InterDisplay-*.woff2`) | SIL OFL 1.1 | allowed; embed or render freely; do not sell the font files alone |
| JetBrains Mono Regular, Medium (`woff2`) | JetBrains Mono 2.304 release, `github.com/JetBrains/JetBrainsMono` | SIL OFL 1.1 | as above |

Ship the OFL texts beside the font files (`OFL-Inter.txt`, `OFL-JetBrainsMono.txt`). No other assets are needed. Do not use Neue Haas Grotesk (commercial, MIT community license only), the Media Lab logo, monogram glyph, group or initiative logos, or templates (several are behind community login).

## Provenance

Read on 2026-10-03 (direct `curl` of the public pages; text and the linked palette images read):

- MIT Media Lab, "MIT Media Lab Brand Portal" by Olivia Verdugo, Aug. 24, 2026 (`https://www.media.mit.edu/posts/MLBrandPortal/`): the monogram glyph is based on a 7×7, 49-unit grid; primary colors black, white and grey ("Most designs should stick to this palette"); secondary colors "introduced sparingly", "one color at a time along with black and white"; tertiary colors from an accessible color generator; Neue Haas Grotesk Display (> 20 px digital) and Text (≤ 20 px); headline leading 85–100 % and up to −20 units tracking; body leading 100–125 % and tracking 0; "Never add additional tracking"; brand architecture (group glyphs built the same way as the Lab's); logo do's and don'ts ("Do not invent your own glyphs" applies to the Lab's logos; this preset's marks are not presented as Media Lab glyphs). Group, initiative and program logos and the templates are behind a login (🔒) and were **not** read.
- The portal's palette images: `primarycolors.png` (#000000 Pantone Black; #969696 PMS Cool Grey 6; #FFFFFF) and `secondarycolors.png` (#07AEF5, #E5178F, #9477FF, #D9D900, #2FA85E, #E54500). The same six hex values appear in the linked generator `https://liv-osv.github.io/accessible-color-generator` (page source read).
- Pentagram, "MIT Media Lab" (`https://www.pentagram.com/work/mit-media-lab`): Michael Bierut, New York office; the identity began from Richard The's 25th-anniversary logo on a seven-by-seven grid; the same grid generated an ML monogram and glyphs for 23 research groups, "an interrelated system of glyphs"; Helvetica reinstated. The page gives no year; **2014** comes from the task brief and is **unverified** here.

Workshop adaptations, not from any source: the white canvas as the default, every color role, the choice of magenta as the single secondary, `#595959` for labels, the type sizes, the 120 px margin, the caption bar, the five original 7×7 marks and the accent-cell rule, the column-module reveal and the morphing mark with all easing and duration values, the narration voice and the accessibility rules. Contrast ratios are computed by the workshop from the hex values. Font substitutions (Inter Display for NHG, JetBrains Mono added) are workshop choices.

Not checked: the logged-in brand assets and templates, any Media Lab video or motion guidance (none found on the public portal), and whether Inter Display's metrics match NHG closely (it is a visual substitute, not a metric clone).

Revision history: 1 (2026-10-03) first version, written with the reference video `outputs/explainer-about-explainers-mit-media-lab`. 2 (2026-10-03) round 2: the flat left-to-right wipe is replaced by column-module reveals; the per-scene marks are now one mark that morphs between scenes, larger (16 px corner cells, 60 px large cells, up from 12 px and 40 px) and redrawn so none reads as a letter; an exploration-before-render rule is added. The grey lattice dots are gone.
