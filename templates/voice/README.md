# Voice profile

Copy this folder to `local/voice/`, which is git-ignored, and fill in this file. `methods/voice-explainer-video.md` describes how an agent uses it.

- **Copied from:** `templates/voice/` on `[date]`
- **Choice:** `[stock Kokoro | own clone]`
- **Recorded:** `[date]`, `[who answered]`

`voice.json` holds the voices and the default, and `scripts/run/py local/voice/voice.py --list` shows them.

A Kokoro voice entry may set `"lang"` to an eSpeak language code (for example `"pt-br"`); it defaults to `"en-us"`, controls synthesis and is recorded in the receipt's `settings.lang`. A Qwen3 voice entry may set `"lang"` to one of the model's language names (for example `"korean"`); it defaults to `"english"`. A spoken form may pin a word's sound as phonemes, written `[word](/phonemes/)`, for example `[Writing](/ɹˈaɪtɪŋ/)`: Kokoro says the phonemes in any voice and language, and other engines say the word. A pin may use only symbols in Kokoro's vocabulary (`ɜɹ`, not `ɝ`); `voice.py` refuses any other, because Kokoro would drop it silently. Use it in a respellings file for names and foreign terms that a language's spelling rules cannot reach.

A Kokoro voice entry may set `"frontend": 3`, so that `voice.py` phonemizes its text with eSpeak instead of Kokoro's own tokenizer. The frontend removes eSpeak's language-switch flags and places pronunciation pins after `L’` or `L'`. A sentence terminator that Kokoro lacks, from any script (for example `।` or `。`), becomes the nearest of `.`, `?` and `!`. eSpeak phoneme symbols never reach Kokoro as punctuation: `ESPEAK_SYMBOLS` maps such a symbol to Kokoro's nearest clear phoneme, for example the retroflex flap `r.` to the tap `ɾ`, and the mark is dropped from any other. The key is part of the voice identity, so changing it voices cached sentences again; receipts record it as `settings.frontend`.

## Clone reference

- `[none | reference.wav: microphone, duration, date recorded, transcript checked by]`

## Standing decisions

The user's voice choices that should hold for every run. Each entry is one line, with its date.

- `[e.g. Default to the clone; use Kokoro when asked (2026-01-01)]`

`cut_takes.py --language CODE` selects Whisper's language (default `en`); `narrate_film.py` forwards its language. Take matching uses shared Unicode normalization. A sentence without matches falls back to the nearest matched words on either side, or the take edges, and marks the cut unclean. Narration number matching is described in [scripts/README.md](../../scripts/README.md).
