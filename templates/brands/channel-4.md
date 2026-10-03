# Channel 4-inspired — video style preset

Status: workshop preset, revision 1 (2026-10-03). This is an original workshop style that borrows the behaviour of the 2023 Channel 4 masterbrand as described in public case studies. It is **not** Channel 4's brand, it is not endorsed by Channel 4, Pentagram or 4creative, and it uses no Channel 4 logo, "4" figure, block logo, 4moji, ident or typeface. Name it "Channel 4-inspired" wherever a viewer can see the name.

This file is self-contained: a video agent can build a 1920×1080 explainer from it alone. The CSS block in "Tokens" is the exact token set. Copy it into the run's `tokens.css` unchanged. The reference implementation is `outputs/explainer-about-explainers-channel-4/production/src/tokens.css` (git-ignored run output).

Value labels used below: **source** = stated in a source listed under Provenance; **observed** = found as a value in channel4.com's public CSS or HTML, not stated by a guideline; **adapted** = a workshop choice built on a source idea or value; **workshop** = a workshop choice with no source value; **unverified** = believed true but not checked against a source in this revision.

## Character

- **Feel:** bold, direct, a little mischievous, and always moving forward. A dark canvas, heavy wide headlines, flat blocks, and one acid green. The organising idea is the source's "4 leads" principle: one thing goes first and everything else follows. In this style the leader is a **lead block**, a plain green square. It sits at the top left of every scene beside the eyebrow, it travels ahead of every connector it draws, and it lands in the end card. Between scenes a gradient **world** column crosses the frame and the old scene nudges out to the left (the source's "travel between worlds" and "nudge into the next world").
- **Restraint for technical teaching** (workshop): expressive moments happen only *between* explanations or at the very start and end. While the narrator explains, the only motion is the element being named. Gradients never sit behind text. The world columns run only inside the inter-scene pause. Elastic overshoot is limited to the lead block, the green fills and the end-card cells, and it overshoots by about 10 %. Diagrams stay flat, square and left-to-right.
- **Avoid:** the Channel 4 "4", any arrangement of irregular blocks that forms a numeral, 4mojis or other icon sets, glows, drop shadows, rounded corners, 3D cubes, looping or idling motion, gradients behind text, more than one gradient on screen during an explanation, camera shake, and centred poster layouts.

## Color

Dark theme only. Every hex below is used as given; no tints are derived except the caption backing (alpha).

| Token | Hex | Role | Basis |
|---|---|---|---|
| `--bg` | `#151719` | canvas | observed value, adapted role |
| `--layer` | `#292929` | panels, cards, tiles | observed value, adapted role |
| `--layer-hi` | `#3e3e3e` | raised layer (defined, not used in the reference video) | observed value, adapted role |
| `--line` | `#444d57` | panel borders, idle rules | observed value, adapted role |
| `--line-faint` | `#292929` | faint rules (defined, not used in the reference video) | observed value, adapted role |
| `--text` | `#ffffff` | primary text | workshop |
| `--text-2` | `#b3b3b3` | secondary text, labels | observed value, adapted role |
| `--text-on-emph` | `#151719` | text on the green fill | workshop |
| `--emph` | `#aaff89` | lead block, active rules, square arrowheads, emphasis text, selection ring | observed value (channel4.com `theme-color`); source says "a vibrant green 4" but gives no hex |
| `--emph-fill` | `#aaff89` | green fill (the one solid green block per scene) | as above |
| `--ok` | `#aaff89` | completion tick (always a glyph) | workshop |
| `--warn` | `#ffc94a` | warning (defined, not used) | workshop |
| `--err` | `#ff5c5c` | error (defined, not used) | workshop |
| `--data-1` | `#ff4fa3` | identity color 1 (card edge), world stop | workshop |
| `--data-2` | `#ff8a3d` | identity color 2, world stop | workshop |
| `--data-3` | `#8f7bff` | identity color 3, world stop | workshop |
| `--data-4` | `#36c9d6` | identity color 4, world stop | workshop |
| `--data-5` | `#b3b3b3` | identity color 5 (defined, not used) | workshop |
| `--world-1` … `--world-4` | two-stop 160° gradients of the data colors and the green | inter-scene world columns and the end-card world grid | adapted (source: "immersive gradients … delightfully clashy spectrum"; the stops are workshop choices) |
| `--caption-bg` | `rgba(21, 23, 25, 0.92)` | caption backing (`--bg` at 92 %) | workshop |

Rules:

- **Green leads.** Green means "this goes first, look here": the lead block, the active connector and its square head, the selected option, and one filled green block per scene. Green completion ticks are the one exception. They mark where the lead has already been.
- **Status needs a glyph.** A tick or word carries the meaning; color only reinforces it.
- **Gradients are places, not paint.** A world gradient fills a whole block or column and never carries text, a label or a status.
- **Data colors identify, never rank.** Use them as a thick card edge paired with the card's name.
- **No color on color.** Text sits on `--bg`, `--layer` or `--emph-fill` only.

### Contrast (computed)

WCAG 2.x relative-luminance ratios, computed from the hex values above (2026-10-03, Python, sRGB). Text needs 4.5:1; large text (≥ 24 px at 1080p here) and meaningful graphics need 3:1.

| Foreground | Background | Ratio | Use | Result |
|---|---|---:|---|---|
| `--text` #ffffff | `--bg` #151719 | 17.97 | headings, body | pass |
| `--text` #ffffff | `--layer` #292929 | 14.55 | text in panels | pass |
| `--text` #ffffff | `--layer-hi` #3e3e3e | 10.70 | text on raised layer | pass |
| `--text` #ffffff | caption backing over `--layer` (#17181a) | 17.77 | captions | pass |
| `--text` #ffffff | caption backing over the brightest world stop #aaff89 (#212a22) | 14.80 | captions while a world column passes, worst case | pass |
| `--text-2` #b3b3b3 | `--bg` #151719 | 8.57 | labels | pass |
| `--text-2` #b3b3b3 | `--layer` #292929 | 6.94 | labels in panels | pass |
| `--emph` #aaff89 | `--bg` #151719 | 14.87 | emphasis text, lead block | pass |
| `--emph` #aaff89 | `--layer` #292929 | 12.04 | prompt line, ring in panels | pass |
| `--text-on-emph` #151719 | `--emph-fill` #aaff89 | 14.87 | text on the green block | pass |
| `--warn` #ffc94a | `--bg` #151719 | 11.73 | warning glyph | pass |
| `--err` #ff5c5c | `--bg` #151719 | 5.94 | error glyph | pass |
| `--data-1` #ff4fa3 | `--layer` #292929 | 4.78 | card edge | pass (3:1) |
| `--data-2` #ff8a3d | `--layer` #292929 | 6.20 | card edge | pass (3:1) |
| `--data-3` #8f7bff | `--layer` #292929 | 4.46 | card edge | pass (3:1) |
| `--data-4` #36c9d6 | `--layer` #292929 | 7.26 | card edge | pass (3:1) |
| `--line` #444d57 | `--bg` #151719 | 2.09 | panel border | **below 3:1: decorative only.** The panel's text names it |
| `--layer` #292929 | `--bg` #151719 | 1.24 | panel fill | decorative only |

## Typography

The Channel 4 typefaces (the source calls the display face "Channel 4 Headline"; the site CSS loads faces named `4headline` and `4text`) are proprietary. The brief for this preset calls the display face Horseferry, and Pentagram says the headline face "has become synonymous with the brand over the past decade". Whether "Channel 4 Headline" is Horseferry renamed is **unverified**. This preset uses open substitutes:

- **Archivo** (variable, weight 100–900, width 62–125 %), SIL OFL 1.1, for everything except code. It is a grotesque with a real width axis, so headlines can run wide and heavy. That echoes the source's "variable condensed and extended styles" without copying any letterform.
- **Space Mono** Regular and Bold, SIL OFL 1.1, for terminal text and file tags. Its quirky geometric shapes supply the mischief.

Load both from local files with `@font-face`. Fallbacks are generic `sans-serif` and `monospace` only, so a missing file shows up as an obvious fallback in stills.

| Role | Family | Size at 1080p | Weight | Width | Line height | Tracking | Case | Basis |
|---|---|---:|---:|---:|---:|---:|---|---|
| Display (title, end card) | Archivo | 104 px | 850 | 112 % | 1.0 | −0.02 em | sentence | adapted |
| H1 (scene head) | Archivo | 76 px | 800 | 112 % | 1.0 | −0.02 em | sentence | adapted |
| H2 (box names, step names) | Archivo | 48 px | 400 | 100 % | 1.1 | 0 | sentence | workshop |
| Body (field values, card names) | Archivo | 36 px | 400 | 100 % | 1.35 | 0 | sentence | workshop |
| Caption | Archivo | 36 px | 400 | 100 % | 1.35 | 0 | sentence | workshop |
| Label / eyebrow | Archivo | 30 px | 650 | 100 % | 1.2 | +0.06 em | UPPERCASE | workshop |
| Code / terminal, file tags | Space Mono | 30 px | 400 | — | 48 px | 0 | as typed | workshop |

Hierarchy: lead block + eyebrow (`STEP 1`), then a heavy wide headline, then content. Weight and width carry hierarchy; color does not. Never use italic, condensed widths for running text, or wide widths below 48 px. Nothing on screen is smaller than 30 px.

## Layout

- Canvas 1920×1080. Base unit `--u` = 30 px; positions and sizes are multiples of it (workshop; the same grid as the other workshop presets so scenes stay comparable).
- 8 columns of 240 px, outer margin `--margin` 120 px (workshop).
- Caption zone: y = 900 to 1020 px (`--caption-bottom` 60 px, `--caption-h` 120 px), inset by the margins. No content enters it.
- Scene head at the top left: the lead block (36 px square) at x = 120, y = 90; the eyebrow 18 px to its right; the headline below at y = 135. The title scene holds the head 60 px lower and the lead block travels up to the common position as the first scene leaves.
- Content reads left to right, because travel is left to right. Asymmetric, left-aligned. The end card puts the title at the left and a 2 × 2 world grid at the right (three gradient cells; the lead block grows into the fourth).

## Visual language

- **Lead block:** one green square, always present from the first second. It never carries text. It is the only element that persists across scenes.
- **Blocks:** flat rectangles on `--layer` with a 4 px `--line` border and 0 radius. One green block per scene marks the subject (Video, the Prepare skill, the chosen style).
- **Connectors:** straight 4 px rules in `--emph`, each led by a small green square head that travels from the origin and drags the rule behind it. No triangles.
- **Worlds:** gradient blocks. Between scenes, one 240 px world column crosses the full frame right to left in 0.9 s, while the outgoing scene slides 120 px left and fades. At the end, three 240 px gradient squares and the lead block form a 2 × 2 grid. These square cells are original shapes, not the Channel 4 blocks.
- **Selection:** a 4 px green outline ring. Completion: a green tick.
- Terminal panels: a label bar, Space Mono text, prompt lines in green.
- No logos, photographs, illustrations, icons or emoji beyond ticks and squares.

## Motion

| Token | Value | Use | Basis |
|---|---|---|---|
| `--ease-standard` | `cubic-bezier(0.65, 0, 0.35, 1)` | rules growing, color changes | workshop |
| `--ease-entrance` | `cubic-bezier(0.22, 1, 0.36, 1)` | elements entering (fast start, long settle) | workshop |
| `--ease-exit` | `cubic-bezier(0.55, 0, 1, 0.45)` | elements leaving | workshop |
| `--ease-expressive` | `cubic-bezier(0.34, 1.32, 0.64, 1)` | elastic overshoot: lead block, green fills, end-card cells only | adapted (source: "physics-based elasticity" of the logo) |
| `--ease-travel` | `cubic-bezier(0.76, 0, 0.24, 1)` | the lead block, connector heads, world columns | adapted (source: "travel and transformation principles") |
| `--dur-fast` | 220 ms | small elements, ticks, rings | workshop |
| `--dur-base` | 420 ms | panels, cards, scene exit | workshop |
| `--dur-slow` | 650 ms | titles, long connectors | workshop |
| `--dur-travel` | 900 ms | world column crossing, lead block's last journey | workshop |
| `--stagger` | 90 ms | delay between items in a sequence | workshop |
| `--enter-shift` | 48 px | new content slides in from the right | workshop |
| `--exit-shift` | −120 px | old content slides out to the left | workshop |

Rules: every element enters on the narration cue that names it, sliding in from the right (24–48 px) with a fade, because the viewer travels rightward. A connector's square head leads the rule. Each scene ends with a **nudge**: during the last 0.45 s of its closing pause the content slides left and fades while a world column crosses; the next scene's head arrives as the column leaves. Nothing loops, spins, pulses, shakes or zooms. Overshoot never exceeds about 10 %. Easing and durations are read from these tokens at run time, never typed into scene code.

## Narration voice

Direct, warm and a little cheeky; second person; present tense. Short sentences, sometimes a two-word one ("First question."), and a light travel image ("Here's the trip."). Plain words for the technical parts: name the thing, then show it. No sarcasm, hype, rhetorical tricks or slang that hides meaning. No colons or dashes in spoken text. The reference video used local Kokoro `af_heart` at speed 0.92 (workshop choice) and measured about 143 words per minute overall (111 words in 46.4 s including pauses).

## Accessibility

- Burned-in captions on every spoken sentence, in the caption zone, 36 px, on `--caption-bg`, balanced line breaks, at most two lines; also ship `captions.vtt`.
- All text pairs above pass 4.5:1; the lowest text pair is 5.94:1 (error glyph), the lowest used in the reference video is 6.94:1 (labels in panels).
- Meaning never depends on color alone: status uses ticks, selection uses an outline ring, identity colors are paired with names.
- Motion: the world column moves fast across the full frame once per transition (4 times in 46 s). It is a single smooth pass, never a flash, a strobe or a repeated pattern. Give a reduced-motion variant a plain 220 ms fade instead (set `--dur-travel` short and drop the columns).
- Minimum on-screen text 30 px at 1080p.

## Tokens

```css
/* STYLE TOKENS: the only place that holds colors, fonts, type scale, grid, easing and durations.
   Mirrors templates/brands/channel-4.md. A new style replaces this file. */
@font-face { font-family: "Archivo"; font-weight: 100 900; font-stretch: 62% 125%; src: url("fonts/Archivo-Variable.ttf") format("truetype"); }
@font-face { font-family: "Space Mono"; font-weight: 400; src: url("fonts/SpaceMono-Regular.ttf") format("truetype"); }
@font-face { font-family: "Space Mono"; font-weight: 700; src: url("fonts/SpaceMono-Bold.ttf") format("truetype"); }
:root {
  /* color: background */
  --bg: #151719;          /* canvas */
  --layer: #292929;       /* panels, cards, tiles */
  --layer-hi: #3e3e3e;    /* raised or selected layer */
  --line: #444d57;        /* borders, connectors, rules */
  --line-faint: #292929;  /* column guides */
  /* color: text */
  --text: #ffffff;        /* primary text */
  --text-2: #b3b3b3;      /* secondary text, labels */
  --text-on-emph: #151719;
  /* color: emphasis (the lead green: "this leads, look here") */
  --emph: #aaff89;        /* emphasis text, lead blocks, active connector */
  --emph-fill: #aaff89;   /* emphasis fill */
  /* color: status (always paired with a glyph or word) */
  --ok: #aaff89;
  --warn: #ffc94a;
  --err: #ff5c5c;
  /* color: data and world gradients (identity only, never the sole carrier of meaning) */
  --data-1: #ff4fa3;
  --data-2: #ff8a3d;
  --data-3: #8f7bff;
  --data-4: #36c9d6;
  --data-5: #b3b3b3;
  --world-1: linear-gradient(160deg, #ff4fa3 0%, #ff8a3d 100%);
  --world-2: linear-gradient(160deg, #8f7bff 0%, #36c9d6 100%);
  --world-3: linear-gradient(160deg, #ff8a3d 0%, #aaff89 100%);
  --world-4: linear-gradient(160deg, #36c9d6 0%, #ff4fa3 100%);
  /* fonts and weights */
  --font-sans: "Archivo", sans-serif;
  --font-mono: "Space Mono", monospace;
  --font-label: "Archivo", sans-serif;
  --w-light: 400;
  --w-regular: 400;
  --w-strong: 700;
  --w-label: 650;
  /* type scale at 1920x1080 */
  --fs-display: 104px;
  --fs-h1: 76px;
  --fs-h2: 48px;
  --fs-body: 36px;
  --fs-label: 30px;
  --fs-code: 30px;
  --fs-caption: 36px;
  --lh-display: 1.0;
  --lh-body: 1.35;
  --ls-display: -0.02em;
  --ls-label: 0.06em;
  --label-case: uppercase;
  --w-display: 850;
  --w-heading: 800;
  --stretch-display: 112%;
  --stretch-heading: 112%;
  /* grid: 8 columns of 240px over the full canvas, 30px increments, margin = half a column */
  --u: 30px;
  --cols: 8;
  --col: 240px;
  --margin: 120px;
  --gutter: 30px;
  --caption-bottom: 60px;
  --caption-h: 120px;
  /* surface */
  --radius: 0px;
  --stroke: 4px;
  --lead: 36px;           /* side of the lead block */
  --caption-bg: rgba(21, 23, 25, 0.92);
  /* motion: travel leads every change; elastic overshoot only on the lead block and green fills */
  --ease-standard: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-entrance: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-exit: cubic-bezier(0.55, 0, 1, 0.45);
  --ease-expressive: cubic-bezier(0.34, 1.32, 0.64, 1);
  --ease-travel: cubic-bezier(0.76, 0, 0.24, 1);
  --dur-fast: 220ms;
  --dur-base: 420ms;
  --dur-slow: 650ms;
  --dur-travel: 900ms;
  --stagger: 90ms;
  --enter-shift: 48px;    /* new content arrives from the right, the direction of travel */
  --exit-shift: -120px;   /* old content leaves to the left */
}
```

Tokens beyond the base workshop set: `--world-1`…`--world-4`, `--font-label`, `--w-label`, `--stretch-display`, `--stretch-heading`, `--lead`, `--ease-travel`, `--dur-travel`, `--enter-shift`, `--exit-shift`. The base workshop composition ignores them; the reference composition reads all of them. `--w-light`, `--layer-hi`, `--line-faint`, `--warn`, `--err`, `--data-5`, `--w-strong`, `--cols` and `--gutter` are defined but unused in the reference video.

## Assets and licenses

| Asset | Where to get it | License | Video use |
|---|---|---|---|
| Archivo variable (`Archivo[wdth,wght].ttf`, saved as `Archivo-Variable.ttf`) | `github.com/google/fonts`, `ofl/archivo/` | SIL OFL 1.1 (Copyright 2020 The Archivo Project Authors) | allowed; embed or render freely; do not sell the font files alone |
| Space Mono Regular, Bold (`ttf`) | `github.com/google/fonts`, `ofl/spacemono/` | SIL OFL 1.1 (Copyright 2016 The Space Mono Project Authors) | as above |

Ship each OFL text beside its font files. No other assets are needed. Do not use the Channel 4 logo, the "4", the block logo or any arrangement that suggests it, 4mojis, idents, programme imagery, the Channel 4 Headline/Text typefaces, or Channel 4 sound.

## Provenance

Read on 2026-10-03 (direct `curl` of the public pages; the text was read, not only search snippets):

- [Pentagram, "Channel 4" case study](https://www.pentagram.com/work/channel-4). Used: the masterbrand brings channels and streaming "under one roof"; "a singular masterbrand colour"; 4 as "a traveller, guiding us through a universe of … content"; the principle "'4 leads'" which "informs the framework for lockups and layout"; worlds "anchored by a cube-based framework" with a "square motif" that can be "recessive or prominent"; "immersive gradients … delightfully clashy spectrum"; "movement that reveals glimpses into adjoining worlds" and "nudging into the next world"; "zooming out" to show the universe; "physics-based elasticity"; "travel and transformation principles"; "a bold and reductive graphic language … peppered with playfulness"; "typography and layout principles … with a clear information hierarchy"; the "Channel 4 Headline typeface … expanded to include variable condensed and extended styles". The page gives no hex values, sizes, curves or durations.
- [Channel 4 press release, "Channel 4 brings iconic blocks back together for single brand streaming future"](https://www.channel4.com/press/news/channel-4-brings-iconic-blocks-back-together-single-brand-streaming-future) (24 May 2023). Used: "a vibrant green '4'"; "a wider colour system of immersive gradients and worlds"; "behavioural principles"; a "sense of mischief". It also confirms the logo is the Lambie-Nairn "4", which this preset does not use.
- channel4.com home page HTML and `homepage/static/2.1.47/css/style.css` (fetched 2026-10-03): `#aaff89` is the site's `theme-color`; `#151719`, `#292929`, `#3e3e3e`, `#444d57`, `#b3b3b3` occur in the stylesheet; font families `4headline` and `4text`. These are **observed** implementation values. Their official names and roles are **unverified**.

Workshop adaptations, not from any source: the lead block as a plain square, the square connector heads, the world column transition, the 2 × 2 end grid, every color role, the gradient stops and the data colors, every easing curve and duration, the type scale, the font substitutions, the 30 px grid and margins, the caption zone, the narration voice, the restraint rules, and the accessibility rules. Contrast ratios are computed by the workshop from the hex values.

Not checked: Channel 4's actual brand guidelines, motion specifications and tone-of-voice document (none found public), the Found and Stink Studios work, and the audio identity. If you need closer fidelity, find those first and revise this file.

Revision history: 1 (2026-10-03) first version, written with the reference video `outputs/explainer-about-explainers-channel-4`.
