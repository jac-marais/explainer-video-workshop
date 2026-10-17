"""Offline CPU adapter for the large-v3-turbo word-timestamp interface."""
import functools
import os

MODEL = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
SAMPLE_RATE = 16000
# mlx-whisper 0.4.3 transcribe() default; retry failed decodes with warmer sampling.
TEMPERATURES = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)


@functools.cache
def model():
    from faster_whisper import WhisperModel
    return WhisperModel(MODEL, device="cpu", compute_type="float32", local_files_only=True,
                        cpu_threads=min(8, os.cpu_count() or 1))


def load_audio(path):
    from faster_whisper.audio import decode_audio
    return decode_audio(path, sampling_rate=SAMPLE_RATE)


def transcribe(audio, *, path_or_hf_repo=None, language, word_timestamps=True,
               condition_on_previous_text=False):
    segments, info = model().transcribe(audio, language=language, word_timestamps=word_timestamps,
                                       condition_on_previous_text=condition_on_previous_text,
                                       beam_size=1, temperature=TEMPERATURES, vad_filter=False)
    return {"language": info.language, "segments": [
        {"text": segment.text, "start": segment.start, "end": segment.end,
         "words": [{"word": word.word, "start": word.start, "end": word.end,
                    "probability": word.probability} for word in (segment.words or [])]}
        for segment in segments]}
