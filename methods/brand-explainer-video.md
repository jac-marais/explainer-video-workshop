# Apply brand guidelines to an explainer — v0.1

Use this procedure to align a film and its companion deck with a brand system. It has been tested locally; broader use remains unvalidated. [Brand guidelines](../README.md#brand-guidelines) introduces the local profile.

## First use: find the profile

1. Follow the profile lookup in `AGENTS.md` and the choices in [Brand guidelines](../README.md#brand-guidelines) before other work. Offline, link `brands/index.html` by its absolute path for the gallery. Also offer [a custom look](#build-a-custom-look-from-references) when the user wants a distinctive house style.
2. Fill `templates/brand.md` from the answer. Set Guidelines to the selected preset from [The nine styles](#the-nine-styles), "user rules below" for a custom look, or "none" for the [neutral default](prepare-explainer-video.md#intake-contract).
3. Use [Decide, then record](#3-decide-then-record) for later corrections and standing decisions.

Record the source's route path in the profile when it has a skill or `AGENTS.md`, and follow [step 1](#1-learn-the-brand-through-its-own-route). Keep that route at its source so it can receive updates.

## The nine styles

Each preset is a self-contained style file that a video agent can build from.

| Style | Preset |
|---|---|
| Airbnb-inspired | [`brands/airbnb.md`](../brands/airbnb.md) |
| Channel 4-inspired | [`brands/channel-4.md`](../brands/channel-4.md) |
| IBM-inspired | [`brands/ibm.md`](../brands/ibm.md) |
| MIT Media Lab-inspired | [`brands/mit-media-lab.md`](../brands/mit-media-lab.md) |
| Mozilla-inspired | [`brands/mozilla.md`](../brands/mozilla.md) |
| NASA-inspired | [`brands/nasa.md`](../brands/nasa.md) |
| NPS Unigrid-inspired | [`brands/nps-unigrid.md`](../brands/nps-unigrid.md) |
| Spotify-inspired | [`brands/spotify.md`](../brands/spotify.md) |
| Uber-inspired | [`brands/uber.md`](../brands/uber.md) |

## Build a custom look from references

The [claim ledger](../library/design-reference-claims.md) holds the evidence and qualifications behind these browsing suggestions. The [use rules](../library/source-map.md#use-rules) say how an agent may browse these sites on the user's behalf.

| Source | Look here for | Use boundary for a rendered film |
|---|---|---|
| [Visuelle](https://visuelle.co.uk/) | Grid and identity relationships | Inspiration only unless the rights holder grants reuse. |
| [CARI](https://cari.institute/) | Aesthetic movements, including Y2K | Inspiration only; its research archive is not an asset licence. |
| [Artvee](https://artvee.com/about-us/) | Palette, texture and historical artwork | Public-domain asset candidate; confirm the artwork’s source record and download tier. |
| [Design Reviewed](https://designreviewed.com/about/) | Print grids and hierarchy | Inspiration only unless reproduction permission is obtained. |
| [Fonts In Use](https://fontsinuse.com/) | Type pairing and packaging typography | Reference images only unless separately cleared. Obtain the font’s own licence from its foundry or distributor. |
| [Public Work](https://www.cosmos.so/public-work) | Public-domain asset discovery | Verify rights at the original collection before reuse; a search result is not clearance. |
| [Rawpixel](https://www.rawpixel.com/services/licenses) | Graphics and textures | Match the item’s CC0, government public-domain, free-with-conditions or premium terms to the intended use. Commercial films need the applicable Business entitlement for licensed content; exclude editorial-only items from them. |
| [Are.na](https://www.are.na/about) | Connections across curated references | Inspiration only; follow a block to its original creator for reuse rights. |
| [ShotDeck](https://shotdeck.com/) | Framing, lighting and colour in film stills | Inspiration only. Its help centre allows reference, research and internal pitches, and bars external commercial use and public republishing. |
| [Texture Ninja](https://texture.ninja/) | Photographic surface textures | Each item page releases its photo under CC0, with no attribution required. CC0 does not clear a mark or artwork shown in the photo, such as a sign or graffiti. |
| [Colormind](https://colormind.io/) | Colour palettes, generated or built around a locked colour | Use this source for inspiration and record the chosen hex values in the brand profile. Its API is free only for personal and non-commercial use, so don't call it from a commercial production without the operator's permission. |
| [Book of Shapes](https://bookofshapes.com/license) | Generative SVG patterns include grids, flow fields, isometric and radial forms. | Its licence allows any use of a generated pattern, commercial included, with no attribution. A pattern may be part of the film but may not be redistributed on its own. Don't use Joy Division, Joy Division Mesh or Brockmann Beethoven Arcs, which recreate existing works. |

For PBR materials and HDRIs, use Poly Haven and ambientCG through [3D assets](../library/3d-assets.md), which holds their licences and intake steps. For a pose to draw a character from, see [pose references](../library/character-pose-references.md).

As a workshop design exercise, combine elements from at least two of these sources, using different underlying works. Look beyond their first or most familiar examples and explain why each choice fits the brief. This exercise explores alternatives; originality remains untested.

In the brand profile’s reference table, record the source name and individual URL, the element taken (grid, palette, texture, type, movement, framing, lighting or asset), and how it changes the design. Mark each as **inspiration only** or **asset for reuse**. Record the licence status, rights-evidence URL, check date and conditions, including attribution or usage limits; use **unconfirmed** when evidence is missing. For an asset, check its territory and any required releases alongside the medium-specific licence audit in [step 2](#2-audit-before-you-edit). For editorial films, confirm Rawpixel permission for the specific use; see [C-DR-050](../library/design-reference-claims.md).

Carry the resulting choices through [Decide, then record](#3-decide-then-record) and [Apply as tokens](#4-apply-as-tokens-not-as-scattered-values). The existing [verification step](#5-verify) owns the asset manifest and release gate.

<a id="figure-styles-are-not-brands"></a>

## Choose a figure style

Choose a [figure module](../templates/composition/README.md#figure-modules) in the scene plan's global visual system. Record it in `local/brand.md` when the user wants it for every run. Where a brand rule and a figure rule disagree, apply the brand rule and record the conflict in the audit. A figure rule wins only with the user's approval.

## Procedure

### 1. Learn the brand through its own route

If the source has its own agent route (a skill, `AGENTS.md` or method), follow that route. Cite the file, page or line for every consequential rule. Distinguish an **official rule**, an **observed implementation** such as a website's CSS, a **derived value**, and **your recommendation**.

### 2. Audit before you edit

Have a separate agent audit the composition, style tokens and any companion deck or page. Give it only the brand source and those artifacts. Save its catalog as `outputs/<topic>/brand-audit.md`, with the current value and location, required change with exact values, rule citation, priority (`must`/`should`/`optional`) and confidence. Include open questions for the brand owner. Cite current source lines because stale stills show only the general look.

Use these areas to guide the audit.

| Area | What to check |
|---|---|
| Type | families, fallbacks, OpenType features, weights, tracking, line-height per role, and the mono face for code |
| Color | exact palette values, background and foreground roles, the accent's allowed use, "no color for emphasis" and "no color on color" rules, and how status (error or success) is shown without a hue |
| Surfaces | borders, radii, chrome, decorative glyphs and emoji, logo use |
| Assets | local font or asset files, licenses for the target medium (video can differ from web) |
| Contradictions | places where two brand sources disagree; keep both and state the effect |

### 3. Decide, then record

The user decides unresolved choices such as substitute fonts, weight exceptions, status encoding and missing licenses. Update `local/brand.md` for standing decisions and corrections, keeping one profile. Put decisions for this run in the audit's "Applied" note.

<a id="4-apply-as-tokens-not-as-scattered-values"></a>

### 4. Apply shared tokens

- Use [Caption layout](../templates/composition/README.md#caption-layout) for geometry and foreground clearance, with the preset's Layout and Tokens values.
- Define each palette role once as a CSS variable (or the route's equivalent). Examples include `--bg`, `--text`, `--text-2`, `--line` and `--emph`.
- Follow [Caption layout](../templates/composition/README.md#caption-layout) for local font files and fallbacks. Symlink the fonts into the build output and verify that each face loaded before capture.
- Stretch a limited palette with alpha only when the brand allows it, and label the result a derived value.
- Give the accent one meaning across the whole film. Show status with glyphs or outlines, and never give a status its own color.
- Brand voice sets the tone and register of the narration. One light nod to its world is fine, but a script built from its vocabulary is a joke about the brand. The narration rules in step 3 of `methods/prepare-explainer-video.md` still apply.
- Brand never overrides a claim. Send every wording change that alters meaning through the [claim map](prepare-explainer-video.md#2-build-the-claim-map-before-prose), and verify a factual repair against the primary source.

### 5. Verify

For a custom brand, flag any reference that fails the [reference-record requirements](#build-a-custom-look-from-references), whether it supplies inspiration or a reused asset.

Follow [M4 to M6](../templates/production-prompt.md) for scene checks, still inspection and exact-file review. Extend the brand pass to any companion deck. List each rule you applied, each rule you skipped with its reason, and each question still open for the brand owner. Record font and asset licenses in `assets-manifest.md`. When the license for this medium is unconfirmed, mark the output as unreleased until it is confirmed.

## Lessons

- **Strict black and white hides code.** A monospace font alone doesn't set an inline code span apart from prose. Give code spans and code blocks a light gray tint from the palette, stretched with alpha, and use a slightly darker band for added diff lines.
- **What works in video can be harsh in a document.** A dark palette that reads well on screen in motion can feel heavy on a text-heavy deck. Ask which mode the reader prefers for each surface.
- **Take out repeated chrome.** Page numbers, running headers and small section labels on every slide add noise, especially in a restrained brand. Keep what helps someone find their way, and cut the rest.
