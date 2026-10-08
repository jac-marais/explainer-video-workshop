# Apply brand guidelines to an explainer — v0.1

Status: a tested procedure for bringing an explainer video and its companion deck into line with a brand system, not proof that it generalizes.

This workshop knows no brand. Brand guidelines come from the operator's local profile, `local/brand.md`. That file is git-ignored, so it never enters this repository. The profile points at the guidelines and holds the decisions that are particular to that brand.

## First use: find the profile

1. Read `local/brand.md`.
2. If the file is missing, your first question to the user is: **"Do you have brand guidelines that you can point me toward?"** Ask it before you do any other work.
3. If they have none, offer the workshop's nine styles. Link the gallery at https://jac-marais.github.io/explainer-video-workshop/brands/, where each style plays the same explainer; offline, link `brands/index.html` by its absolute path. List the nine style names and ask the user to reply with one. Each style's preset is `brands/<slug>.md`, linked under "The nine styles". The neutral readable default from `methods/prepare-explainer-video.md` remains an option.
4. Write the answer to `local/brand.md` with `templates/brand.md` as the shape. A chosen style's preset is its Guidelines path. Record "none" when the user picks no style, so nobody asks again.
5. When the user changes brands or corrects a decision, update the profile. Don't keep a second copy somewhere else.

Any of these can be a source: a brand workshop with its own `AGENTS.md` or skill, a PDF or folder of guidelines, a website, or a few sentences from the user. A workshop is best, because it lets you cite rules and look up assets. Use what the source offers, and write down any rule the user gives you in conversation.

If the source has its own skill or `AGENTS.md`, record its path in the profile and read it from there. Don't copy or mount it into this workshop.

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

## Procedure

### 1. Learn the brand through its own route

If the source has its own agent route (a skill, `AGENTS.md` or method), use that route rather than skimming its files. Cite every consequential rule back to the source: the file, page or line. Keep four kinds of statements apart: **official rule**, **observed implementation** (a website's CSS, for example), **derived value**, and **your recommendation**.

### 2. Audit before you edit

Have a separate agent audit the artifacts: the composition, the style tokens, and any companion deck or page. Give it only the brand source and the artifacts. Ask for a change catalog with these columns: current value and location, required change with exact values, rule citation, priority (`must`/`should`/`optional`) and confidence. Also ask for a list of open questions for the brand owner. Save the catalog as `outputs/<topic>/brand-audit.md`. An audit made from stale stills describes only the general look, so cite the current source lines.

Areas that usually matter:

| Area | What to check |
|---|---|
| Type | families, fallbacks, OpenType features, weights, tracking, line-height per role, and the mono face for code |
| Color | exact palette values, background and foreground roles, the accent's allowed use, "no color for emphasis" and "no color on color" rules, and how status (error or success) is shown without a hue |
| Surfaces | borders, radii, chrome, decorative glyphs and emoji, logo use |
| Assets | local font or asset files, licenses for the target medium (video can differ from web) |
| Contradictions | places where two brand sources disagree; keep both and state the effect |

### 3. Decide, then record

The user decides anything the guidelines leave open: substitute fonts, weight exceptions, how to show status without color, how to handle a missing license. Put the decisions that should hold for every future run in `local/brand.md`. Put decisions for this one run in the audit's "Applied" note.

### 4. Apply as tokens, not as scattered values

- Define each palette role once as a CSS variable (or the route's equivalent). Examples: `--bg`, `--fg`, `--fg2`, `--muted`, `--line`, `--accent`, `--mono`.
- Load fonts from local files with `@font-face` inside the project, and symlink them into the build output. Don't rely on system or container font packages, which fall back silently. Before capture, check that each face loaded.
- Stretch a limited palette with alpha only when the brand allows it, and label the result a derived value.
- Give the accent one meaning across the whole film. Show status with glyphs or outlines, not with color.
- Brand voice means tone and register: how the brand talks, not what it sells. One light nod to its world is fine, but a script built from its vocabulary is a joke about the brand. The narration rules in step 3 of `methods/prepare-explainer-video.md` still apply.
- Brand never overrides a claim. A wording change that alters meaning goes through the claim map, not the brand pass.

### 5. Verify

Run the route's layout and contrast checks, then look at stills of every changed scene. Also look at a companion deck under the same pass. After the render, check the exact final file as the production prompt requires. List each rule you applied, each rule you skipped with its reason, and each question still open for the brand owner. Record font and asset licenses in `assets-manifest.md`. When the license for this medium is unconfirmed, mark the output as unreleased until it is confirmed.

## Lessons

- **Strict black and white hides code.** A monospace font alone doesn't set an inline code span apart from prose. Give code spans and code blocks a light gray tint from the palette, stretched with alpha, and use a slightly darker band for added diff lines.
- **What works in video can be harsh in a document.** A dark palette that reads well on screen in motion can feel heavy on a text-heavy deck. Ask which mode the reader prefers for each surface.
- **Take out repeated chrome.** Page numbers, running headers and small section labels on every slide add noise, especially in a restrained brand. Keep what helps someone find their way, and cut the rest.
- **Keep content fixes apart from the brand pass.** When the audit exposes a factual problem, check it against the primary source, such as the code, not secondary docs. Change it only if it is actually true or false.
- **Say which file you mean.** Link outputs with absolute paths, because a relative link resolves against whatever directory the reader's tool is in.
