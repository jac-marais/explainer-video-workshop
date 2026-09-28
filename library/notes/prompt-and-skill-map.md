# Published skills, creator prompts, and workshop prompts

The most concrete dedicated explainer skill recovered is **HyperFrames `faceless-explainer`**. Its source is inspectable. This research did not reproduce an exceptional finished video with it and did not establish that the eight-hour UMAP creator used it.

## Published implementation references

| Source | What to inspect | What it contributes | Boundaries |
|---|---|---|---|
| [HyperFrames entry point](https://github.com/heygen-com/hyperframes/blob/3db3da7bb284c5f0d89a1f7507d96115236e6bfc/skills/hyperframes/SKILL.md) — S-HF-009 | State/resume, route table, sibling skills | Chooses a workflow and records a durable brief | Vendor defaults cover much more than this workshop. Do not adopt its broad trigger or automatic upgrades blindly. |
| [Faceless explainer](https://github.com/heygen-com/hyperframes/blob/3db3da7bb284c5f0d89a1f7507d96115236e6bfc/skills/faceless-explainer/SKILL.md) — S-HF-010 | Steps 0–6 and linked worker/audio resources | Text → storyboard/script → design system → audio metadata → bounded scene workers → composition/MP4 | Requires sibling skills and scripts; one `SKILL.md` is not the whole tool. Sweet spot 30–90 s, about three-minute cap; longer work uses general-video (S-HF-011). |
| [HyperFrames core](https://github.com/heygen-com/hyperframes/blob/3db3da7bb284c5f0d89a1f7507d96115236e6bfc/skills/hyperframes-core/SKILL.md) — S-HF-003 | Standalone vs subcomposition, timeline identity, clip/audio rules, validation | Seekable deterministic composition contract | Lint errors can skip layout/contrast audits. A report with zero inspected samples does not prove visual correctness. |
| [Remotion official agent plugin](https://github.com/remotion-dev/claude-code-plugin/tree/a39a50197c85e9082826ecc64fec9f37a8b48bfe) — S-TC-001 | `remotion-create`, `remotion-markup`, voiceover, captions, rendering skills | React/frame-driven implementation, measured audio duration, still and full rendering | Check framework and plugin terms separately. Best fit here is an existing React design/project. |
| [Manim Voiceover](https://github.com/ManimCommunity/manim-voiceover/tree/3dc0d95d2f1d9d0937872b3dd68c7b38c4dfc96a) — S-TC-003 | Quickstart duration trackers and bookmarks | Formula/geometry animation synchronized to narration | API documentation and example code, not a viral creator's exact prompt. Provider/recording needs are separate. |
| [Motion Canvas agent skills](https://github.com/VideoZero/skills/tree/d90f87c44bc7109147d094603e33da43c217799b) — S-TC-004 | `motion-canvas-agent` and setup/rendering references | Seek, screenshot, scene-graph/error inspection, render | Requires a local editor/bridge. Version-specific compatibility needs a fixture. |
| [Video Talkcraft](https://github.com/Vincentwei1021/video-talkcraft/tree/914103688cdec20ea35699f73b08e357a817c37a) — S-TC-006 | Narration-first skill and review protocol | Pre-cut before alignment, shotbook, sample shot, selective repair | License unresolved in the receipt: reference and paraphrase, do not vendor its text. |
| [Claude Video Kit](https://github.com/runesleo/claude-video-kit/tree/21f5462067b63c96e33b5bdbf7d4853bf2b94b16) — S-TC-008 | `video-explainer`, review gate, render pipeline | Separate preproduction and exact-MP4 review; deterministic fallback | Source inspected only. “Demo quality” is not publication quality. |
| [Video Layer Skill](https://github.com/Alexander-Kz/video-layer-skill/tree/5c87d0a53f5cd35d8d5c5d9ea23718e5d2100e5c) — S-TC-007 | State, dependency waves, missing-only resume | Resumable external-image generation and assembly | Provider costs and heavy checkpoint machinery are project choices, not mandatory workshop architecture. |
| [Pexo agent](https://github.com/pexoai/pexo-skills/blob/f724267e45a065b6be445ea6f07312e62d3207cd/skills/pexo-agent/SKILL.md) — S-PX-003 | Hosted relay, asset uploads, billing/events | Optional access to a hosted media-production service | Key/account/credits; backend routing and final assembly not independently verified. Root MIT / skill MIT-0 metadata conflict. |

These are exact **published instructions at pinned URLs**. They are not exact prompts known to have produced the indexed showcase videos. Upstream skills are reference material until deliberately selected; their broad defaults, installs, upload instructions, and approvals do not override the user's scope or existing authorization.

## Creator prompt trail

The source-linked index points to [Ian Nuttall's detailed game prompt](https://x.com/iannuttall/status/2102685189558190087) and [Marc the Creator's launch-film prompt screenshot](https://x.com/marcthecreatorr/status/2103133477600206925). Both are adjacent examples, not the eight-hour explainer. The originals were login-gated in this pass; the exact text was **not independently recovered** (S-EX-019/021). Do not invent a verbatim prompt from the index's description.

The UMAP prompt and run trace are not recovered. The workshop's prompts below are original reconstructions from the verified methods, with no creator attribution.

## Workshop-authored prompts

- [Preparation prompt](../../templates/master-prompt.md): source intake, learning target, script/scene plan, renderer choice, and a filled production handoff.
- [Production prompt](../../templates/production-prompt.md): execute an approved preparation package through narration, timing, pilot, scene work, final rendering/review, and reproducible delivery.

## Installation boundary

This workspace's new canonical skills belong in `~/.agents/skills/`; local `.agents/skills` and `.claude/skills` entries are mounts. No upstream video skill or renderer was installed during research. HyperFrames' published `init` and `skills update` operations may refresh global skill sets. Inspect their target/current options before invoking them so a vendor installer does not silently violate the user's skill-placement rule. Use complete upstream bundles when selected; do not copy just an entrypoint and leave its scripts/references missing. Keep a tested package version pinned during a production run and re-check affected output when upgrading.
