# Production scripts

This is the one list of the shared tools for a production and what each does. Each tool prints its full usage with `--help`. Run them from the workshop root. The command lines for a run are in M0 to M6 of `templates/production-prompt.md`.

The voice tools that these build on (`voice.py`, `cut_takes.py`, `plan_runs.py`) live in `templates/voice/`.

## assets/

- `check_asset.py` checks third-party 3D models, textures, HDRIs and archives before a scene loads them, and prints each file's SHA-256 for the asset manifest. It never decodes or runs the file. The sources and the intake steps are in `library/3d-assets.md`.

## audio/

All five narration, cue, caption, film-data and storyboard tools share `audio/text_tokens.py`: matching uses NFKC/casefold and retains Unicode letters, combining marks and numbers. Han/Kana split into character tokens; Latin, Devanagari and Hangul split on whitespace. Caption breaks use those same boundaries and preserve punctuation; Latin words and numbers remain intact. Times within a multi-character ASR piece are interpolated from its measured bounds.

- `narrate_film.py` drives the voice tools for a whole film. It voices the scenes, cuts them into sentences, assembles the narration, aligns the script's words, writes the timing, and checks the audio. `--language` (default `en`) sets Whisper's language for take cutting, alignment and `--check-only`, and the number readings used in matching: French, Hindi, Chinese and Sino-Korean read integers below a million, dot decimals and percents, including a number Whisper joins to a word, such as `12층`; English, Portuguese and Spanish keep their existing readings. Long-form Whisper can skip a stretch of audio, so sentences left with interpolated words get one repair pass: adjacent ones merge into a span, padded by 0.15 s and clamped to the file, which the same model and settings transcribe again; its words replace the long-form words whose midpoints fall inside it only when that leaves fewer interpolated words, because a short clip can swap homophones or hallucinate. The run records nonzero `retranscribed_spans` in the `audio-checks.json` stats. Fully aligned runs make no extra Whisper call. It's a uv script, so run it as `uv run scripts/audio/narrate_film.py`.
- `cues.py` writes measured visual cue times to `cues.json`. Quoted cues match consecutive words in their scene window. Sentence cues use `timing.json` directly; their syntax and translation rules are below.
- `captions.py` builds sentence captions from the timing and the words.

## storyboard/

- `storyboard.py` builds `storyboard.html` from a script. The narration is on the left, and hovering a phrase shows the shots and key frames that start on it. It supports both quoted and sentence cues and fails when the referenced words or sentence are absent. Sentence fractions select an approximate token position for the hover preview, not measured audio time. `--key-script` checks translated sentence counts. `test_storyboard.py` checks it on a small sample script.

## film/

- `build_data.py` writes a composition's `data.js` from the script's cues, captions and narration length, and sets its `data-duration`. `--estimate` times the script evenly for a silent preview before any voice exists, and `--key-script` maps translated quoted cues to the original names by position within each scene. Sentence cue names stay unchanged without that option; when supplied, it also checks sentence counts. `test_build_data.py` checks it on a small sample script.
- `render.py` renders a HyperFrames composition to a new MP4 with the known fixes, including one worker by default, and never overwrites.
- `check_film.py` runs the final checks on an exact MP4 and prints the motion metrics and the failures. `measure_motion.py` is its motion gate, which binds only with `--pacing fast`.

## run/

- `setup_check.sh` checks the local tools a production needs, without changing anything.
- `receipts.py` regenerates the measured tables in receipt documents.
- `runlog.py` prices sessions and appends timed phase rows to `run-state.md`.

- `heavy COMMAND ARG...` serializes expensive work across projects and terminals with one advisory lock at `~/.cache/explainer-video-heavy.lock`. It reports waiting and adds 10 to the command's nice value. The command inherits the lock; exit, failure or a signal releases it. The file remains and must not be deleted while commands are active. All participating commands must use this wrapper under the same OS account.
- `make_film.py` runs one language through `narrate`, `captions`, `cues`, `data`, `render`, `check`. Narration (including TTS and Whisper), rendering and final checks go through `heavy`. It checks that the scenes JSON matches the script before spending work, stops on command failure or audio flags, and never overwrites an MP4. It needs an existing HyperFrames composition, an installed CLI and a configured voice; it does not build the visual design or perform the human playback review.

## Sentence cues and translations

Write `On s03-02`, `On s03-02+0.4`, or a backtick-wrapped name in a Visual shot. Bold sentence names also work. `s03-02` means sentence 2 of scene 3; the suffix is a fraction from 0 to 1, so `+0.4` means 40% through that sentence's measured start/end interval. The cue's end remains the sentence end. The narration, estimates and storyboard share the same sentence splitter, including Chinese punctuation and the Devanagari danda.

Keep the scene numbers, sentence order, sentence counts and cue names identical in every translation. The narration JSON must use scene IDs such as `s03`. Render code reads `FILM.cues["s03|s03-02+0.4"]`. These names need no `--key-script`. Quoted cues such as `On "a leaf grows"` keep working, including mixtures of both cue types. For quoted translations, `--key-script` maps only quoted cues by scene and position; sentence cues remain independent of word order. Supply it to any of the three tools when you also want sentence-count validation against a reference script. A missing referenced sentence always fails, including without `--strict`. Estimated fractions remain planning estimates.

## One command per language

Run this after the package, voice and pilot gates pass. Use separate audio, project and MP4 paths for each language, with the composition referencing that language's `audio/narration.wav` and generated `data.js`:

```sh
scripts/run/make_film.py --language de --voice VOICE_NAME \
  --script outputs/paper-garden/de/script.md --scenes outputs/paper-garden/de/scenes.json \
  --project outputs/paper-garden/de/project --hf /absolute/path/to/hyperframes \
  --out outputs/paper-garden/de/film.mp4
```

`--audio` defaults to `PROJECT/audio`. Optional inputs include `--strings`, `--key-script`, `--spoken`, `--reuse`, `--aliases` and repeated `--embed NAME=FILE.json`. `--tail`, `--pacing`, `--holds`, `--uncaptioned`, `--caption-band`, `--size` and `--fps` configure the matching render/check contract; the composition must already use the declared dimensions and frame rate. `--composition` defaults to `.`.

Add `--from STEP` to run that step and every later step. After a voice or narration edit, start at `narrate`; after caption settings change, `captions`; after cue edits, `cues`; after strings or embedded data change, `data`; after a picture-only edit, `render`; for checking an existing exact MP4, `check`. Earlier artifacts must exist and still match the inputs; this is an explicit restart, not automatic dependency detection. Use a new `--out` when rerendering. A check failure keeps that MP4 for inspection.

## Tests

Run `python3 -m unittest discover -s scripts/DIR` for each of `audio`, `film`, `storyboard` and `run`. Audio tests need the NumPy and SoundFile versions declared in the narration test scripts; they do not load speech models. The run tests use tiny commands and mocked production tools, and the lock test needs permission to lower process priority. No test voices or renders a film or accesses the network.
