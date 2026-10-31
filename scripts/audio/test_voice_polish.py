"""Voice chain configuration, integration, reuse and real-filter regressions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf

import narrate_film as film
import voice_polish as polish


class ConfigurationTests(unittest.TestCase):
    def test_reference_engines_only_and_explicit_bypass(self):
        for engine in ('qwen3', 'chatterbox', 'kokoro', 'qwen3-preset'):
            with self.subTest(engine=engine):
                self.assertEqual(polish.resolve({}, {'engine': engine})['enabled'],
                                 engine in ('qwen3', 'chatterbox'))
                self.assertFalse(polish.resolve({'voice_polish': {'enabled': True}},
                    {'engine': engine, 'voice_polish': {'enabled': False}})['enabled'])

    def test_profile_then_voice_override_and_every_bound(self):
        settings = polish.resolve({'voice_polish': {'highpass_hz': 90}},
                                  {'engine': 'qwen3', 'voice_polish': {'highpass_hz': 60}})
        self.assertEqual(settings['highpass_hz'], 60)
        for key, (_, lower, upper) in polish.PARAMETERS.items():
            for value in (lower, upper):
                self.assertEqual(polish.resolve({'voice_polish': {key: value}},
                                                {'engine': 'kokoro'})[key], value)
            for value in (lower - 1, upper + 1, float('nan'), float('inf'), True, '1'):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    polish.resolve({'voice_polish': {key: value}}, {'engine': 'kokoro'})
        for value in ({'enabled': 1}, {'typo': 1}, None):
            with self.assertRaises(ValueError):
                polish.resolve({'voice_polish': value}, {'engine': 'kokoro'})

    def test_all_stages_order_and_no_automatic_makeup(self):
        for override in ({}, {'highpass_hz': 60, 'presence_gain_db': 0, 'compressor_ratio': 1}):
            settings = polish.resolve({}, {'engine': 'qwen3', 'voice_polish': override})
            graph = polish.filter_graph(settings, 24000)
            names = [part.split('=')[0] for part in graph.split(',')]
            self.assertEqual(names, ['highpass', 'agate', 'deesser', 'equalizer',
                                    'acompressor', 'aresample', 'alimiter', 'aresample'])
            self.assertLess(names.index('agate'), names.index('acompressor'))
            self.assertEqual(graph.count('makeup=1'), 2)
            self.assertIn('level=false:latency=true', graph)
            self.assertIn('aresample=96000', graph)
        self.assertEqual(polish.filter_graph({'enabled': False}, 24000), '')

    def test_effective_global_settings_and_revision_invalidate_enabled_take_cache(self):
        with tempfile.TemporaryDirectory() as name, patch.object(film, 'VOICE_DIR', Path(name)):
            path = Path(name) / 'voice.json'
            spec = {'engine': 'kokoro'}
            def identity(settings=None):
                config = {'voices': {'stock': spec}}
                if settings is not None:
                    config['voice_polish'] = settings
                path.write_text(json.dumps(config))
                return film.voice_identity('stock')[1]
            legacy = hashlib.sha256(json.dumps({'voice': 'stock', 'spec': spec, 'refs': {}}, sort_keys=True).encode()).hexdigest()
            self.assertEqual(identity(), legacy)
            self.assertEqual(identity({'enabled': False}), legacy)
            enabled = identity({'enabled': True})
            self.assertNotEqual(enabled, legacy)
            self.assertNotEqual(identity({'enabled': True, 'highpass_hz': 60}), enabled)
            with patch.object(film, 'POLISH_REVISION', polish.REVISION + 1):
                self.assertNotEqual(identity({'enabled': True}), enabled)

    def test_default_clone_invalidates_old_take_identity_on_both_platforms(self):
        for engine in ('qwen3', 'chatterbox'):
            for platform in ('darwin', 'linux'):
                with self.subTest(engine=engine, platform=platform), tempfile.TemporaryDirectory() as name, \
                        patch.object(film, 'VOICE_DIR', Path(name)), patch.object(film.sys, 'platform', platform):
                    path = Path(name) / 'voice.json'
                    config = {'voices': {'clone': {'engine': engine}}}
                    path.write_text(json.dumps(config))
                    enabled = film.voice_identity('clone')[1]
                    config['voice_polish'] = {'enabled': False}
                    path.write_text(json.dumps(config))
                    self.assertNotEqual(enabled, film.voice_identity('clone')[1])

    def test_voice_cli_processes_each_take_before_loudness_and_records_settings(self):
        module = importlib.util.spec_from_file_location('polish_voice', film.TOOLS_DIR / 'voice.py')
        voice = importlib.util.module_from_spec(module)
        module.loader.exec_module(voice)
        for enabled in (False, True):
            with self.subTest(enabled=enabled), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                texts = [root / 'first.txt', root / 'second.txt']
                for text in texts:
                    text.write_text('The sensor measures the chamber pressure.')
                config = {'default': 'stock', 'voices': {'stock': {'engine': 'kokoro'}},
                          'voice_polish': {'enabled': enabled}}
                events = []
                def process(source, destination, settings):
                    events.append(('polish', settings['enabled']))
                    shutil.copyfile(source, destination)
                    return destination, {'enabled': settings['enabled']}
                def normalize(source, destination):
                    self.assertEqual(source.name, 'polished.wav')
                    events.append(('normalize', enabled))
                    sf.write(destination, np.zeros(24000), 24000)
                loader = lambda *args, **kwargs: (lambda text: (np.zeros(24000), 24000, {}), {'packages': {}})
                with patch.object(voice, 'load_config', return_value=config), \
                        patch.dict(voice.LOADERS, {'kokoro': loader}), \
                        patch.object(voice, 'process_take', side_effect=process), \
                        patch.object(voice, 'ffmpeg_loudnorm', side_effect=normalize), \
                        patch('sys.argv', ['voice.py', *map(str, texts), '--out-dir', str(root)]):
                    voice.main()
                self.assertEqual(events, [('polish', enabled), ('normalize', enabled)] * 2)
                for text in texts:
                    self.assertEqual(json.loads(text.with_suffix('.json').read_text())['voice_polish'], {'enabled': enabled})


@unittest.skipUnless(shutil.which('ffmpeg'), 'Requires ffmpeg')
class FilterTests(unittest.TestCase):
    def test_noise_reduction_frame_preservation_and_final_gates_at_two_rates(self):
        for rate in (24000, 48000):
            with self.subTest(rate=rate), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                source, destination, final = root / 'source.wav', root / 'polish.wav', root / 'final.wav'
                t = np.arange(rate * 8 + 137) / rate
                samples = .001 * np.sin(2 * np.pi * 35 * t)
                for start in (1, 3, 5):
                    mask = (t >= start) & (t < start + 1)
                    samples[mask] += .2 * np.sin(2 * np.pi * 400 * t[mask])
                sf.write(source, samples, rate, subtype='DOUBLE')
                original = source.read_bytes()
                path, receipt = polish.process_take(source, destination, polish.resolve({}, {'engine': 'qwen3'}))
                data, actual_rate = sf.read(path)
                self.assertEqual((len(data), actual_rate), (len(samples), rate))
                self.assertTrue(np.isfinite(data).all())
                self.assertTrue(receipt['frames_preserved'])
                quiet = (t > 2.5) & (t < 2.9)
                self.assertLess(np.mean(data[quiet] ** 2), np.mean(samples[quiet] ** 2) / 10)
                film.normalize(destination, final, preserve_take_levels=True)
                rows = [{'id': str(i), 'scene_id': str(i), 'text': 'The signal is steady.', 'spoken_text': 'The signal is steady.',
                         'start': start, 'end': start + 1.5} for i, start in enumerate((1, 3, 5))]
                asr = [{'word': word} for row in rows for word in row['text'].split()]
                flags, _ = film.audio_checks({'sentences': rows, 'duration': len(data) / rate}, final, asr, [])
                self.assertEqual(flags, [])
                self.assertEqual(source.read_bytes(), original)
                bypass, receipt = polish.process_take(source, root / 'unused.wav', {'enabled': False})
                self.assertEqual(bypass, source)
                self.assertEqual(receipt, {'enabled': False})
                self.assertFalse((root / 'unused.wav').exists())
                self.assertEqual(source.read_bytes(), original)

    def test_refuses_source_overwrite_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as name:
            source = Path(name) / 'source.wav'
            sf.write(source, np.zeros((2400, 2)), 24000)
            settings = polish.resolve({}, {'engine': 'qwen3'})
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                polish.process_take(source, source, settings)
            with self.assertRaisesRegex(ValueError, 'mono'):
                polish.process_take(source, source.with_name('output.wav'), settings)


if __name__ == '__main__':
    unittest.main()
