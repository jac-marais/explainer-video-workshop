# Explainer Video Workshop

[![The closing frame of the 44-second overview, made with this workshop](brands/readme/closing.jpg)](https://jac-marais.github.io/explainer-video-workshop/brands/mit-media-lab.mp4)

▶ [Watch the 44-second overview](https://jac-marais.github.io/explainer-video-workshop/brands/mit-media-lab.mp4), in the workshop's MIT Media Lab-inspired style.

Turn a technical subject and trustworthy sources into a narrated video that explains a mechanism clearly. Sustained agent work is a production technique; the job is the explanation. Models and renderers can change without renaming the workshop.

## Why a workshop

A workshop is a room set up for one craft. A wood shop and a metal shop need different tools, skills and safety rules, and you would never weld next to the sawdust. A woodworker can still learn metalwork by walking into the other shop. Agents work the same way. This repo is the shop for explainer videos. Open the folder, and the agent gets the methods, templates, checks and sources this craft needs.

## Start here

Open this folder in an agent harness and ask:

> Prepare a three-minute explainer about why retry storms happen for engineers who understand HTTP. Give me a sourced script, a scene plan, a renderer choice, and a production prompt with an eight-hour ceiling.

The [preparation method](methods/prepare-explainer-video.md) produces a usable package without claiming that a video exists. The [production prompt](templates/production-prompt.md) then guides an authorized production run through narration, measured timing, a hard-scene pilot, scene construction, rendering, review, and editable handoff. Eight hours is an adjustable ceiling. Stop when the result passes; waiting is not a quality step.

<p>
<a href="https://jac-marais.github.io/explainer-video-workshop/brands/mit-media-lab.mp4#t=16"><img src="brands/readme/step-2.jpg" width="49%" alt="Step 2, Prepare. The prepare skill turns a topic and an audience into a sourced script, a scene plan, a renderer choice and a production prompt."></a>
<a href="https://jac-marais.github.io/explainer-video-workshop/brands/mit-media-lab.mp4#t=27"><img src="brands/readme/step-3.jpg" width="49%" alt="Step 3, Produce. Production records the voice, times scenes to the audio, pilots the hardest scene, then renders and reviews the film."></a>
</p>

## Brand guidelines

The workshop is brand-neutral. On first use, the agent asks whether you have brand guidelines, then records your answer in `local/brand.md`, which is git-ignored. The answer can be a path to a brand workshop, a document, a URL, or "none". No guidelines? [See the nine workshop styles](https://jac-marais.github.io/explainer-video-workshop/brands/) and tell the agent which one you want. Separately from the brand, a run can draw its diagrams as [Hairline](https://github.com/lucasmarkes/hairline)-style isometric line figures, which take their colours from the brand; see [figure modules](templates/composition/README.md#figure-modules). From then on, every run styles and audits its output against that source through [the brand method](methods/brand-explainer-video.md). To change brands, edit or delete `local/brand.md`. The [profile template](templates/brand.md) shows its shape.

<p>
<a href="https://jac-marais.github.io/explainer-video-workshop/brands/mit-media-lab.mp4#t=5"><img src="brands/readme/step-1.jpg" width="49%" alt="Step 1, Start with a brand. The agent asks for brand guidelines, or you pick one of nine styles."></a>
<a href="https://jac-marais.github.io/explainer-video-workshop/brands/mit-media-lab.mp4#t=37"><img src="brands/readme/step-4.jpg" width="49%" alt="Step 4, Check. Each scene is checked against your brand file for layout, contrast and stills."></a>
</p>

## Voice

Narration uses a stock local voice, Kokoro `af_heart`, unless you clone your own. On first use, the agent offers to clone yours with Qwen3-TTS on an Apple Silicon Mac, from a one-minute recording. Your choice and the recording live in `local/voice/`, which is git-ignored. You can still ask any run for the stock voice, and a run in progress keeps the voice it started with. See [the voice method](methods/voice-explainer-video.md).

## Use the shelves by job

| Job | Start with |
|---|---|
| Investigate public examples, prompts, and skills | [Prior art](library/prior-art.md) |
| Choose HTML, live app capture, React, math animation, or hosted generation | [Renderers](library/renderers.md) |
| Get 3D models, HDRIs and textures for a scene | [3D assets](library/3d-assets.md) and `scripts/assets/check_asset.py` |
| Prepare a run | [Method](methods/prepare-explainer-video.md), [brief](templates/brief.md), [scene plan](templates/scene-plan.md), [storyboard builder](scripts/storyboard/storyboard.py) |
| Align output with your brand | [Brand method](methods/brand-explainer-video.md) and [profile template](templates/brand.md) |
| Execute a prepared run | [Production prompt](templates/production-prompt.md) and [scorecard](scorecards/run-quality.md) |
| Check evidence | [Source map](library/source-map.md) and [manifest](library/manifest.json) |

## Setup

Install the tools once per computer, never per checkout or per run. Every checkout, copy and run shares them:

- [uv](https://docs.astral.sh/uv/), on your `PATH`.
- One Python environment, locked by `pyproject.toml` and `uv.lock`, including pypinyin for Mandarin homophone alignment. Run any script that needs packages as `scripts/run/py SCRIPT [ARG...]`, which runs it in that environment and syncs the environment to the lock from uv's own cache. The standard-library scripts also run with any `python3`.
- The models, in their tools' own per-user caches: Hugging Face's for Whisper and Qwen3-TTS, HyperFrames' for Kokoro (see [the voice method](methods/voice-explainer-video.md)), and Stanza's for the sentence splitter and the caption line breaks. Download Stanza's models once per narration language, for example French, with `scripts/run/py -c 'import stanza; stanza.download("fr", processors="tokenize,pos,lemma,depparse", proxies={"https": None})'`. The `proxies` value makes Stanza download its files directly, so no second copy lands in Hugging Face's cache. The tools load them offline.

macOS on Apple Silicon and Linux x86_64 support narration and rendering. macOS keeps its MLX backends; Linux uses CPU speech and alignment as described below. Install Python 3.12 via uv, Node 22+, ffmpeg and Google Chrome or Chromium on `PATH`. Use `UV_PROJECT_ENVIRONMENT="$HOME/.cache/explainer-video-venv" uv sync --locked` in this checkout. Copy the narration WAV and its timing, words, captions and cues before restarting a film at `--from data`. Download Stanza's `tokenize` models for both the film language and its key-script language before the offline build, for example `scripts/run/py -c 'import stanza; stanza.download("en", processors="tokenize", proxies={"https": None})'`. Render-only setup needs no voice models or eSpeak. `setup_check.sh` selects the render-only checks on Linux, discovers Chrome/Chromium on `PATH`, and honors `HYPERFRAMES_BROWSER_PATH`. Heavy jobs use the same per-user lock and low priority on both platforms. Build as a normal user, not root, because Chrome will not start as root with its sandbox on. A restricted execution sandbox, such as an agent's, can block the heavy lock's priority change or Chrome's launch; run builds outside it.

### Linux CPU narration

Run installation and model downloads through `scripts/run/heavy`, as for synthesis and rendering. Use the same shared Python environment (`uv sync --locked`), and install the distribution's `espeak-ng`, `libespeak-ng1` and `sox` packages. No second environment is needed. The default setup check remains render-only; voice dependencies are checked when the chosen engine loads.

- Kokoro uses the existing `kokoro-onnx` engine, the same v1.0 model and voice pack, and the same configured voice, speed and frontend. eSpeak library discovery is platform-specific. Linux also applies the bounded [final-level correction](methods/voice-explainer-video.md#linux-kokoro-levels), with unchanged audio gates. Keep the model and voices in the default Kokoro cache described in the voice method.
- Qwen uses `qwen-tts` on CPU in float32. A configured `mlx-community/Qwen3-TTS-12Hz-{size}B-{Base|CustomVoice}-bf16` maps to the corresponding `Qwen/` release. Quantized or unknown variants fail instead of silently changing the model. Speaker, language, sampling settings, chunk limit and per-chunk seed are carried through. Presets use incremental text conditioning; reference clones use full-text conditioning and an effective repetition penalty of at least 1.5, matching the MLX paths. The CPU adapter also applies repetition penalties once per unique token in the last 64 generated tokens, excluding the prompt, as MLX does. Linux receipts record these effective settings. CPU and MLX use different random streams, so they do not guarantee identical samples; validate voice and duration against an approved reference before production. Linux Qwen uses a distinct narration reuse identity, so transferred Mac Qwen takes are regenerated together instead of mixing with new CPU takes after an edit. Existing Mac and Kokoro cache identities stay unchanged.
- Alignment uses `mobiuslabsgmbh/faster-whisper-large-v3-turbo` on CPU in float32, with word timestamps, no VAD, previous-text conditioning disabled, and the MLX default decode retry temperatures (0.0, 0.2, 0.4, 0.6, 0.8, 1.0). Each attempt uses one hypothesis and at most 224 new tokens. An instance adapter follows MLX retry thresholds, stops on high no-speech probability, and retains the last attempt if every temperature fails. Cache its snapshot with `huggingface_hub.snapshot_download` before building. Qwen snapshots use the same default Hugging Face cache. Runtime loading is offline.

The CLI and outputs remain the same: final narration is 48 kHz mono 24-bit PCM, followed by timing, words, audio checks, captions and cues. `--strict` still rejects fallback words. The shared heavy lock, whole-take reuse, sentence matching and audio gates remain in force. Existing Mac command vectors and MLX synthesis settings are unchanged. Chatterbox remains Mac-only.

Never point `UV_CACHE_DIR`, `HF_HOME`, `KOKORO_TTS_CACHE` or `STANZA_RESOURCES_DIR` at a copy inside a checkout or a run. `sh scripts/run/setup_check.sh` checks the setup and downloads nothing.

## Layout and runtime

```text
AGENTS.md                   mission, routing, guarantees
pyproject.toml, uv.lock     the shared Python environment's packages and lock
brands/                     style gallery, published on GitHub Pages
library/                    source map, prior art, renderer and 3D asset notes
methods/                    preparation, brand, and voice procedures
templates/                  files copied into a run or local/
scripts/                    shared production and asset-check tools
scorecards/                 preparation and production-evidence gates
outputs/                    new user work (git-ignored)
local/                      operator's brand profile, voice, and pronunciation verdicts (git-ignored)
.agents/skills/             preparation and brand skills
.claude/skills/             link to .agents/skills for Claude Code
anthropic/                  Anthropic skills copied with their Apache-2.0 license, then adapted
```

Only the workshop itself is committed: routing, methods, templates, scorecards, the library, the style gallery, and the skills. Everything an agent produces while working stays local and git-ignored, under `outputs/` and `local/`.

The skills live in `.agents/skills/`, and `.claude/skills` links to that folder, so Codex and Claude Code share one copy. `CLAUDE.md` points to `AGENTS.md`. The skills rely on this workshop's maintained methods/templates and resolve paths from the repository root; they are not standalone video engines.

No MCP server, cloud renderer, voice API, or vendor skill bundle is required to prepare a run. Follow the selected route's current, pinned setup instructions and record actual versions in a production project. Vendor installers may refresh global skill sets; check their target before running them.

This workshop is not a generic video studio, a model leaderboard, a collection of copied third-party prompts, or a scheduler that keeps an agent alive for eight hours. Source videos, voices, service credits, and private documents retain their own use boundaries. See [source use](library/source-map.md#use-rules).

## License

The workshop is [MIT licensed](LICENSE). Cited third-party sources keep their own licenses.

The optional Hairline figure module in `templates/composition/figure-modules/` ports its geometry and motion from [Hairline](https://github.com/lucasmarkes/hairline) by Lucas Marques, under the MIT license in [`HAIRLINE-LICENSE.txt`](templates/composition/figure-modules/HAIRLINE-LICENSE.txt). It is an adaptation, not the Hairline package, and Hairline's author has not endorsed it.
