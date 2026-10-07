# Voice profile

Copy this folder to `local/voice/`, which is git-ignored, and fill in this file. `methods/voice-explainer-video.md` describes how an agent uses it.

- **Copied from:** `templates/voice/` on `[date]`
- **Choice:** `[stock Kokoro | own clone]`
- **Recorded:** `[date]`, `[who answered]`

`voice.json` holds the voices and the default, and `uv run local/voice/voice.py --list` shows them.

## Clone reference

- `[none | reference.wav: microphone, duration, date recorded, transcript checked by]`

## Standing decisions

The user's voice choices that should hold for every run. Each entry is one line, with its date.

- `[e.g. Default to the clone; use Kokoro when asked (2026-01-01)]`
