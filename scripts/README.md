# Production scripts

This is the one list of the shared tools for a production and what each does. Each tool prints its full usage with `--help`. Run them from the workshop root. The command lines for a run are in M0 to M6 of `templates/production-prompt.md`.

The voice tools that these build on (`voice.py`, `cut_takes.py`, `plan_runs.py`) live in `templates/voice/`.

## assets/

- `check_asset.py` checks third-party 3D models, textures, HDRIs and archives before a scene loads them, and prints each file's SHA-256 for the asset manifest. It never decodes or runs the file. The sources and the intake steps are in `library/3d-assets.md`.

## audio/

All five narration, cue, caption, film-data and storyboard tools share `audio/text_tokens.py`: matching uses NFKC/casefold and retains Unicode letters, combining marks and numbers. Han/Kana split into character tokens; Latin, Devanagari and Hangul split on whitespace. Caption breaks use those same boundaries and preserve punctuation; Latin words and numbers remain intact. Times within a multi-character ASR piece are interpolated from its measured bounds.

- `narrate_film.py` drives the voice tools for a whole film. It voices the scenes, cuts them into sentences, assembles the narration, aligns the script's words, writes the timing, and checks the audio. `--language` (default `en`) sets Whisper's language for take cutting, alignment and `--check-only`, and the number readings used in matching: French, Hindi, Chinese and Sino-Korean read integers below a million, dot decimals and percents, including a number Whisper joins to a word, such as `12층`; English, Portuguese and Spanish keep their existing readings. Long-form Whisper can skip a stretch of audio, so sentences left with interpolated words get one repair pass: adjacent ones merge into a span, padded by 0.15 s and clamped to the file, which the same model and settings transcribe again; its words replace the long-form words whose midpoints fall inside it only when that leaves fewer interpolated words, because a short clip can swap homophones or hallucinate. The run records nonzero `retranscribed_spans` in the `audio-checks.json` stats. Fully aligned runs make no extra Whisper call. It's a uv script, so run it as `uv run scripts/audio/narrate_film.py`.
- `cues.py` times each quoted visual cue in a script against the measured words. It matches each quoted span to consecutive words in its scene's window, and writes the span's start and end to `cues.json`.
- `captions.py` builds sentence captions from the timing and the words.

## storyboard/

- `storyboard.py` builds `storyboard.html` from a script. The narration is on the left, and hovering a phrase shows the shots and key frames that start on it. It fails on a cue that isn't in its scene's narration. `test_storyboard.py` checks it on a small sample script.

## film/

- `build_data.py` writes a composition's `data.js` from the script's cues, captions and narration length, and sets its `data-duration`. `--estimate` times the script evenly for a silent preview before any voice exists, and `--key-script` keeps a translated film's cue names. `test_build_data.py` checks it on a small sample script.
- `render.py` renders a HyperFrames composition to a new MP4 with the known fixes, including one worker by default, and never overwrites.
- `check_film.py` runs the final checks on an exact MP4 and prints the motion metrics and the failures. `measure_motion.py` is its motion gate, which binds only with `--pacing fast`.

## run/

- `setup_check.sh` checks the local tools a production needs, without changing anything.
- `receipts.py` regenerates the measured tables in receipt documents.
- `runlog.py` prices sessions and appends timed phase rows to `run-state.md`.
