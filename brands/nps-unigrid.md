# NPS Unigrid-inspired — video style preset

Status: workshop preset, revision 1 (2026-10-03). This is an original workshop style that borrows the structure of the Unigrid, the publication design system that Massimo Vignelli made for the U.S. National Park Service in 1977. It is **not** the National Park Service's brand, it is not endorsed by the NPS, and it uses no NPS arrowhead, emblem, wordmark, agency name line or proprietary typeface. Name it "NPS Unigrid-inspired" wherever a viewer can see the name.

This file is self-contained: a video agent can build a 1920×1080 explainer from it alone. The CSS block in "Tokens" is the exact token set. Copy it into the run's `tokens.css` unchanged. The reference implementation is `outputs/explainer-about-explainers-nps-unigrid/production/src/tokens.css` (git-ignored run output).

Value labels used below: **source** = read on a public NPS page (see Provenance); **adapted** = a workshop choice built on a source fact; **workshop** = a workshop choice with no source value; **unverified** = believed true but not checked against a source in this revision.

## Character

- **Feel:** informative, illustrated, layered, map-like. A park brochure unfolded on screen: a black title band across the top of every scene, warm paper below, black hairline panels, a serif text voice, red route lines, map colors for identity. The band is the signature. Standardize the layout, let the content vary.
- **Source idea (source):** the Unigrid "standardizes formatting and production" so that designers, writers and cartographers can "focus on content"; brochures are known as "black-band brochures"; the grid "sets physical boundaries for individual elements yet allows for a great deal of flexibility".
- **Avoid:** the NPS arrowhead or any emblem in the band, the words "National Park Service" or "Department of the Interior" as a sign-off line, gradients, shadows, rounded corners, emoji, photographs you cannot license, playful bounce, centered poster layouts, more than one filled black block per scene below the band, color without a name or glyph.

## Color

Light paper theme with a black band. Every hex below is a workshop value; no NPS color specification was read (see Provenance). The caption backing is the only alpha value.

| Token | Hex | Role | Basis |
|---|---|---|---|
| `--bg` | `#f3efe4` | paper canvas | workshop (evokes uncoated brochure stock) |
| `--layer` | `#fbf9f3` | panels, cards, tiles | workshop |
| `--layer-hi` | `#e6dfcc` | raised or selected layer, map land tint (defined, not used in the reference video) | workshop |
| `--line` | `#1f1f1f` | panel borders, unselected rules | adapted (Unigrid black rules) |
| `--line-faint` | `#cfc6b0` | fold-line guides | workshop |
| `--text` | `#161616` | primary text on paper | workshop |
| `--text-2` | `#4a463d` | secondary text, labels | workshop |
| `--band` | `#000000` | title band | source fact ("black-band brochures"), exact value **unverified** |
| `--band-text` | `#ffffff` | title in the band | adapted |
| `--band-text-2` | `#bdbdbd` | eyebrow in the band | workshop |
| `--text-on-emph` | `#ffffff` | text on the black block | workshop |
| `--emph` | `#b2322a` | route red: active rules, arrowheads, selection rings, emphasis text on paper | workshop (evokes map road red) |
| `--emph-fill` | `#000000` | the one filled block per scene (same black as the band) | adapted |
| `--ok` | `#2f6b34` | success tick (always a glyph) | workshop |
| `--warn` | `#8a5a00` | warning (defined, not used in the reference video) | workshop |
| `--err` | `#a01f1a` | error (defined, not used in the reference video) | workshop |
| `--data-1` | `#3f6e3a` | identity 1, park green (card edge) | workshop |
| `--data-2` | `#2f6797` | identity 2, water blue | workshop |
| `--data-3` | `#a8741a` | identity 3, ochre | workshop |
| `--data-4` | `#7b4a2a` | identity 4, earth brown | workshop |
| `--data-5` | `#6b6b6b` | identity 5, road grey (defined, not used in the reference video) | workshop |
| `--caption-bg` | `rgba(0, 0, 0, 0.88)` | caption backing, a small black band | workshop |
| `--caption-fg` | `#ffffff` | caption text | workshop |

Rules:

- **Black means "title" or "this one".** The band holds the scene title. Below the band, at most one filled black block per scene marks the subject (the chosen style, the skill, the output).
- **Red is the route.** `--emph` draws paths, arrowheads and selection rings. It is never a fill and never body text. Red on black fails text contrast (3.38:1), so never put red in the band.
- **Status needs a glyph.** A tick, cross or word carries the meaning; color only reinforces it.
- **Map colors identify, never rank.** Use them as a thick card edge or swatch beside a name.
- **No color on color.** Text sits on `--bg`, `--layer`, `--band` or `--emph-fill` only.

### Contrast (computed)

WCAG 2.x relative-luminance ratios, computed from the hex values above (2026-10-03). Text needs 4.5:1; large text (≥ 24 px at 1080p here) and meaningful graphics need 3:1.

| Foreground | Background | Ratio | Use | Result |
|---|---|---:|---|---|
| `--text` #161616 | `--bg` #f3efe4 | 15.75 | text on paper | pass |
| `--text` #161616 | `--layer` #fbf9f3 | 17.19 | text in panels | pass |
| `--text` #161616 | `--layer-hi` #e6dfcc | 13.61 | text on raised layer | pass |
| `--text-2` #4a463d | `--bg` #f3efe4 | 8.18 | labels on paper | pass |
| `--text-2` #4a463d | `--layer` #fbf9f3 | 8.93 | labels in panels | pass |
| `--band-text` #ffffff | `--band` #000000 | 21.00 | band title | pass |
| `--band-text-2` #bdbdbd | `--band` #000000 | 11.18 | band eyebrow | pass |
| `--text-on-emph` #ffffff | `--emph-fill` #000000 | 21.00 | text on the black block | pass |
| `--caption-fg` #ffffff | caption backing over `--layer` (#1e1e1d) | 16.68 | captions, worst case | pass |
| `--emph` #b2322a | `--bg` #f3efe4 | 5.40 | route red text and rules on paper | pass |
| `--emph` #b2322a | `--layer` #fbf9f3 | 5.90 | ring inside panels | pass |
| `--emph` #b2322a | `--band` #000000 | 3.38 | **not allowed for text**; graphics only | 3:1 only |
| `--emph-fill` #000000 | `--bg` #f3efe4 | 18.28 | black block edge | pass |
| `--line` #1f1f1f | `--bg` #f3efe4 | 14.35 | panel border | pass |
| `--ok` #2f6b34 | `--layer` #fbf9f3 | 6.09 | tick glyph | pass |
| `--warn` #8a5a00 | `--bg` #f3efe4 | 5.16 | warning glyph | pass |
| `--err` #a01f1a | `--bg` #f3efe4 | 6.76 | error glyph | pass |
| `--data-1` #3f6e3a | `--layer` #fbf9f3 | 5.69 | identity edge | pass (3:1) |
| `--data-2` #2f6797 | `--layer` #fbf9f3 | 5.69 | identity edge | pass (3:1) |
| `--data-3` #a8741a | `--layer` #fbf9f3 | 3.85 | identity edge | pass (3:1); not for text |
| `--data-4` #7b4a2a | `--layer` #fbf9f3 | 6.99 | identity edge | pass (3:1) |
| `--data-5` #6b6b6b | `--layer` #fbf9f3 | 5.06 | identity edge | pass (3:1) |
| `--line-faint` #cfc6b0 | `--bg` #f3efe4 | 1.48 | fold-line guides | decorative only |

## Typography

The source page says the original Unigrid faces were Helvetica and Times Roman, and that today's standard faces are Frutiger and NPS Rawlinson (source). All four are proprietary or not licensed for this use, so this preset substitutes open faces from one superfamily, all SIL OFL 1.1:

| Original | Substitute | Why |
|---|---|---|
| Frutiger (humanist sans) | **Source Sans 3** | open humanist sans with similar open apertures and calm width |
| NPS Rawlinson (text serif) | **Source Serif 4** | open text serif with sturdy slab-like serifs; reads as a park-guide text voice |
| (none; terminals need a mono) | **Source Code Pro** | matches the superfamily |

Load them from local `woff2` files with `@font-face`; do not rely on system fonts. Fallbacks are generic `sans-serif`, `serif` and `monospace` only, so a missing file shows up as an obvious fallback in stills.

| Role | Family | Size at 1080p | Weight | Line height | Tracking | Case | Basis |
|---|---|---:|---:|---:|---:|---|---|
| Display (cover and end title, in the band) | Sans | 96 px | 700 | 1.05 | −0.015 em | title | workshop |
| H1 (scene title, in the band) | Sans | 72 px | 700 | 1.05 | −0.015 em | sentence | workshop |
| H2 (box names, step names) | Serif | 48 px | 400 | 1.1 | 0 | sentence | workshop |
| Body (field values, card names, tiles) | Serif | 36 px (tiles 30 px) | 400 | 1.4 (1.2–1.3 in tight boxes) | 0 | sentence | workshop |
| Caption | Sans | 36 px | 400 | 1.35 | 0 | sentence | workshop |
| Label / eyebrow | Sans | 30 px | 600 | 1.2 | +0.06 em | UPPERCASE | workshop |
| Code / terminal | Mono | 32 px | 400 | 48 px | 0 | as typed | workshop |

Hierarchy: the band title is bold sans, white on black; everything below the band speaks in the serif, with small tracked sans labels as map-legend captions. Weight carries hierarchy; color does not. Serif 600 and Mono 500 are loaded for rare strong emphasis; the reference video does not use them. Never use italic or condensed faces. Nothing on screen is smaller than 30 px.

## Layout

The Unigrid is a print grid; this preset maps it onto 16:9 as follows.

- **Print facts (source):** the building block is a 4 × 8¼ inch panel defined by fold lines; sheets are one or two panels wide ("A" or "B" formats) and up to six panels long; the black band runs across the top.
- **16:9 adaptation (adapted):** treat the 1920×1080 frame as an unfolded **four-panel sheet seen sideways**. Scale is 112.5 px per inch, so one panel is 450 px wide (4 in). Four panels are 1800 px, leaving 60 px (`--fold-0`) at each side. The band takes the top 180 px (`--band-h`, 1.6 in at this scale; the real band depth is **unverified**). The panel area below is 900 px tall, a 1:2 panel against the print 1:2.06; the 8¼ in height is shortened by about 3 % to fit. Fold lines sit at x = 60, 510, 960, 1410 and 1858 px and are drawn as faint guides on the cover only.
- **Content grid (workshop):** inside the panels, positions snap to a 30 px unit `--u`, with a 120 px reading margin `--margin` on both sides; `--col` 240 px remains for box widths. Content need not respect fold lines (later Unigrids "unify images, text, and maps", source), but text must never sit across a visible fold guide.
- **Band contents:** scene title at the left margin, vertically centered; the eyebrow (`STEP 1`) right-aligned at the right margin in `--band-text-2`. The band stays on screen for the whole film; only its words change, so every scene reads as the same brochure.
- **Caption zone:** the bottom band from y = 900 to 1020 px (`--caption-bottom` 60 px, `--caption-h` 120 px), inset by the margins. No content enters it. Captions sit on a small black band of their own.
- Content sits between y ≈ 240 and 870 px, left-aligned, read left to right like a brochure panel.

## Visual language

- The black title band on every scene. On the cover and end card the band holds the display title.
- Flat panels on `--layer` with a 3 px black border; 0 radius. Panels read like brochure boxes and map insets.
- Connections are route lines: 3 px `--emph` red rules that draw from their origin and end in a solid red triangular arrowhead, like a road on a park map.
- Identity uses a thick left edge (0.4 `--u`) in a map color: green, water blue, ochre, earth brown, always next to a name.
- One filled black block below the band per scene marks the subject.
- A 3 px red outline ring marks "current" or "selected".
- Fold-line guides (2 px `--line-faint`) fade in under the band on the cover only.
- Terminal panels: a sans label bar, mono text, prompt lines in route red.
- Step numbers as small sans labels (`01`, `02`); check chips show scene numbers in the serif at H2 size; ticks in `--ok`.
- No arrowhead emblem, no agency sign-off, no park photographs. Illustration means diagrams drawn from these parts.

## Motion

Calm and placed, like layers laid onto a page. Elements slide half the base distance (`--slide-scale` 0.5) and settle with a gentle ease-out; rules draw at an even pace like a pen on a map.

| Token | Value | Use | Basis |
|---|---|---|---|
| `--ease-standard` | `cubic-bezier(0.45, 0, 0.55, 1)` | rules drawing, color changes, fades | workshop (sine in-out) |
| `--ease-entrance` | `cubic-bezier(0.25, 0.1, 0.25, 1)` | elements entering | workshop |
| `--ease-exit` | `cubic-bezier(0.55, 0, 1, 0.45)` | elements leaving | workshop |
| `--ease-expressive` | `cubic-bezier(0.16, 1, 0.3, 1)` | band title on the cover and end card | workshop |
| `--dur-fast` | 300 ms | small elements, rings, exits | workshop |
| `--dur-base` | 560 ms | panels, cards | workshop |
| `--dur-slow` | 900 ms | titles, long rules | workshop |
| `--stagger` | 160 ms | delay between items in a sequence | workshop |
| `--slide-scale` | 0.5 | multiplier on every entrance slide distance | workshop |

Rules: every element enters on the narration cue that names it, with a short slide and a fade. Route lines draw from their origin. The band never moves; scene words in it fade out and in. Each scene's content fades out over `--dur-fast` just before the next scene; no wipes, zooms, bounces, spins or loops. Easing, durations and slide scale are read from these tokens at run time, never typed into scene code.

## Narration voice

Informative and welcoming, like the text panel of a public brochure: plain words, complete sentences, second person ("you"), present tense. State what happens in order, with plain sequence words ("Start by", "Next", "Last"). One idea per sentence. Tone and register only: no puns or wordplay on parks, trails, routes or maps. No hype, no rhetorical questions, no colons or dashes in spoken text, no "X, not Y" constructions. The reference video used local Kokoro `af_heart` at speed 0.92 (workshop choice; any calm, warm voice fits) and measured about 145 words per minute overall (109 words in 45.0 s, including pauses); aim for 140–150.

## Accessibility

- Burned-in captions on every spoken sentence, in the caption zone, 36 px sans, white on a black caption band, balanced line breaks, at most two lines; also ship `captions.vtt`.
- All text pairs above pass 4.5:1; the lowest text pair in use is 5.40:1 (route red on paper). Route red is never used as text in the band.
- Meaning never depends on color alone: status uses ticks, selection uses an outline ring and a black fill, identity colors are paired with names.
- Minimum on-screen text 30 px at 1080p. Hold every text element on screen for at least the length of the sentence that introduces it.
- No flashing, looping or strobing motion.

## Tokens

```css
@font-face { font-family: "Source Sans 3"; font-weight: 400; src: url("fonts/source-sans-3-latin-400-normal.woff2") format("woff2"); }
@font-face { font-family: "Source Sans 3"; font-weight: 600; src: url("fonts/source-sans-3-latin-600-normal.woff2") format("woff2"); }
@font-face { font-family: "Source Sans 3"; font-weight: 700; src: url("fonts/source-sans-3-latin-700-normal.woff2") format("woff2"); }
@font-face { font-family: "Source Serif 4"; font-weight: 400; src: url("fonts/source-serif-4-latin-400-normal.woff2") format("woff2"); }
@font-face { font-family: "Source Serif 4"; font-weight: 600; src: url("fonts/source-serif-4-latin-600-normal.woff2") format("woff2"); }
@font-face { font-family: "Source Code Pro"; font-weight: 400; src: url("fonts/source-code-pro-latin-400-normal.woff2") format("woff2"); }
@font-face { font-family: "Source Code Pro"; font-weight: 500; src: url("fonts/source-code-pro-latin-500-normal.woff2") format("woff2"); }
:root {
  --bg: #f3efe4; --layer: #fbf9f3; --layer-hi: #e6dfcc; --line: #1f1f1f; --line-faint: #cfc6b0;
  --text: #161616; --text-2: #4a463d; --text-on-emph: #ffffff;
  --emph: #b2322a; --emph-fill: #000000;
  --band: #000000; --band-text: #ffffff; --band-text-2: #bdbdbd;
  --ok: #2f6b34; --warn: #8a5a00; --err: #a01f1a;
  --data-1: #3f6e3a; --data-2: #2f6797; --data-3: #a8741a; --data-4: #7b4a2a; --data-5: #6b6b6b;
  --font-sans: "Source Sans 3", sans-serif; --font-serif: "Source Serif 4", serif; --font-mono: "Source Code Pro", monospace;
  --font-body: var(--font-serif); --font-head: var(--font-sans); --font-label: var(--font-sans);
  --w-light: 400; --w-regular: 400; --w-strong: 600; --w-bold: 700;
  --fs-display: 96px; --fs-h1: 72px; --fs-h2: 48px; --fs-body: 36px; --fs-label: 30px; --fs-code: 32px; --fs-caption: 36px;
  --lh-display: 1.05; --lh-body: 1.4; --ls-display: -0.015em; --ls-label: 0.06em; --label-case: uppercase; --w-label: 600;
  --w-display: var(--w-bold); --w-heading: var(--w-bold);
  --u: 30px; --cols: 8; --col: 240px; --margin: 120px; --gutter: 30px; --caption-bottom: 60px; --caption-h: 120px;
  --band-h: 180px; --panel: 450px; --fold-0: 60px;
  --radius: 0px; --stroke: 3px; --caption-bg: rgba(0, 0, 0, 0.88); --caption-fg: #ffffff;
  --slide-scale: 0.5;
  --ease-standard: cubic-bezier(0.45, 0, 0.55, 1); --ease-entrance: cubic-bezier(0.25, 0.1, 0.25, 1);
  --ease-exit: cubic-bezier(0.55, 0, 1, 0.45); --ease-expressive: cubic-bezier(0.16, 1, 0.3, 1);
  --dur-fast: 300ms; --dur-base: 560ms; --dur-slow: 900ms; --stagger: 160ms;
}
```

Tokens beyond the IBM preset's set: `--band`, `--band-text`, `--band-text-2`, `--font-serif`, `--font-body`, `--font-head`, `--font-label`, `--w-bold`, `--w-label`, `--band-h`, `--panel`, `--fold-0`, `--caption-fg`, `--slide-scale`. The composition must read the body, heading and label families, the label weight, caption color and slide scale from these tokens. `--gutter`, `--cols` and `--layer-hi` are defined for layouts that need them; the reference video uses none of them.

## Assets and licenses

| Asset | Where to get it | License | Video use |
|---|---|---|---|
| Source Sans 3 Regular, SemiBold, Bold (latin `woff2`) | npm `@fontsource/source-sans-3` 5.3.0 | SIL OFL 1.1 | allowed; embed or render freely; do not sell the font files alone |
| Source Serif 4 Regular, SemiBold (latin `woff2`) | npm `@fontsource/source-serif-4` 5.3.0 | SIL OFL 1.1 | as above |
| Source Code Pro Regular, Medium (latin `woff2`) | npm `@fontsource/source-code-pro` 5.3.0 | SIL OFL 1.1 | as above |

Ship the OFL texts beside the font files (`OFL-Source-Sans-3.txt`, `OFL-Source-Serif-4.txt`, `OFL-Source-Code-Pro.txt`). No other assets are needed. Do not use the NPS arrowhead, any NPS or Department of the Interior emblem, NPS Rawlinson, Frutiger, or park photographs or illustrations without a checked license.

## Provenance

Read on 2026-10-03 (direct `curl` of the public pages; text read, not just search results):

- [NPS Harpers Ferry Center, "A Brief History of the Unigrid"](https://www.nps.gov/subjects/hfc/a-brief-history-of-the-unigrid.htm) (last updated March 10, 2023): 1977 origin with Massimo Vignelli; "a comprehensive graphic design system that standardizes formatting and production"; 4 × 8¼ inch panels defined by fold lines, "A" or "B" formats, up to six panels long, sized for a 25 × 38 inch press sheet; original faces Helvetica and Times Roman, today Frutiger and NPS Rawlinson; the arrowhead first appeared in the black band in 1999; the grid "sets physical boundaries … yet allows for a great deal of flexibility"; later designs favor the "uni", unifying images, text and maps.
- [NPS Harpers Ferry Center, "Publications"](https://www.nps.gov/subjects/hfc/publications.htm): "black-band brochures"; maps, illustrations and text as the brochure's main parts; accessible formats (audio-described, large print, braille).
- [NPS Harpers Ferry Center, "National Park Service Style Guides"](https://www.nps.gov/subjects/hfc/national-park-service-style-guides.htm): editorial principles "clarity, simplicity, and nonbiased language"; arrowhead use is governed by NPS Brand Management, which is why this preset excludes it.

Workshop adaptations, not from any NPS source: every hex value and color role (including the paper, route red and map colors), the 16:9 mapping (112.5 px per inch, 180 px band, four 450 px panels, 60 px side margins), the type substitutions and scale, the 30 px unit and 120 px reading margin, the caption band, all motion values, the narration voice, and the accessibility rules. Contrast ratios are computed by the workshop from the hex values.

Not checked: the Unigrid specification itself (band depth, title type size and position, rule weights, NPS map color specifications). The Harpers Ferry Center pages read here describe the system but do not publish its measurements. If you need closer fidelity, find the HFC publication standards and revise this file.

Revision history: 1 (2026-10-03) first version, written with the reference video `outputs/explainer-about-explainers-nps-unigrid`.
