"""Reuse eSpeak's library wrapper across backend settings for each language."""
import functools

from phonemizer.backend import EspeakBackend
from phonemizer.backend.base import BaseBackend
from phonemizer.backend.espeak.base import BaseEspeakBackend
from phonemizer.backend.espeak.wrapper import EspeakWrapper


@functools.cache
def espeak_wrapper(language: str):
    return EspeakWrapper()


class CachedBaseEspeakBackend(BaseEspeakBackend):
    def __init__(self, language, punctuation_marks=None, preserve_punctuation=False, logger=None):
        self._espeak = espeak_wrapper(self._cache_language)
        BaseBackend.__init__(self, language, punctuation_marks=punctuation_marks,
                             preserve_punctuation=preserve_punctuation, logger=logger)

    def is_available(self):
        return True

    def version(self):
        return self._espeak.version

    def _init_language(self, language):
        if language not in {voice.language for voice in self._espeak.available_voices()}:
            raise RuntimeError(f'language "{language}" is not supported by the {self.name()} backend')
        return language


class CachedEspeakBackend(EspeakBackend, CachedBaseEspeakBackend):
    # The intermediate base keeps upstream phonemization while skipping its redundant library probes.
    def __init__(self, language, *, cache_language=None, **options):
        self._cache_language = cache_language or language
        super().__init__(language, **options)


@functools.cache
def tokenizer_backend(language: str):
    return CachedEspeakBackend(language, preserve_punctuation=True, with_stress=True)
