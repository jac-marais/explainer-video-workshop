# Renderers — evidence-backed route notes

This note records what each renderer route's public sources expose, what remains unverified, and what has run locally. It is not a renderer installation guide.

## Route matrix

Method step 5 in `methods/prepare-explainer-video.md` chooses the route for each learner job. This table records each route's public evidence, dependencies, and local status.

Local runs in this workshop have taken the HyperFrames route through render and agent final review, with each final review bound to its MP4 checksum. Live-app capture has run once locally, through render and agent review of per-sentence stills. No other route has been trialed, so trial each one before claiming that it works.

| Route | Public method evidence | Dependencies / disqualifiers | Current status |
|---|---|---|---|
| Remotion | `useCurrentFrame()`/`interpolate()`; audio durations feed composition metadata; Studio/stills/selected-frame preview; MP4 render | Node, React/TypeScript, Chrome/headless render; official plugin metadata has no declared repository license; Remotion license needs its own decision | Retained for existing React projects; no local trial here |
| HyperFrames | Apache-2.0 repository; standalone HTML; `data-*` timing; one paused seekable timeline; local CLI/Studio; word timestamps/imported transcripts; published route/lifecycle (S-HF-009–S-HF-011) | Node 22+, FFmpeg, browser runtime; standalone composition contract; the vendor's published faceless-explainer route covers topic/article explainers without product or website capture, with a 30–90 s sweet spot and about a 3 min cap, and longer pieces route to its general-video path | First local route for new browser-native work, and run locally; scope/length guidance is vendor-route-specific, not a universal duration rule |
| Live-app capture | Workshop-built from one local run; no published method. Playwright drives the running app, and a Chrome DevTools Protocol screencast captures the frames | Node, Playwright, Chromium, FFmpeg; the app running locally with mock or test data; the app must allow same-origin framing (no blocking `X-Frame-Options` or CSP `frame-ancestors`); every take runs in real time | Run locally once; first choice when the film shows how an existing web app behaves |
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

## What live-app capture records

Live-app capture films the running product instead of rebuilding it, so every screen in the film is a real state of the app. A stage page served on the app's own origin holds the app in same-origin iframes beside the explanation layer: a code or schema panel, outlines on real elements, and captions. Because it is one page, the app and the explanation share one frame clock.

```text
for each narration line: log its cue time → drive the app and the overlays
  → wait for the line's measured audio length
screencast frames + cue log → constant-rate video, each audio file at its cue,
  captions from the same cues
```

The cue log keeps the approved audio as the timing authority without aligning separate clips. The cost is that an audio or script change needs a new real-time take.

The route-specific acceptance traps for HyperFrames and live-app capture are in `methods/renderer-traps.md`.

## Evidence boundaries and use policy

Source-use rules are under "Use rules" in `library/source-map.md`. In `methods/prepare-explainer-video.md`, "Intake contract" holds the evidence limits for creator claims and public repositories, and "Applicability and known failure modes" holds those for stills and licenses.
