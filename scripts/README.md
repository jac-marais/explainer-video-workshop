# Production scripts

This is the one list of the shared tools for a production and what each does. Each tool prints its full usage with `--help`. Run them from the workshop root. The command lines for a run are in M0 to M6 of `templates/production-prompt.md`.

The voice tools that these build on (`voice.py`, `cut_takes.py`, `plan_runs.py`) live in `templates/voice/`.

## assets/

- `check_asset.py` checks third-party 3D models, textures, HDRIs and archives before a scene loads them, and prints each file's SHA-256 for the asset manifest. It never decodes or runs the file. The sources and the intake steps are in `library/3d-assets.md`.

## audio/

All five narration, cue, caption, film-data and storyboard tools share `audio/text_tokens.py`: matching uses NFKC/casefold and retains Unicode letters, combining marks and numbers. Han/Kana split into character tokens; Latin, Devanagari and Hangul split on whitespace. Times within a multi-character ASR piece are interpolated from its measured bounds. Sentence boundaries come from Stanza's tokenizer for the language, filtered and completed as `sentences()` there describes, and its dependency parse places the caption line breaks. The tools that split or parse run with `scripts/run/py`, with Stanza's models from [Setup](../README.md#setup).

- `narrate_film.py` drives the voice tools for a whole film. Its take length limit is in [the voice method](../methods/voice-explainer-video.md#estimated-runs). It voices the scenes, cuts them into sentences, assembles the narration, aligns the script's words, writes the timing, and checks the audio. `--language` (default `en`) sets Whisper's language for take cutting, alignment and `--check-only`, and the number readings used in matching: French, Hindi, Chinese and Sino-Korean read integers below a million, dot decimals and percents, including a number Whisper joins to a word, such as `12층`; English, Portuguese and Spanish keep their existing readings. Long-form Whisper can skip a stretch of audio, so sentences left with interpolated words get one repair pass: adjacent ones merge into a span, padded by 0.15 s and clamped to the file, which the same model and settings transcribe again; its words replace the long-form words whose midpoints fall inside it only when that leaves fewer interpolated words, because a short clip can swap homophones or hallucinate. The run records nonzero `retranscribed_spans` in the `audio-checks.json` stats. Fully aligned runs make no extra Whisper call. Run it as `scripts/run/py scripts/audio/narrate_film.py`.
- `cues.py` writes measured visual cue times to `cues.json`. Quoted cues match consecutive words in their scene window. Sentence cues use `timing.json` directly; their syntax and translation rules are below.
- `captions.py` builds sentence captions from the timing and the words, with lines measured in the caption font.

## storyboard/

- `storyboard.py` builds `storyboard.html` from a script. The narration is on the left with each cue's words underlined, and hovering a phrase shows the shots and key frames that start on it, above a strip of every shot in the scene. With `--audio`, read aloud plays the film's clip for each sentence that the clip still matches, under the guard in its docstring, and a system voice reads the rest. It supports both quoted and sentence cues and fails when the referenced words or sentence are absent, or when a sentence is under the word floor in [step 3 of the prepare method](../methods/prepare-explainer-video.md#3-draft-the-narrative-and-honest-time-estimate), which it checks in the `--key-script` when one is given. Sentence fractions select an approximate token position for the hover preview, not measured audio time. `--language` names the script's language, and `--key-script` with `--key-language` checks translated sentence counts. `test_storyboard.py` checks it on a small sample script, with no audio and with audio whose clips partly match.

## film/

- `build_data.py` writes a composition's `data.js` from the script's cues, captions and narration length, and sets its `data-duration`. `--estimate --language CODE` times the script evenly for a silent preview before any voice exists, and `--key-script` maps translated quoted cues to the original names by position within each scene. Sentence cue names stay unchanged without that option. `test_build_data.py` checks it on a small sample script.
- `render.py` renders a HyperFrames composition to a new MP4 with the known fixes that its docstring lists, and never overwrites. It finds host Chrome on macOS and Chrome or Chromium on Linux, and its `encoded_true_peak()` measures a master's true peak after the AAC encoding, for a caller that mixes its own audio. `test_render.py` checks its guards and browser choice with a stand-in CLI.
- `check_film.py` runs the final checks on an exact MP4 and prints the motion metrics and the failures. `measure_motion.py` is its motion gate, which binds only with `--pacing fast`.

## run/

- `setup_check.sh` checks the local tools a production needs and downloads nothing.
- `py [PYTHON_ARG...]` runs Python in the environment that every checkout on this computer shares; see [Setup](../README.md#setup).
- `receipts.py` regenerates the measured tables in receipt documents.
- `runlog.py` prices sessions and appends timed phase rows to `run-state.md`.

- `heavy COMMAND ARG...` serializes expensive work across projects and terminals with one advisory lock at `~/.cache/explainer-video-heavy.lock`. It reports waiting and adds 10 to the command's nice value. Nested calls use the ancestor's lock and priority through `EXPLAINER_VIDEO_HEAVY_LOCK`, so child commands must finish before that ancestor exits. The command inherits the lock; exit, failure or a signal releases it. The file remains and must not be deleted while commands are active. All participating commands must use this wrapper under the same OS account.
- `make_film.py` runs one language through `narrate`, `captions`, `cues`, `data`, `render`, `check`, or the range from `--from` to `--to`. Sentence splitting, narration (including TTS and Whisper), captions, rendering and final checks go through `heavy`. It checks that the scenes JSON matches the script before spending work, and a run that starts at `narrate` also checks the storyboard's word floor, in the `--key-script` when one is given. It stops on command failure or audio flags, and never overwrites an MP4. It needs an existing HyperFrames composition, an installed CLI and a configured voice; it does not build the visual design or perform the human playback review.

## Sentence cues and translations

Write `On s03-02`, `On s03-02+0.4`, or a backtick-wrapped name in a Visual shot. Bold sentence names also work. `s03-02` means sentence 2 of scene 3; the suffix is a fraction from 0 to 1, so `+0.4` means 40% through that sentence's measured start/end interval. The cue's end remains the sentence end. The narration, estimates, storyboard and `make_film.py` share one sentence splitter, `sentences()` in `audio/text_tokens.py`.

Keep the scene numbers and cue names identical in every translation, and with sentence cues also the sentence order and counts. The narration JSON must use scene IDs such as `s03`. Render code reads `FILM.cues["s03|s03-02+0.4"]`. These names need no `--key-script`. Quoted cues such as `On "a leaf grows"` keep working, including mixtures of both cue types. For quoted translations, `--key-script` maps only quoted cues by scene and position; sentence cues remain independent of word order. With `--key-language`, `storyboard.py` checks sentence counts against it, and `make_film.py` does too when either script uses a sentence cue. A missing referenced sentence always fails, including without `--strict`. Estimated fractions remain planning estimates.

For a hard cut on a sentence, use `FILM.caption_onsets["s03|s03-02"]`, the start of that sentence's first caption, instead of its sentence cue. The first measured word can follow the cue by a few frames even when sentences have no pause between them; an earlier cut can obscure the caption change checked by `check_film.py`. A cut at a scene start goes in the pause before the cue; inspect the measured timing for a real pause rather than subtracting a fixed offset. If there is no scene pause, use the caption onset for a hard cut on its first sentence. `build_data.py` exposes onsets for every sentence with caption metadata, independently of quoted cue renaming and fraction cues. A sentence without captions or `sentence_id`/`scene_id` metadata has no onset entry; do not silently fall back to its cue. `--estimate` supplies the same map from estimated captions, which remains planning data.

## One command per language

Run this after the package, voice and pilot gates pass. Use separate audio, project and MP4 paths for each language, with the composition referencing that language's `audio/narration.wav` and generated `data.js`:

```sh
scripts/run/make_film.py --language fr --voice VOICE_NAME \
  --script outputs/paper-garden/fr/script.md --scenes outputs/paper-garden/fr/scenes.json \
  --project outputs/paper-garden/fr/project --hf /absolute/path/to/hyperframes \
  --out outputs/paper-garden/fr/film.mp4
```

`--audio` defaults to `PROJECT/audio`. Optional inputs include `--strings`, `--key-script` with `--key-language`, `--spoken`, `--reuse`, `--aliases` and repeated `--embed NAME=FILE.json`. The `--caption-font`, `--caption-font-size`, `--caption-font-weight` and `--caption-line-width` options pass through to `captions.py`, which describes them. `--tail`, `--pacing`, `--holds`, `--uncaptioned`, `--caption-band`, `--size` and `--fps` configure the matching render/check contract; the composition must already use the declared dimensions and frame rate. `--composition` defaults to `.`. Arguments after a bare `--` go to `hyperframes render` through `render.py`.

Add `--from STEP` to run that step and every later step. After a voice or narration edit, start at `narrate`; after caption settings change, `captions`; after cue edits, `cues`; after strings or embedded data change, `data`; after a picture-only edit, `render`; for checking an existing exact MP4, `check`. Earlier artifacts must exist and still match the inputs; this is an explicit restart, not automatic dependency detection. Use a new `--out` when rerendering. A check failure keeps that MP4 for inspection. `--to STEP` stops after that step, for example `--to data` builds the composition data without starting a browser. The MP4 guard applies only to a run that includes `render`.

To add music or effects, run through `--to data`, mix them with `AUDIO/narration.wav` into a mono WAV as long as the narration, then run `--from render --mix MIX.wav`. Render muxes the mix in place of the narration, and check measures the film's length, loudness and silences against it. `--mix` is refused with an earlier `--from`, because those steps change what the mix contains.

## Tests

Run `scripts/run/py -m unittest discover -s scripts/DIR` for each of `audio`, `film`, `storyboard` and `run`, with `scripts/run/heavy` in front for `audio`, `film` and `storyboard`, because they load Stanza's English model. A test checks the workshop's code, not the computer, so it needs no model beyond Setup's English Stanza model and eSpeak, and no file under `local/`; it mocks Stanza for another language's rule. The audio tests do not load speech models. The run tests use tiny commands and mocked production tools, and the lock test needs permission to lower process priority. No test voices or renders a film or accesses the network.
