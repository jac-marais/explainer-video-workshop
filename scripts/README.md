# Production scripts

Shared tools for a production. Each one prints its full usage with `--help`. Run them from the workshop root.

The voice tools that these build on (`voice.py`, `cut_takes.py`, `plan_runs.py`) live in `templates/voice/`.

## audio/

- `narrate_film.py` turns a scenes file into narration, timing and aligned words, then checks the audio. It's a uv script, so run it as `uv run scripts/audio/narrate_film.py`.
- `cues.py` times each quoted visual cue in a script against the measured words.
- `captions.py` builds sentence captions from the timing and the words.

## film/

- `render.py` renders a HyperFrames composition to a new MP4 with the known fixes, and never overwrites.
- `check_film.py` runs the final checks on an exact MP4 and prints only the failures.

## run/

- `setup_check.sh` checks the local tools a production needs, without changing anything.
- `receipts.py` regenerates the measured tables in receipt documents.
- `runlog.py` prices sessions and appends timed phase rows to `run-state.md`.
