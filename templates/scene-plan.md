# Scene and shot plan — preparation artifact

Status: `draft` | Brief: `[path or ID]` | Audio receipt: `not available / [ID]`

One scene has one learner-facing comprehension job. One shot is a contiguous renderable interval. A fade, zoom, or camera move by itself is not a comprehension job.

## Narrative map

| Scene | Comprehension job | Claim IDs | Narration purpose | Visual idea | Why motion helps | Words | Target WPM/range | Speech seconds* | Breathing pause budget* | Learner pause budget* | Total planned window* |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `S01` | `[one job]` | `C-…` | `[setup / mechanism / contrast / recap]` | `[diagram, UI, formula, etc.]` | `[specific temporal relationship]` | `[count]` | `[e.g. 130–165]` | `[words/WPM × 60]` | `[seconds]` | `[seconds]` | `[speech + pauses]` |

\* Speech seconds are estimated from the scene's words and target WPM and exclude breathing and learner-processing pauses. Total planned window includes speech plus both pause budgets. After the voice track is approved, measured audio duration supersedes the total-window estimate; retain planned pause annotations unless the timing artifact measures them separately.

## Narration-window consistency

Before accepting the plan, check:

- scene word counts sum to the script's narration word count, excluding explicitly marked non-spoken text;
- each scene's speech seconds use the stated WPM/range and do not hide pauses inside an inflated WPM;
- each total planned window is at least speech seconds plus breathing and learner pause budgets;
- the sum of scene windows matches the target duration within declared transition/end-card tolerance;
- any scene outside the approved WPM range is repaired by changing words, window, or structure rather than forcing delivery speed;
- measured audio, when it exists, supersedes every estimate and invalidates dependent timing when edited.

## Shot sequence

| Shot | Scene | Audio segment | Start/end or timing key | Visual elements and motion grammar | On-screen text | Assets and rights | Renderer/dependency | Entry/exit condition |
|---|---|---|---|---|---|---|---|---|
| `S01-01` | `S01` | `[line or audio range]` | `[estimate or word IDs]` | `[what moves and why]` | `[exact text]` | `[path, source, license]` | `[Remotion/Manim/Motion Canvas/HTML]` | `[condition]` |

## Required scene checks

For every scene, answer these questions in one or two sentences:

- What should the learner be able to point to, predict, compare, or explain when this scene ends?
- Which claim or source receipt justifies each number, label, formula, API behavior, or causal arrow?
- What must remain on screen long enough to read?
- What is the hardest timing or layout risk?
- What changes if the audio is re-recorded?
- What can be reviewed with stills, and what requires a contiguous motion sample?

## Global visual system

- Brand: `[none | the source in local/brand.md; the audit is in brand-audit.md]`
- Canvas and safe area: `[values]`
- Type sizes and contrast: `[values or tokens]`
- Color meaning: `[mapping]`
- Reusable components: `[names]`
- Accessibility rules: `[captions, color, motion, audio]`
- Route decision and disqualifiers: `[reason]`

## Pilot selection

- Hardest/most representative shot: `[shot ID]`
- Why it is representative: `[global system, dependency, timing, or content risk]`
- Pilot evidence: `[stills / contiguous 2–4 s voiced clip / scene graph or low-quality render]`
- Pilot status: `not run | pass | revise | blocked`
