# Prepare an explainer-video agent run — v0.1

Status: promoted preparation method. This prepares a production run and its handoff. Production has run end to end on two routes, HyperFrames and live-app capture, through render and agent review; `library/renderers.md` gives the status of each route. Sustained or multi-hour production and educational effectiveness remain unvalidated.

This method is an original workshop reconstruction. It is not a creator's prompt and does not copy a published skill. Source IDs resolve to original URLs through `library/manifest.json`.

## Job and trigger

Use this method when the request supplies, or asks the agent to collect, a subject, audience, sources, and a time or money budget for an explainer. The output is a preparation package that another agent can execute or resume:

```text
brief → claim map → learning target → script estimate → scene/shot plan → storyboard
      → route and dependency check → approved audio/timing plan
      → representative-scene pilot plan → scored handoff
```

The method handles conceptual, procedural, scientific, and product explainers. It does not handle generic filmmaking, entertainment shorts, advertising strategy, voice impersonation without consent, or publication/upload.

## Intake contract

Collect these fields before drafting a script. If a non-factual preference is absent, use a labeled default instead of blocking a natural request: 16:9, 1920×1080, 30 fps, captions when narration is present, a neutral readable visual system (or the brand in `local/brand.md`, applied through `methods/brand-explainer-video.md`), and no publication/upload. Ask only when the missing value changes the route, acceptance claim, rights, or learning target.

- subject and the learner's starting knowledge;
- one observable learning target and the check that would show it was met;
- source list with owner, title, date/version, URL or local path, rights/use note, and whether the content was actually readable;
- target length, aspect ratio, resolution, frame rate, language, captions, tone, accessibility, and required delivery files;
- available assets and audio, prohibited assets, renderer/tool constraints, and the externally imposed cost or wall-clock limit;
- creator preferences and exclusions, keeping them separate from factual claims.

If an essential source is missing, unreadable, inaccessible, or only represented by a search snippet, stop the claims that depend on it. Record the source, attempted access, the dependent claims, and the smallest safe next action. Continue only on a narrowed brief that explicitly excludes those claims, and continue independent work that does not rely on the blocked source. Never invent a missing source, prompt, or result. A readable source is not automatically authoritative; record what its owner is qualified to establish.

If no viable brief remains, the intake is blocked. Call the result "blocked at intake", record it in `run-state.md` with the phase `blocked at intake`, the blocked source, dependent claims, attempted access, missing authority, and next action, and stop. Fill only the parts of the template that carry this information. Do not manufacture empty script, scene, audio, pilot, scorecard, or production-prompt files. Do not call the result a prepared package or emit a filled production prompt for a route whose essential inputs do not exist. The full downstream package below applies after intake yields a viable, narrowed brief.

Do not infer a model identity, elapsed run time, human intervention level, final video duration, or quality result from a post, screenshot, index label, or repository alone. Public prompt material is limited and does not prove the prompt was executed as shown. A source repository, published skill text, or visible prompt receipt supports an inspectable method or prompt artifact, not that a creator used it or that the run was unattended (S-EX-004, S-EX-011, S-EX-018–S-EX-021, S-TC-009). This research recovered no independent eight-hour reproduction for the reported examples (S-EX-001–S-EX-025). The model and task-budget sources likewise do not establish an explainer-video SLA or wall-clock allowance (S-FA-001–S-FA-004).

## Ordered procedure

### 1. Define the learning target

Write one sentence in the form:

> After watching, **[audience]** can **[observable action or explanation]** under **[stated condition]**, as checked by **[short question, prediction, or worked example]**.

Reject a target that only says “understand,” “be inspired,” or “see how it works.” A target can be a design choice, but its source and scope should be clear. Keep the target narrow enough to fit the requested duration; educational-video guidance supports brief, targeted lessons, signaling, segmenting, weeding, complementary audio/visual channels, and active processing, while warning that engagement is not the same as learning (S-FA-006–S-FA-008).

Before teaching, decide whether the film needs a misconception beat. Answer three yes/no questions in the brief, each with its evidence.

- **Do they hold it?** A source shows where the wrong idea comes from, such as how today's tools behave, the docs, an issue thread, or the user saying so. The agent's own guess does not count.
- **Does it give the wrong answer?** Someone who holds the wrong idea would fail the learning-target check.
- **Can the film break it on screen in one scene?**

Three yeses mean use the beat, and the check is a prediction question that the wrong idea answers wrongly. Any no means skip the beat, and the brief records which question failed. Never invent a strawman to fill the slot. An audience that is new to the topic usually has no wrong model to break, so expect a no on the first question. That is a workshop inference and not a finding of S-FA-010. One controlled study of first-year physics students found larger learning gains from a video that stated and refuted common misconceptions than from a clear exposition. It covers one university physics population, so it does not show the same effect for other audiences or topics (S-FA-010).

### 2. Build the claim map before prose

Give every factual, numerical, causal, historical, API, or safety claim a stable ID. For each claim, record:

| Field | Required content |
|---|---|
| `claim_id` | `C-001`, `C-002`, … |
| proposition | One testable statement, with units and conditions |
| source | Source ID plus exact page, section, timestamp, or code locator |
| status | `supported`, `qualified`, `disputed`, `assumption`, `design choice` (a deliberate non-factual decision, such as a route or style), or `omit` |
| planned use | Spoken line, on-screen text, diagram, or omitted |
| check | How a reviewer will verify it |

Promote a claim into the script only when its source receipt is readable and the status is supported or properly qualified. If sources disagree, preserve the disagreement and state the scope in the script or omit the claim; do not average it into an untraceable sentence. Put a qualified claim in the narration or on screen only when the brief, the learning target, or its check needs it, and then keep its qualification with it. Otherwise set its planned use to omitted and give the reason. This is the workshop application of NIST's fact-checking and domain-review guidance and its warning about confabulation and automation bias (S-FA-005).

### 3. Draft the narrative and honest time estimate

Draft the narration in scenes. Each scene must have one comprehension job, one central visual idea, one sentence describing why motion helps, and a planned transition. Keep spoken words, screen text, and source citations separate so a crowded frame does not become the teaching method.

When the brief's rubric from step 1 says to use the beat, open with it. The film states the wrong idea in words the audience would use, pauses so the viewer can predict, shows what breaks it, and only then teaches the right model. Budget the prediction pause as learner-processing time in the scene plan.

A second story line, such as a human or historical thread that runs beside the mechanism, is optional. It suits a longer film about an idea, and it adds length and build cost. The misconception evidence does not cover it. A short film, such as a PR walk-through, should not use it.

Write the narration for a listener who hears it once and cannot reread it. Use full sentences, and keep the linking words, such as "because", "so", and "until", that carry the logic from one sentence to the next. Avoid "this, not that" constructions. Never use an em dash or colon in the middle of a sentence. Split the thought into two sentences or rewrite it. Say why a mechanism exists before saying how it works. Explain each term that the audience does not already know in plain words before naming it, and then use that one name every time. Keep code identifiers out of speech unless the learner must say or type them. On screen, lead with the plain name and show the identifier beside it. Speak only the numbers that the learning target needs.

List every acronym, product name, code identifier, and number in the narration with its planned spoken form in the script's pronunciation line. Try each term as written first, and spell letters with hyphens, such as `G-P-U`, because spaced letters and spelled-out words can misread in a synthetic voice. Keep the operator's verdicts in the git-ignored `local/pronunciation.md`, which `templates/pronunciation.md` shows how to start. Add the candidate-list words that the narration uses to the pronunciation line, and apply the known fixes for the planned voice. After each ear check, record the new verdicts there.

Estimate the script duration explicitly:

```text
estimated_seconds = narration_word_count / chosen_words_per_minute × 60
```

Record the word count and the chosen WPM range (for example, 130–165 WPM) beside the estimate. This is planning arithmetic. It is not measured audio. Once audio exists, record its actual file duration and derive scene, sentence, word, and caption timing from that file. A later trim, re-record, speed change, or pause edit invalidates timing and every visual or caption artifact that consumes it (S-TC-001, S-TC-003, S-TC-006, S-TC-008).

Run the same arithmetic per scene. Record narration words, target WPM or range, speech seconds, breathing-pause budget, learner-processing-pause budget, and the total planned scene window. Speech seconds are `words / WPM × 60` and exclude both kinds of pause. Require each rough scene window to cover speech plus its declared pauses, and require the scene-window sum to match the target duration within declared transition or end-card tolerance. A global word count can fit while one scene demands implausible speech; repair the scene words, window, or narrative before production, never by faster delivery. To fit a duration, remove whole claims or narrow the learning target, and keep the explanation that each remaining claim needs. If the learning target needs a longer duration, tell the user how long it needs and record that duration in the brief. Continue with that duration unless the user directly asks to keep the original one. In that case, offer one to three narrower targets for the user to choose from. Final approved audio remains authoritative when it exists.

Before any audio exists, test the narration on a cold listener. Give a fresh agent or person the audience's starting knowledge from the brief, the spoken text, and a plain description of what each scene shows, written from each scene's planned visual idea without filling its gaps. Withhold the claim map and sources. Ask them to explain the mechanism in their own words, answer the learning-target check, and name each sentence that they had to guess at or that seemed to contradict another. Also ask them to name anything the check relies on that the film had not shown before the check, and what the viewer sees that confirms the answer. Also ask what they believed about the topic before hearing the film, and whether the film changed it. If the film uses the beat and the stated misconception is not one they held or recognise, treat that as a sign that the beat is a strawman. Repair each problem, check the changed sentences against the claim map, and repeat the test until the explanation and the answer match the claim map. Record each round in `run-state.md`.

### 4. Convert the narrative into a scene and shot sequence

Use `templates/scene-plan.md`. A scene is a learner-facing comprehension unit; a shot is a contiguous renderable interval. For each shot, specify the narration segment, claim IDs, visual elements, motion grammar, screen text, asset paths and rights, entry/exit condition, and dependency. The plan must expose any shot that needs an external asset, a browser/editor, a particular renderer, a secret, or a human recording. Take third-party 3D models, HDRIs and textures from the sources in `library/3d-assets.md`, through its intake steps.

Use the information structure to choose motion. Signaling, segmenting, and removing decorative motion have direct educational rationale (S-FA-006, S-FA-008). A generic fade or zoom is not an explanation. If the visual cannot make the target action or mechanism easier to see, use a static card or omit it.

Pin every visual that must land on a spoken moment to the quoted words it lands on, in the form in `templates/scene-plan.md`, never to a second. Seconds exist only after audio does.

Then draw the storyboard, `storyboard.html` in the run folder, from `templates/storyboard.html`. It is one page of key frames, so a reader can see how the film fits together before any audio exists. Each frame has a shot ID from `scene-plan.md`, a short title, an SVG line sketch on the brief's canvas, and one or two sentences on what the viewer sees. Draw one frame for each key visual moment, and at least one per scene. Draw the moment that carries the shot's comprehension job, such as the state the viewer must notice, not decoration. When motion carries the idea, draw its start and end states, and check that a reader can follow the argument from the frames and notes alone. Frames name shot IDs and do not copy narration, timing, or counts, so the scene plan stays the one place for those. Sketches are enough. Use the brand fonts and colors from `local/brand.md` when it exists, and show the page to the user. Redraw affected frames while preparation changes the script or scene plan. Once production starts, the storyboard stays as it is, and the scene plan and approved audio win wherever they differ from it. The storyboard step is a workshop design choice from one run, not a source-backed finding.

### 5. Route the learner job to a renderer

Choose the path after the shot plan, not before it:

| Learner job | Candidate route | Use another route when |
|---|---|---|
| How an existing web app behaves when someone uses it: its real screens, clicks, typing, and dialogs | Live-app capture | The app refuses to load in a frame, the take needs credentials it cannot hold, or scenes must be seekable or re-rendered one at a time |
| Existing React/UI project, charts, captions, supplied recordings, reusable React scenes | Remotion | The project cannot satisfy its Node/React/Chrome or license constraints |
| New plain-HTML/browser-native diagrams, captions, supplied recordings, or brand motion | HyperFrames local route | The composition cannot satisfy its standalone HTML, `data-*` timing, paused seekable timeline, Node/FFmpeg, or Apache-2.0 constraints |
| Formula, geometry, precise mathematical or scientific transformation | Manim + Manim Voiceover | The lesson is mostly UI, arbitrary web assets, or brand layout |
| TypeScript vector scenes where seek, screenshots, scene graph, and error inspection matter | Motion Canvas | The browser/editor bridge or FFmpeg dependency is unavailable |
| Small generic diagrams or canvas scenes, when direct canvas is the simplest sufficient route | HTML/Canvas or Motion Canvas | HyperFrames is a better fit for a new browser-native composition, or a specialized route has a clear acceptance advantage |
| Photoreal multi-shot generation or hosted asset orchestration | Pexo optional hosted route, only when the user explicitly chooses it | Credentials, account, credits, data-transfer terms, or final assembly evidence are unavailable |

The route capabilities are source-backed, except live-app capture, which comes from one local run; the learner-job mapping is a workshop design choice (S-TC-001–S-TC-004, S-HF-001–S-HF-005, S-PX-003). HyperFrames and live-app capture are the only routes run locally so far (`library/renderers.md`), which does not make them better for every learner job. Live-app capture films the product itself instead of rebuilding it, so no screen in the film is a reconstruction that can drift from the real app. Pexo is a hosted, credentialed optional route; the public client repository does not make its service free and does not prove final assembly quality (S-PX-003). Do not silently change routes when a dependency, license, account, or data-transfer condition fails: record the disqualifier and revise the plan. The route must leave an editable source and an inspectable render command when the local stack supports them. The narration-bound path of approved audio, measured timing, visuals that consume timing, a pilot, and exact-output review survives a renderer swap; only its implementation changes (S-TC-001, S-TC-003, S-TC-006, S-TC-008, S-TC-009).

Apply the chosen route's traps in `methods/renderer-traps.md` when it lists them.

### 6. Plan audio and timing as invalidatable artifacts

When audio exists, the approved voice track is the timing authority. Before audio exists, `audio-receipt.md` and `timing.md` record the intended source and timing plan, say why measured audio is not available, and mark measured timing pending. The exact implementation can use measured scene durations, which suit scene-based UI or vector explainers and captions (for example, Remotion or Claude Video Kit metadata), or in-scene duration/bookmark tracking, which suits word-triggered formula or diagram motion (for example, Manim Voiceover); both still consume approved audio when production runs (S-TC-001, S-TC-003, S-TC-008).

Time the pinned cues from the measured words with `scripts/audio/cues.py`, and build the captions from the same measured audio with `scripts/audio/captions.py`. `scripts/README.md` says what each tool does, and M1 of `templates/production-prompt.md` gives their command lines. Scenes read their cue times from `cues.json` and never hard-code one, so a new voice or edit re-times the film by rerunning `cues.py` and rebuilding, not by redrawing each scene.

Record an audio receipt with path, provider or recorder, language, sample rate if known, duration, checksum if available, and approval status. Record timing with scene and word/sentence bounds, match confidence, and the audio receipt it was derived from. Do not edit audio after timing without rebuilding the timing artifact.

Use this invalidation table:

| Changed artifact | Invalidate and rebuild |
|---|---|
| source, claim status, or learning target | claim map; affected script, scene plan, review, audio, timing, pilot |
| script words or scene order | cold-listener test and claim check of the changed sentences; audio; timing; captions; affected scenes; script-bound pre-render review |
| a scene's planned visual idea | cold-listener test; affected scenes; pre-render review |
| approved audio bytes or trim | timing; captions; `cues.json` and every scene that reads it; pilot and pre-render review |
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
storyboard.html
audio-receipt.md
timing.md
assets-manifest.md
pilot-review.md
pre-render-review.md
run-state.md
production-prompt.md
```

Start each file from its template in `templates/` when one exists.

The run state lives in `templates/run-state.md`. Its ledger gives each artifact a status and an explicit dependency, and its resume protocol says how to resume a run. A renderer may also require JSON or TypeScript inputs; keep those as implementation files, not as the workshop's only record. Dependency waves are useful for generated assets: gate roots before dependent continuations (S-TC-005, S-TC-007).

`AGENTS.md` owns the default that checkpoints are agent gates, and when to ask the user. The filled `production-prompt.md` can name taste gates (script, voice, stills) that the user answers asynchronously; contract item 5 of `templates/production-prompt.md` defines them.

### 9. Score the preparation package

Use `scorecards/run-quality.md`. Score a preparation package against planned evidence and score production evidence against measured artifacts. A weighted total helps prioritize work, but it cannot erase a critical failure. Any critical failure in the scorecard fails the relevant claim regardless of the numeric score.

### 10. Final handoff

For a viable brief, the step 8 files together contain:

- brief, learning target, audience assumptions, and duration estimate with word count/WPM;
- readable source receipts, claim map, unresolved claims, and rights/privacy notes;
- script, scene/shot plan, route decision with alternatives and disqualifiers;
- audio receipt and timing plan, including what invalidates them;
- pilot plan, plus pilot media when production was requested and actually run, or an explicit statement that no local pilot was run;
- scorecard result, machine-check plan in `pre-render-review.md`, run state, renderer/version commands, and the external cost/time instrumentation plan in `run-state.md`;
- a `production-prompt.md` filled from `templates/production-prompt.md`, so the next agent executes the run instead of receiving another preparation request. It accepts this package and can execute the future narration, pilot, scene build, render, full playback, review, resume, and exact handoff route;
- editable project and asset/source manifest when they exist;
- remaining uncertainty and the next concrete validation trial, recorded in `run-state.md`.

Call the package “prepared” only when it passes the scorecard's preparation mode. Call a scene “piloted” only when a voiced pilot actually ran and was reviewed. Call a video “rendered” only after an actual render and exact-byte final review. Call it “successful,” “accurate,” or “educationally effective” only when the relevant evidence exists. The workshop's current task ends at preparation unless the user explicitly requests production.

The final response reports the preparation status, learning target, source and readability stops, claim coverage, estimated words and WPM against any measured audio, scene count, renderer route with disqualifiers, pilot evidence, scorecard result, measured time and spend, and unanswered choices. It states whether a local pilot or full render actually ran, and it says "prepared package" unless an actual render and exact-byte review are evidenced.

A blocked intake never reaches this step. See "Intake contract".

## Lite route

Use it when the user asks for less than the full package, such as a film from a script that they supply. Run these in order: the script with its claim check and the cold listener test from step 3, `scripts/audio/narrate_film.py`, `scripts/audio/captions.py`, `scripts/audio/cues.py`, the build, `scripts/film/render.py`, `scripts/film/check_film.py`, and one independent review of the exact MP4. It skips `storyboard.html`, the pilot, and the pre-render review. It keeps the structure of a script the user supplies, so it adds the misconception beat from step 1 only when the user asks and the rubric gives three yeses. Never call its result a "prepared package" or a "piloted" scene. The tool steps are in M1, M5, and M6 of `templates/production-prompt.md`, and `scripts/README.md` says what each tool does.

## Adjustable eight-hour ceiling

An eight-hour figure is a planning ceiling for an end-to-end production attempt, not eight hours of paperwork, a promise, a required runtime, or a quality target. Preparation-only work can finish earlier after its package passes. Stop at acceptance or the external limit. The user or external controller enforces actual wall-clock and money limits; an advisory prompt cannot enforce them. Record actual elapsed time and spend from the controller or billing source.

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
- Still frames cannot establish continuous motion, audio quality, synchronization, or whole-film quality; the contiguous pilot and final exact-byte review are required (S-TC-009).
- Tool instructions with no declared license must be paraphrased and reimplemented unless a license decision permits reuse (S-TC-001, S-TC-006). Keep provider secrets outside source artifacts.
- Voice quality, pronunciation, and caption matching vary by language and provider. A recorded and a generated-audio variant should be trialed before treating either as default (S-TC-003, S-TC-006).

