# Run quality scorecard — v0.1

Use this scorecard in two modes. In `preparation` mode, score the brief, claim map, script, scene plan, route, timing plan, and pilot plan; a local render, audio file, or pilot is optional. In `production-evidence` mode, score the measured audio, voiced pilot, render checks, and exact artifact review that actually ran. It distinguishes factuality, learning, motion/visual design, and audio/timing. It scores evidence, not confidence or polish. Production criteria and numeric thresholds are workshop design choices, not calibrated predictors of video quality.

## Rating scale

Rate each criterion from 0 to 4:

- `4` — complete, specific evidence meets the criterion;
- `3` — usable evidence with a bounded, low-risk gap;
- `2` — partial evidence; repair is required before scaling;
- `1` — assertion or weak evidence with a material gap;
- `0` — absent, contradicted, or failed.

Weighted score is `rating / 4 × weight`. A numeric score never overrides a critical failure.

## Weighted rubric

| Dimension | Weight | Criterion | Required evidence |
|---|---:|---|---|
| Factuality | 15 | Essential claims have stable IDs, readable authoritative sources, and exact locators | `claim-map.md`, source receipts |
| Factuality | 10 | Numbers, formulas, causality, API behavior, uncertainty, and disagreements are qualified accurately | claim checks and independent review notes |
| Factuality | 5 | Rights, attribution, privacy, and supplied-asset provenance are explicit | `assets-manifest.md`, source/use notes |
| Learning | 10 | One observable target is stated for this audience and duration | `brief.md` |
| Learning | 10 | Scenes and narration build toward the target; a check or self-evaluation opportunity exists; the brief answers the three misconception questions with evidence, and its decision to use or skip the beat follows from the answers | `brief.md`, `scene-plan.md`, script, target check |
| Learning | 5 | Signal/segment/weed choices reduce cognitive load without claiming that engagement proves learning | script and visual rationale |
| Motion/visual | 8 | Every scene has one comprehension job and motion that communicates a time-varying relationship; in production-evidence mode, the pilot shows it | `scene-plan.md`, `storyboard.html`, and pilot evidence when run |
| Motion/visual | 7 | Hardest shot has a delivery-size inspection plan; in production-evidence mode, text, formulas, contrast, and labels are legible | pilot plan, or contiguous pilot clip/stills/route inspection |
| Audio/timing | 8 | Timing plan names the intended approved audio source and marks measured receipt pending when audio is absent; in production-evidence mode, the audio receipt records measured duration | timing plan, or audio receipt and timing artifact |
| Audio/timing | 7 | Each scene has words, target WPM/range, speech seconds, breathing and learner-pause budgets, and a feasible total window; in production-evidence mode, scene/word/caption bounds match approved audio | `scene-plan.md`, timing consistency check, or timing match report |
| Reproducibility | 10 | Route, versions, dependencies, commands, artifacts, resume state, the filled production prompt, and actual local-run status are explicit | `run-state.md`, `production-prompt.md` |
| Reproducibility | 5 | Pilot, pre-render, and final-review evidence are bound to the artifact they actually inspect | receipts/checksums or explicit “not run” |
| **Total** | **100** |  |  |

## Critical failures

Mark `critical failure = yes` when any of these is true:

- an essential source is unreadable, inaccessible, or represented only by a snippet and its claim remains promoted;
- a promoted factual, numerical, causal, API, or safety claim lacks a readable source and exact locator;
- a source disagreement is hidden or a reconstruction is labeled as an exact creator prompt/run;
- the script estimate is presented as measured audio, or approved audio changed without timing/caption invalidation;
- global word/WPM arithmetic passes while any scene window cannot cover its speech plus declared breathing and learner pauses, or scene windows do not sum to the target within declared tolerance;
- the narration has no cold-listener test from step 3 of `methods/prepare-explainer-video.md`, or a problem that the test found is unrepaired;
- the package has no timing plan, or a timing, pilot, pre-render, or final-review receipt is stale against its inputs;
- the preparation package has no hardest/representative pilot plan, or a production-evidence claim has no voiced pilot when the requested local stack could run it;
- a claimed pilot has render errors, stale output, clipped/illegible text, misleading motion, or timing that does not follow the audio;
- an asset has no rights/use note, or a private credential is written into a source artifact;
- a viable preparation package lacks a filled `production-prompt.md` matching its current route, limits, and acceptance contract;
- the run state says an artifact passed while filesystem reconciliation shows missing, corrupt, or mismatched bytes;
- the package claims a rendered, accurate, successful, or educationally effective video without the required actual artifact evidence.

## Decision

Suggested preparation thresholds:

- `Pass to pilot`: at least 70/100 in preparation mode, no critical failure, and Factuality, Learning, and Reproducibility each at least 3/4 on average;
- `Pass preparation`: at least 80/100 in preparation mode, no critical failure, and Factuality, Learning, Motion/visual, and Audio/timing each at least 3/4 on average. This says the run is prepared; it does not say that audio, a pilot, or a render exists;
- `Pass production evidence`: at least 80/100 in production-evidence mode, no critical failure, with the requested pilot/render/final-review artifacts present and the same four core dimensions at least 3/4;
- `Needs repair`: below a threshold or any critical failure;
- `Blocked`: an essential source or required dependency remains unreadable/unavailable after the stop/narrow decision.

“Pass preparation” means the package is ready for a production attempt within the user's authorization when the installed/licensed route is available. A score does not expand task scope or authorize publication. A separate final-artifact review must score the exact MP4 after a real render.

## Completed review

- Brief/run ID: `[value]`
- Mode: `preparation | production-evidence`
- Reviewer context: `fresh | same agent | independent domain reviewer`
- Local pilot actually run: `yes/no`
- Full render actually run: `yes/no`
- Critical failure: `yes/no — explain`
- Weighted score: `[__/100]`
- Decision: `pass to pilot | pass preparation | pass production evidence | needs repair | blocked`
- Top repairs: `[ordered list]`
- Evidence gaps left open: `[list with source IDs or artifact paths]`
