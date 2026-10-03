# Airbnb-inspired — video style preset

Status: workshop preset, revision 1 (2026-10-03). This is an original workshop style that borrows the warmth of Airbnb's public identity. It is **not** Airbnb's brand, it is not endorsed by Airbnb, and it uses no Airbnb logo, no Bélo symbol, no wordmark and no Airbnb typeface. Name it "Airbnb-inspired" wherever a viewer can see the name.

This file is self-contained: a video agent can build a 1920×1080 explainer from it alone. The CSS block in "Tokens" is the exact token set. Copy it into the run's `tokens.css` unchanged. The reference implementation is `outputs/explainer-about-explainers-airbnb/production/src/tokens.css` (git-ignored run output).

No comprehensive, current, public Airbnb brand manual was found. The 2014 identity is documented only by a design-studio case study and press coverage, which describe the idea but give no colors, type sizes or motion values. Concrete values here come from CSS custom properties observed in the public airbnb.com page source (an implementation, not a published guideline). See Provenance.

Value labels used below: **source** = read in a public source listed in Provenance; **observed** = found as a value in airbnb.com's page CSS on 2026-10-03 (implementation, may change without notice; role names are Airbnb's CSS names, not documented rules); **adapted** = a workshop choice built on a source or observed value; **workshop** = a workshop choice with no source value; **unverified** = believed true but not checked in this revision.

## Character

- **Feel:** warm, human, welcoming, grounded in real situations. A light, warm off-white canvas, white rounded cards with soft shadows, one warm coral-red accent, friendly rounded sans type in sentence case, generous space. Diagrams feel like a host showing you around: a few clear objects, gentle connections, nothing mechanical. (Adapted from the sources: "Belong Anywhere", "warmth and welcome", "about people and not about the places", a symbol "simple enough to be drawn by anyone", "a simple font" chosen for readers less used to Roman characters.)
- **Avoid:** dark canvases, hard square corners, grid lines, all-caps labels, heavy borders, gradients on text, more than one accent meaning, cold technical "system drawing" layouts, busy illustration, emoji, stock photos of people, any Airbnb logo, Bélo or Bélo-like loop, wordmark, or Airbnb Cereal.

## Color

Light theme only. Every hex below is used as given; no tints are derived except the caption backing (alpha) and the shadow (black at low alpha).

| Token | Hex | Role | Basis |
|---|---|---|---|
| `--bg` | `#f7f6f2` | warm canvas | observed (`--palette-beige100`), adapted role |
| `--layer` | `#ffffff` | cards, tiles, panels | observed (`--palette-bg-primary`) |
| `--layer-hi` | `#fff5f6` | selected tint (defined, not used in the reference video) | observed (`--palette-rausch100`), adapted role |
| `--line` | `#dddddd` | card borders (1 px), inactive connectors | observed (`--palette-border-secondary`) |
| `--line-faint` | `#ebebeb` | dividers (defined, not used in the reference video) | observed (`--palette-bg-divider`) |
| `--text` | `#222222` | primary text | observed (`--palette-hof`, `--palette-bg-primary-inverse`) |
| `--text-2` | `#6a6a6a` | secondary text, labels | observed (`--palette-foggy`) |
| `--text-on-emph` | `#ffffff` | text on the emphasis fill | observed (`--palette-text-on-brand`) |
| `--emph` | `#da1249` | emphasis text, selection rings, active connectors, connector dots | observed (`--palette-text-brand`, `--palette-rausch700`) |
| `--emph-fill` | `#e00b41` | emphasis fill (the one solid coral-red block per scene) | observed (`--palette-product-rausch`), adapted role |
| `--ok` | `#008a05` | success tick (always a glyph) | observed (`--palette-spruce`), adapted role |
| `--warn` | `#e07912` | warning glyph, on `--layer` only (defined, not used in the reference video) | observed (`--palette-ondo`), adapted role |
| `--err` | `#c13515` | error glyph (defined, not used in the reference video) | observed (`--palette-arches`) |
| `--data-1` | `#ff385c` | identity color 1 (card edge) | observed (`--palette-rausch`, the familiar coral) |
| `--data-2` | `#e07912` | identity color 2 | observed (`--palette-ondo`) |
| `--data-3` | `#503eb2` | identity color 3 | observed (avatar text, purple) |
| `--data-4` | `#0d4daa` | identity color 4 | observed (avatar text, blue) |
| `--data-5` | `#92174d` | identity color 5 (defined, not used in the reference video) | observed (`--palette-bg-primary-plus`) |
| `--caption-bg` | `rgba(255, 255, 255, 0.96)` | caption pill (`--layer` at 96 %) | workshop |
| `--shadow` | `0 0 0 1px rgba(0,0,0,0.02), 0 8px 24px rgba(0,0,0,0.1)` | soft lift under cards, tiles, captions | adapted from observed `--elevation-elevation3-box-shadow` (`color-mix` rewritten as `rgba`) |

Why two reds: the familiar coral `#ff385c` gives white text only 3.52:1, so it never carries text. Text and fills use the deeper observed reds `#da1249` and `#e00b41`; the coral appears only as an identity edge (graphic, 3:1 rule).

Rules:

- **One meaning for red.** `--emph`/`--emph-fill` mean "look here now". At most one filled red block per scene.
- **Status needs a glyph.** A tick, cross or word carries the meaning; color only reinforces it.
- **Data colors identify, never rank.** Use them as a card edge or swatch, never as body text color and never as the only way to tell items apart.
- **No color on color.** Text sits on `--bg`, `--layer`, the caption pill or `--emph-fill` only.

### Contrast (computed)

WCAG 2.x relative-luminance ratios, computed by script from the hex values above (2026-10-03). Text needs 4.5:1; large text (≥ 24 px at 1080p here) and meaningful graphics need 3:1. The caption worst case is the 96 % white pill over the red fill (#fef5f7).

| Foreground | Background | Ratio | Use | Result |
|---|---|---:|---|---|
| `--text` #222222 | `--bg` #f7f6f2 | 14.71 | headings, body on canvas | pass |
| `--text` #222222 | `--layer` #ffffff | 15.91 | text in cards | pass |
| `--text` #222222 | `--layer-hi` #fff5f6 | 14.88 | text on selected tint | pass |
| `--text` #222222 | caption pill over `--emph-fill` (#fef5f7) | 14.86 | captions, worst case | pass |
| `--text-2` #6a6a6a | `--bg` #f7f6f2 | 5.00 | labels on canvas | pass |
| `--text-2` #6a6a6a | `--layer` #ffffff | 5.41 | labels in cards | pass |
| `--emph` #da1249 | `--bg` #f7f6f2 | 4.66 | emphasis text on canvas | pass |
| `--emph` #da1249 | `--layer` #ffffff | 5.04 | emphasis text in cards | pass |
| `--text-on-emph` #ffffff | `--emph-fill` #e00b41 | 4.89 | text on the red block | pass |
| `--emph-fill` #e00b41 | `--bg` #f7f6f2 | 4.52 | red block edge (graphic) | pass (3:1) |
| `--ok` #008a05 | `--layer` #ffffff | 4.53 | tick glyph | pass |
| `--warn` #e07912 | `--layer` #ffffff | 3.04 | warning glyph | pass (3:1), glyph only, on `--layer` only |
| `--warn` #e07912 | `--bg` #f7f6f2 | 2.81 | — | **fails 3:1: never on the canvas** |
| `--err` #c13515 | `--bg` #f7f6f2 | 5.13 | error glyph | pass |
| `--data-1` #ff385c | `--layer` #ffffff | 3.52 | identity edge | pass (3:1) |
| `--data-2` #e07912 | `--layer` #ffffff | 3.04 | identity edge | pass (3:1) |
| `--data-3` #503eb2 | `--layer` #ffffff | 7.86 | identity edge | pass (3:1) |
| `--data-4` #0d4daa | `--layer` #ffffff | 7.90 | identity edge | pass (3:1) |
| `--data-5` #92174d | `--layer` #ffffff | 8.56 | identity edge | pass (3:1) |
| `--line` #dddddd | `--bg` #f7f6f2 | 1.26 | card border, inactive connector | **decorative only.** The shadow and the card's own text name the card; a border is never the only cue |
| `--line-faint` #ebebeb | `--layer` #ffffff | 1.19 | dividers | decorative only |

## Typography

Airbnb uses its proprietary typeface Airbnb Cereal (observed in the page CSS as `'Airbnb Cereal VF'`, with `Circular` as the next fallback). It is not licensed for this use. **Substitute: DM Sans** (Colophon Foundry for Google Fonts, SIL OFL 1.1), a low-contrast geometric sans with round bowls and open shapes that reads close to Cereal's friendly tone at video sizes. **DM Mono** (same family, SIL OFL 1.1) is used only for typed commands and file names. Load both from local files with `@font-face`; fallbacks are generic `sans-serif` and `monospace` only, so a missing file shows as an obvious fallback in stills. The match to Cereal is a workshop judgment by eye, not a metric comparison.

| Role | Family | Size at 1080p | Weight | Line height | Tracking | Case | Basis |
|---|---|---:|---:|---:|---:|---|---|
| Display (title, end card) | DM Sans | 96 px | 700 | 1.1 | −0.02 em | sentence | workshop |
| H1 (scene head) | DM Sans | 64 px | 600 | 1.1 | −0.02 em | sentence | workshop |
| H2 (box names, step names, chip numbers) | DM Sans | 44 px | 400 | 1.1 | 0 | sentence | workshop |
| Body (field values, card names) | DM Sans | 36 px | 400 | 1.4 (1.2–1.3 in tight boxes) | 0 | sentence | workshop |
| Caption | DM Sans | 36 px | 400 | 1.35 | 0 | sentence | workshop |
| Label / eyebrow | DM Sans | 30 px | 500 | 1.2 | 0 | sentence | workshop |
| Code / terminal, file names | DM Mono | 30 px | 400 | 48 px | 0 | as typed | workshop |

Hierarchy: a small grey sentence-case eyebrow ("Step 1") over a bold, tightly tracked headline, then content. Weight and size carry hierarchy; color does not. Never use all caps, italics, or weights above 700. Nothing on screen is smaller than 30 px. Labels use `--font-label` (DM Sans), not the mono face.

## Layout

- Canvas 1920×1080. Base unit `--u` = 30 px; positions and sizes are multiples of 30 px (half units only for optical centring). 8 columns of 240 px, outer margin `--margin` 120 px. All **workshop** (the sources give no video grid); the grid is for placement only and is never drawn (`--guide-w: 0px`).
- Caption zone: the bottom band from y = 900 to 1020 px (`--caption-bottom` 60 px, `--caption-h` 120 px), inset by the margins. No content enters it.
- Title and end card are **centered**: a welcoming front door. Content scenes put a small eyebrow at y = 90 px and the headline at y = 135 px, top left, with content between y ≈ 270 and 870 px.
- Generous space: few objects per scene, at least one unit of air between cards, and empty canvas left empty rather than filled.

## Visual language

- White cards on the warm canvas: `--radius` 24 px corners, a 1 px `--line` border and the soft `--shadow`. No hard edges, no heavy outlines. (Rounded corners and soft elevation: observed `--corner-radius-*` 4–32 px and `--elevation-*` shadows; the 24 px choice is adapted.)
- Option tiles and selection rings are pills (`--radius-pill`); the S05 scene checks are circles.
- Connections are 4 px (`--stroke`) lines with round ends that finish in a round `--dot` (18 px) in `--emph`. No arrowheads, no right-angle system drawings beyond the one fan-out spine.
- One filled `--emph-fill` card per scene marks the subject (the video, the chosen style, the skill).
- A 4 px `--emph` pill or rounded ring marks "current" or "selected".
- Identity colors appear as a thick rounded left edge on a card.
- Terminal: a white card with a sentence-case label bar, DM Mono text, the agent's question in `--emph`.
- Numbers (`01`, `02`) are DM Sans; ticks in `--ok` mark completed checks.
- No logos, symbols, photographs, illustrations or icons beyond ticks and dots. Do not draw loops, hearts, location pins or an "A" that could read as the Bélo.

## Motion

| Token | Value | Use | Basis |
|---|---|---|---|
| `--ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` | lines growing, color changes, fades | observed (`--motion-standard-curve`) |
| `--ease-entrance` | `cubic-bezier(0.1, 0.9, 0.2, 1)` | elements entering: quick start, long soft landing | observed (`--motion-enter-curve`) |
| `--ease-exit` | `cubic-bezier(0.4, 0, 1, 1)` | elements leaving | observed (`--motion-exit-curve`) |
| `--ease-expressive` | `cubic-bezier(0.34, 1.36, 0.64, 1)` | title, the "Video" result card, end card: a gentle overshoot | workshop, approximating the observed `--motion-springs-*-bounce` springs |
| `--dur-fast` | 250 ms | small elements, rings, exits | workshop |
| `--dur-base` | 450 ms | cards, tiles | adapted (observed `--motion-springs-fast-duration` ≈ 452 ms) |
| `--dur-slow` | 750 ms | titles, long lines | adapted (observed `--motion-springs-slow-duration` ≈ 746 ms) |
| `--stagger` | 100 ms | delay between items in a sequence | workshop |

Rules: every element arrives on the narration cue that names it, with a short slide and fade that lands softly. Lines draw from their origin and end in a dot. Lists stagger. Only the title, the result card and the end card overshoot, and only once; nothing loops, spins or pulses. Each scene fades out over `--dur-fast` just before the next begins. Easing and durations are read from these tokens at run time, never typed into scene code.

## Narration voice

Warm, welcoming, second person, present tense, like a good host showing a guest around. Short sentences, one idea each, plain words, a little hospitality ("Welcome", "make yourself at home") but no hype, no rhetorical questions, no colons or em dashes in spoken text. Ground each line in what you actually do. The reference video used local Kokoro `af_heart` at speed 0.92 (workshop choice; any warm, calm voice fits). It measured about 150 words per minute (116 words in 46.3 s including pauses).

## Accessibility

- Burned-in captions on every spoken sentence, in the caption zone, 36 px, on the white rounded caption pill, balanced line breaks, at most two lines; also ship `captions.vtt`.
- All text pairs above pass 4.5:1; the lowest is 4.66:1 (`--emph` on the canvas). The coral `#ff385c` never carries text.
- Meaning never depends on color alone: status uses ticks, selection uses a ring or fill plus position, identity colors are paired with names.
- Minimum on-screen text 30 px at 1080p. Hold each text element at least for the sentence that introduces it.
- No flashing, looping or strobing. The overshoot is small (about 4 % past rest, computed from the curve) and happens at most three times per video.

## Tokens

This block is byte-identical to the reference `tokens.css`. It defines every custom property of the IBM-inspired preset (same names) plus the shape tokens this style needs: `--font-label`, `--w-bold`, `--w-label`, `--radius-pill`, `--border`, `--dot`, `--guide-w`, `--shadow`, `--caption-radius`. A composition that predates these tokens needs the small CSS overrides listed under "Assets and licenses".

```css
/* STYLE TOKENS: the only place that holds colors, fonts, type scale, grid, shapes, easing and durations.
   Mirrors templates/brands/airbnb.md. A new style replaces this file. */
@font-face { font-family: "DM Sans"; font-weight: 100 1000; src: url("fonts/DMSans-VF.ttf") format("truetype"); }
@font-face { font-family: "DM Mono"; font-weight: 400; src: url("fonts/DMMono-Regular.ttf") format("truetype"); }
@font-face { font-family: "DM Mono"; font-weight: 500; src: url("fonts/DMMono-Medium.ttf") format("truetype"); }
:root {
  /* color: background */
  --bg: #f7f6f2;          /* warm canvas */
  --layer: #ffffff;       /* cards, tiles, panels */
  --layer-hi: #fff5f6;    /* selected tint */
  --line: #dddddd;        /* card borders, inactive connectors */
  --line-faint: #ebebeb;  /* dividers */
  /* color: text */
  --text: #222222;        /* primary text */
  --text-2: #6a6a6a;      /* secondary text, labels */
  --text-on-emph: #ffffff;
  /* color: emphasis (one meaning: "this is the thing to look at") */
  --emph: #da1249;        /* emphasis text, rings, active connectors, dots */
  --emph-fill: #e00b41;   /* emphasis fill */
  /* color: status (always paired with a glyph or word) */
  --ok: #008a05;
  --warn: #e07912;
  --err: #c13515;
  /* color: data (identity only, never the sole carrier of meaning) */
  --data-1: #ff385c;
  --data-2: #e07912;
  --data-3: #503eb2;
  --data-4: #0d4daa;
  --data-5: #92174d;
  /* fonts and weights */
  --font-sans: "DM Sans", sans-serif;
  --font-mono: "DM Mono", monospace;
  --font-label: var(--font-sans);
  --w-light: 400;
  --w-regular: 400;
  --w-strong: 600;
  --w-bold: 700;
  --w-label: 500;
  /* type scale at 1920x1080 */
  --fs-display: 96px;
  --fs-h1: 64px;
  --fs-h2: 44px;
  --fs-body: 36px;
  --fs-label: 30px;
  --fs-code: 30px;
  --fs-caption: 36px;
  --lh-display: 1.1;
  --lh-body: 1.4;
  --ls-display: -0.02em;
  --ls-label: 0em;
  --label-case: none;
  --w-display: var(--w-bold);
  --w-heading: var(--w-strong);
  /* grid: 30px unit, 8 columns of 240px, margin = half a column */
  --u: 30px;
  --cols: 8;
  --col: 240px;
  --margin: 120px;
  --gutter: 30px;
  --caption-bottom: 60px;
  --caption-h: 120px;
  /* surface and shape: rounded, soft, no grid lines */
  --radius: 24px;
  --radius-pill: 999px;
  --border: 1px;
  --stroke: 4px;
  --dot: 18px;
  --guide-w: 0px;
  --shadow: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 8px 24px rgba(0, 0, 0, 0.1);
  --caption-bg: rgba(255, 255, 255, 0.96);
  --caption-radius: 16px;
  /* motion: soft decelerating entrances, a gentle overshoot only for the title, the result and the closing card */
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --ease-entrance: cubic-bezier(0.1, 0.9, 0.2, 1);
  --ease-exit: cubic-bezier(0.4, 0, 1, 1);
  --ease-expressive: cubic-bezier(0.34, 1.36, 0.64, 1);
  --dur-fast: 250ms;
  --dur-base: 450ms;
  --dur-slow: 750ms;
  --stagger: 100ms;
}
```

`--gutter`, `--cols`, `--w-light`, `--layer-hi`, `--line-faint` (the zero-width guides only), `--warn`, `--err` and `--data-5` are defined but unused in the reference video.

## Assets and licenses

| Asset | Where to get it | License | Video use |
|---|---|---|---|
| DM Sans variable (`DMSans-VF.ttf`, opsz + wght axes; file `ofl/dmsans/DMSans[opsz,wght].ttf`) | github.com/google/fonts, `main` branch, fetched 2026-10-03 | SIL OFL 1.1 | allowed; embed or render freely; do not sell the font files alone |
| DM Mono Regular, Medium (`DMMono-Regular.ttf`, `DMMono-Medium.ttf`) | github.com/google/fonts `ofl/dmmono/` | SIL OFL 1.1 | as above |

Ship the OFL texts (`OFL-DMSans.txt`, `OFL-DMMono.txt`) beside the font files. No other assets are needed. Never use Airbnb Cereal, the Bélo symbol, the Airbnb wordmark, Airbnb photography, or a look-alike loop symbol.

Composition overrides used by the reference video (shape only; every value comes from a token): labels use `--font-label`/`--w-label`; panels and tiles use a `--border` border and `--shadow`; tiles use `--radius-pill`; rules have round ends; arrowheads are `--dot` circles; S05 check chips are circles; column guides use `--guide-w`; the caption span has `--caption-radius` and `--shadow`; the S01 title and S05 end card are centered.

## Provenance

Read on 2026-10-03 (direct `curl` of the public pages, text read; text receipts in the reference run's `production/sources/`):

- [Further (formerly DesignStudio), "Airbnb" case study](https://www.further.group/work/airbnb): the brand mission "Belong Anywhere"; "Airbnb is all about people and not about the places"; the Bélo as "a symbol that represents Belonging, transcends language and is simple enough to be drawn by anyone"; language shifted "from location and price to focus on the warmth and welcome"; photography and film "captured the real people and places". No colors, type or motion values.
- [Dezeen, "Airbnb rebrand by DesignStudio"](https://www.dezeen.com/2014/07/16/airbnb-rebrand-designstudio-logo-belo/) (16 July 2014): the symbol "that can be drawn by anyone", its meanings (person, location marker, upside-down heart, letter A), and "a simple font, chosen so that it could be more easily read by users who aren't used to reading Roman characters". No colors or sizes.
- [airbnb.com home page source](https://www.airbnb.com/): CSS custom properties for the palette (`--palette-rausch` `#FF385C`, `--palette-product-rausch` `#E00B41`, `--palette-text-brand` `#DA1249`, `--palette-hof` `#222222`, `--palette-foggy` `#6A6A6A`, beige scale, status colors), corner radii 4–32 px, elevation shadows, motion curves and spring durations, and the font stack `'Airbnb Cereal VF', 'Circular', …`. These are an implementation snapshot, not documented brand rules.
- Fonts: OFL texts and `METADATA.pb` (designer "Colophon Foundry", license "OFL") read from google/fonts.

**No comprehensive current public Airbnb brand manual was found**, so color roles, the type scale, layout, the narration voice and accessibility rules are workshop choices. **Unverified:** that `#FF5A5F` (seen once in the page source) was the 2014 "Rausch"; that the observed CSS names reflect Airbnb's internal design-system intent; any similarity in proportions between DM Sans and Cereal beyond visual judgment.

Workshop adaptations, not from any Airbnb source: every color **role**, the two-red rule, the type scale and tracking, the 30 px grid and margins, the caption zone and pill, the centered title and end card, the dot-ended connectors, circle chips, the overshoot curve, the stagger, the scene fade-out, the narration voice and the accessibility rules. Contrast ratios are computed by the workshop from the hex values.

Revision history: 1 (2026-10-03) first version, written with the reference video `outputs/explainer-about-explainers-airbnb`.
