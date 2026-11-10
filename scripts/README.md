# Production scripts

This is the shared tool list for a production. Run the tools from the workshop root. Each CLI's `--help` and source header own its options, defaults and guards. [M0 to M6 of templates/production-prompt.md](../templates/production-prompt.md) supply the production commands and milestones.

See [the voice method](../methods/voice-explainer-video.md#generate-narration) for the underlying voice tools.

## assets/

- `check_asset.py` checks third-party 3D models, textures, HDRIs and archives before a scene loads them and prints each file's SHA-256 for the asset manifest. [library/3d-assets.md](../library/3d-assets.md) owns sources and intake steps, and the tool's header defines its inspection limits.

## audio/

Narration, cues, captions, film data and storyboards share [audio/text_tokens.py](audio/text_tokens.py) for Unicode matching and sentence splitting. Its `sentences()` contract owns language-specific sentence boundaries, and [audio/captions.py](audio/captions.py) owns the dependency parse that places caption breaks. Run tools that split or parse with `scripts/run/py`, using the Stanza models from [Setup](../README.md#setup).

- Use `narrate_film.py` through [M1](../templates/production-prompt.md) for narration. Its header covers number readings, alignment repairs and check reports. [The voice method](../methods/voice-explainer-video.md#estimated-runs) owns take-length limits.
- Use `cues.py` and `captions.py` through [M1](../templates/production-prompt.md). [Sentence cues and translations](#sentence-cues-and-translations) owns cue naming, and [Caption layout](../templates/composition/README.md#caption-layout) owns font selection and geometry.
- Use [mix.py](audio/mix.py) for generated music and effects, with [the mix restart](#one-command-per-language). Its help owns event fields, sequencing, output levels and stems, and its source owns the event names and ducking levels.

## storyboard/

- Use `storyboard.py` through [step 4 of the prepare method](../methods/prepare-explainer-video.md#4-convert-the-narrative-into-a-scene-and-shot-sequence). Its header owns clip matching and hover estimates. [Step 3](../methods/prepare-explainer-video.md#3-draft-the-narrative-and-honest-time-estimate) owns the word floor, and the translation rules below own cue naming.

## film/

- Use `build_data.py` for composition data. Its header owns measured and estimated timing, and the translation rules below own cue mapping.
- Use `build_scenes.py --project DIR --template FILE [sNN ...]` to assemble scene fragments when a composition uses a page template. Its help owns placeholders, duration, closures and separate selected-scene outputs.
- Use `render.py` through [M5](../templates/production-prompt.md). Its source owns renderer fixes, browser selection and `encoded_true_peak()` for callers mixing a master.
- Use [stills.mjs](film/stills.mjs) for layout and pose inspection, and [sheet.py](film/sheet.py) for pose comparisons. Their help owns capture modes, outputs and guards.
- Use [render-seek.mjs](film/render-seek.mjs) for the host-browser fallback. Its help owns capture ranges, retained segments and the audio post-processing command. [Write a scene](../templates/composition/README.md#write-a-scene) covers timeline registration.
- Use `check_film.py` through [M5 and M6](../templates/production-prompt.md). [Step 8 of the prepare method](../methods/prepare-explainer-video.md#8-run-machine-checks-and-bounded-checkpoints) owns the motion gate.

Both JavaScript capture tools share [seek-browser.mjs](film/seek-browser.mjs), whose header owns browser setup, page selection, request restrictions, readiness and page errors.

## run/

- Follow [Setup](../README.md#setup) for `setup_check.sh` and `py [PYTHON_ARG...]`.
- Use `scenes_json.py --script SCRIPT.md --out SCENES.json` to create narration input from an authored script. Its help owns the fields and the fresh-take mark.
- Use `receipts.py` through [M1 and M5](../templates/production-prompt.md) for receipt tables.
- `runlog.py` prices sessions and appends timed phase rows to `run-state.md`.
- `heavy COMMAND ARG...` serializes expensive work across projects and terminals under `~/.cache/explainer-video-heavy.lock`. Wrap standalone production mixes with `scripts/run/heavy` too. All participating commands must use it under the same OS account. Nested calls inherit the ancestor's lock through `EXPLAINER_VIDEO_HEAVY_LOCK`, so child commands must finish before the ancestor exits. Keep the lock file while commands are active. The [source](run/heavy) defines priority, waiting and lock release.
- Use [make_film.py](run/make_film.py) through [One command per language](#one-command-per-language) for builds, repairs and mixes. Its help and source own input checks, step execution and failure guards. [The production milestones](../templates/production-prompt.md) supply visual work and playback review.

## Sentence cues and translations

Write `On s03-02`, `On s03-02+0.4` or a backtick-wrapped name in a Visual shot. Bold sentence names work too. `s03-02` means sentence 2 of scene 3. A suffix from 0 to 1 selects a fraction of its measured start/end interval, so `+0.4` means 40% through it. The cue ends at the sentence end. Estimated fractions remain planning data.

Keep scene numbers and cue names identical across translations, and keep sentence order and counts for sentence cues. The narration JSON uses scene IDs such as `s03`, and render code reads `FILM.cues["s03|s03-02+0.4"]`. These names need no `--key-script`. Quoted cues such as `On "a leaf grows"` can mix with sentence cues. For quoted translations, `--key-script` maps cues by scene and position, so sentence cues remain independent of word order. With `--key-language`, `storyboard.py` checks counts against the key script, and `make_film.py` does too when either script uses a sentence cue. [cues.py](audio/cues.py) owns quoted-word matching and missing-sentence errors, including without `--strict`.

For a hard cut on a sentence, use `FILM.caption_onsets["s03|s03-02"]`, the start of its first caption. The first measured word can follow the sentence cue by a few frames even without a pause between sentences, so an earlier cut can obscure the caption change that `check_film.py` checks. Put a scene-start cut in a real measured pause before the cue. When there is no pause, use the first sentence's caption onset. `build_data.py` owns onset metadata requirements (`sentence_id`/`scene_id`), independence from cue renaming and fractions, and the `--estimate` map. A missing onset must stay an error.

## One command per language

Follow [the production contract and milestones](../templates/production-prompt.md) for prerequisites and language-specific paths. Follow the composition's [Files](../templates/composition/README.md#files) and [Set up a run](../templates/composition/README.md#set-up-a-run) for its audio and data references.

```sh
scripts/run/make_film.py --language fr --voice VOICE_NAME \
  --script outputs/paper-garden/fr/script.md --scenes outputs/paper-garden/fr/scenes.json \
  --project outputs/paper-garden/fr/project --hf /absolute/path/to/hyperframes \
  --out outputs/paper-garden/fr/film.mp4
```

`make_film.py --help` describes every option, including render forwarding after a bare `--`.

Choose `--from STEP` from the changed input. Start at `narrate` after a voice or narration edit, `captions` after caption settings change, `cues` after cue edits, `data` after strings or embedded data change, `render` after a picture-only edit, or `check` to inspect an existing exact MP4. Earlier artifacts must still match their inputs because the tool does not detect stale dependencies automatically. Follow [M5](../templates/production-prompt.md) for rerender outputs and failed-file inspection. The tool's source owns `--to STEP` and the render-only MP4 guard.

To add music or effects, run through `--to data`, capture events with `stills.mjs` and mix them with `AUDIO/narration.wav` using `mix.py`. Resume with `--from render --mix MIX.wav`.  See [make_film.py](run/make_film.py) for the `--mix` restart guard.

## Tests

Run `scripts/run/py -m unittest discover -s scripts/DIR` for `audio`, `film`, `storyboard` and `run`, with `scripts/run/heavy` in front for `audio`, `film` and `storyboard`, because they load Stanza's English model. Tests need Setup's English Stanza model and eSpeak, use mocks for other languages and need no files under `local/`. Audio tests load no speech models. Run tests use tiny commands and mocked production tools, and the lock test needs permission to lower process priority. No test voices or renders a film or accesses the network.

Run the browser-free JavaScript tests with `node --test scripts/film/test_seek.mjs`. Tool coverage lives in `test_build_data.py`, `test_render.py`, `test_storyboard.py`, [test_mix.py](audio/test_mix.py), [test_sheet.py](film/test_sheet.py) and [test_seek.mjs](film/test_seek.mjs).

See [Polish each take](../methods/voice-explainer-video.md#polish-each-take) for processing and the [trial report](../library/voice-polish-measurements.md#reproduce) for its measurement command.
