# Voice profile

Copy this folder to `local/voice/`, which is git-ignored, and fill in this file. `methods/voice-explainer-video.md` describes how an agent uses it.

- **Copied from:** `templates/voice/` on `[date]`
- **Choice:** `[stock Kokoro | own clone]`
- **Recorded:** `[date]`, `[who answered]`

`voice.json` holds the voices and the default, and `uv run local/voice/voice.py --list` shows them.

A Kokoro voice entry may set `"lang"` to an eSpeak language code (for example `"pt-br"`); it defaults to `"en-us"`, controls synthesis and is recorded in the receipt's `settings.lang`. A Qwen3 voice entry may set `"lang"` to one of the model's language names (for example `"korean"`); it defaults to `"english"`. A spoken form may pin a word's sound as phonemes, written `[word](/phonemes/)`, for example `[Writing](/ɹˈaɪtɪŋ/)`: Kokoro says the phonemes in any voice and language, and other engines say the word. Use it in a respellings file for names and foreign terms that a language's spelling rules cannot reach.

## Clone reference

- `[none | reference.wav: microphone, duration, date recorded, transcript checked by]`

## Standing decisions

The user's voice choices that should hold for every run. Each entry is one line, with its date.

- `[e.g. Default to the clone; use Kokoro when asked (2026-01-01)]`

`cut_takes.py --language CODE` selects Whisper's language (default `en`); `narrate_film.py` forwards its language. Take matching uses shared Unicode normalization. A sentence without matches falls back to the nearest matched words on either side, or the take edges, and marks the cut unclean. Narration number matching is described in [scripts/README.md](../../scripts/README.md).
