# Voice polish claim map

The proposal was decomposed before implementation on 2026-10-31. Source receipts are in the [source map](source-map.md#voice-polish-sources). A linked proposition is stated at its operating or measurement home; its evidence and status remain here.

| claim_id | Proposition, units and conditions | Source and exact locator | Status | Planned use | Check |
|---|---|---|---|---|---|
| C-VP-001 | A high-pass attenuates frequencies below its cutoff, with a finite slope, rather than removing all of them. | S-VP-001, `highpass`, frequency and poles | supported | Method purpose | Inspect filter graph and low-frequency test |
| C-VP-002 | A cutoff near 100 Hz can reduce low-frequency rumble but is not appropriate for every voice. | S-VP-002, “The spectrum of speech”; S-VP-003, p. 8 “Bass Rolloff” | qualified | Adjustable cutoff | Compare low-register speech and rumble |
| C-VP-003 | “Almost none of your voice is below 100 Hz” is not a safe generalization; male fundamentals can fall outside the typical 100–120 Hz range. | S-VP-002, “The spectrum of speech” | disputed | Drop original; retain qualification | Read source, preserve low voice body |
| C-VP-004 | Downward expansion attenuates signals below a threshold; low ratios give gentler attenuation than a hard gate. | S-VP-004, printed p. 9, Expander/Gate; S-VP-001, `agate` mode/ratio | supported | Method purpose | Quiet-interval RMS and graph test |
| C-VP-005 | Fan noise, breaths and keyboard sounds are workshop examples of the below-threshold signals in C-VP-004. Quiet speech can also be suppressed. | S-VP-004, printed p. 9 threshold warning | qualified | Conditional benefit and caution | Quiet-word ASR and listening comparison |
| C-VP-006 | De-essing reduces excessive high-frequency sibilance, commonly in roughly 4–10 kHz. It does not guarantee that all other speech is unchanged. | S-VP-004, printed p. 8 De-Esser and p. 12 “Lispy Vocals”; S-VP-001, `deesser` | qualified | Method purpose | 4–10 kHz energy plus ASR |
| C-VP-007 | The 2–4 kHz region carries important consonant information; a 3.5 kHz boost may help deficient material, not every recording. | S-VP-002, “Executive summary” and “Important frequencies” | qualified | Adjustable presence EQ | Measure band change; check clarity |
| C-VP-008 | Exactly 3.5 kHz and a small boost are useful universal settings. | No universal evidence; workshop inference for starting parameters | assumption | Drop universality; label preset a design choice | Per-voice comparison |
| C-VP-009 | Some broadcast vocal microphones have a presence switch; the SM7B is one example, not proof of an exact 3.5 kHz bell response. | S-VP-003, pp. 7–9 “Adjust the Frequency Response Switches” | supported | Evidence ledger only | Read manufacturer guide |
| C-VP-010 | Downward compression reduces level above threshold and reduces dynamic contrast; excessive compression can flatten delivery. | S-VP-001, `acompressor` introduction and mode/threshold/ratio; S-VP-004 printed p. 8 Compressor | supported | Method purpose | Loudness range and sentence-level checks |
| C-VP-011 | Compression alone always raises quiet noise. | S-VP-001, `acompressor` makeup; S-VP-004 printed p. 11 “Noise Rushups, Hiss Buildup” | disputed | Replace with makeup/final gain qualification | Compare fixed gain with makeup disabled |
| C-VP-012 | See the gain rationale in [the ordering rule](../methods/voice-explainer-video.md#polish-order). | S-VP-001, `acompressor` makeup; S-VP-004 printed p. 11 | qualified | Ordering rationale | Noise RMS at matched final loudness |
| C-VP-013 | Expansion must precede compression in every valid voice chain. | S-VP-004, printed p. 9, Expander/Gate | disputed | Drop universality | Read counterexample |
| C-VP-014 | See [the workshop ordering rule](../methods/voice-explainer-video.md#polish-order). | Workshop inference from C-VP-004/010/012 | design choice | Enforced order rule | Assert graph stage order |
| C-VP-015 | A lookahead limiter bounds peaks at its processing rate; it cannot repair earlier clipping or guarantee encoded true peak. | S-VP-001, `alimiter` introduction, limit, latency and oversampling advice; workshop inference on earlier clipping | qualified | Preserve final true-peak gate | Oversampled limiter, remeasure final PCM |
| C-VP-016 | Reference-conditioned cloning can inherit recording artifacts, but does not reproduce reference acoustics exactly. The evidence is vendor-specific; applying this risk to local engines is a workshop inference. | S-VP-005, “Instant Voice Cloning” and opening “What voice cloning does not do” | qualified | Correct existing method overstatement | Check the vendor scope. |
| C-VP-017 | Every TTS engine copies rumble, hiss, breaths and sibilance from a reference. | S-VP-005, “Instant Voice Cloning”; its reference-conditioned scope does not cover stock engines, which need no user reference. | disputed | Drop generalization | Distinguish stock from reference engines |
| C-VP-018 | See [the default and override rule](../methods/voice-explainer-video.md#polish-each-take). | Workshop inference from C-VP-016 | design choice | Provisional default; narrow if trial fails | Config tests and synthetic narration comparison |

Post-implementation checks add locally reproduced claims without changing the proposal ledger above.

| claim_id | Proposition, units and conditions | Source and exact locator | Status | Planned use | Check |
|---|---|---|---|---|---|
| C-VP-019 | See [the measured comparison](voice-polish-measurements.md#measurement). | [Trial](voice-polish-measurements.md#measurement); `scripts/audio/measure_voice_polish.py:measure` | supported | Report only, scoped to fixture | Reproduce offline trial |
| C-VP-020 | See [the test results](voice-polish-measurements.md#tests-and-remaining-questions). | [Trial](voice-polish-measurements.md#tests-and-remaining-questions); four unittest discovery groups in `scripts/README.md` | supported | Validation report | Rerun checks and full suite |
