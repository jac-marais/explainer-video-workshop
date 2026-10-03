# NASA-inspired — video style preset

Status: workshop preset, revision 1 (2026-10-03). This is an original workshop style that borrows the editorial discipline of the 1976 NASA Graphics Standards Manual (NHB 1430.2). It is **not** NASA's brand and it is not endorsed by NASA. The descriptive style name "NASA-inspired" may appear on screen (for example in a style list). Use of the NASA insignia ("meatball") and logotype ("worm") is restricted by law, so neither may appear, nor may the seal, mission patches or any other NASA mark. Nothing on screen or in narration may imply that NASA made, approved or endorses the video.

This file is self-contained: a video agent can build a 1920×1080 explainer from it alone. The CSS block in "Tokens" is the exact token set. Copy it into the run's `tokens.css` unchanged. The reference implementation is `outputs/explainer-about-explainers-nasa/production/src/tokens.css` (git-ignored run output).

Value labels used below: **source** = read in the manual (printed page given); **sampled** = measured from the scanned manual, so it is approximate; **adapted** = a workshop choice built on a source value or rule; **workshop** = a workshop choice with no source value; **unverified** = believed true but not checked against a source in this revision.

## Character

- **Feel:** scientific, editorial, confident, restrained. A light paper page, black type and rules, one warm red accent. Diagrams look like figures in a technical report: open outlined boxes, thin straight connectors, flush-left type that hangs from a heavy rule.
- **Source basis:** the manual asks for correct technical detailing and asks the designer to analyze the communication task before choosing an illustration technique (p. 5.1); to reduce competing elements and strive for simplicity (p. 5.7); and to use a grid to give cohesive style and continuity (p. 5.14). Typography is flush left, ragged right, upper and lower case, with Light text and Medium headings (pp. 5.2, 5.3).
- **Avoid:** gradients, shadows, glows, rounded corners, emoji, icons, photographs, stock imagery, pastel or faded colors (p. 5.2), red next to other bright saturated colors (p. 1.3), red on a medium or dark background (pp. 1.3, 1.4), centered poster layouts, bounce or overshoot, any NASA logotype, insignia, seal, patch, star field, rocket or space imagery.

## Color

Light theme only. The manual says NASA red is used only on white or a light neutral background (p. 1.3). Every hex below is used as given; no tints are derived except the caption backing (alpha).

| Token | Hex | Role | Basis |
|---|---|---|---|
| `--bg` | `#f5f3ee` | canvas (light warm neutral "paper") | workshop, following the light-neutral rule on p. 1.3 |
| `--layer` | `#ffffff` | panels, figure boxes, tiles | workshop |
| `--layer-hi` | `#e8e4dc` | raised or selected layer (defined, not used in the reference video) | workshop |
| `--line` | `#141414` | figure box outlines, rules | workshop |
| `--line-faint` | `#d6d1c7` | grid guides | workshop |
| `--text` | `#141414` | primary text, masthead rules | workshop |
| `--text-2` | `#57514a` | secondary text, labels, step captions | adapted (a darker shade in the hue of NASA warm gray) |
| `--text-on-emph` | `#ffffff` | text on the red block | workshop |
| `--emph` | `#ca243a` | emphasis text, rings, active connectors, arrowheads | sampled (NASA red swatch, p. 1.5 scan) |
| `--emph-fill` | `#ca243a` | emphasis fill (the one solid red block per scene) | sampled, as above |
| `--ok` | `#141414` | tick glyph (black; no green beside the red) | workshop |
| `--warn` | `#8a5a00` | warning (defined, not used in the reference video) | workshop |
| `--err` | `#141414` | error (defined, not used). Use a cross glyph and a word; red is reserved for emphasis | workshop |
| `--data-1` | `#141414` | identity edge 1 (card tab) | workshop |
| `--data-2` | `#57514a` | identity edge 2 | adapted |
| `--data-3` | `#7d766c` | identity edge 3 | adapted |
| `--data-4` | `#a29b91` | identity edge 4 | sampled (NASA warm gray swatch, p. 1.5 scan) |
| `--data-5` | `#d6d1c7` | identity edge 5 (defined, not used in the reference video) | workshop |
| `--caption-bg` | `rgba(245, 243, 238, 0.94)` | caption backing (`--bg` at 94 %) | workshop |

The manual gives NASA red and NASA warm gray as printed swatches, not as hex (p. 1.5; its 4-color formula is "solid red plus solid yellow"). The two **sampled** hex values were averaged from a 100 dpi render of the scanned page, so they are approximate. No Pantone number appears in the text of the manual that was read; any PMS reference for NASA red is **unverified** here.

Rules:

- **One accent, one meaning.** Red means "look here now". Use at most one filled red block per scene. Everything else is black, warm gray or paper.
- **Data colors are a gray ramp.** They identify cards like tabs in a binder; the card name always carries the identity. Never use them for body text.
- **Status needs a glyph.** A tick, cross or word carries the meaning; color never does.
- **No color on color.** Text sits on `--bg`, `--layer` or `--emph-fill` only.

### Contrast (computed)

WCAG 2.x relative-luminance ratios, computed from the hex values above (2026-10-03). Text needs 4.5:1; large text (≥ 24 px at 1080p here) and meaningful graphics need 3:1.

| Foreground | Background | Ratio | Use | Result |
|---|---|---:|---|---|
| `--text` #141414 | `--bg` #f5f3ee | 16.61 | body, headings | pass |
| `--text` #141414 | `--layer` #ffffff | 18.42 | text in figure boxes | pass |
| `--text` #141414 | `--layer-hi` #e8e4dc | 14.53 | text on raised layer | pass |
| `--text` #141414 | caption backing over black content (#e7e6e1) | 14.74 | captions, worst case | pass |
| `--text-2` #57514a | `--bg` #f5f3ee | 7.06 | labels | pass |
| `--text-2` #57514a | `--layer` #ffffff | 7.83 | labels in boxes | pass |
| `--emph` #ca243a | `--bg` #f5f3ee | 4.95 | emphasis text, rules | pass |
| `--emph` #ca243a | `--layer` #ffffff | 5.49 | emphasis text in boxes (terminal question) | pass |
| `--text-on-emph` #ffffff | `--emph-fill` #ca243a | 5.49 | text on the red block | pass |
| `--ok` #141414 | `--layer` #ffffff | 18.42 | tick glyph | pass |
| `--warn` #8a5a00 | `--bg` #f5f3ee | 5.34 | warning glyph | pass |
| `--data-2` #57514a | `--layer` #ffffff | 7.83 | identity edge | pass (3:1) |
| `--data-3` #7d766c | `--layer` #ffffff | 4.49 | identity edge | pass (3:1) |
| `--data-4` #a29b91 | `--layer` #ffffff | 2.75 | identity edge | **below 3:1: decorative only.** The card name carries the identity |
| `--line-faint` #d6d1c7 | `--bg` #f5f3ee | 1.37 | grid guides | decorative only |

## Typography

The manual's main style is Helvetica Light text with Helvetica Medium headings, upper and lower case, flush left, ragged right (pp. 5.2, 5.3). Helvetica is proprietary, so this preset substitutes **Inter** (SIL OFL 1.1), a neutral grotesque with true Light and Medium weights. It is close in spirit, not a Helvetica clone: Inter has a taller x-height and more open apertures, which help legibility on video. The manual has no monospace face; **Source Code Pro** (SIL OFL 1.1) is a workshop addition for terminal text and file names only. Load both from local `woff2` files with `@font-face`. Fallbacks are generic `sans-serif` and `monospace` only, so a missing file shows up as an obvious fallback in stills.

| Role | Family | Size at 1080p | Weight | Line height | Tracking | Case | Basis |
|---|---|---:|---:|---:|---:|---|---|
| Display (title, end card) | Inter | 108 px | 300 Light | 1.1 | −0.02 em | sentence | adapted (Light, p. 5.3) |
| H1 (scene head) | Inter | 72 px | 500 Medium | 1.1 | −0.02 em | sentence | adapted (Medium headings, p. 5.3) |
| H2 (box names, step names) | Inter | 48 px | 400 | 1.1 | 0 | sentence | workshop |
| Body (field values, card names) | Inter | 36 px | 400 | 1.4 (1.2–1.3 in tight boxes) | 0 | sentence | workshop |
| Caption | Inter | 36 px | 400 | 1.35 | 0 | sentence | workshop |
| Label / eyebrow | Inter | 30 px | 500 Medium | 1.2 | 0 | sentence (upper and lower case) | adapted (p. 5.2) |
| Code / terminal, file names | Source Code Pro | 32 px | 400 | 48 px | 0 | as typed | workshop |

Hierarchy: a heavy black masthead rule, then a Medium eyebrow (`Step 1`), then a Medium headline, then content. Weight and size carry hierarchy; color does not. Never use italic, all caps or weights above 500. Nothing on screen is smaller than 30 px.

## Layout

- Canvas 1920×1080. Base unit `--u` = 30 px; positions and sizes are multiples of 30 px. 8 columns of 240 px, outer margin `--margin` 120 px. **Workshop**: the manual's grids are for print pages (pp. 5.14–5.20); this preset keeps their principle (one grid for every scene, for continuity, p. 5.14) and uses a video grid.
- Masthead: every scene head hangs from a 6 px black rule (`--head-rule`) that spans the margins at y = 75 px (title card: y = 120 px). Eyebrow under the rule, headline at y = 135 px. **Adapted** from p. 5.19 ("typography hangs from top of page", "several horizontal reference lines"); the rule's weight and position are workshop choices.
- Caption zone: the bottom band from y = 900 to 1020 px (`--caption-bottom` 60 px, `--caption-h` 120 px), inset by the margins. No content enters it.
- Content sits between y ≈ 270 and 870 px, flush left to the margin, read left to right. Leave the right side empty rather than stretching content to fill it.

## Visual language

- Figures, not decoration. Every diagram is an open white box with a 2 px black outline on paper, 0 radius, like a figure in a technical brief (p. 5.8 recommends an outline box around all diagrams).
- Connections are straight 2 px rules. The active path is red and ends in a solid red triangular arrowhead.
- One filled red block per scene marks the subject (the output, the skill, the chosen style).
- A 2 px red outline ring marks "current" or "selected".
- Cards carry a 12 px tab on the left edge in the gray ramp (`--data-*`).
- Grid guides (2 px, `--line-faint`) may show on the title and end cards only.
- Ticks are black. Step numbers are Medium labels (`01`, `02`).
- No logos, insignia, photographs, illustrations, star fields or icons beyond ticks and arrowheads.

## Motion

The manual has no motion system. Every motion rule here is a **workshop adaptation** of its print principles (restraint, technical precision, fewer competing elements).

| Token | Value | Use | Basis |
|---|---|---|---|
| `--reveal` | `wipe` | each element is drawn in from the left edge (a clip-path wipe, like a drafting stroke), with a short fade; nothing slides | workshop |
| `--ease-standard` | `cubic-bezier(0.4, 0, 0.2, 1)` | rules growing, color changes, fades | workshop |
| `--ease-entrance` | `cubic-bezier(0.2, 0, 0.2, 1)` | element wipes | workshop |
| `--ease-exit` | `cubic-bezier(0.4, 0, 1, 1)` | elements leaving | workshop |
| `--ease-expressive` | `cubic-bezier(0.3, 0, 0.1, 1)` | title and end card only | workshop |
| `--dur-fast` | 300 ms | small elements, rings, exits | workshop |
| `--dur-base` | 500 ms | panels, cards | workshop |
| `--dur-slow` | 1000 ms | titles, long rules | workshop |
| `--stagger` | 140 ms | delay between items in a sequence | workshop |

Rules: every element enters on the narration cue that names it, wiping in left to right; the masthead rule therefore draws across with its eyebrow. Connectors grow from their origin. Items in a list stagger. Nothing slides, loops, bounces, spins or pulses. Each scene fades out over `--dur-fast` with `--ease-exit` just before the next one begins; there are no zooms or cross-scene wipes. Easing, durations and the reveal mode are read from these tokens at run time, never typed into scene code.

## Narration voice

Measured and exact, like a mission briefing read by an engineer. Second person, present tense, short declarative sentences in procedural order ("Next", "then"). Name the step, then what it produces. No hype words, no rhetorical questions, no colons or dashes in spoken text, no "X, not Y" constructions. The reference video used local Kokoro `af_heart` at speed 0.92 (workshop choice) and measured about 145 words per minute overall (110 words in 45.5 s, including a 1.2 s pause between scenes); aim for 140–150. **Workshop**: the manual has no voice guidance.

## Accessibility

- Burned-in captions on every spoken sentence, in the caption zone, 36 px, on `--caption-bg`, balanced line breaks, at most two lines; also ship `captions.vtt`.
- All text pairs above pass 4.5:1; the lowest text pair is 4.95:1 (red emphasis text on paper).
- Meaning never depends on color alone: status uses ticks, selection uses an outline ring, identity uses names.
- Minimum on-screen text 30 px at 1080p. Hold every text element on screen for at least the sentence that introduces it.
- No flashing, looping or strobing motion. The wipe reveal never covers more than one element at a time.

## Tokens

```css
@font-face { font-family: "Inter"; font-weight: 300; src: url("fonts/Inter-300.woff2") format("woff2"); }
@font-face { font-family: "Inter"; font-weight: 400; src: url("fonts/Inter-400.woff2") format("woff2"); }
@font-face { font-family: "Inter"; font-weight: 500; src: url("fonts/Inter-500.woff2") format("woff2"); }
@font-face { font-family: "Source Code Pro"; font-weight: 400; src: url("fonts/SourceCodePro-400.woff2") format("woff2"); }
@font-face { font-family: "Source Code Pro"; font-weight: 500; src: url("fonts/SourceCodePro-500.woff2") format("woff2"); }
:root {
  --bg: #f5f3ee; --layer: #ffffff; --layer-hi: #e8e4dc; --line: #141414; --line-faint: #d6d1c7;
  --text: #141414; --text-2: #57514a; --text-on-emph: #ffffff;
  --emph: #ca243a; --emph-fill: #ca243a;
  --ok: #141414; --warn: #8a5a00; --err: #141414;
  --data-1: #141414; --data-2: #57514a; --data-3: #7d766c; --data-4: #a29b91; --data-5: #d6d1c7;
  --font-sans: "Inter", sans-serif; --font-mono: "Source Code Pro", monospace; --font-label: var(--font-sans);
  --w-light: 300; --w-regular: 400; --w-strong: 500; --w-label: 500;
  --fs-display: 108px; --fs-h1: 72px; --fs-h2: 48px; --fs-body: 36px; --fs-label: 30px; --fs-code: 32px; --fs-caption: 36px;
  --lh-display: 1.1; --lh-body: 1.4; --ls-display: -0.02em; --ls-label: 0em; --label-case: none;
  --w-display: var(--w-light); --w-heading: var(--w-strong);
  --u: 30px; --cols: 8; --col: 240px; --margin: 120px; --gutter: 30px; --caption-bottom: 60px; --caption-h: 120px;
  --radius: 0px; --stroke: 2px; --head-rule: 6px; --caption-bg: rgba(245, 243, 238, 0.94);
  --reveal: wipe;
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1); --ease-entrance: cubic-bezier(0.2, 0, 0.2, 1);
  --ease-exit: cubic-bezier(0.4, 0, 1, 1); --ease-expressive: cubic-bezier(0.3, 0, 0.1, 1);
  --dur-fast: 300ms; --dur-base: 500ms; --dur-slow: 1000ms; --stagger: 140ms;
}
```

Tokens beyond the IBM preset's set: `--font-label` and `--w-label` (labels use Inter Medium, not a monospace face), `--head-rule` (the masthead rule; 0 removes it) and `--reveal` (`wipe` here; any other value keeps the slide-and-fade entrance). The reference `composition.html` reads all four. `--gutter`, `--cols`, `--layer-hi`, `--warn`, `--err`, `--data-5` and Source Code Pro 500 are defined but unused in the reference video.

## Assets and licenses

| Asset | Where to get it | License | Video use |
|---|---|---|---|
| Inter Light, Regular, Medium (Latin subset `woff2`) | npm `@fontsource/inter` 5.3.0 (from Google Fonts; upstream `rsms/inter`) | SIL OFL 1.1 | allowed; render and embed freely; do not sell the font files alone |
| Source Code Pro Regular, Medium (Latin subset `woff2`) | npm `@fontsource/source-code-pro` 5.3.0 (Adobe, via Google Fonts) | SIL OFL 1.1, Reserved Font Name "Source" | as above; a modified font may not use the reserved name |

Ship the OFL texts beside the font files (`OFL-Inter.txt`, `OFL-SourceCodePro.txt`). No other assets are needed. Do not use the NASA logotype, insignia, seal, mission patches, any other NASA mark, or NASA photographs, and do not imply NASA endorsement. The style name "NASA-inspired" is allowed.

## Provenance

Read on 2026-10-03: the scanned NASA Graphics Standards Manual, NHB 1430.2, January 1976 (`https://www.nasa.gov/wp-content/uploads/2015/01/nasa_graphics_manual_nhb_1430-2_jan_1976.pdf`, local copy, 60 PDF pages). Text was extracted with `pdftotext`, and pages 1.5, 5.8 and 5.14 were also viewed as images. Pages read:

- p. 1.3 "The NASA Color": red only on white or a light neutral background; not with other bright saturated colors or medium and dark value colors.
- p. 1.4 "Use of Color": red never on a medium-value background.
- p. 1.5 "Color Standards": NASA red and NASA warm gray swatches; 4-color formula "solid red plus solid yellow". Hex values in this preset are **sampled** from the scan.
- p. 5.1 "NASA Publications": correct technical detailing is necessary; analyze the communication task an illustration must accomplish before choosing technique; simplicity, appropriateness and strength of composition; typography as the "architecture" of a publication.
- p. 5.2: Helvetica Light and Medium, upper and lower case, flush left, ragged right, bold headlines; avoid pastel colors; NASA red as an accent.
- p. 5.3 "Typography – Sans Serif, Helvetica": Light text with Medium headings, upper and lower case.
- p. 5.7 "Cover Design: Leaflets & Folders": reduce the number of competitive elements and strive for simplicity.
- p. 5.8 "Cover Design: Journals and Technical Publications": straightforward, simple, devoid of frills; an outline box around all diagrams.
- p. 5.14 "The Grid – What it is": a grid gives cohesive style and brings continuity to diverse publications.
- p. 5.19 "Interior Grid Formats: Quality Publications": typography hangs from the top of the page; several horizontal reference lines.

Workshop adaptations, not from the manual: the paper background hex, all color roles, the gray ramp, the black tick, the type sizes and tracking, the 30 px video grid and margins, the masthead rule's weight and position, the caption zone, the whole motion system (the manual has none), the narration voice and the accessibility rules. Inter and Source Code Pro are substitutes. Contrast ratios are computed by the workshop from the hex values.

Not checked: any NASA brand guidance after 1976, Pantone references for NASA red, and the signage and vehicle sections beyond a skim.

Revision history: 1 (2026-10-03) first version, written with the reference video `outputs/explainer-about-explainers-nasa`.
