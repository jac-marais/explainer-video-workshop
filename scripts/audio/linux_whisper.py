"""Offline CPU adapter for the large-v3-turbo word-timestamp interface."""
import functools
from dataclasses import replace
import os

MODEL = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
SAMPLE_RATE = 16000
# mlx-whisper 0.4.3 transcribe() default; retry failed decodes with warmer sampling.
TEMPERATURES = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
DECODE_POLICY = "mlx-whisper-0.4.3-single-sample-224-last-fallback-v1"


@functools.cache
def model():
    from faster_whisper import WhisperModel
    engine = WhisperModel(MODEL, device="cpu", compute_type="float32", local_files_only=True,
                          cpu_threads=min(8, os.cpu_count() or 1))
    install_reference_fallback(engine)
    return engine


def install_reference_fallback(engine):
    """Keep MLX's retry decisions around this instance's public decoder method."""
    generate = engine.generate_with_fallback

    @functools.wraps(generate)
    def reference_fallback(encoder_output, prompt, tokenizer, options):
        if not options.temperatures:
            raise ValueError("Whisper needs at least one decoding temperature")
        for temperature in options.temperatures:
            # TranscriptionOptions is a dataclass. The caller's options and every
            # unrelated field stay intact; a single attempt cannot pick a prior result.
            attempted = generate(encoder_output, prompt, tokenizer,
                                 replace(options, temperatures=[temperature]))
            result, avg_logprob, _, compression_ratio = attempted
            retry = ((options.compression_ratio_threshold is not None
                      and compression_ratio > options.compression_ratio_threshold)
                     or (options.log_prob_threshold is not None
                         and avg_logprob < options.log_prob_threshold))
            if options.no_speech_threshold is not None and result.no_speech_prob > options.no_speech_threshold:
                retry = False
            if not retry:
                break
        return attempted

    engine.generate_with_fallback = reference_fallback


def load_audio(path):
    from faster_whisper.audio import decode_audio
    return decode_audio(path, sampling_rate=SAMPLE_RATE)


def transcribe(audio, *, path_or_hf_repo=None, language, word_timestamps=True,
               condition_on_previous_text=False):
    segments, info = model().transcribe(audio, language=language, word_timestamps=word_timestamps,
                                       condition_on_previous_text=condition_on_previous_text,
                                       beam_size=1, best_of=1, max_new_tokens=224,
                                       temperature=TEMPERATURES, vad_filter=False)
    return {"language": info.language, "segments": [
        {"text": segment.text, "start": segment.start, "end": segment.end,
         "words": [{"word": word.word, "start": word.start, "end": word.end,
                    "probability": word.probability} for word in (segment.words or [])]}
        for segment in segments]}
