# Production scripts

This is the shared tool list for a production. Run the tools from the workshop root. Each CLI's `--help` and source header own its options, defaults and guards. [M0 to M6 of templates/production-prompt.md](../templates/production-prompt.md) supply the production commands and milestones.

The underlying voice tools (`voice.py`, `cut_takes.py`, `plan_runs.py`) live in `templates/voice/`.

## assets/

- `check_asset.py` checks third-party 3D models, textures, HDRIs and archives before a scene loads them and prints each file's SHA-256 for the asset manifest. [library/3d-assets.md](../library/3d-assets.md) owns sources and intake steps, and the tool's header defines its inspection limits.

## audio/

Narration, cues, captions, film data and storyboards share [audio/text_tokens.py](audio/text_tokens.py) for Unicode matching and sentence splitting. Its `sentences()` contract owns language-specific sentence boundaries, and [audio/captions.py](audio/captions.py) owns the dependency parse that places caption breaks. Run tools that split or parse with `scripts/run/py`, using the Stanza models from [Setup](../README.md#setup).

- `narrate_film.py` voices scenes, cuts them into sentences, assembles narration, aligns the script's words, writes timing and checks the audio. Run `scripts/run/py scripts/audio/narrate_film.py`. Its header describes `--language`, `--check-only`, number readings and alignment repairs, including `audio-checks.json` and `retranscribed_spans`. [The voice method](../methods/voice-explainer-video.md#estimated-runs) owns take-length limits.
- `cues.py` writes measured visual cue times to `cues.json`. Use it after narration alignment, with the shared naming rules in [Sentence cues and translations](#sentence-cues-and-translations).
- `captions.py` builds sentence captions from measured timing and words. Apply the composition's [Caption layout](../templates/composition/README.md#caption-layout) when choosing its fonts and line width.
- `mix.py` synthesizes a music bed and sound effects under mono narration from code, without samples or downloads. Run `scripts/run/py scripts/audio/mix.py --project outputs/sample-film/project --events outputs/sample-film/stills/sfx.json --out outputs/sample-film/mix.wav --stems outputs/sample-film/stems`. Its [source](audio/mix.py) documents event fields and names, `--narration WAV`, `--timing JSON`, `PROJECT/audio/narration.wav`, `PROJECT/audio/timing.json`, music sequencing, ducking, output levels and the `music.wav` and `effects.wav` stems.

## storyboard/

- `storyboard.py` builds `storyboard.html` from a script for checking shots against narration before rendering. [Step 4 of the prepare method](../methods/prepare-explainer-video.md#4-convert-the-narrative-into-a-scene-and-shot-sequence) owns the page's layout and preparation use. The tool's header owns the `--audio` clip-matching guard and sentence-fraction hover estimates. Its word floor comes from [step 3](../methods/prepare-explainer-video.md#3-draft-the-narrative-and-honest-time-estimate). Translation naming is below.

## film/

- `build_data.py` writes a composition's `data.js` from cues, captions and narration length and sets `data-duration`. Use `--estimate --language CODE` for a silent preview before voicing. Its header owns timing details, and the translation rules below describe `--key-script`.
- `render.py` renders and post-processes HyperFrames compositions. Its source owns renderer fixes and browser selection. For a caller mixing a master, `encoded_true_peak()` measures its peak after AAC encoding.
- `stills.mjs` captures a built composition for layout and pose inspection, saving `t*.png` and exporting `sfx.json` from `window.SFX`. Run `node scripts/film/stills.mjs --project outputs/sample-film/project outputs/sample-film/stills 0 1.5 3`. Its help and source describe `--every 0.5 0 3`, `--sheets` capture of `<section class="sheet">` in `PROJECT/frames.html`, and time and page guards.
- `sheet.py` tiles `t*.png` in numeric time order into labelled `sheet.png` for comparing poses. Run `scripts/run/py scripts/film/sheet.py outputs/sample-film/stills 4`. Its [docstring](film/sheet.py) owns columns, tile sizes and input guards.
- `render-seek.mjs` provides a silent MP4 fallback when HyperFrames' bundled browser cannot run on the host. Run `scripts/run/heavy node scripts/film/render-seek.mjs --project outputs/sample-film/project outputs/sample-film/silent.mp4 --from 0 --to 2 --fps 30 --workers 2`, then `scripts/run/py scripts/film/render.py --skip-render outputs/sample-film/silent.mp4 -o outputs/sample-film/film.mp4 --narration outputs/sample-film/mix.wav`. Its help owns range defaults, output guards and retained `.seek-*` segments. The [composition](../templates/composition/README.md#write-a-scene) explains timeline registration, and [Motion modules](../templates/composition/README.md#motion-modules) owns stage seek determinism.
- `check_film.py` checks an exact MP4 and reports motion metrics and failures. [Step 8 of the prepare method](../methods/prepare-explainer-video.md#8-run-machine-checks-and-bounded-checkpoints) owns when the `measure_motion.py` gate binds, including `--pacing fast`.

Both JavaScript capture tools share [seek-browser.mjs](film/seek-browser.mjs). Their help describes `--page NAME` and `PAGE`. The shared source owns Chrome and Playwright setup, including project or run-folder `node_modules` and `PLAYWRIGHT`, request restrictions, capture readiness and page errors.

## run/

- `setup_check.sh` checks the local tools a production needs and downloads nothing.
- `py [PYTHON_ARG...]` runs Python in the environment shared by every checkout on this computer. See [Setup](../README.md#setup).
- `receipts.py` regenerates measured tables in receipt documents.
- `runlog.py` prices sessions and appends timed phase rows to `run-state.md`.
- `heavy COMMAND ARG...` serializes expensive work across projects and terminals under `~/.cache/explainer-video-heavy.lock`. Wrap standalone production mixes with `scripts/run/heavy` too. All participating commands must use it under the same OS account. Nested calls inherit the ancestor's lock through `EXPLAINER_VIDEO_HEAVY_LOCK`, so child commands must finish before the ancestor exits. Keep the lock file while commands are active. The [source](run/heavy) defines priority, waiting and lock release.
- `make_film.py` drives the mechanical language build on an existing composition, with an installed HyperFrames CLI and configured voice. Its [source](run/make_film.py) owns input checks, step execution, heavy-work wrapping and failure guards. Use [One command per language](#one-command-per-language) for repairs and mixes. [The production milestones](../templates/production-prompt.md) supply visual work and playback review.

## Sentence cues and translations

Write `On s03-02`, `On s03-02+0.4` or a backtick-wrapped name in a Visual shot. Bold sentence names work too. `s03-02` means sentence 2 of scene 3. A suffix from 0 to 1 selects a fraction of its measured start/end interval, so `+0.4` means 40% through it. The cue ends at the sentence end. Estimated fractions remain planning data.

Keep scene numbers and cue names identical across translations, and keep sentence order and counts for sentence cues. The narration JSON uses scene IDs such as `s03`, and render code reads `FILM.cues["s03|s03-02+0.4"]`. These names need no `--key-script`. Quoted cues such as `On "a leaf grows"` can mix with sentence cues. For quoted translations, `--key-script` maps cues by scene and position, so sentence cues remain independent of word order. With `--key-language`, `storyboard.py` checks counts against the key script, and `make_film.py` does too when either script uses a sentence cue. [cues.py](audio/cues.py) owns quoted-word matching and missing-sentence errors, including without `--strict`.

For a hard cut on a sentence, use `FILM.caption_onsets["s03|s03-02"]`, the start of its first caption. The first measured word can follow the sentence cue by a few frames even without a pause between sentences, so an earlier cut can obscure the caption change that `check_film.py` checks. Put a scene-start cut in a real measured pause before the cue. When there is no pause, use the first sentence's caption onset. `build_data.py` owns onset metadata requirements (`sentence_id`/`scene_id`), independence from cue renaming and fractions, and the `--estimate` map. A missing onset must stay an error.

## One command per language

Follow [the production contract and milestones](../templates/production-prompt.md) for prerequisites and language-specific paths. The composition references that language's `audio/narration.wav` and generated `data.js`.

```sh
scripts/run/make_film.py --language fr --voice VOICE_NAME \
  --script outputs/paper-garden/fr/script.md --scenes outputs/paper-garden/fr/scenes.json \
  --project outputs/paper-garden/fr/project --hf /absolute/path/to/hyperframes \
  --out outputs/paper-garden/fr/film.mp4
```

`make_film.py --help` owns `--audio` and `PROJECT/audio`, `--strings`, `--key-script`, `--key-language`, `--spoken`, `--reuse`, `--aliases`, repeated `--embed NAME=FILE.json`, and `--composition`. It also describes `--caption-font`, `--caption-font-size`, `--caption-font-weight`, `--caption-line-width`, `--tail`, `--pacing`, `--holds`, `--uncaptioned`, `--caption-band`, `--size`, `--fps`, and arguments after a bare `--`. The composition must use the dimensions and frame rate declared to render and check.

Choose `--from STEP` from the changed input. Start at `narrate` after a voice or narration edit, `captions` after caption settings change, `cues` after cue edits, `data` after strings or embedded data change, `render` after a picture-only edit, or `check` to inspect an existing exact MP4. Earlier artifacts must still match their inputs because the tool does not detect stale dependencies automatically. Use a new `--out` when rerendering and keep a failed MP4 for inspection. The tool's source owns `--to STEP` and the render-only MP4 guard.

To add music or effects, run through `--to data`, capture events with `stills.mjs` and mix them with `AUDIO/narration.wav` using `mix.py`. Resume with `--from render --mix MIX.wav`. Render muxes that track and check uses it as the audio reference. See [make_film.py](run/make_film.py) for the `--mix` restart guard.

## Tests

Run `scripts/run/py -m unittest discover -s scripts/DIR` for `audio`, `film`, `storyboard` and `run`, with `scripts/run/heavy` in front for `audio`, `film` and `storyboard`, because they load Stanza's English model. Tests need Setup's English Stanza model and eSpeak, use mocks for other languages and need no files under `local/`. Audio tests load no speech models. Run tests use tiny commands and mocked production tools, and the lock test needs permission to lower process priority. No test voices or renders a film or accesses the network.

Run the browser-free JavaScript tests with `node --test scripts/film/test_seek.mjs`. Tool coverage lives in `test_build_data.py`, `test_render.py`, `test_storyboard.py`, [test_mix.py](audio/test_mix.py), [test_sheet.py](film/test_sheet.py) and [test_seek.mjs](film/test_seek.mjs).

See [Polish each take](../methods/voice-explainer-video.md#polish-each-take) for processing and the [trial report](../library/voice-polish-measurements.md#reproduce) for its measurement command.
