# Master prompt — prepare an explainer-video run

**Prompt provenance:** original workshop reconstruction for this workbench. It is model-neutral and is not an exact prompt from a creator or vendor. Fill the bracketed fields from `templates/brief.md`; keep the evidence and design-choice labels.

Route basis: S-TC-001–S-TC-004, S-HF-001–S-HF-005, and S-PX-003. Local HyperFrames runs in this workshop are environment observations, not route validation; Pexo is a hosted optional route with separate credentials, billing, and data-transfer boundaries.

```text
You are preparing a reproducible explainer-video production run.

JOB
Subject: [subject]
Audience and starting knowledge: [audience]
Learning target: After watching, [audience] can [observable action/explanation]
Target check: [question, prediction, or worked example]
Target duration and format: [duration, aspect ratio, resolution, FPS, language, captions]
External controller limits: [actual wall-clock and money limits, or none]
Adjustable full-production ceiling: [default 8 hours; planning ceiling only]

INPUTS
Sources: [paths/URLs and stable source IDs]
Supplied assets and audio: [paths, owners, rights]
Constraints and preferences: [tone, accessibility, exclusions]
Existing run state, if resuming: [path]

OPERATING RULES
1. Read the supplied sources before making factual claims. If an essential source is missing,
   unreadable, inaccessible, or only a snippet, stop and report the source, dependent claim,
   and smallest safe next action. Continue only with a narrowed brief that excludes it.
2. Give every factual, numerical, causal, API, historical, and safety claim a stable ID.
   Record the source ID and exact locator. Label each statement as evidence-backed,
   qualified, disputed, assumption, or design choice. Never turn a reconstruction into an
   exact creator prompt or claim that a public post proves a hidden run.
3. Write one learning target, then a script and scene/shot plan. Every scene has one
   comprehension job, a specific reason motion helps, claim IDs, on-screen text, asset
   rights, and a failure risk. Record scene words, target WPM/range, speech seconds
   excluding pauses, separate breathing and learner-processing pause budgets, and total
   window. Each window must cover speech plus pauses and the scene-window sum must match
   the target within declared tolerance. Keep spoken words separate from screen text.
4. Estimate script duration from word count and a stated WPM range. Label that estimate.
   Once approved audio exists, measure its real duration and derive scene, sentence/word,
   and caption timing from it. Audio is the timing authority.
5. Route on the learner job: Remotion for existing React/UI/captions/supplied recordings;
   HyperFrames as the candidate first local renderer for new plain-HTML/browser-native
   diagrams, captions, supplied recordings, and brand motion; Manim + Manim Voiceover for
   formulas/geometry/precise transformations; Motion Canvas for TypeScript vector scenes
   where seek/screenshots/scene graph help; generic HTML/Canvas when it is the simplest
   sufficient route. Pexo is an optional hosted, credentialed route for photoreal or
   multi-shot generation, never a free-service default. Record disqualifiers and do not
   switch silently.
6. Choose the hardest or most representative shot and write its pilot plan. If production
   is requested and the local stack exists, run a voiced pilot, inspect stills and a
   contiguous 2–4 second motion sample (plus route-specific error/scene inspection when
   available). If this is preparation-only, mark the pilot not run. A completed pilot is
   production evidence for that scene; it does not prove full-render success or educational
   effectiveness.
7. Keep a small artifact set: brief, claim map, script, scene plan, audio receipt, timing,
   assets manifest, pilot review, pre-render review, run state, and handoff. Use renderer
   JSON/TypeScript only as implementation inputs. Checkpoint after useful artifacts and
   proceed on passing agent gates; do not demand a human approval at every phase.
8. On resume, reconcile the run state with the filesystem. Missing, corrupt, or mismatched
   artifacts are invalid. Rebuild only the affected artifact and dependents. A changed
   source, claim, target, script, audio byte, scene, asset, renderer, FPS, or dimension
   invalidates the receipts that depend on it. Never reuse an old MP4 as a new success.
9. Apply the preparation scorecard. A weighted total cannot erase a critical failure such
   as an essential unreadable source, unsupported claim, missing timing or pilot plan,
   stale timing, a missing voiced pilot in a production-evidence claim, render error,
   missing rights evidence, or stale receipt.
10. Record actual elapsed time and spend from the external controller. The preparation
    full-production ceiling is adjustable planning information; this prompt cannot enforce
    time or cost.

PHASES AND CHECKPOINTS
Phase 0 — Intake: write brief, source receipts, rights notes, and stop/narrow decisions.
Checkpoint: every promoted source is readable and scoped.
Phase 1 — Evidence: write learning target and claim map with exact locators.
Checkpoint: no essential unsupported claim is hidden in prose.
Phase 2 — Narrative: write script estimate and scene/shot plan.
Checkpoint: each scene has one comprehension job, target coverage, and a feasible narration
window; global word arithmetic cannot hide an infeasible scene. A cold listener can explain
the mechanism from the narration and scene descriptions (method step 3).
Phase 3 — Route: choose renderer, versions/dependencies, commands, and disqualifiers.
Checkpoint: route can be inspected and has an editable source path when available.
Phase 4 — Audio: obtain or plan approved audio; write its receipt and timing plan, measuring
timing only when audio exists.
Checkpoint: timing names the audio receipt and invalidation rule.
Phase 5 — Pilot plan (and, when production is requested, pilot): specify the hardest
representative shot; run and inspect voiced motion only when the user requested production
and the local stack exists.
Checkpoint: the pilot plan is complete, or the actual pilot score passes or records a
bounded repair.
Phase 6 — Preflight and handoff: score the package, write run state, resume notes, and
final handoff. Fill `production-prompt.md` from the original production route template so
another agent can execute the future run. State clearly whether any local pilot or full
render actually ran.

OUTPUTS
When intake produces a viable brief, write these files under [output directory]:
- brief.md
- claim-map.md
- script.md
- scene-plan.md
- audio-receipt.md (or “not available” with reason)
- timing.md (or “not available” with reason)
- assets-manifest.md
- pilot-review.md
- pre-render-review.md
- run-state.md
- production-prompt.md (filled for this package; future route, not executed here)
- handoff.md

If intake is blocked by an essential unreadable or unavailable source, write only a concise
`handoff.md` with the blocked source, dependent claims, attempted access, missing authority,
and smallest safe next action. Add `run-state.md` only if it preserves useful recovery
information. Do not create empty script, scene, audio, pilot, scorecard, or production-
prompt files for a blocked package.

FINAL RESPONSE
Report: preparation status, learning target, source/readability stops, claim coverage,
estimated words/WPM versus measured audio (if any), scene count, renderer route and
disqualifiers, pilot evidence, scorecard result, actual time/spend measurements, and
unanswered choices. Say “prepared package” unless an actual render and exact-byte review
are evidenced. Do not publish or upload.
```

The prompt's phases are agent checkpoints. An external controller is responsible for enforcing any real time, spend, network, or publication permission.
