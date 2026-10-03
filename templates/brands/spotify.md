# Spotify-inspired — video style preset

Status: workshop preset, revision 1 (2026-10-03). This is an original workshop style that borrows the feel of Spotify's public identity, which the agency COLLINS developed in 2015. It is **not** Spotify's brand, it is not endorsed by Spotify or COLLINS, and it uses no Spotify logo, icon, wordmark, sound-wave mark, circle-and-waves motif, or the proprietary Circular typeface. Name it "Spotify-inspired" wherever a viewer can see the name.

This file is self-contained: a video agent can build a 1920×1080 explainer from it alone. The CSS block in "Tokens" is the exact token set. Copy it into the run's `tokens.css` unchanged. The reference implementation is `outputs/explainer-about-explainers-spotify/production/src/tokens.css` (git-ignored run output).

Value labels used below: **source** = read on a public page listed in Provenance; **observed** = a value found in a public page's CSS or markup, not stated in its text as a brand value; **adapted** = a workshop choice built on a source idea; **workshop** = a workshop choice with no source value; **unverified** = believed true but not checked against a source in this revision.

## Character

- **Feel:** energetic, bold, loud color, confident. Whole scenes sit on a saturated color field in a "vibrating" two-color pair, then the film drops back to a near-black canvas for dense scenes. Heavy, tight headlines. Rounded cards and pill shapes. Things pop in with a small overshoot. Flexible within a consistent frame: every scene keeps the same margins, head position and caption zone, while the color pair changes.
- **Source ideas behind it:** COLLINS describes "bold, high-contrast color pairs that most brands avoid" that bring "tension and energy", duotone treatment of artist photography drawn from screen printing, and a system that stays coherent "from bachata to black metal". Spotify's developer guidelines call green the "resting color, used whenever Spotify's voice needs to be recognizable". A Spotify art director (AIGA, 2019) compares the brand to a magazine: "it has an identity, but it's flexible".
- **Avoid:** any Spotify logo, icon, the three-wave mark, a green circle (it reads as the icon), Circular or look-alike lettering of the wordmark, gradients, drop shadows, glows, thin light headlines, all-caps labels, the IBM-style grid guides, more than one field pair per scene, text over busy fills, oversaturated neon on neon without a contrast check.

## Color

Dark canvas plus three duotone fields. Every hex is used as given; the only derived value is the caption backing (alpha).

| Token | Hex | Role | Basis |
|---|---|---|---|
| `--bg` | `#191414` | canvas on dark scenes | source value ("use Spotify color #191414" in the developer guidelines), adapted role |
| `--layer` | `#2a2424` | cards, panels, tiles | workshop (a lighter step of `--bg`) |
| `--layer-hi` | `#3e3838` | raised layer (defined, not used in the reference video) | workshop |
| `--line` | `#5e5656` | terminal divider, inactive connectors | workshop |
| `--line-faint` | `#3e3838` | faint dividers (defined, not used) | workshop |
| `--text` | `#ffffff` | primary text | workshop |
| `--text-2` | `#b3b3b3` | secondary text, labels on dark | workshop; **unverified** as a Spotify value |
| `--text-on-emph` | `#191414` | text on green | source value, adapted role |
| `--emph` | `#1ed760` | the green: active ring, active connectors, arrowheads, prompt text | observed (developer guidelines page CSS, "YES" labels); Spotify Green's official hex is **unverified** |
| `--emph-fill` | `#1ed760` | green fill: the chosen item, the skill node, the end field | as above |
| `--ok` | `#1ed760` | done tick (always a glyph) | as above, adapted role |
| `--warn` | `#ffa42b` | warning (defined, not used) | workshop |
| `--err` | `#ff5c6c` | error (defined, not used) | workshop (the observed page red `#e91429` is only 3.99:1 on `--bg`, so it is not used) |
| `--data-1` | `#1ed760` | identity edge 1 | observed |
| `--data-2` | `#f573a0` | identity edge 2 | observed (developer page navigation icon fill) |
| `--data-3` | `#cdf564` | identity edge 3 | observed (developer guidelines page markup) |
| `--data-4` | `#9b8cff` | identity edge 4 | workshop |
| `--data-5` | `#ffa42b` | identity edge 5 (defined, not used) | workshop |
| `--field-1-bg` / `--field-1-fg` | `#400073` / `#f573a0` | title field: deep violet with pink type | observed (both on the developer page CSS); pairing is adapted from COLLINS "vibrating color" |
| `--field-2-bg` / `--field-2-fg` | `#2d46b9` / `#cdf564` | middle field: blue with lime type | blue is workshop (**unverified** as a Spotify value); lime is observed on the developer page |
| `--field-3-bg` / `--field-3-fg` | `#1ed760` / `#191414` | end field: the green resting color with near-black type | observed / source |
| `--caption-bg` | `rgba(25, 20, 20, 0.92)` | caption backing (`--bg` at 92 %) | workshop |

Rules:

- **Green means "this one, go, done".** The chosen item, the active step and finished ticks. At most one green fill block per dark scene; the end field is the one exception, and it closes the film.
- **One field pair per scene.** A field scene paints the whole canvas `--field-N-bg` and uses `--field-N-fg` for its eyebrow, headline and rules. Content cards on a field stay `--layer` with `--text`. Dark scenes use `--bg`. Alternate field and dark scenes for rhythm.
- **Status needs a glyph.** Ticks and rings carry the meaning; color only reinforces it.
- **Data colors identify, never rank.** Use them as a thick card edge, never as body text color.
- **Duotone imagery.** If a video needs a photograph, map it to two tones of one field pair (shadows to `--field-N-bg`, highlights to `--field-N-fg`) and put no text on it. The reference video uses no photographs.

### Contrast (computed)

WCAG 2.x relative-luminance ratios, computed from the hex values above (2026-10-03). Text needs 4.5:1; large text (≥ 24 px at 1080p here) and meaningful graphics need 3:1.

| Foreground | Background | Ratio | Use | Result |
|---|---|---:|---|---|
| `--text` #ffffff | `--bg` #191414 | 18.24 | body, headings on dark | pass |
| `--text` #ffffff | `--layer` #2a2424 | 15.26 | text in cards | pass |
| `--text` #ffffff | `--layer-hi` #3e3838 | 11.49 | text on raised layer | pass |
| `--text` #ffffff | caption backing over white (#2b2727), worst case | 14.77 | captions | pass |
| `--text-2` #b3b3b3 | `--bg` #191414 | 8.70 | labels | pass |
| `--text-2` #b3b3b3 | `--layer` #2a2424 | 7.28 | labels in cards | pass |
| `--emph` #1ed760 | `--bg` #191414 | 9.50 | prompt text, rings | pass |
| `--emph` #1ed760 | `--layer` #2a2424 | 7.95 | prompt text in terminal, ticks | pass |
| `--text-on-emph` #191414 | `--emph-fill` #1ed760 | 9.50 | text on green, end field | pass |
| `--field-1-fg` #f573a0 | `--field-1-bg` #400073 | 5.35 | title field type | pass |
| `--field-1-bg` #400073 | `--field-1-fg` #f573a0 | 5.35 | text in the pink box | pass |
| `--emph` #1ed760 | `--field-1-bg` #400073 | 7.47 | green rule on violet | pass |
| `--field-2-fg` #cdf564 | `--field-2-bg` #2d46b9 | 6.26 | middle field type and rules | pass |
| `--emph` #1ed760 | `--field-2-bg` #2d46b9 | 4.07 | green node edge on blue (graphic) | pass (3:1) |
| `--text` #ffffff | `--field-2-bg` #2d46b9 | 7.81 | white text on blue, if needed | pass |
| `--warn` #ffa42b | `--bg` #191414 | 9.20 | warning glyph | pass |
| `--err` #ff5c6c | `--bg` #191414 | 6.08 | error glyph | pass |
| `--data-2` #f573a0 | `--layer` #2a2424 | 5.70 | identity edge | pass (3:1) |
| `--data-3` #cdf564 | `--layer` #2a2424 | 12.24 | identity edge | pass (3:1) |
| `--data-4` #9b8cff | `--layer` #2a2424 | 5.51 | identity edge | pass (3:1) |
| `--data-5` #ffa42b | `--layer` #2a2424 | 7.70 | identity edge | pass (3:1) |
| `--line` #5e5656 | `--bg` #191414 | 2.55 | terminal divider | **below 3:1: decorative only** |
| `--layer` #2a2424 | `--field-2-bg` #2d46b9 | 1.95 | card on blue field | shape edge only; every card is named by its text |
| `--layer` #2a2424 | `--field-1-bg` #400073 | 1.06 | card on violet field | too close: do not put `--layer` cards on the violet field; use the pink or green boxes there |

H.264 encoding renders `#1ed760` slightly darker (about `#0ebd5c` in the reference frames). Dark text on it still passes by a wide margin; do not put white text on green (1.92:1).

## Typography

Spotify's own typeface (Circular, by Lineto) is proprietary and is **not** used. The open substitute is **Figtree** (SIL OFL 1.1), a geometric sans with round bowls and a friendly, compact build that sits close to Circular's tone at heavy weights. Code and terminal text use **DM Mono** (SIL OFL 1.1). Load both from local files with `@font-face`; fallbacks are generic `sans-serif` and `monospace` only, so a missing file shows up as an obvious fallback in stills. Spotify's developer guidelines tell integrators to use the platform's default sans (Helvetica Neue, Helvetica, Arial); that rule is for partner apps, not for this style.

| Role | Family | Size at 1080p | Weight | Line height | Tracking | Case | Basis |
|---|---|---:|---:|---:|---:|---|---|
| Display (title, end card) | Figtree | 120 px | 800 | 1.05 | −0.03 em | sentence | workshop |
| H1 (scene head) | Figtree | 84 px | 800 | 1.05 | −0.03 em | sentence | workshop |
| H2 (box names, step names) | Figtree | 48 px | 400 (700 in the title-card boxes) | 1.1 | 0 | sentence | workshop |
| Body (field values, card names) | Figtree | 36 px | 400 | 1.4 (1.2–1.3 in tight boxes) | 0 | sentence | workshop |
| Caption | Figtree | 36 px | 400 | 1.35 | 0 | sentence | workshop |
| Label / eyebrow | Figtree | 30 px | 700 | 1.2 | 0 | sentence | workshop |
| Code / terminal | DM Mono | 32 px | 400 | 48 px | 0 | as typed | workshop |

Hierarchy: a bold small eyebrow (`Step 1`) over a heavy, tightly tracked headline, then content. Weight and size carry hierarchy. Labels are bold sentence case, never all caps. Never use italic or weights below 400 for text. Nothing on screen is smaller than 30 px.

## Layout

The frame stays fixed while the color changes. This is the workshop's reading of COLLINS's "Flex Deck" idea (a logic that keeps the identity coherent across uses); the case study does not publish a grid, so every value here is **workshop**.

- Canvas 1920×1080. Base unit `--u` = 30 px; positions and sizes are multiples of 30 px.
- 8 columns of 240 px over the canvas (`--col`), used for placing boxes; no visible grid.
- Outer margin `--margin` 120 px left and right.
- Caption zone: the bottom band from y = 900 to 1020 px (`--caption-bottom` 60 px, `--caption-h` 120 px), inset by the margins. No content enters it.
- Scene head at the top left: eyebrow at y = 90 px, headline at y = 135 px. Content sits between y ≈ 270 and 870 px, left-aligned to the margin.
- Field scenes paint the full canvas, edge to edge. Content on them keeps the same frame as on dark scenes.
- Left-aligned and asymmetric. Leave space empty rather than stretching content.

## Visual language

- Cards and panels: `--layer` fill, no visible border, `--radius` 18 px corners.
- Pills: option tiles, scene chips and file names use `--radius-pill` (fully rounded ends). The chosen tile turns green with dark text.
- Connections: straight 3 px rules ending in a solid triangular arrowhead; active rules are `--emph` on dark scenes and `--field-N-fg` on a field.
- One filled green block per dark scene marks the subject; a 3 px green ring (rounded to match its box) marks "current".
- Card identity: a thick (12 px) colored left edge in a data color.
- Terminal panels: a bold label bar over DM Mono text; the agent's question in `--emph`.
- Ticks in `--ok` for completed checks.
- End card: a green field wipes up from the bottom; heavy near-black type sits on it.
- No logos, icons, photographs, illustrations, circles in green, sound-wave shapes or equalizer bars.

## Motion

| Token | Value | Use | Basis |
|---|---|---|---|
| `--ease-standard` | `cubic-bezier(0.3, 0, 0, 1)` | rules growing, color changes, fades | workshop |
| `--ease-entrance` | `cubic-bezier(0.16, 1, 0.3, 1)` | elements entering (fast start, long settle) | workshop |
| `--ease-exit` | `cubic-bezier(0.7, 0, 0.84, 0)` | elements leaving | workshop |
| `--ease-expressive` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | pop-in with a small overshoot: pills, tiles, chips, title boxes, the title | workshop |
| `--dur-fast` | 200 ms | rings, ticks, exits | workshop |
| `--dur-base` | 360 ms | cards, pills | workshop |
| `--dur-slow` | 600 ms | titles, long rules, the end-field wipe | workshop |
| `--stagger` | 70 ms | delay between items in a sequence | workshop |
| `--pop-scale` | 0.8 | starting scale of a pop-in | workshop |

Rules: every element enters on the narration cue that names it. Pills and tiles pop from `--pop-scale` to full size with `--ease-expressive`; text blocks slide 12–36 px with `--ease-entrance`. Connectors draw from their origin. Lists stagger quickly. Each scene's content fades out over `--dur-fast` just before the next scene, and the field color then cuts hard on the scene change. The overshoot is small (about 6 %); nothing loops, spins, pulses or bounces more than once. Easing and durations are read from these tokens at run time, never typed into scene code. No source page gives Spotify motion values; the developer guidelines have no video or motion guidance.

## Narration voice

Warm, upbeat, second person, present tense, a little casual: "First up", "Next", "And yes". Short sentences. One light touch of personality per scene at most; the facts stay plain. Voice means tone and register, not subject matter: no wordplay on music or the product (track, playlist, remix, beat, drop and the like). No hype words ("amazing", "seamless"), no colons or dashes in spoken text. A single direct question is fine when the video shows that question on screen. The reference video used local Kokoro `af_heart` at speed 0.92 (workshop choice; any bright, friendly voice fits) and measured 105 words in 43.1 s including pauses.

## Accessibility

- Burned-in captions on every spoken sentence, in the caption zone, 36 px, on `--caption-bg` with `--caption-radius` corners, balanced line breaks, at most two lines; also ship `captions.vtt`.
- All text pairs above pass 4.5:1; the lowest text pair is 5.35:1 (pink on violet).
- Field colors change the mood, never the meaning. Status uses ticks, selection uses a ring or a green fill plus position, identity colors are paired with names.
- Minimum on-screen text 30 px at 1080p. Hold every text element for at least the sentence that introduces it.
- The color cut between a field scene and a dark scene happens at most once per scene (no flashing). No strobing or looping motion.

## Tokens

This block is byte-identical to the reference `tokens.css`. It defines every custom property of `ibm.md` under the same names, plus `--field-1..3-bg/fg`, `--font-label`, `--w-label`, `--radius-pill`, `--caption-radius` and `--pop-scale`. Font paths are relative to the composition folder.

```css
/* STYLE TOKENS: the only place that holds colors, fonts, type scale, grid, easing and durations.
   Mirrors templates/brands/spotify.md. A new style replaces this file. */
@font-face { font-family: "Figtree"; font-weight: 300 900; src: url("fonts/Figtree-Variable.ttf") format("truetype"); }
@font-face { font-family: "DM Mono"; font-weight: 400; src: url("fonts/DMMono-Regular.ttf") format("truetype"); }
@font-face { font-family: "DM Mono"; font-weight: 500; src: url("fonts/DMMono-Medium.ttf") format("truetype"); }
:root {
  /* color: background */
  --bg: #191414;          /* canvas on dark scenes */
  --layer: #2a2424;       /* panels, cards, tiles */
  --layer-hi: #3e3838;    /* raised or selected layer */
  --line: #5e5656;        /* borders, inactive connectors */
  --line-faint: #3e3838;  /* faint dividers */
  /* color: text */
  --text: #ffffff;
  --text-2: #b3b3b3;
  --text-on-emph: #191414;
  /* color: emphasis, the green resting color ("go, this one, done") */
  --emph: #1ed760;
  --emph-fill: #1ed760;
  /* color: status (always paired with a glyph or word) */
  --ok: #1ed760;
  --warn: #ffa42b;
  --err: #ff5c6c;
  /* color: data (identity only, never the sole carrier of meaning) */
  --data-1: #1ed760;
  --data-2: #f573a0;
  --data-3: #cdf564;
  --data-4: #9b8cff;
  --data-5: #ffa42b;
  /* color: vibrating duotone fields, one pair per field scene */
  --field-1-bg: #400073;  /* title field */
  --field-1-fg: #f573a0;
  --field-2-bg: #2d46b9;  /* middle field */
  --field-2-fg: #cdf564;
  --field-3-bg: #1ed760;  /* end field */
  --field-3-fg: #191414;
  /* fonts and weights */
  --font-sans: "Figtree", sans-serif;
  --font-mono: "DM Mono", monospace;
  --font-label: "Figtree", sans-serif;
  --w-light: 300;
  --w-regular: 400;
  --w-strong: 700;
  --w-label: 700;
  /* type scale at 1920x1080 */
  --fs-display: 120px;
  --fs-h1: 84px;
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
  --w-display: 800;
  --w-heading: 800;
  /* grid: 30px unit, 8 columns of 240px, margin = half a column */
  --u: 30px;
  --cols: 8;
  --col: 240px;
  --margin: 120px;
  --gutter: 30px;
  --caption-bottom: 60px;
  --caption-h: 120px;
  /* surface */
  --radius: 18px;
  --radius-pill: 999px;
  --stroke: 3px;
  --caption-bg: rgba(25, 20, 20, 0.92);
  --caption-radius: 12px;
  /* motion: snappy by default, a small overshoot for pills and the title */
  --ease-standard: cubic-bezier(0.3, 0, 0, 1);
  --ease-entrance: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-exit: cubic-bezier(0.7, 0, 0.84, 0);
  --ease-expressive: cubic-bezier(0.34, 1.56, 0.64, 1);
  --dur-fast: 200ms;
  --dur-base: 360ms;
  --dur-slow: 600ms;
  --stagger: 70ms;
  --pop-scale: 0.8;
}
```

`--gutter`, `--cols`, `--layer-hi`, `--line-faint`, `--warn`, `--err`, `--data-5` and DM Mono 500 are defined for other layouts; the reference video uses none of them.

## Assets and licenses

| Asset | Where to get it | License | Video use |
|---|---|---|---|
| Figtree variable font, weights 300–900 (`Figtree-Variable.ttf`) | `github.com/google/fonts`, `ofl/figtree/Figtree[wght].ttf` | SIL OFL 1.1 (no Reserved Font Name) | allowed; embed or render freely; do not sell the font file alone |
| DM Mono Regular and Medium (`DMMono-Regular.ttf`, `DMMono-Medium.ttf`) | `github.com/google/fonts`, `ofl/dmmono/` | SIL OFL 1.1 (no Reserved Font Name) | as above |

Ship the OFL texts (`OFL-Figtree.txt`, `OFL-DMMono.txt`) beside the font files. No other assets are needed. No Spotify logo, icon, wordmark, artwork, playlist cover or photograph may be used. Circular is licensed by Lineto and is not used.

## Provenance

Read on 2026-10-03 (direct `curl` of the public pages; text read, not just search results):

- [COLLINS, Spotify case study](https://wearecollins.com/case-studies/spotify/). The page now frames the 2015 work as a business case and lists "Augments": "3P IP Adapter: Lens" (duotone treatment "drawn from the duotone screen-printing used throughout music's history" so that third-party artist photography reads as Spotify), "Vibrating Color" ("bold, high-contrast color pairs that most brands avoid … tension and energy"), "Memory Marker" and "Flex Deck" (a logic for coherence across applications). It gives **no** hex values, typeface, grid or motion values.
- [AIGA Eye on Design, "Inside the World of a Spotify Brand Designer"](https://eyeondesign.aiga.org/inside-the-world-of-a-spotify-brand-designer/) (2019-05-13), interview with Felipe Rocha, then Senior Art Director: the COLLINS 2015 guidelines are "the base for mostly everything we do"; the duotone was once the default way to "brand everything", and the brand now works "more like a container"; "I associate [Spotify] more with a magazine: it has an identity, but it's flexible"; work should keep "the same font and colors". No values.
- [Spotify for Developers, "Design & Branding Guidelines"](https://developer.spotify.com/documentation/design). **Scope: partners integrating Spotify content into their apps; this is not a brand manual for video or motion and has no video guidance.** Read: green is the "resting color"; "Do get creative with surprising color combinations"; "Do choose colors with high contrast to ensure accessibility"; the green logo only on black, white or non-duotoned photography; "use Spotify color #191414" as a fallback background; partner apps use the platform default sans. Logo rules were read only to avoid them. The hex values `#1ed760`, `#400073`, `#f573a0` and `#cdf564` were **observed** in the page's own CSS and markup, which is site implementation, not a stated brand palette.
- Fonts: OFL texts read from the google/fonts repository files that were downloaded.

Workshop adaptations, not from any source: every color **role**; the pairs violet/pink, blue/lime and green/near-black as scene fields; `--layer`, `--line`, `--text-2` and the status colors; the choice of Figtree and DM Mono; the type scale, weights and tracking; the 30 px unit, 8 columns, margin and caption zone (kept from the workshop's IBM-inspired preset so the frame stays fixed across styles); rounded cards and pills; all easing curves, durations and the pop-in; the narration voice; and the accessibility rules. Contrast ratios are computed by the workshop from the hex values.

Not checked: Spotify's internal brand guidelines (not public), the official hex of Spotify Green (commonly cited as `#1DB954`; **unverified**, not found on the pages read), Circular's metrics against Figtree, Spotify's Encore design-system documentation, and any Spotify motion guidance. If you need closer fidelity, read those first and revise this file.

Revision history: 1 (2026-10-03) first version, written with the reference video `outputs/explainer-about-explainers-spotify`.
