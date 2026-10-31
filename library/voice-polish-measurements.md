# Voice polish synthetic narration trial

Locally reproduced on Linux x86_64, 2026-10-31, with FFmpeg 6.1.1, stock Kokoro v1.0 `af_heart`, frontend 3, speed 0.92, and the production faster-whisper large-v3-turbo CPU float32 decoder. No reference recording, private voice, or `local/` input is used. The invented passage and exact computation live in [`measure_voice_polish.py`](../scripts/audio/measure_voice_polish.py). This is evidence for the fixture, not for every clone or language.

## Reproduce

```bash
scripts/run/heavy scripts/run/py scripts/audio/measure_voice_polish.py outputs/voice-polish-chain
```

The required models must already be in their default per-user caches. The command downloads nothing. Audio, full receipts, transcripts and metrics stay in the ignored output directory. The script exits nonzero if an existing gate fails, a word falls back, or the raw recognition word-error count changes.

## Measurement

The 26.649-second passage contains six sentences and 67 words. Each synthesized sentence is followed by 0.5 seconds of known silence; the measured quiet window is 0.25 to 0.05 seconds before the end of that gap. Thus these are controlled gaps between sentences, not detected pauses within words. The noisy variant adds seeded Gaussian noise with amplitude standard deviation 0.0015 and a 35 Hz sine of peak amplitude 0.004 to the same samples. Both versions go through the existing per-take loudness normalization and final run-voice normalization and checks. No final localized level correction or additional loudness correction was needed.

Quiet RMS is unweighted dBFS over the same windows. “Sibilant band” is mean energy after a fourth-order Butterworth 4–10 kHz bandpass over the same speech intervals; it is a broad proxy, not isolated S phonemes or a perceptual score. LRA, integrated loudness and true peak are measured from final PCM24 through the production FFmpeg meter. Word errors are token-level Levenshtein substitutions + insertions + deletions on the raw ASR output; the ordinary repaired ASR and strict fallback gates also run.

| Condition | Quiet RMS dBFS | Speech 4–10 kHz dBFS | LRA LU | Integrated LUFS | True peak dBTP | ASR word errors | Fallback words | Gate flags |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| clean / before | digital silence | -29.55 | 2.0 | -16.32 | -1.50 | 0 | 0 | 0 |
| clean / after | digital silence | -30.49 | 2.1 | -16.25 | -1.50 | 0 | 0 | 0 |
| added noise / before | -43.04 | -29.50 | 2.0 | -16.30 | -1.50 | 0 | 0 | 0 |
| added noise / after | -53.07 | -30.45 | 2.1 | -16.28 | -1.50 | 0 | 0 | 0 |

All four outputs contain 1,279,136 frames at 48 kHz. All pass the existing −16 ±1 LU integrated-loudness gate, ≤−1 dBTP peak gate, ±3 dB sentence-level gate, 2.5 dB scene-jump gate, tail check, duration check, ASR difference check and strict fallback check. The processing target remains −1.5 dBTP. Peak handling and every gate threshold are unchanged.

## Tuning and interpretation

The initial preset used de-esser intensity 0.15 and a +1 dB presence boost. It passed the same gates, but the noisy sample’s 4–10 kHz energy rose from −29.50 to −28.51 dBFS. That did not support a sibilance-reduction claim. Fixed-fixture probes found intensity 0.5 too aggressive for a conservative starting point (about 7 dB band reduction at matched loudness). The final preset uses intensity 0.35 and +0.5 dB presence. Those choices are workshop inferences from this trial, not sourced universal settings.

The final noisy sample loses 10.03 dB of quiet-window noise and 0.94 dB of speech-band energy. LRA changes from 2.0 to 2.1 LU, so this short fixture shows no flattening by that metric. Recognition remains zero errors. This does not prove preserved timbre, breath character, long-form delivery or listener preference; no listening-panel result is claimed. The clean fixture also keeps zero errors and loses 0.94 dB in the same band.

## Tests and remaining questions

The full suite passes: 170 audio tests (including the opt-in real FFmpeg level probes), 16 film tests, 8 storyboard tests and 28 run-tool tests, 222 total. No gate or test is deleted. The backend cache test now explicitly bypasses polish: its former guarantee, unchanged Mac/Kokoro backend hashes, still lives in `test_bypassed_mac_and_kokoro_identity_preserves_legacy_hash`. Enabled clones intentionally invalidate old takes; `test_default_clone_invalidates_old_take_identity_on_both_platforms` and the effective-settings test cover that requirement.

Open validation: reference clones on both backends, low-register voices, other languages, longer expressive delivery and human listening comparisons. The clone-only default is provisional and can be bypassed per voice. This trial does not justify enabling polish for all stock engines.
