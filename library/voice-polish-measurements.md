# Voice polish synthetic narration trial

Locally reproduced on Linux x86_64, 2026-10-31, with FFmpeg 6.1.1, stock Kokoro v1.0 `af_heart`, frontend 3, speed 0.92, and the production faster-whisper large-v3-turbo CPU float32 decoder. No reference recording, private voice, or `local/` input is used. The invented passage and exact computation live in [`measure_voice_polish.py`](../scripts/audio/measure_voice_polish.py).

## Reproduce

```bash
scripts/run/heavy scripts/run/py scripts/audio/measure_voice_polish.py outputs/voice-polish-chain
```

Use the cached models from [Setup](../README.md#setup); the command downloads nothing. Audio and full receipts follow the repository’s [output retention rule](../README.md#layout-and-runtime). This is an explicit experiment, separate from the model-free test suite. The script exits nonzero if an existing gate fails, a word falls back, or the raw recognition word-error count changes.

## Measurement

The 26.649-second passage contains six sentences and 67 words. Each synthesized sentence is followed by 0.5 seconds of known silence; the measured quiet window is 0.25 to 0.05 seconds before the end of that gap. Thus these are controlled gaps between sentences, not detected pauses within words. The noisy variant adds seeded Gaussian noise with amplitude standard deviation 0.0015 and a 35 Hz sine of peak amplitude 0.004 to the same samples. Both versions use the processing path in [the voice method](../methods/voice-explainer-video.md#polish-each-take). No final localized level correction or additional loudness correction was needed.

Quiet RMS is unweighted dBFS over the same windows. “Sibilant band” is mean energy after a fourth-order Butterworth 4–10 kHz bandpass over the same speech intervals; it is a broad proxy, not isolated S phonemes or a perceptual score. LRA, integrated loudness and true peak are measured from final PCM24 through the production FFmpeg meter. Word errors are token-level Levenshtein substitutions + insertions + deletions on the raw ASR output.

| Condition | Quiet RMS dBFS | Speech 4–10 kHz dBFS | LRA LU | Integrated LUFS | True peak dBTP | ASR word errors | Fallback words | Gate flags |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| clean / before | digital silence | -29.55 | 2.0 | -16.32 | -1.50 | 0 | 0 | 0 |
| clean / after | digital silence | -30.49 | 2.1 | -16.25 | -1.50 | 0 | 0 | 0 |
| added noise / before | -43.04 | -29.50 | 2.0 | -16.30 | -1.50 | 0 | 0 | 0 |
| added noise / after | -53.07 | -30.45 | 2.1 | -16.28 | -1.50 | 0 | 0 | 0 |

All four outputs contain 1,279,136 frames at 48 kHz. The gate flags above come from `audio_checks` and strict fallback checking, using the existing thresholds in [`narrate_film.py`](../scripts/audio/narrate_film.py).

## Preset

| Parameter | Default | Allowed range |
|---|---:|---:|
| `highpass_hz` | 70 | 40–120 |
| `expander_threshold_dbfs` | -45 | -70–-25 |
| `expander_ratio` | 1.5 | 1–3 |
| `expander_range_db` | -12 | -24–0 |
| `expander_attack_ms` | 5 | 1–50 |
| `expander_release_ms` | 100 | 20–500 |
| `deesser_intensity` | 0.35 | 0–0.5 |
| `deesser_max` | 0.25 | 0–0.5 |
| `deesser_frequency` | 0.5 | 0–1 |
| `presence_hz` | 3500 | 2000–4500 |
| `presence_gain_db` | 0.5 | 0–3 |
| `presence_q` | 1 | 0.5–2 |
| `compressor_threshold_dbfs` | -18 | -30–-6 |
| `compressor_ratio` | 1.5 | 1–3 |
| `compressor_attack_ms` | 20 | 5–50 |
| `compressor_release_ms` | 150 | 50–500 |
| `limiter_dbfs` | -1.6 | -6–-1.5 |
| `limiter_attack_ms` | 5 | 1–10 |
| `limiter_release_ms` | 50 | 20–200 |

Both dynamics stages use RMS detection and unity makeup. The high-pass has two poles. The limiter runs at four times the take’s sample rate with automatic makeup off and latency compensation on.

## Tuning and interpretation

The initial preset used de-esser intensity 0.15 and a +1 dB presence boost. It passed the same gates, but the noisy sample’s 4–10 kHz energy rose from −29.50 to −28.51 dBFS. That did not support a sibilance-reduction claim. Fixed-fixture probes found intensity 0.5 too aggressive for a conservative starting point (about 7 dB band reduction at matched loudness). The [preset above](#preset) records the resulting settings.

## Tests and remaining questions

The full suite passes with 170 audio tests, 16 film tests, 8 storyboard tests and 28 run-tool tests, for 222 distinct tests with no skips. The three `test_linux_levels.RealFilterTests` probes also pass when rerun explicitly from `scripts/audio` with `RUN_FFMPEG_LEVEL_TESTS=1`.

No test or gate is removed or relaxed. The earlier cache-test change preserves the bypass guarantee in `test_bypassed_mac_and_kokoro_identity_preserves_legacy_hash`; `test_default_clone_invalidates_old_take_identity_on_both_platforms` and the effective-settings test cover enabled processing. The measured graph and settings match the implementation.

The short fixture’s band-energy, recognition and loudness-range results do not establish preserved timbre, breath character, long-form delivery or listener preference. Reference clones on both backends, low-register voices, other languages, longer expressive delivery and human listening comparisons remain unvalidated. The trial cannot justify enabling polish for every stock engine.
