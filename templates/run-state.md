# Run state — resumable run record

Status: `draft` | Run ID: `[short ID]` | Last updated: `[UTC timestamp]`

This is one human-readable state record. A renderer may keep implementation-specific JSON, but this record remains the recovery index.

The `## Run log` table of spend and active time per phase comes from `scripts/run/runlog.py mark RUN_STATE.md PHASE SESSION...`. Its first call appends the table with a start row to the end of this file. Do not type its rows.

## Current state

- Current phase: `preparation step [1–10] | production milestone [M0–M7] | blocked at [intake, step, or milestone] | accepted`
- Next action: `[single concrete action]`
- Full-production ceiling: `[hours; adjustable]`
- External elapsed time: `[controller measurement or unknown]`
- External spend: `[billing/controller measurement or unknown]`
- Renderer/version: `[route and pinned versions, or not chosen]`
- Publication/upload: `not authorized by this workshop`

## Artifact ledger

The rows follow the run-folder file list in step 8 of `methods/prepare-explainer-video.md`.

| Artifact | Status | Derived from | Receipt/check | Invalidated by | Next action |
|---|---|---|---|---|---|
| `brief.md` | `missing/draft/checked/invalidated/accepted` | `[inputs]` | `[check]` | `[change]` | `[action]` |
| `claim-map.md` | `[status]` | `[sources + brief]` | `[source locators]` | `[source/target change]` | `[action]` |
| `script.md` | `[status]` | `[claim map + target]` | `[word count]` | `[claim/target change]` | `[action]` |
| `scene-plan.md` | `[status]` | `[script]` | `[coverage check]` | `[source, claim, target, script, or route change]` | `[action]` |
| `storyboard.html` | `[status]` | `[scene plan]` | `[storyboard.py exits 0]` | `[scene-plan change before production]` | `[action]` |
| `audio-receipt.md` | `[status]` | `[script or recording]` | `[duration + checksum]` | `[source, claim, target, script, or audio change]` | `[action]` |
| `timing.md` | `[status]` | `[approved audio]` | `[match report]` | `[source, claim, target, script, or audio change]` | `[action]` |
| `assets-manifest.md` | `[status]` | `[scene plan]` | `[paths + rights]` | `[asset/route change]` | `[action]` |
| `pilot-review.md` | `[status]` | `[pilot media + artifacts]` | `[stills + contiguous clip]` | `[source, claim, target, audio, code, asset, renderer, FPS, or dimension change]` | `[action]` |
| `pre-render-review.md` | `[status]` | `[claim/script/scene/audio]` | `[scorecard]` | `[any upstream change]` | `[action]` |
| `final-review.md` | `[status, production only]` | `[exact MP4 + claim map]` | `[MP4 checksum]` | `[new MP4 bytes]` | `[action]` |
| `production-prompt.md` | `[status]` | `[accepted preparation package]` | `[filled route/limits/checklist]` | `[contract, route, limit, or acceptance change]` | `[action]` |

## Resume protocol

1. Read this ledger, then inspect the filesystem for each `accepted` artifact.
2. Treat a missing, empty, corrupt, or mismatched artifact as invalid even if the ledger says accepted.
3. Verify receipts against the current source, script, audio, renderer, and output where a receipt declares a dependency.
4. Rebuild only the invalid artifact and its dependents, using the invalidation table in step 6 of `methods/prepare-explainer-video.md`. Keep old artifacts in a dated archive or mark them historical; never present an old MP4 as the new result.
5. Append the reason, action, result, and next action below.

## Decisions and failures

Log each decision, failure, invalidation, and retry as a row.

| Time | Phase | Decision or failure | Evidence | Consequence/invalidations | Next action |
|---|---|---|---|---|---|
| `[UTC]` | `[phase]` | `[what happened]` | `[receipt/path]` | `[what changed]` | `[action]` |

## Completion claim

- Preparation package scored: `not scored | pass | fail`
- Local pilot actually run: `yes/no` (if no, say why)
- Full render actually run: `yes/no`
- Exact final-byte review: `not applicable | pending | complete`
- Remaining uncertainty: `[list]`
- Next validation trial: `[one concrete trial]`
- Safe claim to make now: `[prepared package only / other evidence-backed claim]`
