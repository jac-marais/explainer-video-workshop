# Mozilla-inspired: video style preset

Status: workshop preset, revision 1 (2026-10-03). This is an original workshop style that borrows the look of Mozilla's public brand guidelines. It is **not** Mozilla's brand, it is not endorsed by Mozilla, and it uses no Mozilla logo, wordmark, flag symbol, mascot, pixel art or illustration. It uses only the openly licensed Mozilla Headline and Mozilla Text typefaces. Name it "Mozilla-inspired" wherever a viewer can see the name.

This file is self-contained: a video agent can build a 1920×1080 explainer from it alone. The CSS block in "Tokens" is the exact token set. Copy it into the run's `tokens.css` unchanged. The reference implementation is `outputs/explainer-about-explainers-mozilla/production/src/tokens.css` (git-ignored run output).

Value labels used below: **source** = read on a public Mozilla brand page (see Provenance); **adapted** = a workshop choice built on a source value or rule; **workshop** = a workshop choice with no source value.

## Character

- **Feel:** direct, warm, a bit bold. A light canvas, black type, one bright green used as a pop, flat boxes with heavy black outlines, big left-aligned headlines, numbers in condensed ExtraLight. Motion is precise and sequential: things type in, highlights sweep in behind words, one dark wipe per scene change.
- **Avoid:** colored text, gradients, shadows, rounded corners, emoji, stock imagery, centered layouts, bounce or overshoot, green as a large background, strong black or strong white as a background, any Mozilla logo, flag, wordmark or mascot, and pixel or glitch effects (they lean on brand artwork this preset does not use).

## Color

| Token | Hex | Role | Basis |
|---|---|---|---|
| `--canvas` | `#fafafa` | scene background, box fill | source ("White"), adapted role |
| `--field` | `#161616` | dark panels, terminal, caption backing, wipe, end card | source ("Black"), adapted role |
| `--ink` | `#000000` | all type and outlines on `--canvas` and `--pop` | source ("Strong Black") |
| `--ink-on-field` | `#ffffff` | all type on `--field` | source ("Strong White") |
| `--pop` | `#00d230` | highlight bars, selected tile, ticks' squares, progress fill, cursor on field, wipe edge | source ("Green"), adapted role |
| `--pop-soft` | `#d6ffcd` | soft highlight (defined, not used in the reference video) | source ("Green +1") |

Rules (source unless marked):

- About 45 % black, 45 % white, 10 % green. Green marks calls to action, highlights and framing or focus.
- Type is always Strong Black or Strong White. No colored text.
- Do not use Strong Black or Strong White as a background. (`#000` and `#fff` stay ink; the backgrounds are `#fafafa` and `#161616`.)
- Bright tones appear as pops only, never as a full background.
- **Adapted:** green on the light canvas is 1.96:1, so a green shape on `--canvas` always carries an `--ink` outline or `--ink` text. Green never carries meaning alone: a tick, a word or a position does.

### Contrast (computed)

WCAG 2.x relative-luminance ratios, computed by the workshop from the hex values (2026-10-03). Text needs 4.5:1; large text and meaningful graphics need 3:1.

| Foreground | Background | Ratio | Use | Result |
|---|---|---:|---|---|
| `--ink` #000000 | `--canvas` #fafafa | 20.12 | all type on the canvas | pass |
| `--ink-on-field` #ffffff | `--field` #161616 | 18.10 | terminal, captions, end card | pass |
| `--ink` #000000 | `--pop` #00d230 | 10.26 | type on a highlight bar or selected tile | pass |
| `--pop` #00d230 | `--field` #161616 | 8.84 | cursor and wipe edge on field | pass (3:1) |
| `--ink` #000000 | `--pop-soft` #d6ffcd | 19.04 | type on soft highlight | pass |
| `--field` #161616 | `--canvas` #fafafa | 17.34 | dark panel edge on canvas | pass (3:1) |
| `--pop` #00d230 | `--canvas` #fafafa | 1.96 | green shape on canvas | **fails 3:1: always ink-outlined** |
| `--pop-soft` #d6ffcd | `--canvas` #fafafa | 1.06 | soft highlight on canvas | **decorative only** |

Portal labelling error (found 2026-10-03). The color page's "Accessible Combinations" list labels "Strong Black on Green −1" as 19.04:1. Computed, `#000` on Green −1 `#28733f` is **3.61:1**; 19.04:1 is the ratio for Green **+1** `#d6ffcd`. The same list shows "Strong Black on Orange −1" as 18.67:1 and "Strong Black on Pink −1" as 19.18:1; computed with the page's own hex values (Orange −1 `#ff453f`, Pink −1 `#ae49ec`) they are **6.18:1** and **4.96:1**. Do not put black text on Green −1; white on Green −1 is 5.81:1. This preset uses none of those three colors.

## Typography

Families: **Mozilla Headline** (variable: width 75–125 %, weight 200–700) and **Mozilla Text** (variable: weight 200–700), SIL Open Font License 1.1. Load them from local files with `@font-face`; fallbacks are generic `sans-serif` only, so a missing file shows up in stills.

| Role | Family | Size at 1080p | Weight | Line height | Tracking | Basis |
|---|---|---:|---:|---:|---:|---|
| XL (title, end card) | Headline | 150 px | 600 | 0.9 | −0.02 em | adapted (headlines 90 %; XL tracking may go negative) |
| H1 (scene head) | Headline | 88 px | 600 | 0.9 | 0 | adapted |
| H2 (box, station names) | Headline | 52 px | 600 | 1.1 | 0 | adapted (subheads 110 %) |
| Big number | Headline, width 75 % | 108 px | 200 ExtraLight | 0.9 | −0.02 em | source (Condensed ExtraLight, −2 % for large numbers) |
| Body | Text | 36 px | 400 | 1.25 | 0 | adapted (body 125 %) |
| Terminal | Text | 34 px | 400 | 48 px | 0 | workshop |
| Label, eyebrow | Text | 30 px | 600 | 1.1 | 0 | workshop |
| Caption | Text | 38 px | 500 | 1.3 | 0 | workshop |

Rules: always left-aligned, sentence case (source). Hierarchy comes from size and weight, not color. Weight tokens 500 and 700 exist for emphasis; the reference video uses 500 and not 700. Nothing on screen is smaller than 30 px. Write "open source" and "internet" in sentence case.

## Layout

- Canvas 1920×1080, base unit `--u` 24 px; positions are multiples of a quarter unit (workshop).
- Outer margin `--margin` 144 px on the left; 12 columns of 136 px are defined for reference (`--cols`, `--col`), not used by the reference video (workshop).
- Scene head top left: eyebrow label at 4u (96 px), H1 at 6u (144 px). Content sits between about 9u and 28u, left-aligned to the margin, reading left to right. Leave the right side empty rather than stretching.
- Title and end card: eyebrow at 9u, XL lines from 12u.
- Caption zone: bottom band, `--caption-bottom` 48 px, `--caption-h` 136 px, inset by the margins. No content enters it.

## Visual language

- **Boxes:** `--canvas` fill, 4 px `--ink` outline, 0 radius.
- **Fields:** `--field` panels with `--ink-on-field` type for terminals and the end card.
- **Highlight focus** (adapted from the portal's typography motion): a `--pop` bar sweeps left to right behind black words.
- **Typing cursor** (adapted from the same source): characters appear one by one with a block cursor, `--pop` on a field and `--ink` on the canvas.
- **Selection:** a 4 px `--pop` frame on a field, or a `--pop` fill with black type on the canvas.
- **Progress and status:** a `--pop` bar fills an outlined rail. A completed step is a `--pop` square with an `--ink` outline and an `--ink` tick.
- **Connectors:** 4 px `--ink` rules with a solid triangular arrowhead.
- **Numbers:** condensed ExtraLight numerals (`01`–`05`) as station markers.
- **Scene transition:** one `--field` wipe with a 24 px `--pop` leading edge crosses left to right; the next scene swaps in under its middle.
- No logos, photographs, illustrations, pixel textures or icons beyond ticks and arrowheads.

## Motion

The portal defines three motion modes (Fearless, Optimistic, Insightful). This preset uses **Insightful** for all element motion ("precise movements, sequential reveals, deliberate transitions") and the portal's global transition curve for scene changes only.

| Token | Value | Use | Basis |
|---|---|---|---|
| `--ease-in` | `cubic-bezier(0.22, 1, 0.36, 1)` | every entrance, sweep, fill | source (Insightful in) |
| `--ease-out` | `cubic-bezier(0.64, 0, 0.78, 0)` | exits (defined; the reference video has none) | source (Insightful out) |
| `--ease-transition` | `cubic-bezier(0.68, 0, 0.12, 1)` | the scene wipe | source (global transition) |
| `--dur-in` | 330 ms | entrances | source (Insightful 0.33 s) |
| `--dur-out` | 330 ms | exits | source (Insightful 0.33 s) |
| `--dur-transition` | 800 ms | scene wipe | source (global 0.8 s) |
| `--dur-sweep` | 500 ms | highlight bars, progress fill | workshop |
| `--dur-char` | 30 ms | per typed character | workshop |
| `--stagger` | 110 ms | delay between items in a sequence | workshop |
| `--shift` | 32 px | entrance slide distance | workshop |

Rules: each element enters on the narration cue that names it, with a short slide and a fade. Lists stagger. Nothing loops, bounces, pulses or flashes. Every single animation finishes in under 1 s, well inside the portal's "keep critical animations under 5 seconds". Easing and durations are read from these tokens at run time, never typed into scene code.

Reduced-motion stance: a rendered MP4 cannot respond to a viewer's reduce-motion setting. This preset therefore keeps motion small (≤ 32 px slides, one wipe per scene change, no flashing: at most one wipe per scene, far below three per second) and never relies on animation alone. Every state change is also a lasting visual state (a tick, a filled bar, a frame). If a reduced-motion version is needed, render a second cut with all durations set to 0 ms and the wipe replaced by a cut.

## Narration voice

Adapted from the portal's voice guidance (passionate, welcoming, plain-spoken; fearless, optimistic, insightful): warm and direct, second person, contractions, short sentences, plain words, one idea per sentence, no Oxford comma, "internet" not "web", no hype. No mid-sentence colons or em dashes in spoken text. A question is fine as a welcoming opener. The reference video used local Kokoro `af_heart` at speed 0.92 (workshop choice) and measured 119 words in 46.2 s including pauses.

## Accessibility

- Burned-in captions on every spoken sentence: left-aligned, 38 px Mozilla Text 500, white on a `--field` backing, at most two balanced lines, in the caption zone. Also ship `captions.vtt`.
- Lowest text pair in use: 10.26:1 (black on green). Green on the light canvas (1.96:1) is never used without an ink outline.
- Meaning never depends on color alone: status uses ticks, selection uses a frame or position, highlights sit behind words that are also spoken.
- Minimum on-screen text 30 px at 1080p.
- No flashing or looping motion (see Motion for the reduced-motion stance).

## Tokens

```css
/* STYLE TOKENS: the only place that holds colors, fonts, type scale, grid, geometry, easing and durations.
   Mirrors templates/brands/mozilla.md exactly. A new style replaces this file. */
@font-face { font-family: "Mozilla Headline"; src: url("fonts/MozillaHeadline-VF.ttf") format("truetype"); font-weight: 200 700; font-stretch: 75% 125%; }
@font-face { font-family: "Mozilla Text"; src: url("fonts/MozillaText-VF.ttf") format("truetype"); font-weight: 200 700; }
:root {
  /* color */
  --canvas: #fafafa;
  --field: #161616;
  --ink: #000000;
  --ink-on-field: #ffffff;
  --pop: #00d230;
  --pop-soft: #d6ffcd;
  /* fonts and weights */
  --font-head: "Mozilla Headline", sans-serif;
  --font-text: "Mozilla Text", sans-serif;
  --w-xlight: 200;
  --w-regular: 400;
  --w-medium: 500;
  --w-semibold: 600;
  --w-bold: 700;
  --wdth-condensed: 75%;
  /* type scale at 1920x1080 */
  --fs-xl: 150px;
  --fs-h1: 88px;
  --fs-h2: 52px;
  --fs-num: 108px;
  --fs-body: 36px;
  --fs-label: 30px;
  --fs-term: 34px;
  --fs-caption: 38px;
  --lh-head: 0.9;
  --lh-sub: 1.1;
  --lh-body: 1.25;
  --lh-caption: 1.3;
  --ls-xl: -0.02em;
  --ls-num: -0.02em;
  /* grid: 24px unit, 144px margins, 12 columns of 136px */
  --u: 24px;
  --margin: 144px;
  --cols: 12;
  --col: 136px;
  --caption-bottom: 48px;
  --caption-h: 136px;
  --caption-pad: 8px 20px;
  /* geometry */
  --radius: 0px;
  --stroke: 4px;
  --shift: 32px;
  --tick-w: 14px;
  --tick-h: 26px;
  --cursor-w: 0.5em;
  --cursor-gap: 0.1em;
  --wipe-edge: 24px;
  /* motion: Insightful mode; the global curve only for scene transitions */
  --ease-in: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-out: cubic-bezier(0.64, 0, 0.78, 0);
  --ease-transition: cubic-bezier(0.68, 0, 0.12, 1);
  --dur-in: 330ms;
  --dur-out: 330ms;
  --dur-transition: 800ms;
  --dur-sweep: 500ms;
  --dur-char: 30ms;
  --stagger: 110ms;
}
```

Unused in the reference video, defined for reuse: `--pop-soft`, `--ease-out`, `--dur-out`, `--w-bold`, `--cols`, `--col`. Font URLs are relative to the composition's folder; place the fonts in `fonts/`.

## Assets and licenses

| Asset | Where to get it | License | Video use |
|---|---|---|---|
| Mozilla Headline variable font `MozillaHeadline[wdth,wght].ttf` | google/fonts repository, `ofl/mozillaheadline/` (upstream mozilla/mozilla-headline-type, commit a6ff8ec; designer Studio DRAMA). Reference copy sha256 `7d04f994cbffedacf9281f7d141c2d50bc7e3c02321bd8a12f7b323d813c7bdc` | SIL OFL 1.1, no Reserved Font Name declared | allowed: embed or render freely; do not sell the font files alone |
| Mozilla Text variable font `MozillaText[wght].ttf` | google/fonts repository, `ofl/mozillatext/` (upstream mozilla/mozilla-text-type, commit 5ff275e). Reference copy sha256 `a74b1a5c77811bab140c8c30b02adea4f6a90fe8811c669c52541dd78f5c5e87` | SIL OFL 1.1, no Reserved Font Name declared | as above |

Ship the OFL text beside the font files. No other assets are needed. No Mozilla logo, wordmark, flag symbol, mascot, icon, illustration or photograph may be used.

## Provenance

Read on 2026-10-03 by rendering the public portal pages in headless Chromium (text extracted and read; receipts in the reference run's `production/sources/`):

- [Motion](https://brand.mozilla.com/document/231#/-/motion) (page last modified 2026-01-23): the three modes with their in/out curves and durations, the global transition curve and 0.8 s, Insightful's attributes, typography motion (typing cursor, highlight focus), and the accessibility list (reduce-motion options, no more than three flashes per second, don't rely on animation alone, keep critical animations under 5 s).
- [Color](https://brand.mozilla.com/document/231#/-/color) (last modified 2026-01-23): all hex values and names used here, the 45/45/10 split, green's uses, the type-color and background rules, and the "Accessible Combinations" labels quoted under Contrast. The page also shows swatches that look like placeholders (`#00ff11`, "Everglade" `#123123`, "Conifer" `#bada55`); this preset ignores them.
- [Typography](https://brand.mozilla.com/document/231#/-/typography-1) (last modified 2026-04-18): the two families, display sizes and weights, Condensed ExtraLight with −2 % tracking for large numbers, line spacing 90/110/125 %, tracking 0 except negative for XL, left alignment, sentence case.
- [Voice and tone](https://brand.mozilla.com/document/240#/-/voice-tone) (last modified 2026-01-05): personality and voice words, contractions, sentence case, no Oxford comma, short sentences, plain language, "internet" not "web".
- Fonts: OFL texts and metadata read in the google/fonts repository.

Inferred or adapted, not stated on any page read: every color **role** beyond the source rules, the pixel type scale at 1080p, the 24 px unit, 144 px margin, 12-column reference grid and caption zone, the sweep, typing, stagger and shift values, the scene wipe as the use of the global curve, the green-on-canvas outline rule, the reduced-motion stance for a rendered file, the narration rules beyond the voice page, and the choice of Insightful as the single mode. Contrast ratios are computed by the workshop.

Not checked: the portal's logo, mascot, iconography, illustration and photography pages (not needed: this preset uses none of those assets), and any Mozilla guidance specific to video captions.

Revision history: 1 (2026-10-03) first version, written with the reference video `outputs/explainer-about-explainers-mozilla`.
