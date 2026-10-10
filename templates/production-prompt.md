# Production prompt — execute a prepared explainer run

**Prompt provenance:** original workshop reconstruction. This is a model-neutral, documented route for a production agent. It is not a creator's prompt, a named-model recipe, or evidence that any route reliably produces a successful video, and no eight-hour run has been validated. Route status is in `library/renderers.md`. It assumes the package has already passed the preparation mode of `scorecards/run-quality.md`.

**Evidence basis:** measured audio as timing truth and invalidation rule (S-TC-001, S-TC-003, S-TC-006, S-TC-008); contiguous pilot and exact-output review (S-TC-001, S-TC-004, S-TC-009); durable state and missing-only resume (S-TC-005, S-TC-007, S-TC-008). The milestones, limits, parallelism, and acceptance language are workshop design choices derived from those sources.

Fill every bracketed field from the prepared package or external controller before sending this prompt; write `none` when a limit does not exist. Keep this file beside the run state so a later agent can resume it.

```text
You are executing a prepared explainer-video production run.

PREPARED PACKAGE
Package directory: [path]
Required records: [the package files from step 8 of methods/prepare-explainer-video.md, copied when this prompt is filled so later changes to that list do not alter this run]
Output directory: [path]
Renderer route and pinned versions: [HyperFrames / live-app capture / Remotion / Manim / Motion Canvas / HTML-Canvas, or an explicitly selected hosted route; versions and commands from the package]

EXTERNAL LIMITS
Wall-clock limit: [controller-enforced value]
Spend limit: [controller-enforced value]
Max pilot repair cycles: [default 2, or controller value]
Max selective-repair cycles: [default 2, or controller value]
Full-production planning ceiling: [default 8 hours; adjustable ceiling, never a required runtime and never a quality guarantee]
Taste gates: [none, or any of script, voice, stills that the user answers; an unnamed gate is an agent gate]
Length ceiling: [maximum film length and sentence count, or none]

The external controller enforces time, money, credentials, network, and publication permissions. Record actual elapsed time and spend. Stop at acceptance or when a limit, critical blocker, or missing authority prevents safe progress. Do not keep working to fill the eight-hour ceiling.

PRODUCTION CONTRACT
1. Read the prepared package and reconcile run-state.md with the filesystem before changing anything. A missing, empty, corrupt, or mismatched artifact is invalid even if the state file says it passed. Never reuse an old MP4 as the result of a failed or changed render.
2. Preserve the claim map and source boundaries. If an essential source is unreadable, a required asset lacks a rights note, or a promoted claim has no readable locator, stop and report the blocker. Narrowing the claim or asset set requires recording the change and invalidating affected script, scene, audio, timing, and review artifacts.
3. Use the prepared renderer route when its dependencies and license permit it. Do not lock the run to a named model. Choose available providers and tools that satisfy the package, record their versions/roles, and stop if the route cannot meet the acceptance contract.
4. Treat the approved audio bytes as timing truth once they exist. A re-record, trim, speed change, pause edit, or script change invalidates timing, captions, audio-bound visual cues, the pilot, and the pre-render receipt. Rebuild the affected artifacts before proceeding.
5. Checkpoints are agent gates by default, not human approvals; proceed when the gate evidence is present. A gate named in the Taste gates field is answered by the user, asynchronously. The script gate comes before voicing, and sends the script with its term and source check against the text and the cold listener's result. The voice gate comes before the picture build, and sends a voiced read of the full script or its hardest two minutes, made the way the final will be (one take, the cut rule, the chosen voice). The stills gate comes before the full build, and sends two options at delivery size, including the tightest frames. The user picks, you keep the alternative, and you may not accept your own deviation from the contract. While a user gate is open, continue work that it does not affect. Ask the user otherwise only before a purchase, a publication or upload, contacting a creator or brand owner, another irreversible external write, or a private preference that the prepared package does not resolve.
6. Use storyboard.html as the composition reference when building the pilot and the scenes. Where it differs from the scene plan or approved audio, follow those and leave the storyboard unchanged.
7. Keep the run lean. Start each film in a fresh session from the prepared package and run-state.md. The lead reads check reports and verdicts, and leaves mechanical work to a script (`scripts/README.md` lists the tools). Mark every milestone with `scripts/run/runlog.py mark RUN_STATE.md PHASE SESSION...`. Keep the script and film inside the length ceiling. Reports and hand-backs use absolute paths and stay short. Do not commit or push unless asked. If a hand-back is refused, report once by text and stop. Only one session edits the workshop at a time.

MILESTONES

M0 — Preflight and resume

- Read the brief, claim map, script, scene plan, assets manifest, route, and state. Inspect any existing project and preserve its meaningful files.
- Verify source readability, asset rights notes, required dependencies, output dimensions, FPS, language, caption requirement, and the current next action.
- Run `sh scripts/run/setup_check.sh [HYPERFRAMES_BIN]`, which only reads the environment, and resolve every FAIL it prints before building. Pass the route's HyperFrames CLI, or that check prints SKIP.
- Apply the chosen route's traps in `methods/renderer-traps.md` before accepting its checks. For HyperFrames, that is its "HyperFrames preflight traps" section, and a lint-disabled or `0-of-0` audit is not a pass.
- Locate completed artifacts and classify missing/empty/corrupt/stale files. Rebuild only the affected artifact and dependents. Append the decision and invalidation to run-state.md.

Checkpoint: the route, inputs, limits, and current dependency graph are explicit.

M1 — Narration and timing

- The script gate, when named, opens before the first voicing, and the voice gate before M2.
- Apply the known fixes in `local/pronunciation.md` and record each new verdict there (format in `templates/pronunciation.md`).
- Before full synthesis, synthesize one test sentence that says every term in the script's pronunciation line. Transcribe it with a local speech-to-text model, such as Whisper, and respell each term that it hears wrong. Then get the user's approval by ear, which overrules the transcript. The ear check is required unless the user waives it. Without it, accept a term only when the transcript hears it correctly. If no spelling passes, keep the closest one and list it in the audio receipt for the final listen. Record the approved spoken forms in the script and the audio receipt.
- Use the supplied approved audio when valid. If production is authorized and audio is pending, create or record it using the provider/recorder allowed by the package.
- Pick the voice as "Pick the voice for a run" in `methods/voice-explainer-video.md` says. Generate through `scripts/audio/narrate_film.py`, which drives `local/voice/voice.py`; that method covers both.
- Run `uv run scripts/audio/narrate_film.py SCENES.json --voice NAME --out AUDIO_DIR --strict`, adding `--spoken RESPELLINGS.json` for the approved spoken forms. It voices, cuts, and assembles the narration, and writes `timing.json`, `words.json` aligned to the script, and `audio-checks.json`. `--strict` fails only when a script word has no Whisper time. The audio flags do not change the exit code, so open `audio-checks.json` and resolve every flag. After a script edit, rerun with `--reuse OLD_AUDIO_DIR` under the canonical take-level reuse rule in `methods/voice-explainer-video.md#take-level-reuse`. `--check-only AUDIO_DIR` checks supplied audio.
- Then run `scripts/audio/captions.py TIMING.json WORDS.json --output CAPTIONS.vtt --json-output captions.json`, and `scripts/audio/cues.py SCRIPT.md WORDS.json TIMING.json --out cues.json --strict`. `--strict` fails on a quoted cue with no matching words, so fix its quote or give the word an alias with `--aliases ALIASES.json` (format in the script's docstring).
- Save the audio receipt with path, provider or recorder, language, measured duration, and checksum when available. Keep credentials outside the source artifacts. Generate every receipt table with `scripts/run/receipts.py FILE.md... --audio AUDIO_DIR` between its `<!-- receipts:NAME -->` markers (`--init FILE.md BLOCK...` adds them), never by hand. Add `--film MP4`, `--captions captions.json`, or `--scenes SCENES.json` for the `film`, `captions`, and `scenes` blocks.
- Pre-cut audio before alignment when edits are needed. Derive scene, sentence/word, and caption timestamps from the approved audio. Mark low-confidence matches and repair them before visual timing depends on them.
- Keep the script's word/WPM duration estimate beside the measured duration; never replace one with the other.

Checkpoint: timing names the exact approved audio receipt, or the run stops with a concrete audio blocker. Do not build audio-dependent scenes against a guessed duration.

M2 — Hard voiced pilot and shared style

- Choose the pilot shot from the prepared scene plan, and judge it by the pilot selection rule and the pilot gate in step 7 of `methods/prepare-explainer-video.md`.
- If `local/brand.md` names guidelines, build the shared style from them per `methods/brand-explainer-video.md`.
- Build the shared style and this shot with its real or representative audio. Produce still frames and a contiguous 2–4 second voiced sample; inspect neighboring frames at delivery size.
- Use every check that the chosen route offers. Examples are the M0 preflight for HyperFrames, Studio/stills for Remotion, a low-quality render for Manim, and the scene graph and errors for Motion Canvas.
- Repair only bounded pilot defects. Record each cycle and stop if the configured repair limit is reached. A passing pilot is evidence for this scene; it is not full-film proof.
- The stills gate, when named, opens here, before M3.

Checkpoint: the pilot passes its gate, or the run stops with the remaining defect and evidence.

PARALLEL WORK RULE

Independent bounded source or asset checks named by the prepared package may run in parallel before M3. Each worker records source IDs, exact locators, rights notes, and proposed changes; one sequential convergence step updates the canonical claim map or asset manifest before dependent work consumes it. After M2 passes, independent scene construction may proceed in parallel when each worker uses the locked style tokens, claim IDs, timing IDs, asset paths, and renderer versions. Keep shared dependencies sequential: source/claim changes, script order, audio production, timing, global style, captions, scene transitions, final mix, full render, and final review. If a shared dependency changes, invalidate every affected branch before merging it.

M3 — Build all scenes

- Implement each prepared shot and scene with the approved audio/timing contract. Read every audio-bound cue time from `cues.json`, never a hard-coded second. After a re-voice, rerun M1's captions and cues commands and rebuild.
- Keep one comprehension job per scene. Preserve source-backed labels, formulas, units, captions, and uncertainty from the claim map. Remove decorative motion that competes with the learning target.
- Render cheap stills or selected frames for changed layout, text, or asset questions. For motion changes, render the changed scene and its boundary overlap; do not spend a full render on a known local defect.
- Skip picture review for a scene whose source and timing are byte-identical to the last reviewed version (M4).
- Record missing assets, failed renders, retries, and actual external spend.

Checkpoint: every planned scene has an implementation or an explicit blocker, and scene coverage, claim coverage, and timing coverage are reconciled.

M4 — Selective inspection and repair

- Run deterministic checks for source/asset presence, dimensions, FPS, duration metadata, caption bounds, scene coverage, renderer errors, and stale outputs. Run `scripts/film/check_film.py` on the latest render of the film or of the changed scenes. It prints failures only.
- Inspect changed scenes and their neighboring transitions at delivery size. A scene whose source and timing are byte-identical to the last reviewed version keeps its earlier picture review, with the matching hashes recorded. Check formulas, labels, contrast, visual hierarchy, motion purpose, pronunciation, caption text, and timing against the approved audio.
- Run the fresh-reviewer pass of M6 on a scene here only when the checks flag it. Repair every move or statement that no source step supports.
- Apply at most [max selective-repair cycles] selective-repair cycles. Stop with a repair report when the limit is reached or an upstream dependency needs to be reopened.

Checkpoint: pre-render review is updated and bound to the current script, audio/timing, scene plan, assets, renderer, and dimensions.

M5 — Full render

- Render only after M4 passes. Record the exact command, dependency versions, start/end time, exit status, output path, dimensions, FPS, duration, and output checksum.
- For HyperFrames, render with `scripts/film/render.py --hf CLI --project DIR COMPOSITION -o OUT.mp4 --narration NARRATION.wav --expect-seconds S`. It never overwrites an existing output and names the next free `OUT.vN.mp4`. It replaces the audio with the approved mix as dual-mono, with the video stream copied, and fails if the loudness moves more than 0.5 LU. It also fails if the frame count is wrong. Add `--relabel-601` only for a Docker render image built on ffmpeg 5.1, as the colour trap in `methods/renderer-traps.md` explains. `--skip-render INPUT.mp4` post-processes an existing render.
- Then run `scripts/film/check_film.py OUT.mp4 --timing timing.json --captions captions.json --narration NARRATION.wav`, adding `--holds`, `--tail`, and `--uncaptioned` as the film declares. Pass `--caption-band x,y,w,h` when the film's captions sit elsewhere than the default band. It sets where the caption check looks and where the freeze check stops. Regenerate the `film` and `sha` receipt blocks with `scripts/run/receipts.py`.
- For a route that `render.py` does not cover, compare the MP4 audio with the approved final mix. When both MP4 channels carry the same mono narration, measure one channel, because a loudness meter adds the power of both. If the integrated loudness differs by more than 1 LU or the voice onset moved, mux the approved mix into the MP4 with the video stream copied, then measure again.
- Reject an absent, empty, stale, or failed output. Preserve failed-render diagnostics and do not let a previous MP4 satisfy this checkpoint.

Checkpoint: a new output exists and objective checks pass.

M6 — Full playback, listening, and final review

- Before the watch, run `scripts/film/check_film.py OUT.mp4 --timing timing.json --sheet SHEET_DIR` and inspect each scene's contact sheet. It holds a frame from 0.1 s before the end of every sentence. Check each frame against its caption and the script, because a layout check can pass a frame that shows the wrong thing. Open the full-size frame when a sheet frame is too small to judge.
- Get one independent review of the exact MP4. Give a fresh reviewer the sources, the script, the built scene source, and the MP4, and withhold the claim map. Ask them to list every element that moves between parts of the picture, with its label, start, end, and cue, and to name the source step that supports each move and each spoken statement about what goes where. Repair every move or statement that no source step supports. No other review layer overlaps it.
- Watch and listen to the complete exact MP4 at the delivery resolution and normal speed.
- Check every claim against the claim map and source receipts; check whether the learning target is served; check scene order, visual explanation, motion, legibility, audio levels, pronunciation, caption text and bounds, transitions, and end card.
- Review captions while listening, not as a detached text file. Record defects against scene or time range. If a repair changes any dependency, return to the affected milestone and invalidate its receipts before rerendering.
- Save the review as `final-review.md`, bound to the exact MP4 checksum, and record unresolved uncertainty.

Checkpoint: final review passes or the run stops with a bounded repair list and the exact artifact it applies to. Do not claim educational effectiveness from a review alone.

M7 — Exact handoff and stop at acceptance

Deliver the MP4, editable project/source, render command, pinned dependencies, source and asset manifests with rights notes, script, timing/captions, pilot and review receipts, run state with its decisions log, actual time/spend, failed-render history, and unresolved claims. State whether each artifact was actually run. Stop when the acceptance contract passes; optional polish is a new request. Do not publish or upload.

RESUME RULE

On interruption, read run-state.md and reconcile it with files before proceeding. Verify receipts against their declared dependencies. Regenerate only missing, empty, corrupt, stale, or invalidated artifacts and their dependents. Keep historical receipts labeled as historical. Append the interruption, diagnosis, repair, and next action. If a source, route, provider, credential, or rights condition changed, stop and report the new blocker instead of silently changing the contract.

FINAL REPORT

Report: acceptance status; route and versions; actual external time/spend; audio and timing receipt; pilot evidence; scene/render checks; full playback/listen result; caption, factual, learning, motion, and audio findings; exact MP4 checksum; delivered files; unresolved claims/defects; and the safe claim supported by the evidence. Say “production route stopped at [milestone]” when acceptance did not pass. Say “rendered and reviewed” only when M5 and M6 evidence exists.
```
