# Production paths — evidence-backed routing notes

This note is a source map for the preparation workbench. It records what the public sources expose and what remains unverified. It is not a renderer installation guide and does not claim a local render.

## Shared path invariant

The most reusable unit is a narration-bound scene:

```text
source-backed brief → script/scene plan → approved audio → measured timing
→ visuals consume timing → cheap still/contiguous pilot → exact-output review
```

The path is a workshop synthesis from S-TC-001, S-TC-003, S-TC-006, S-TC-008, and S-TC-009. It survives a renderer swap; the implementation details do not.

## Route matrix

| Route | Choose when | Public method evidence | Dependencies / disqualifiers | Current status |
|---|---|---|---|---|
| Remotion | Existing React/UI explainers, charts, captions, supplied recordings, reusable React scenes | `useCurrentFrame()`/`interpolate()`; audio durations feed composition metadata; Studio/stills/selected-frame preview; MP4 render | Node, React/TypeScript, Chrome/headless render; official plugin metadata has no declared repository license; Remotion license needs its own decision | Retained for existing React projects; no local trial here |
| HyperFrames | New plain-HTML/browser-native diagrams, captions, supplied recordings, brand motion; the published faceless-explainer route covers topic/article explainers without product or website capture, with a 30–90 s sweet spot and about a 3 min cap | Apache-2.0 repository; standalone HTML; `data-*` timing; one paused seekable timeline; local CLI/Studio; word timestamps/imported transcripts; published route/lifecycle (S-HF-009–S-HF-011) | Node 22+, FFmpeg, browser runtime; standalone composition contract; longer pieces route to the vendor's general-video path; local route is inspectable but this workshop has not executed it | Candidate first local route for new browser-native work; scope/length guidance is vendor-route-specific, not a universal duration rule |
| Manim + Manim Voiceover | Formulas, geometry, precise scientific transformations | Low-quality scene loop; `VoiceoverScene`, `tracker.duration`, bookmarks; recorded service after motion settles | Python/Manim/FFmpeg; provider credentials or microphone; weak fit for arbitrary UI/brand layouts | Preferred for formula-heavy work; no local audio trial here |
| Motion Canvas + agent plugin | TypeScript vector scenes where seek, screenshots, scene graph, and error inspection matter | Editor HTTP endpoints for status, seek, screenshot, scene graph, errors, render; MP4 through FFmpeg | Node/Vite/TypeScript, open editor/browser, FFmpeg; published setup pins Vite 5; programmable sound is alpha | Viable alternative; no local trial here |
| HTML/Canvas | Small diagrams, simple generic scenes, or a project where direct browser canvas is the simplest sufficient route | Examples lane and toolchain lane expose code-first Canvas/WebGL workflows, but execution receipts are absent | Browser capture/audio/mixing and route-specific tooling must be supplied; quality gates remain the same | Available alternative; exact implementation is job-specific |
| Pexo | Photoreal multi-shot generation or hosted asset orchestration when a user explicitly chooses it | Hosted relay requires credentials/account/credits and transmits approved briefs/assets; adjacent proxy evidence covers per-shot media/audio orchestration | Hosted service boundary, provider billing, data transfer, MIT/MIT-0 metadata conflict, final assembly opaque | Optional hosted route; no free-service implication and no default |

## Shared execution recipe

1. Inspect the existing project and preserve meaningful files.
2. Lock the brief, claim map, scene plan, route, and rights notes.
3. Produce or accept audio; pre-cut before timing if editing is needed.
4. Derive measured scene/sentence/word timestamps and captions from the approved audio.
5. Plan the hardest representative scene; when production is requested, render stills and a voiced contiguous 2–4 second sample.
6. Check errors, dimensions, FPS, captions, source/asset coverage, and stale output.
7. Scale only after the pilot and pre-render review pass; checkpoint state and regenerate missing dependents on resume.
8. Review the exact final MP4 and deliver editable source, commands, manifests, receipts, and remaining uncertainty.

This recipe is a workshop reconstruction from S-TC-001, S-TC-005–S-TC-009. The mounted preparation skill covers its planning and handoff. The full production recipe remains unexecuted and must be trialed before claiming production operability.

## What HyperFrames renders

HyperFrames' core is HTML/CSS/JavaScript animation, with a seekable timeline commonly driven by GSAP. The renderer seeks each output frame in headless Chrome and encodes the captured frames with FFmpeg (S-HF-002/003). This browser is a rendering runtime; it does not need the user's personal Chrome session.

```text
agent writes HTML/CSS/JS + timeline
  → seek a timestamp → capture the browser frame
  → repeat for the video duration → FFmpeg encodes MP4
```

Images, generated clips, narration, and music can be separate assets in that composition. A text-to-video model may generate an inserted clip, but it is not required for the core browser-animation path. A natural-language prompt can therefore produce a video by having the agent write and revise animation code. Inspect the actual assets and provider receipts before attributing a particular video's pixels or voices to any model.

## HyperFrames preflight traps

Use these checks when the route is HyperFrames. They are route-specific acceptance traps, not general claims about every HTML renderer (S-HF-001–S-HF-005):

- Require a standalone composition HTML file; do not assume a template scaffold supplies the accepted source.
- Require the root `data-composition-id` to match the paused timeline key that the renderer seeks.
- Require every referenced audio ID to resolve to an intended asset before timing or render acceptance.
- Run the lint/check path and treat any lint error that disables layout or contrast audits as a failure requiring repair.
- Require positive layout/contrast samples. A report with zero samples or `0-of-0` checks is not a pass.
- Persist Studio caption/timing changes into source files and refresh the preview before accepting them (S-HF-005).

HyperFrames itself has not been executed in this workshop. Node and FFmpeg availability in the current environment is an environment observation, not a renderer validation receipt.

## Timing choices

| Timing model | Best fit | Evidence | Invalidation |
|---|---|---|---|
| Measured scene durations | Scene-based UI/vector explainers, captions | Remotion metadata and Claude Video Kit metadata (S-TC-001, S-TC-008) | Any approved audio byte or script change rebuilds timing and downstream visuals |
| Tracker/bookmarks | Word-triggered formula or diagram motion | Manim Voiceover tracker and bookmark workflow (S-TC-003) | Any audio or text change rebuilds tracker/bookmark mapping |

Do not report WPM arithmetic as measured duration. Do not edit audio after timestamps without invalidating the dependent artifacts.

## Evidence boundaries and use policy

- Public repositories establish that code or instructions exist; they do not prove that a creator's posted video came from that repository or ran unattended (S-EX-004, S-EX-011, S-TC-009).
- Public prompt material is limited and does not establish an executed creator run; all workshop prompts in `templates/` are reconstructions (S-EX-018–S-EX-021).
- Author-reported eight-hour, time, cost, and “one prompt” claims stay attributed to their authors. No source establishes that eight hours improves video quality or that a model provides an explainer-video SLA (S-EX-001–S-EX-003, S-FA-001–S-FA-004).
- Stills and sampled frames cannot establish continuous motion, audio quality, synchronization, or factual correctness; review a contiguous sample and then the exact final artifact (S-TC-009).
- Keep private credentials out of source artifacts. Copy or vendor published text only after its license is clear; otherwise paraphrase and reimplement (S-TC-001, S-TC-006).

