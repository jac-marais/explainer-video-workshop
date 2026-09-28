# Production prompt — execute a prepared explainer run

**Prompt provenance:** original workshop reconstruction. This is a documented, unexecuted route for a future production agent. It is not a creator's prompt, a named-model recipe, or evidence that this workshop has rendered a successful video. It assumes the preparation package has already passed its preparation scorecard.

**Evidence basis:** measured audio as timing truth and invalidation rule (S-TC-001, S-TC-003, S-TC-006, S-TC-008); contiguous pilot and exact-output review (S-TC-001, S-TC-004, S-TC-009); durable state and missing-only resume (S-TC-005, S-TC-007, S-TC-008). The milestones, limits, parallelism, and acceptance language are workshop design choices derived from those sources.

Fill every bracketed field from the prepared package or external controller before sending this prompt; write `none` when a limit does not exist. Keep this file beside the run state so a later agent can resume it.

```text
You are executing a prepared explainer-video production run.

PREPARED PACKAGE
Package directory: [path]
Required records: brief.md, claim-map.md, script.md, scene-plan.md,
audio-receipt.md or an explicit audio plan, timing.md or an explicit pending-timing
plan, assets-manifest.md, pre-render-review.md, run-state.md, and this production prompt.
Output directory: [path]
Renderer route and pinned versions: [HyperFrames / Remotion / Manim / Motion Canvas /
HTML-Canvas, or an explicitly selected hosted route; versions and commands from the package]

EXTERNAL LIMITS
Wall-clock limit: [controller-enforced value]
Spend limit: [controller-enforced value]
Max pilot repair cycles: [default 2, or controller value]
Max selective-repair cycles: [default 2, or controller value]
Full-production planning ceiling: [default 8 hours; adjustable ceiling, never a required
runtime and never a quality guarantee]

The external controller enforces time, money, credentials, network, and publication
permissions. Record actual elapsed time and spend. Stop at acceptance or when a limit,
critical blocker, or missing authority prevents safe progress. Do not keep working to fill
the eight-hour ceiling.

PRODUCTION CONTRACT
1. Read the prepared package and reconcile run-state.md with the filesystem before changing
   anything. A missing, corrupt, or mismatched artifact is invalid even if the state file
   says it passed. Never reuse an old MP4 as the result of a failed or changed render.
2. Preserve the claim map and source boundaries. If an essential source is unreadable, a
   required asset lacks a rights note, or a promoted claim has no readable locator, stop
   and report the blocker. Narrowing the claim or asset set requires recording the change
   and invalidating affected script, scene, audio, timing, and review artifacts.
3. Use the prepared renderer route when its dependencies and license permit it. Do not lock
   the run to a named model. Choose available providers and tools that satisfy the package,
   record their versions/roles, and stop if the route cannot meet the acceptance contract.
4. Treat the approved audio bytes as timing truth once they exist. A re-record, trim, speed
   change, pause edit, or script change invalidates timing, captions, audio-bound visual
   cues, the pilot, and the pre-render receipt. Rebuild the affected artifacts before
   proceeding.
5. Use agent gates, not mandatory user approvals at every stage. Ask for authority only for
   a purchase, publication/upload, irreversible external write, or a private preference
   that the prepared package does not resolve.

MILESTONES

M0 — Preflight and resume

- Read the brief, claim map, script, scene plan, assets manifest, route, and state.
- Verify source readability, asset rights notes, required dependencies, output dimensions,
  FPS, language, caption requirement, and the current next action.
- If the route is HyperFrames, apply the “HyperFrames preflight traps” in
  `library/notes/production-paths.md` before accepting `check`: a standalone composition,
  matching composition/timeline identity, resolved audio IDs, and positive layout/contrast
  samples are required; a lint-disabled or 0-of-0 audit is not a pass.
- Locate completed artifacts and classify missing/corrupt/stale files. Rebuild only the
  affected artifact and dependents. Append the decision and invalidation to run-state.md.

Checkpoint: the route, inputs, limits, and current dependency graph are explicit.

M1 — Narration and timing

- Use the supplied approved audio when valid. If production is authorized and audio is
  pending, create or record it using the provider/recorder allowed by the package.
- Save the audio receipt with path, provider or recorder, language, measured duration, and
  checksum when available. Keep credentials outside the source artifacts.
- Pre-cut audio before alignment when edits are needed. Derive scene, sentence/word, and
  caption timestamps from the approved audio. Mark low-confidence matches and repair them
  before visual timing depends on them.
- Keep the script's word/WPM duration estimate beside the measured duration; never replace
  one with the other.

Checkpoint: timing names the exact approved audio receipt, or the run stops with a concrete
audio blocker. Do not build audio-dependent scenes against a guessed duration.

M2 — Hard voiced pilot and shared style

- Choose the hardest or most representative shot from the prepared scene plan. It must
  exercise the global visual system, the route's key dependency, a tight timing beat, and a
  likely failure-prone asset.
- If `local/brand.md` names guidelines, build the shared style from them per `methods/apply-brand.md`.
- Build the shared style and this shot with its real or representative audio. Produce still
  frames and a contiguous 2–4 second voiced sample; inspect neighboring frames at delivery
  size. Use route-specific checks when available: Studio/stills for Remotion, low-quality
  render for Manim, or scene graph/errors for Motion Canvas.
- Check that visual events align with the intended spoken cue, labels and captions are
  legible, motion explains the claim, and supplied assets remain permitted.
- Repair only bounded pilot defects. Record each cycle and stop if the configured repair
  limit is reached. A passing pilot is evidence for this scene; it is not full-film proof.

Checkpoint: the pilot score passes, or the run stops with the remaining defect and evidence.

PARALLEL WORK RULE

Independent bounded source or asset checks named by the prepared package may run in parallel
before M3. Each worker records source IDs, exact locators, rights notes, and proposed
changes; one sequential convergence step updates the canonical claim map or asset manifest
before dependent work consumes it. After M2 passes, independent scene construction may
proceed in parallel when each worker uses the locked style tokens, claim IDs, timing IDs,
asset paths, and renderer versions. Keep shared dependencies sequential: source/claim
changes, script order, audio production, timing, global style, captions, scene transitions,
final mix, full render, and final review. If a shared dependency changes, invalidate every
affected branch before merging it.

M3 — Build all scenes

- Implement each prepared shot and scene with the approved audio/timing contract.
- Keep one comprehension job per scene. Preserve source-backed labels, formulas, units,
  captions, and uncertainty from the claim map. Remove decorative motion that competes with
  the learning target.
- Render cheap stills or selected frames for changed layout, text, or asset questions. For
  motion changes, render the changed scene and its boundary overlap; do not spend a full
  render on a known local defect.
- Record missing assets, failed renders, retries, and actual external spend.

Checkpoint: every planned scene has an implementation or an explicit blocker, and scene
coverage, claim coverage, and timing coverage are reconciled.

M4 — Selective inspection and repair

- Run deterministic checks for source/asset presence, dimensions, FPS, duration metadata,
  caption bounds, scene coverage, renderer errors, and stale outputs.
- Inspect changed scenes and their neighboring transitions at delivery size. Check formulas,
  labels, contrast, visual hierarchy, motion purpose, pronunciation, caption text, and
  timing against the approved audio.
- Apply at most [max selective-repair cycles] selective-repair cycles. Stop with a repair report when the
  limit is reached or an upstream dependency needs to be reopened.

Checkpoint: pre-render review is updated and bound to the current script, audio/timing,
scene plan, assets, renderer, and dimensions.

M5 — Full render

- Render only after M4 passes. Record the exact command, dependency versions, start/end
  time, exit status, output path, dimensions, FPS, duration, and output checksum.
- Reject an absent, empty, stale, or failed output. Preserve failed-render diagnostics and
  do not let a previous MP4 satisfy this checkpoint.

Checkpoint: a new output exists and objective checks pass.

M6 — Full playback, listening, and final review

- Watch and listen to the complete exact MP4 at the delivery resolution and normal speed.
- Check every claim against the claim map and source receipts; check whether the learning
  target is served; check scene order, visual explanation, motion, legibility, audio levels,
  pronunciation, caption text and bounds, transitions, and end card.
- Review captions while listening, not as a detached text file. Record defects against scene
  or time range. If a repair changes any dependency, return to the affected milestone and
  invalidate its receipts before rerendering.
- Bind the final review to the exact MP4 checksum and record unresolved uncertainty.

Checkpoint: final review passes or the run stops with a bounded repair list and the exact
artifact it applies to. Do not claim educational effectiveness from a review alone.

M7 — Exact handoff and stop at acceptance

Deliver the MP4, editable project/source, render command, pinned dependencies, source and
asset manifests with rights notes, script, timing/captions, pilot and review receipts,
run-state and director log, actual time/spend, failed-render history, and unresolved claims.
State whether each artifact was actually run. Stop when the acceptance contract passes;
optional polish is a new request. Do not publish or upload.

RESUME RULE

On interruption, read run-state.md and reconcile it with files before proceeding. Verify
receipts against their declared dependencies. Regenerate only missing, corrupt, stale, or
invalidated artifacts and their dependents. Keep historical receipts labeled as historical.
Append the interruption, diagnosis, repair, and next action. If a source, route, provider,
credential, or rights condition changed, stop and report the new blocker instead of silently
changing the contract.

FINAL REPORT

Report: acceptance status; route and versions; actual external time/spend; audio and timing
receipt; pilot evidence; scene/render checks; full playback/listen result; caption, factual,
learning, motion, and audio findings; exact MP4 checksum; delivered files; unresolved
claims/defects; and the safe claim supported by the evidence. Say “production route stopped
at [milestone]” when acceptance did not pass. Say “rendered and reviewed” only when M5 and
M6 evidence exists.
```

This prompt is a future production route. It is intentionally model-neutral and does not claim that any renderer, provider, or eight-hour run has been validated in this workshop.
