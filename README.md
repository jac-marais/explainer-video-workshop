# Explainer Video Workshop

Turn a technical subject and trustworthy sources into a narrated video that explains a mechanism clearly. Sustained agent work is a production technique; the job is the explanation. Models and renderers can change without renaming the workshop.

## Start here

Open this folder in an agent harness and ask:

> Prepare a three-minute explainer about why retry storms happen for engineers who understand HTTP. Give me a sourced script, a scene plan, a renderer choice, and a production prompt with an eight-hour ceiling.

The [preparation method](methods/prepare-explainer-run.md) produces a usable package without claiming that a video exists. The [production prompt](templates/production-prompt.md) then guides an authorized production run through narration, measured timing, a hard-scene pilot, scene construction, rendering, review, and editable handoff. Eight hours is an adjustable ceiling. Stop when the result passes; waiting is not a quality step.

## Brand guidelines

The workshop is brand-neutral. On first use, the agent asks whether you have brand guidelines, then records your answer in `local/brand.md`, which is git-ignored. The answer can be a path to a brand workshop, a document, a URL, or "none". From then on, every run styles and audits its output against that source through [the brand method](methods/apply-brand.md). To change brands, edit or delete `local/brand.md`. The [profile template](templates/brand-profile.md) shows its shape.

## Use the shelves by job

| Job | Start with |
|---|---|
| Investigate concrete public examples | [Example atlas](library/notes/example-atlas.md) |
| Find actual prompts, skills, and versions | [Prompt and skill map](library/notes/prompt-and-skill-map.md) |
| Choose HTML, React, math animation, or hosted generation | [Production paths](library/notes/production-paths.md) |
| Prepare a run | [Method](methods/prepare-explainer-run.md), [brief](templates/brief.md), [scene plan](templates/scene-plan.md), [preparation prompt](templates/master-prompt.md) |
| Align output with your brand | [Brand method](methods/apply-brand.md) and [profile template](templates/brand-profile.md) |
| Execute a prepared run | [Production prompt](templates/production-prompt.md) and [quality gate](scorecards/preparation-quality.md) |
| Check evidence | [Source map](library/source-map.md) and [manifest](library/manifest.json) |

## Layout and runtime

```text
AGENTS.md                   mission, routing, guarantees
library/                    source index and accepted knowledge by job
methods/                    maintained preparation procedure
templates/                  brief, scene plan, state, preparation/production prompts
scorecards/                 preparation and production-evidence gates
outputs/                    new user work (git-ignored)
local/                      operator's brand profile and pronunciation verdicts (git-ignored)
.agents/skills/             preparation and brand skills
.claude/skills/             link to .agents/skills for Claude Code
```

Only the workshop itself is committed: routing, methods, templates, scorecards, the library, and the skills. Everything an agent produces while working stays local and git-ignored, under `outputs/` and `local/`.

The skills live in `.agents/skills/`, and `.claude/skills` links to that folder, so Codex and Claude Code share one copy. `CLAUDE.md` points to `AGENTS.md`. The skills rely on this workshop's maintained methods/templates and resolve paths from the repository root; they are not standalone video engines.

No MCP server, cloud renderer, voice API, or vendor skill bundle is required to prepare a run. Follow the selected route's current, pinned setup instructions and record actual versions in a production project. Vendor installers may refresh global skill sets; check their target before running them.

This workshop is not a generic video studio, a model leaderboard, a collection of copied third-party prompts, or a scheduler that keeps an agent alive for eight hours. Source videos, voices, service credits, and private documents retain their own use boundaries. See [source use](library/source-use-policy.md).

## License

The workshop is [MIT licensed](LICENSE). Cited third-party sources keep their own licenses.
