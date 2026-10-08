# Production scripts

This is the one list of the shared tools for a production and what each does. Each tool prints its full usage with `--help`. Run them from the workshop root. The command lines for a run are in M0 to M6 of `templates/production-prompt.md`.

The voice tools that these build on (`voice.py`, `cut_takes.py`, `plan_runs.py`) live in `templates/voice/`.

## audio/

- `narrate_film.py` drives the voice tools for a whole film. It voices the scenes, cuts them into sentences, assembles the narration, aligns the script's words, writes the timing, and checks the audio. It's a uv script, so run it as `uv run scripts/audio/narrate_film.py`.
- `cues.py` times each quoted visual cue in a script against the measured words. It matches each quoted span to consecutive words in its scene's window, and writes the span's start and end to `cues.json`.
- `captions.py` builds sentence captions from the timing and the words.

## film/

- `render.py` renders a HyperFrames composition to a new MP4 with the known fixes, and never overwrites.
- `check_film.py` runs the final checks on an exact MP4 and prints only the failures.

## run/

- `setup_check.sh` checks the local tools a production needs, without changing anything.
- `receipts.py` regenerates the measured tables in receipt documents.
- `runlog.py` prices sessions and appends timed phase rows to `run-state.md`.
