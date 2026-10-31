"""CPU dispatch preserves voice choices, offline loading, and word timestamps."""
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import tempfile
from unittest.mock import Mock, patch

import linux_speech
import linux_whisper


class CpuSpeechTests(unittest.TestCase):
    def tearDown(self):
        linux_whisper.model.cache_clear()

    def test_whisper_is_offline_cpu_turbo_and_retains_word_times(self):
        word = SimpleNamespace(word=" Garden", start=1.25, end=1.7, probability=.98)
        segment = SimpleNamespace(text=" Garden", start=1., end=2., words=[word])
        engine = Mock()
        engine.transcribe.return_value = (iter([segment]), SimpleNamespace(language="en"))
        constructor = Mock(return_value=engine)
        with patch.dict(sys.modules, {"faster_whisper": SimpleNamespace(WhisperModel=constructor)}):
            result = linux_whisper.transcribe("example.wav", language="en")
        self.assertEqual(constructor.call_args.args, (linux_whisper.MODEL,))
        self.assertEqual(constructor.call_args.kwargs["device"], "cpu")
        self.assertTrue(constructor.call_args.kwargs["local_files_only"])
        self.assertEqual(result["segments"][0]["words"],
                         [{"word": " Garden", "start": 1.25, "end": 1.7, "probability": .98}])
        self.assertTrue(engine.transcribe.call_args.kwargs["word_timestamps"])
        self.assertFalse(engine.transcribe.call_args.kwargs["condition_on_previous_text"])
        self.assertEqual(engine.transcribe.call_args.kwargs["temperature"], (0.0, 0.2, 0.4, 0.6, 0.8, 1.0))
        self.assertEqual(engine.transcribe.call_args.kwargs["beam_size"], 1)
        self.assertEqual(engine.transcribe.call_args.kwargs["best_of"], 1)
        self.assertEqual(engine.transcribe.call_args.kwargs["max_new_tokens"], 224)
        self.assertFalse(engine.transcribe.call_args.kwargs["vad_filter"])

    def test_decoder_reads_final_pcm_format_at_whisper_rate(self):
        import numpy as np
        import soundfile as sf
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.wav"
            sf.write(path, np.zeros(48000, dtype="float32"), 48000, subtype="PCM_24")
            samples = linux_whisper.load_audio(str(path))
        self.assertEqual(samples.shape, (16000,))
        self.assertEqual(samples.dtype, np.float32)
        self.assertTrue(np.isfinite(samples).all())

    def test_qwen_maps_only_corresponding_full_precision_models(self):
        for size in ("0.6", "1.7"):
            for kind in ("Base", "CustomVoice"):
                name = f"Qwen3-TTS-12Hz-{size}B-{kind}"
                self.assertEqual(linux_speech.qwen_model_id(f"mlx-community/{name}-bf16"), f"Qwen/{name}")
                self.assertEqual(linux_speech.qwen_model_id(f"Qwen/{name}"), f"Qwen/{name}")
        with self.assertRaisesRegex(SystemExit, "No faithful CPU mapping"):
            linux_speech.qwen_model_id("mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-4bit")

    def test_linux_dispatch_keeps_preset_and_chunk_settings(self):
        path = Path(__file__).resolve().parents[2] / "templates/voice/voice.py"
        spec = importlib.util.spec_from_file_location("voice_dispatch", path)
        voice = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(voice)
        settings = {"model": "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16", "speaker": "Serena", "lang": "chinese"}
        with patch.object(sys, "platform", "linux"), patch.object(linux_speech, "load_qwen3", return_value=("synth", "identity")) as loader:
            self.assertEqual(voice.load_qwen3(settings, 17, {}, 250), ("synth", "identity"))
            loader.assert_called_once_with(settings, 17, {}, 250)

    def test_qwen_cpu_preserves_all_sampling_and_chunk_seeds(self):
        import numpy as np
        settings = {"model": "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16",
                    "speaker": "Serena", "lang": "chinese"}
        engine = Mock()
        engine.get_supported_speakers.return_value = ["serena"]
        engine.generate_custom_voice.return_value = ([np.ones(24, dtype="float32")], 24000)
        constructor = Mock(return_value=engine)
        torch = SimpleNamespace(float32="float32", manual_seed=Mock())
        sampling = {"temperature": .7, "top_p": .9, "top_k": 50, "repetition_penalty": 1.1}
        modules = {"torch": torch, "qwen_tts": SimpleNamespace(Qwen3TTSModel=SimpleNamespace(from_pretrained=constructor)),
                   "huggingface_hub": SimpleNamespace(snapshot_download=Mock(return_value="cached/revision")),
                   "voice": SimpleNamespace(CHUNK_PAUSE=.25, MLX_SAMPLING=sampling, QWEN3_LANG="english",
                                            sha256_file=Mock(), split_chunks=lambda text, limit: ["First.", "Second."])}
        with patch.dict(sys.modules, modules), patch.object(linux_speech, "version", return_value="test"):
            synthesize, identity = linux_speech.load_qwen3(settings, 11, {}, 1)
            samples, rate, extra = synthesize("First. Second.")
        modules["huggingface_hub"].snapshot_download.assert_called_once_with(
            "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", local_files_only=True)
        self.assertEqual(constructor.call_args.kwargs,
                         {"device_map": "cpu", "dtype": "float32", "attn_implementation": "eager", "local_files_only": True})
        self.assertEqual([call.args[0] for call in torch.manual_seed.call_args_list], [11, 12])
        self.assertEqual((rate, len(samples), extra["chunks"]), (24000, 6048, 2))
        for call in engine.generate_custom_voice.call_args_list:
            for key, value in sampling.items():
                self.assertEqual(call.kwargs[key], value)
            self.assertEqual(call.kwargs["subtalker_temperature"], .7)
            self.assertEqual(call.kwargs["subtalker_top_p"], .9)
            self.assertEqual(call.kwargs["subtalker_top_k"], 50)
            self.assertEqual(call.kwargs["speaker"], "serena")
            self.assertEqual(call.kwargs["language"], "chinese")
            self.assertEqual(call.kwargs["max_new_tokens"], 4096)
            self.assertFalse(call.kwargs["non_streaming_mode"])
            self.assertTrue(call.kwargs["do_sample"])
            self.assertTrue(call.kwargs["subtalker_dosample"])
        self.assertEqual(identity["settings"]["speaker"], "Serena")
        self.assertFalse(identity["settings"]["non_streaming_mode"])
        self.assertEqual(identity["settings"]["repetition_penalty"], 1.1)
        self.assertEqual(identity["settings"]["subtalker_temperature"], .7)
        self.assertEqual(identity["settings"]["max_new_tokens"], 4096)


    def test_qwen_clone_matches_icl_conditioning_and_effective_penalty(self):
        import numpy as np
        settings = {"model": "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16", "lang": "english"}
        for configured, effective in [(1.1, 1.5), (1.8, 1.8)]:
            with self.subTest(configured=configured), tempfile.TemporaryDirectory() as directory:
                reference = Path(directory) / "reference.txt"
                reference.write_text("A reference sentence.\n")
                refs = {"ref_audio": Path(directory) / "reference.wav", "ref_text": reference}
                engine = Mock()
                engine.generate_voice_clone.return_value = ([np.ones(24, dtype="float32")], 24000)
                torch = SimpleNamespace(float32="float32", manual_seed=Mock())
                sampling = {"temperature": .7, "top_p": .9, "top_k": 50, "repetition_penalty": configured}
                modules = {"torch": torch,
                           "qwen_tts": SimpleNamespace(Qwen3TTSModel=SimpleNamespace(from_pretrained=Mock(return_value=engine))),
                           "huggingface_hub": SimpleNamespace(snapshot_download=Mock(return_value="cached/revision")),
                           "voice": SimpleNamespace(CHUNK_PAUSE=.25, MLX_SAMPLING=sampling, QWEN3_LANG="english",
                                                    sha256_file=lambda path: "example-hash", split_chunks=lambda text, limit: [text])}
                with patch.dict(sys.modules, modules), patch.object(linux_speech, "version", return_value="test"):
                    synthesize, identity = linux_speech.load_qwen3(settings, 11, refs, 400)
                    synthesize("An example sentence.")
                kwargs = engine.generate_voice_clone.call_args.kwargs
                self.assertEqual(kwargs["ref_audio"], str(refs["ref_audio"]))
                self.assertEqual(kwargs["ref_text"], "A reference sentence.")
                self.assertEqual(kwargs["text"], "An example sentence.")
                self.assertEqual(kwargs["language"], "english")
                self.assertTrue(kwargs["non_streaming_mode"])
                self.assertFalse(kwargs["x_vector_only_mode"])
                self.assertEqual(kwargs["repetition_penalty"], effective)
                for key in ("temperature", "top_p", "top_k"):
                    self.assertEqual(kwargs[key], sampling[key])
                    self.assertEqual(kwargs["subtalker_" + key], sampling[key])
                for key in ("non_streaming_mode", "x_vector_only_mode", "repetition_penalty",
                            "do_sample", "subtalker_dosample", "subtalker_temperature",
                            "subtalker_top_p", "subtalker_top_k", "max_new_tokens"):
                    self.assertEqual(identity["settings"][key], kwargs[key])
                self.assertEqual(sampling["repetition_penalty"], configured)
                engine.generate_custom_voice.assert_not_called()

    def test_cut_model_matches_selected_platform(self):
        path = Path(__file__).resolve().parents[2] / "templates/voice/cut_takes.py"
        for platform, expected in [("linux", linux_whisper.MODEL),
                                   ("darwin", "mlx-community/whisper-large-v3-turbo")]:
            with self.subTest(platform=platform), patch.object(sys, "platform", platform):
                spec = importlib.util.spec_from_file_location("cut_dispatch", path)
                cut = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(cut)
                self.assertEqual(cut.WHISPER, expected)


class WhisperFallbackTests(unittest.TestCase):
    def options(self, **changes):
        from dataclasses import fields
        from inspect import signature
        from faster_whisper import WhisperModel
        from faster_whisper.transcribe import TranscriptionOptions

        defaults = signature(WhisperModel.transcribe).parameters
        values = {field.name: defaults[field.name].default
                  for field in fields(TranscriptionOptions) if field.name != "temperatures"}
        values.update(temperatures=list(linux_whisper.TEMPERATURES), beam_size=1, best_of=1, max_new_tokens=224)
        values.update(changes)
        return TranscriptionOptions(**values)

    def test_first_success_preserves_options_other_arguments_and_return_object(self):
        import copy
        from dataclasses import asdict
        options = self.options()
        before = copy.deepcopy(asdict(options))
        result = (SimpleNamespace(no_speech_prob=.1), -.2, 0., 1.)
        original = Mock(return_value=result)
        engine = SimpleNamespace(generate_with_fallback=original)
        untouched = SimpleNamespace(generate_with_fallback=original)
        encoder, prompt, tokenizer = object(), [1, 2], object()
        linux_whisper.install_reference_fallback(engine)
        self.assertIs(engine.generate_with_fallback(encoder, prompt, tokenizer, options), result)
        self.assertEqual(asdict(options), before)
        self.assertIs(untouched.generate_with_fallback, original)
        self.assertEqual(original.call_count, 1)
        passed = original.call_args.args
        self.assertIs(passed[0], encoder)
        self.assertIs(passed[1], prompt)
        self.assertIs(passed[2], tokenizer)
        self.assertIsNot(passed[3], options)
        actual = asdict(passed[3]); actual["temperatures"] = before["temperatures"]
        self.assertEqual(actual, before)
        self.assertEqual(passed[3].temperatures, [0.])

    def test_all_fail_returns_last_attempt_instead_of_highest_score(self):
        options = self.options()
        attempts = [(SimpleNamespace(no_speech_prob=.1), -.1-index, temperature, 3.)
                    for index, temperature in enumerate(options.temperatures)]
        original = Mock(side_effect=attempts)
        engine = SimpleNamespace(generate_with_fallback=original)
        linux_whisper.install_reference_fallback(engine)
        self.assertIs(engine.generate_with_fallback(object(), [], object(), options), attempts[-1])
        self.assertEqual([call.args[3].temperatures for call in original.call_args_list],
                         [[temperature] for temperature in options.temperatures])
        self.assertEqual(options.temperatures, list(linux_whisper.TEMPERATURES))

    def test_high_no_speech_stops_independently_of_log_probability(self):
        for logprob in (-10., 0.):
            with self.subTest(logprob=logprob):
                result = (SimpleNamespace(no_speech_prob=.9), logprob, 0., 3.)
                original = Mock(return_value=result)
                engine = SimpleNamespace(generate_with_fallback=original)
                linux_whisper.install_reference_fallback(engine)
                self.assertIs(engine.generate_with_fallback(object(), [], object(), self.options()), result)
                self.assertEqual(original.call_count, 1)

    def test_disabled_thresholds_and_logprob_retry(self):
        first = (SimpleNamespace(no_speech_prob=.1), -2., 0., 1.)
        second = (SimpleNamespace(no_speech_prob=.1), -.1, .2, 1.)
        original = Mock(side_effect=[first, second])
        engine = SimpleNamespace(generate_with_fallback=original)
        linux_whisper.install_reference_fallback(engine)
        self.assertIs(engine.generate_with_fallback(object(), [], object(), self.options()), second)
        self.assertEqual(original.call_count, 2)
        original.reset_mock(side_effect=True); original.return_value = first
        self.assertIs(engine.generate_with_fallback(object(), [], object(), self.options(
            compression_ratio_threshold=None, log_prob_threshold=None, no_speech_threshold=None)), first)
        self.assertEqual(original.call_count, 1)


class RepetitionWindowTests(unittest.TestCase):
    def test_excludes_prefix_and_penalizes_unique_generated_ids_once(self):
        import torch
        from transformers import LogitsProcessorList

        penalty = linux_speech.RecentTokenRepetitionPenalty(2.0)
        processors = LogitsProcessorList([penalty])
        scores = torch.tensor([[4., -3., 2., -5., 6.]])
        torch.testing.assert_close(processors(torch.tensor([[3, 4]]), scores), scores)
        result = processors(torch.tensor([[3, 4, 0, 0, 1, 99]]), scores)
        torch.testing.assert_close(result, torch.tensor([[2., -6., 2., -5., 6.]]))
        torch.testing.assert_close(scores, torch.tensor([[4., -3., 2., -5., 6.]]))

    def test_window_is_last_64_generated_ids_and_independent_per_row(self):
        import torch

        penalty = linux_speech.RecentTokenRepetitionPenalty(2.0)
        scores = torch.tensor([[2., 4., 6., -8.], [2., 4., 6., -8.]])
        penalty(torch.empty((2, 0), dtype=torch.long), scores)
        ids = torch.tensor([[2, 3] + [1] * 63, [3, 2] + [0] * 63])
        result = penalty(ids, scores)
        # The first ID is outside the window; its distinct successor is inside.
        torch.testing.assert_close(result, torch.tensor([[2., 2., 6., -16.], [1., 4., 3., -8.]]))

    def test_wrapper_preserves_arguments_and_processors_and_resets_each_call(self):
        import torch

        original = Mock(return_value="generated")
        untouched = SimpleNamespace(generate=original)
        talker = SimpleNamespace(generate=original)
        linux_speech.install_qwen_repetition_window(talker)
        prior = [lambda input_ids, scores: scores]
        self.assertEqual(talker.generate(inputs_embeds="embedding-prompt", repetition_penalty=1.5,
                                        logits_processor=prior, top_k=50, temperature=.7,
                                        min_new_tokens=2), "generated")
        first = original.call_args.kwargs
        self.assertEqual(first["repetition_penalty"], 1.0)
        self.assertEqual(first["min_new_tokens"], 0)
        self.assertEqual(first["inputs_embeds"], "embedding-prompt")
        self.assertEqual((first["top_k"], first["temperature"]), (50, .7))
        self.assertEqual(first["logits_processor"][:-1], prior)
        self.assertEqual(len(prior), 1)
        processor = first["logits_processor"][-1]
        self.assertEqual(processor.penalty, 1.5)
        processor(torch.empty((1, 0), dtype=torch.long), torch.tensor([[3., -3.]]))
        torch.testing.assert_close(processor(torch.tensor([[0]]), torch.tensor([[3., -3.]])),
                                   torch.tensor([[2., -3.]]))
        talker.generate(inputs_embeds="new-prompt", repetition_penalty=1.5)
        fresh = original.call_args.kwargs["logits_processor"][-1]
        self.assertIsNot(fresh, processor)
        self.assertIsNone(fresh.prefix_length)
        self.assertIs(untouched.generate, original)

    def test_loader_installs_only_on_loaded_talker(self):
        from types import SimpleNamespace
        engine = Mock()
        engine.get_supported_speakers.return_value = ["serena"]
        modules = {"torch": SimpleNamespace(float32="float32"),
                   "qwen_tts": SimpleNamespace(Qwen3TTSModel=SimpleNamespace(from_pretrained=Mock(return_value=engine))),
                   "huggingface_hub": SimpleNamespace(snapshot_download=Mock(return_value="cached/revision")),
                   "voice": SimpleNamespace(CHUNK_PAUSE=.25,
                        MLX_SAMPLING={"temperature": .7, "top_p": .9, "top_k": 50, "repetition_penalty": 1.1},
                        QWEN3_LANG="english", sha256_file=Mock(), split_chunks=Mock())}
        with patch.dict(sys.modules, modules), patch.object(linux_speech, "version", return_value="test"), \
                patch.object(linux_speech, "install_qwen_repetition_window") as install:
            _, identity = linux_speech.load_qwen3(
                {"model": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", "speaker": "serena"}, 11, {}, 400)
        install.assert_called_once_with(engine.model.talker)
        self.assertEqual(identity["settings"]["repetition_context_size"], 64)
        self.assertEqual(identity["settings"]["repetition_scope"], "generated_tokens")
        self.assertEqual(identity["settings"]["min_new_tokens"], 0)


class ReuseBackendTests(unittest.TestCase):
    def test_bypassed_mac_and_kokoro_identity_preserves_legacy_hash(self):
        import narrate_film as film
        for engine in ("kokoro", "qwen3", "qwen3-preset"):
            voice = {"engine": engine, "model": "example-model", "ref_audio": "reference.wav"}
            refs = {"ref_audio": hashlib.sha256(b"reference bytes").hexdigest()}
            legacy = hashlib.sha256(json.dumps({"voice": "example", "spec": voice, "refs": refs},
                                                sort_keys=True).encode()).hexdigest()
            with tempfile.TemporaryDirectory() as directory:
                profile = Path(directory)
                (profile / "voice.json").write_text(json.dumps({"voices": {"example": voice}, "voice_polish": {"enabled": False}}))
                (profile / "reference.wav").write_bytes(b"reference bytes")
                for platform in ("darwin", "linux"):
                    with self.subTest(engine=engine, platform=platform), \
                            patch.object(film, "VOICE_DIR", profile), patch.object(sys, "platform", platform):
                        _, identity = film.voice_identity("example")
                        if platform == "linux" and engine != "kokoro":
                            self.assertNotEqual(identity, legacy)
                        else:
                            self.assertEqual(identity, legacy)

    def test_partial_edit_reuses_only_takes_from_same_qwen_backend(self):
        import narrate_film as film
        for engine in ("qwen3", "qwen3-preset"):
            voice = {"engine": engine, "model": "example-model"}
            with tempfile.TemporaryDirectory() as directory:
                profile = Path(directory)
                (profile / "voice.json").write_text(json.dumps({"voices": {"example": voice}}))
                identities = {}
                for platform in ("darwin", "linux"):
                    with patch.object(film, "VOICE_DIR", profile), patch.object(sys, "platform", platform):
                        identities[platform] = film.voice_identity("example")[1]
                current = [{"id": "a", "scene_id": "opening", "key": film.cache_key(identities["linux"], "Hello.")},
                           {"id": "b", "scene_id": "ending", "key": film.cache_key(identities["linux"], "Changed.")}]
                for platform in ("darwin", "linux"):
                    old = film.ReuseSource(profile,
                        {"a": film.cache_key(identities[platform], "Hello."),
                         "b": film.cache_key(identities[platform], "Goodbye.")},
                        {"a": "take-a", "b": "take-b"}, {"a": "opening", "b": "ending"},
                        {"a": profile / "a.wav", "b": profile / "b.wav"})
                    with self.subTest(engine=engine, source_platform=platform):
                        reused = film.decide_reuse(current, engine, [old])
                        self.assertEqual(set(reused.audio), {"a"} if platform == "linux" else set())


if __name__ == "__main__":
    unittest.main()
