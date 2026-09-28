# Prepare an explainer-video agent run — v0.1

Status: promoted preparation method. This prepares a production run and its handoff. Local rendering, sustained production, and educational effectiveness remain unvalidated.

This method is an original workshop reconstruction. It is not a creator's prompt and does not copy a published skill. Source IDs resolve to original URLs through `library/manifest.json`.

## Job and trigger

Use this workbench when the request supplies, or asks the agent to collect, a subject, audience, sources, and a time or money budget for an explainer. The output is a preparation package that another agent can execute or resume:

```text
brief → claim map → learning target → script estimate → scene/shot plan
      → route and dependency check → approved audio/timing plan
      → representative-scene pilot plan → scored handoff
```

The workbench handles conceptual, procedural, scientific, and product explainers. It does not handle generic filmmaking, entertainment shorts, advertising strategy, voice impersonation without consent, or publication/upload.

## Intake contract

Collect these fields before drafting a script. If a non-factual preference is absent, use a labeled default instead of blocking a natural request: 16:9, 1920×1080, 30 fps, captions when narration is present, a neutral readable visual system (or the brand in `local/brand.md`, applied through `methods/apply-brand.md`), and no publication/upload. Ask only when the missing value changes the route, acceptance claim, rights, or learning target.

- subject and the learner's starting knowledge;
- one observable learning target and the check that would show it was met;
- source list with owner, title, date/version, URL or local path, rights/use note, and whether the content was actually readable;
- target length, aspect ratio, resolution, frame rate, language, captions, tone, accessibility, and required delivery files;
- available assets and audio, prohibited assets, renderer/tool constraints, and the externally imposed cost or wall-clock limit;
- creator preferences and exclusions, keeping them separate from factual claims.

If an essential source is missing, unreadable, inaccessible, or only represented by a search snippet, stop before making claims from it. Record the source, attempted access, the claim that depends on it, and the smallest safe next action. Continue only with a narrowed brief that explicitly excludes those claims. A readable source is not automatically authoritative; record what its owner is qualified to establish.

If intake stops, do not manufacture empty script, scene, audio, pilot, or production-prompt files. Write one concise `handoff.md` containing the blocked source, dependent claims, attempted access, missing authority, and next action. Add `run-state.md` only when it preserves useful recovery information. The full downstream package below applies after intake yields a viable, narrowed brief.

Do not infer a model identity, elapsed run time, human intervention level, final video duration, or quality result from a post, screenshot, index label, or repository alone. Public prompt material is limited and does not prove the prompt was executed as shown; this research recovered no independent eight-hour reproduction for the reported examples (S-EX-001–S-EX-025). The model and task-budget sources likewise do not establish an explainer-video SLA or wall-clock allowance (S-FA-001–S-FA-004).

## Ordered procedure

### 1. Define the learning target

Write one sentence in the form:

> After watching, **[audience]** can **[observable action or explanation]** under **[stated condition]**, as checked by **[short question, prediction, or worked example]**.

Reject a target that only says “understand,” “be inspired,” or “see how it works.” A target can be a design choice, but its source and scope should be clear. Keep the target narrow enough to fit the requested duration; educational-video guidance supports brief, targeted lessons, signaling, segmenting, weeding, complementary audio/visual channels, and active processing, while warning that engagement is not the same as learning (S-FA-006–S-FA-008).

### 2. Build the claim map before prose

Give every factual, numerical, causal, historical, API, or safety claim a stable ID. For each claim, record:

| Field | Required content |
|---|---|
| `claim_id` | `C-001`, `C-002`, … |
| proposition | One testable statement, with units and conditions |
| source | Source ID plus exact page, section, timestamp, or code locator |
| status | `supported`, `qualified`, `disputed`, `assumption`, or `omit` |
| planned use | Spoken line, on-screen text, diagram, or omitted |
| check | How a reviewer will verify it |

Promote a claim into the script only when its source receipt is readable and the status is supported or properly qualified. If sources disagree, preserve the disagreement and state the scope in the script or omit the claim; do not average it into an untraceable sentence. This is the workshop application of NIST's fact-checking and domain-review guidance and its warning about confabulation and automation bias (S-FA-005).

### 3. Draft the narrative and honest time estimate

Draft the narration in scenes. Each scene must have one comprehension job, one central visual idea, one sentence describing why motion helps, and a planned transition. Keep spoken words, screen text, and source citations separate so a crowded frame does not become the teaching method.

Estimate the script duration explicitly:

```text
estimated_seconds = narration_word_count / chosen_words_per_minute × 60
```

Record the word count and the chosen WPM range (for example, 130–165 WPM) beside the estimate. This is planning arithmetic. It is not measured audio. Once audio exists, record its actual file duration and derive scene, sentence, word, and caption timing from that file. A later trim, re-record, speed change, or pause edit invalidates timing and every visual or caption artifact that consumes it (S-TC-001, S-TC-003, S-TC-006, S-TC-008).

Run the same arithmetic per scene. Record narration words, target WPM or range, speech seconds, breathing-pause budget, learner-processing-pause budget, and the total planned scene window. Speech seconds are `words / WPM × 60` and exclude both kinds of pause. Require each rough scene window to cover speech plus its declared pauses, and require the scene-window sum to match the target duration within declared transition or end-card tolerance. A global word count can fit while one scene demands implausible speech; repair the scene words, window, or narrative before production. Final approved audio remains authoritative when it exists.

### 4. Convert the narrative into a scene and shot sequence

Use `templates/scene-plan.md`. A scene is a learner-facing comprehension unit; a shot is a contiguous renderable interval. For each shot, specify the narration segment, claim IDs, visual elements, motion grammar, screen text, asset paths and rights, entry/exit condition, and dependency. The plan must expose any shot that needs an external asset, a browser/editor, a particular renderer, a secret, or a human recording.

Use the information structure to choose motion. Signaling, segmenting, and removing decorative motion have direct educational rationale (S-FA-006, S-FA-008). A generic fade or zoom is not an explanation. If the visual cannot make the target action or mechanism easier to see, use a static card or omit it.

### 5. Route the learner job to a renderer

Choose the path after the shot plan, not before it:

| Learner job | Candidate route | Use another route when |
|---|---|---|
| Existing React/UI project, charts, captions, supplied recordings, reusable React scenes | Remotion | The project cannot satisfy its Node/React/Chrome or license constraints |
| New plain-HTML/browser-native diagrams, captions, supplied recordings, or brand motion | HyperFrames local route | The composition cannot satisfy its standalone HTML, `data-*` timing, paused seekable timeline, Node/FFmpeg, or Apache-2.0 constraints |
| Formula, geometry, precise mathematical or scientific transformation | Manim + Manim Voiceover | The lesson is mostly UI, arbitrary web assets, or brand layout |
| TypeScript vector scenes where seek, screenshots, and scene graph inspection matter | Motion Canvas | The browser/editor bridge or FFmpeg dependency is unavailable |
| Small generic diagrams or canvas scenes | HTML/Canvas or Motion Canvas | HyperFrames is a better fit for a new browser-native composition, or a specialized route has a clear acceptance advantage |
| Photoreal multi-shot generation or hosted asset orchestration | Pexo optional hosted route | Credentials, account, credits, data-transfer terms, or final assembly evidence are unavailable |

The route capabilities are source-backed; the learner-job mapping is a workshop design choice (S-TC-001–S-TC-004, S-HF-001–S-HF-005, S-PX-003). HyperFrames is a candidate local route, not a claim of local execution or universal superiority. Pexo is a hosted, credentialed optional route; the public client repository does not make its service free and does not prove final assembly quality (S-PX-003). Do not silently change routes when a dependency, license, account, or data-transfer condition fails: record the disqualifier and revise the plan. The route must leave an editable source and an inspectable render command when the local stack supports them.

When HyperFrames is selected, apply the route-specific preflight traps in `library/notes/production-paths.md`; a lint-disabled audit or `0-of-0` sample report is not acceptance evidence.

### 6. Plan audio and timing as invalidatable artifacts

When audio exists, the approved voice track is the timing authority. Before audio exists, record the intended source and timing plan and mark measured timing pending. The exact implementation can use measured scene durations (for example, Remotion metadata) or in-scene duration/bookmark tracking (for example, Manim Voiceover); both still consume approved audio when production runs (S-TC-001, S-TC-003, S-TC-008).

Record an audio receipt with path, provider or recorder, language, sample rate if known, duration, checksum if available, and approval status. Record timing with scene and word/sentence bounds, match confidence, and the audio receipt it was derived from. Do not edit audio after timing without rebuilding the timing artifact.

Use this invalidation table:

| Changed artifact | Invalidate and rebuild |
|---|---|
| source, claim status, or learning target | claim map; affected script, scene plan, review, audio, timing, pilot |
| script words or scene order | audio; timing; captions; affected scenes; script-bound pre-render review |
| approved audio bytes or trim | timing; captions; all audio-bound visual cues; pilot and pre-render review |
| scene code, assets, renderer, FPS, or dimensions | affected scene preview; machine checks; pilot; pre-render review |
| final MP4 bytes | final review receipt only; retain the old receipt as historical evidence |

This keeps the old MP4 from masquerading as a successful new render, a failure pattern explicitly called out in the production sources (S-TC-005, S-TC-007, S-TC-008).

### 7. Plan, then (when requested) pilot the hardest representative scene

Pick the hardest or most representative shot, not the easiest title card. It should exercise the global visual system, the route's key dependency, the longest or tightest timing beat, and the most failure-prone asset. In a preparation-only request, record the pilot shot, inputs, commands, and acceptance checks, and mark the pilot as not run. When production is requested and the local stack exists, produce a voiced short preview and stills. For motion, inspect a contiguous 2–4 second region with neighboring frames; for route-specific tools, also inspect Studio stills, the Motion Canvas scene graph/errors, or a low-quality Manim render as applicable (S-TC-001–S-TC-004, S-TC-009).

The pilot gate asks:

- Does the scene teach the intended claim without a misleading metaphor?
- Do visual events align with the intended spoken cue, or is any lead/lag a deliberate explanatory choice?
- Are labels, formulas, captions, and contrast legible at delivery size?
- Does the renderer actually produce the motion encoded by the scene clock?
- Are external assets present, permitted, and credited in the manifest?

An accepted pilot is production evidence for that scene. It does not prove a full render, full-film audio quality, factual correctness of every scene, or educational effectiveness. A preparation package may pass with a pilot plan marked not run.

### 8. Run machine checks and bounded checkpoints

For a viable brief, use a small set of durable artifacts instead of a forest of status files:

```text
brief.md
claim-map.md
script.md
scene-plan.md
audio-receipt.md
timing.md
assets-manifest.md
pilot-review.md
pre-render-review.md
run-state.md
production-prompt.md
handoff.md
```

Each artifact has a status (`missing`, `draft`, `checked`, `invalidated`, `accepted`) and an explicit dependency. A renderer may also require JSON or TypeScript inputs; keep those as implementation files, not as the workshop's only record.

The run state records the current phase, completed artifacts, invalidations, retries, external time and spend measurements, renderer/version, and next action. Resume by reconciling state with the filesystem: a missing or corrupt artifact is not complete merely because a flag says so. Regenerate only the affected artifact and its dependents. Dependency waves are useful for generated assets: gate roots before dependent continuations (S-TC-005, S-TC-007).

Checkpoints are agent gates, not mandatory human approvals. The agent may proceed when the gate evidence is present. Stop for user authority only for a purchase, publication, irreversible external write, or a private preference the brief cannot resolve.

### 9. Score the preparation package

Use `scorecards/preparation-quality.md`. Score a preparation package against planned evidence and score production evidence against measured artifacts. A weighted total helps prioritize work, but it cannot erase a critical failure. Essential unreadable sources, unsupported promoted claims, missing timing or pilot plans, infeasible per-scene narration windows, render errors in a claimed pilot, missing rights evidence, or a stale receipt fail the relevant claim regardless of the numeric score.

### 10. Final handoff

For a viable brief, the preparation handoff contains:

- brief, learning target, audience assumptions, and duration estimate with word count/WPM;
- readable source receipts, claim map, unresolved claims, and rights/privacy notes;
- script, scene/shot plan, route decision with alternatives and disqualifiers;
- audio receipt and timing plan, including what invalidates them;
- pilot plan, plus pilot media when production was requested and actually run, or an explicit statement that no local pilot was run;
- scorecard, machine-check plan, run state, renderer/version commands, and external cost/time instrumentation plan;
- a filled `production-prompt.md` that accepts this package and can execute the future narration, pilot, scene build, render, full playback, review, resume, and exact handoff route;
- editable project and asset/source manifest when they exist;
- remaining uncertainty and the next concrete validation trial.

Call the package “prepared” only when the preparation scorecard passes. Call a scene “piloted” only when a voiced pilot actually ran and was reviewed. Call a video “rendered” only after an actual render and exact-byte final review. Call it “successful,” “accurate,” or “educationally effective” only when the relevant evidence exists. The workshop's current task ends at preparation unless the user explicitly requests production.

For a blocked intake, call the result “blocked at intake,” deliver the concise `handoff.md`, and stop. Do not call it a prepared package or emit a filled production prompt for a route whose essential inputs do not exist.

## Adjustable eight-hour ceiling

An eight-hour figure is a planning ceiling for an end-to-end production attempt, not eight hours of paperwork, a promise, a required runtime, or a quality target. Preparation-only work can finish earlier after its package passes. The user or external controller enforces actual wall-clock and money limits; an advisory prompt cannot enforce them. Record actual elapsed time and spend from the controller or billing source.

One adjustable starting allocation for a full production attempt is:

| Work | Ceiling | What earns the time |
|---|---:|---|
| Research, brief, claim map, and script | 1.5 h | Source receipts, learning target, traceable narrative |
| Scene build and asset integration | 2.25 h | Global visual system and most representative scenes |
| Narration and measured timing | 1.0 h | Approved audio, captions, and invalidation map |
| Pilot, inspect, and repair | 0.75 h | Voiced hard-scene evidence when production is requested |
| Render, inspect, and targeted repair | 1.75 h | Actual output checks and changed-scene renders |
| Handoff, state, and contingency | 0.75 h | Editable package, resume notes, and named blockers |
| **Total ceiling** | **8.0 h** | Adjustable; unused time is not a defect |

If the external limit is smaller, reduce scope and declare the omitted scenes or claims. If a source or renderer blocks progress, stop or narrow; do not spend the ceiling pretending that uncertainty is progress.

## Applicability and known failure modes

- This method is strongest for a bounded explainer with readable sources and an editable code-first or vector route.
- It does not establish that a model can run unattended for eight hours, that a specific model is best, or that a polished-looking film teaches well (S-FA-001–S-FA-004, S-EX-001–S-EX-025).
- A source repository or visible prompt receipt supports an inspectable method or prompt artifact, not that the posted artifact used it or that the run was unattended (S-EX-004, S-EX-011, S-EX-018–S-EX-021, S-TC-009).
- Still frames cannot establish continuous motion, audio quality, synchronization, or whole-film quality; the contiguous pilot and final exact-byte review are required (S-TC-009).
- Tool instructions with no declared license must be paraphrased and reimplemented unless a license decision permits reuse (S-TC-001, S-TC-006). Keep provider secrets outside source artifacts.
- Voice quality, pronunciation, and caption matching vary by language and provider. A recorded and a generated-audio variant should be trialed before treating either as default (S-TC-003, S-TC-006).

