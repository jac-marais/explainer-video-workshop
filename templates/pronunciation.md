# Pronunciation

Copy this file to `local/pronunciation.md`, which is git-ignored, the first time a run needs it. Keep it across runs. A synthetic voice makes the same mistake every time for the same text, voice, and version, so each verdict recorded here saves a later run from finding the mistake again.

## Candidate words

Some words change their stress or sound with their meaning, such as "REC-ord" the noun and "re-CORD" the verb. A transcript spells both forms the same, so speech-to-text cannot catch them. Only an ear check can.

Check every narration word on this list, including its inflections (`records`, `recorded`):

address, alternate, attribute, close, combine, compound, conduct, conflict, console, content, contract, convert, decrease, desert, duplicate, estimate, export, extract, graduate, import, increase, insert, invalid, lead, live, minute, moderate, object, perfect, permit, present, produce, progress, project, protest, read, rebel, record, refund, refuse, reject, row, separate, subject, survey, suspect, tear, transfer, update, upset, use, wind, wound

Add a word when a run finds a new one.

## Verdicts by voice

A verdict applies only to the exact voice setup. When the model, voice, or phonemizer changes, mark the old verdicts "recheck" before you rely on them.

Prefer a fix in this order. First reword the sentence, because then no voice can say it wrong. Next, respell the word in the spoken text only and keep the written word in the captions. Use phonemes only as the last fix.

### `[provider and model version]`, voice `[voice]`, `[runtime and phonemizer versions]`

| Word | Sense | Result | Fix | Verdict by |
|---|---|---|---|---|
| `[word]` | `[verb, noun, or name, with the sentence]` | `[ok, or what it says wrong]` | `[none, rewording, or respelling]` | `[user's ear or transcript, date]` |
