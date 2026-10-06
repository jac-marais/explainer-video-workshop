# Renderers — evidence-backed route notes

This note records what each renderer route's public sources expose, what remains unverified, and what has run locally. It is not a renderer installation guide.

## Route matrix

Method step 5 in `methods/prepare-explainer-video.md` chooses the route for each learner job. This table records each route's public evidence, dependencies, and local status.

Local runs in this workshop have taken the HyperFrames route through render and agent final review, with each final review bound to its MP4 checksum. The user's own watch-and-listen of those videos is still pending. No other route has been trialed, so trial each one before claiming that it works.

| Route | Public method evidence | Dependencies / disqualifiers | Current status |
|---|---|---|---|
| Remotion | `useCurrentFrame()`/`interpolate()`; audio durations feed composition metadata; Studio/stills/selected-frame preview; MP4 render | Node, React/TypeScript, Chrome/headless render; official plugin metadata has no declared repository license; Remotion license needs its own decision | Retained for existing React projects; no local trial here |
| HyperFrames | Apache-2.0 repository; standalone HTML; `data-*` timing; one paused seekable timeline; local CLI/Studio; word timestamps/imported transcripts; published route/lifecycle (S-HF-009–S-HF-011) | Node 22+, FFmpeg, browser runtime; standalone composition contract; the vendor's published faceless-explainer route covers topic/article explainers without product or website capture, with a 30–90 s sweet spot and about a 3 min cap, and longer pieces route to its general-video path | First local route for new browser-native work, and the only one run locally; scope/length guidance is vendor-route-specific, not a universal duration rule |
| Manim + Manim Voiceover | Low-quality scene loop; `VoiceoverScene`, `tracker.duration`, bookmarks; recorded service after motion settles | Python/Manim/FFmpeg; provider credentials or microphone; weak fit for arbitrary UI/brand layouts | Preferred for formula-heavy work; no local audio trial here |
| Motion Canvas + agent plugin | Editor HTTP endpoints for status, seek, screenshot, scene graph, errors, render; MP4 through FFmpeg | Node/Vite/TypeScript, open editor/browser, FFmpeg; published setup pins Vite 5; programmable sound is alpha | Viable alternative; no local trial here |
| HTML/Canvas | Examples lane and toolchain lane expose code-first Canvas/WebGL workflows, but execution receipts are absent | Browser capture/audio/mixing and route-specific tooling must be supplied; the scorecard still applies | Available alternative; exact implementation is job-specific |
| Pexo | Hosted relay requires credentials/account/credits and transmits approved briefs/assets; adjacent proxy evidence covers per-shot media/audio orchestration | Hosted service boundary, provider billing, data transfer, MIT/MIT-0 metadata conflict, final assembly opaque | Optional hosted route; no local trial here |

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
- Set `HYPERFRAMES_NO_UPDATE_CHECK=1` and `HYPERFRAMES_NO_AUTO_INSTALL=1` for `check` and `render`. In a local 0.8.57 run, the CLI's background self-update installed 0.8.99 during a render, deleted files in `dist/`, and failed the render with "Missing manifest".
- `check` does not test elements marked `data-layout-allow-overlap`, so an overlap they cause can pass. The per-sentence frame sweep in M6 of the production prompt covers them.
- Persist Studio caption/timing changes into source files and refresh the preview before accepting them (S-HF-005).

These local HyperFrames runs show that the route works in this environment; they do not validate the renderer in general.

## Evidence boundaries and use policy

Source-use rules are under "Use rules" in `library/source-map.md`. In `methods/prepare-explainer-video.md`, "Intake contract" holds the evidence limits for creator claims and public repositories, and "Applicability and known failure modes" holds those for stills and licenses.
