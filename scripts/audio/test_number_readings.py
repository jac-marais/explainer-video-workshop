"""Invented number and cut examples; no models, synthesis or network required."""
import importlib.util
import contextlib
import io
import sys
from types import SimpleNamespace
import numpy as np
import soundfile as sf
from pathlib import Path
import tempfile
import json
import unittest
from unittest.mock import Mock, patch

import narrate_film as film
from text_tokens import norm
from number_readings import HI

ROOT = Path(__file__).resolve().parents[2]


class NumberTests(unittest.TestCase):
    def test_readings_and_alignment(self):
        examples = {
            'fr': [('246', 'deux cent quarante-six'), ('81', 'quatre-vingt-un'),
                   ('71', 'soixante et onze'), ('80', 'quatre-vingts'),
                   ('3000', 'trois mille'), ('280000', 'deux cent quatre-vingt mille'),
                   ('45.06', 'quarante-cinq virgule zéro six'), ('62%', 'soixante-deux pour cent')],
            'hi': [('246', 'दो सौ छियालीस'), ('98007', 'अट्ठानवे हजार सात'),
                   ('200000', 'दो लाख'), ('45.06', 'पैंतालीस पॉइंट शून्य छह'),
                   ('62%', 'बासठ प्रतिशत')],
            'zh': [('246', '二百四十六'), ('10007', '一万零七'), ('110', '一百一十'),
                   ('200000', '二十万'), ('45.06', '四十五点零六'), ('62%', '百分之六十二')],
            'ko': [('246', '이백사십육'), ('10007', '만칠'), ('200000', '이십만'),
                   ('45.06', '사십오 점 영육'), ('62%', '육십이 퍼센트')],
        }
        for language, cases in examples.items():
            for digits, text in cases:
                with self.subTest(language=language, digits=digits):
                    self.assertIn(norm(text), film.readings(digits, language))
                    self.assertIn(norm(text), film.readings(" " + digits + ".", language))
                    sentence = {'id': 's01', 'text': text, 'spoken_text': text, 'start': 0, 'end': 2}
                    asr = [{'word': digits, 'start': 0, 'end': 2}]
                    _, fallbacks = film.align_words([sentence], asr, language)
                    self.assertEqual(fallbacks, [])
                    self.assertEqual(film.asr_differences([sentence], asr, language), [])

    def test_limits_zero_and_hindi_table(self):
        self.assertEqual(len(HI), 100)
        for lang, zero in [('fr', 'zéro'), ('hi', 'शून्य'), ('zh', '零'), ('ko', '영')]:
            self.assertEqual(film.readings('0', lang), {norm(zero)})
            self.assertTrue(film.readings('999999', lang))
            for invalid in ['1000000', '-4', 'flower', '4..2']:
                self.assertEqual(film.readings(invalid, lang), set())
        for n, word in [(29, 'उनतीस'), (49, 'उनचास'), (79, 'उनासी'), (99, 'निन्यानवे')]:
            self.assertEqual(film.readings(str(n), 'hi'), {word})

    def test_legacy_readings(self):
        for lang in ['en', 'pt', 'es']:
            self.assertEqual(film.readings('2046', lang), {'twothousandfortysix', 'twentyfortysix'})
            self.assertEqual(film.readings('1000000', lang), set())

    def test_check_only_forwards_language(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'timing.json').write_text(json.dumps({'sentences': []}))
            with patch.object(film, 'transcribe', return_value=([], 'cached')), \
                    patch.object(film, 'audio_checks', return_value=([], {})) as checks, \
                    patch.object(film, 'align_words', return_value=([], [])) as align, \
                    patch.object(film, 'report', return_value={'ok': True}), self.assertRaises(SystemExit):
                film.check_only(path, None, 'hi')
            self.assertEqual(checks.call_args.args[-1], 'hi')
            self.assertEqual(align.call_args.args[-1], 'hi')


class CutTests(unittest.TestCase):
    def modules(self):
        spec = importlib.util.spec_from_file_location('cut_test', ROOT / 'templates/voice/cut_takes.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module

    def test_unicode_matching(self):
        for cut in self.modules():
            for first, second in [('फूल', 'खिला'), ('꽃이', '피어'), ('小花', '开放'), ('A-M-S', 'done')]:
                sentences = [{'text': first}, {'text': second}]
                words = [{'word': norm(first), 'start': 0, 'end': 1}, {'word': second, 'start': 2, 'end': 3}]
                self.assertEqual(cut.sentence_bounds(sentences, words, 4), [(1, 2, True)])

    def test_cut_logs_unmatched_as_unclean_and_forwards_language(self):
        for cut in self.modules():
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                sf.write(root / 'S01.wav', np.full(24000, .1), 24000)
                (root / 'sentences.json').write_text(json.dumps([
                    {'id': 'a', 'scene': 'S01', 'text': '花'},
                    {'id': 'b', 'scene': 'S01', 'text': 'Goodbye.'}]))
                # Only a take in another language hears its unmatched English sentence again, in English.
                for language, heard in [('zh', ['zh', 'en']), ('en', ['en'])]:
                    whisper = SimpleNamespace(transcribe=lambda *a, **kw: None)
                    args = ['cut_takes.py', str(root / 'S01.wav'), '--sentences', str(root / 'sentences.json'),
                            '--out', str(root / 'cut'), '--language', language]
                    stdout = io.StringIO()
                    with self.subTest(language=language), patch.dict(sys.modules, {'mlx_whisper': whisper}), \
                            patch.object(sys, 'argv', args), \
                            patch.object(whisper, 'transcribe', return_value={'segments': [{'words': [
                                {'word': '花', 'start': .1, 'end': .3}]}]}) as transcribe, \
                            contextlib.redirect_stdout(stdout):
                        cut.main()
                        self.assertEqual([call.kwargs['language'] for call in transcribe.call_args_list], heard)
                        logs = [json.loads(line) for line in stdout.getvalue().splitlines()]
                        self.assertEqual(logs[0]['unclean_cuts'], ['a'])
                        self.assertFalse(next(row for row in logs if 'clean' in row)['clean'])

    def test_unmatched_english_is_heard_again_in_english(self):
        for cut in self.modules():
            quotes = [{'text': '꽃이 핀다.'}, {'text': 'I see a cup.'}, {'text': 'It is red.'}, {'text': '끝이다.'}]
            words = [{'word': w, 'start': a, 'end': b} for w, a, b in
                     [('꽃이', 0, .5), ('핀다.', .5, 1), ('아이', 1.5, 2), ('씨', 3, 3.5), ('끝이다.', 5, 6)]]
            english = [{'word': w, 'start': a, 'end': b} for w, a, b in
                       [('I', 1.2, 1.3), ('see', 1.3, 1.5), ('a', 1.5, 1.6), ('cup.', 1.6, 2), ('It', 3, 3.2), ('is', 3.2, 3.4),
                        ('red.', 3.4, 3.6)]]
            self.assertEqual(cut.sentence_bounds(quotes, words, 6), [(1, 5, False)] * 3)
            heard = cut.rehear(quotes, words, cut.sentence_bounds(quotes, words, 6), lambda a, b: english)
            self.assertEqual(cut.sentence_bounds(quotes, heard, 6), [(1, 1.2, True), (2, 3, True), (3.6, 5, True)])
            korean = [{'text': '꽃이 핀다.'}, {'text': '잎이 난다.'}, {'text': '끝이다.'}]
            hear = Mock()
            self.assertEqual(cut.rehear(korean, words, cut.sentence_bounds(korean, words, 6), hear), words)
            hear.assert_not_called()

    def test_missing_middle_edges_and_all(self):
        for cut in self.modules():
            sentences = [{'text': text} for text in ['花', 'twenty', '开']]
            words = [{'word': word, 'start': i, 'end': i + .5} for i, word in enumerate(['花', '20', '开'])]
            self.assertEqual(cut.sentence_bounds(sentences, words, 3), [(0.5, 2, False), (0.5, 2, False)])
            self.assertEqual(cut.sentence_bounds([{'text': '花'}, {'text': 'Goodbye.'}], words[:1], 3), [(0.5, 3, False)])
            self.assertEqual(cut.sentence_bounds([{'text': '!'}, {'text': '花'}], words[:1], 3), [(0, 0, False)])
            self.assertEqual(cut.sentence_bounds(sentences, [], 3), [(0, 3, False), (0, 3, False)])

    def test_shared_windows_cut_distinct_pauses(self):
        for cut in self.modules():
            for missing in [1, 2]:
                with self.subTest(module=cut.__file__, missing=missing), tempfile.TemporaryDirectory() as directory:
                    root, rate = Path(directory), 24000
                    tone = .2 * np.sin(2 * np.pi * 220 * np.arange(rate) / rate)
                    dipped = tone.copy()
                    for at in [.2, .5, .8]:
                        dipped[int(at * rate):int((at + .02) * rate)] = 1e-4
                    parts, pauses = [tone], []
                    for i in range(missing + 1):
                        start = sum(len(part) for part in parts)
                        silence = np.full(int((.4 + .1 * i) * rate), 1e-4)
                        pauses.append((start, start + len(silence)))
                        parts.extend([silence, dipped if i < missing else tone])
                    sf.write(root / 'S01.wav', np.concatenate(parts), rate)
                    texts = ['花'] + ['Murmur.', 'Ripple.'][:missing] + ['开']
                    sentences = [{'id': f's{i}', 'scene': 'S01', 'text': text} for i, text in enumerate(texts)]
                    (root / 'sentences.json').write_text(json.dumps(sentences))
                    words = [{'word': '花', 'start': .1, 'end': .9},
                             {'word': '开', 'start': pauses[-1][1] / rate + .1,
                              'end': sum(len(part) for part in parts) / rate - .1}]
                    whisper = SimpleNamespace(transcribe=lambda *a, **kw: {'segments': [{'words': words}]})
                    args = ['cut_takes.py', str(root / 'S01.wav'), '--sentences', str(root / 'sentences.json'),
                            '--out', str(root / 'cut')]
                    stdout = io.StringIO()
                    with patch.dict(sys.modules, {'mlx_whisper': whisper}), patch.object(sys, 'argv', args), \
                            contextlib.redirect_stdout(stdout):
                        cut.main()
                    frames = [sf.info(root / 'cut' / f"{s['id']}.wav").frames for s in sentences]
                    self.assertTrue(all(size > 0 for size in frames))
                    self.assertEqual(sum(frames), sum(len(part) for part in parts))
                    self.assertEqual(len(list((root / 'cut').glob('*.wav'))), missing + 2)
                    joined = np.concatenate([sf.read(root / 'cut' / f"{s['id']}.wav", dtype='int16')[0]
                                             for s in sentences])
                    np.testing.assert_array_equal(joined, sf.read(root / 'S01.wav', dtype='int16')[0])
                    for edge, (start, end) in zip(np.cumsum(frames)[:-1], pauses):
                        self.assertGreater(edge, start)
                        self.assertLess(edge, end)
                        self.assertAlmostEqual(edge / rate, (start + end) / (2 * rate), delta=.02)
                    logs = [json.loads(line) for line in stdout.getvalue().splitlines()]
                    self.assertEqual(logs[0]['unclean_cuts'], [s['id'] for s in sentences[:-1]])

    def test_shared_window_fills_missing_pauses(self):
        for cut in self.modules():
            for min_gap in [cut.MIN_GAP, 2.0]:
                with self.subTest(module=cut.__file__, min_gap=min_gap), tempfile.TemporaryDirectory() as directory:
                    root, rate = Path(directory), 24000
                    # Constant power gives one whole-take quiet run; a two-second minimum gives none.
                    sf.write(root / 'S01.wav', np.full(rate, .1), rate)
                    sentences = [{'id': f's{i}', 'scene': 'S01', 'text': text}
                                 for i, text in enumerate(['Bud.', 'Leaf.', 'Stem.', 'Root.'])]
                    (root / 'sentences.json').write_text(json.dumps(sentences))
                    whisper = SimpleNamespace(transcribe=lambda *a, **kw: {'segments': []})
                    args = ['cut_takes.py', str(root / 'S01.wav'), '--sentences', str(root / 'sentences.json'),
                            '--out', str(root / 'cut')]
                    stdout = io.StringIO()
                    with patch.dict(sys.modules, {'mlx_whisper': whisper}), patch.object(sys, 'argv', args), \
                            patch.object(cut, 'MIN_GAP', min_gap), contextlib.redirect_stdout(stdout):
                        cut.main()
                    frames = [sf.info(root / 'cut' / f"{s['id']}.wav").frames for s in sentences]
                    self.assertTrue(all(size > 0 for size in frames))
                    self.assertEqual(sum(frames), rate)
                    middle = rate // 2 + (int(rate * cut.WINDOW) // 2 if min_gap < 1 else 0)
                    self.assertEqual(list(np.cumsum(frames)[:-1]),
                                     [middle // 2, middle, (middle + rate) // 2])
                    logs = [json.loads(line) for line in stdout.getvalue().splitlines()]
                    self.assertEqual(logs[0]['unclean_cuts'], [s['id'] for s in sentences[:-1]])
                    gaps = [row['gap_s'] for row in logs if 'gap_s' in row]
                    self.assertEqual(sum(gap > 0 for gap in gaps), int(min_gap < 1))

    def test_invalid_edges_stop_before_writing(self):
        for cut in self.modules():
            for bounds in [[(.5, .5, False)] * 2,
                           [(.7, .9, True), (.1, .2, True)]]:
                with self.subTest(module=cut.__file__, bounds=bounds), tempfile.TemporaryDirectory() as directory:
                    root, rate = Path(directory), 24000
                    sf.write(root / 'S01.wav', np.full(rate, .1), rate)
                    sentences = [{'id': f's{i}', 'scene': 'S01', 'text': text}
                                 for i, text in enumerate(['Bud.', 'Leaf.', 'Root.'])]
                    (root / 'sentences.json').write_text(json.dumps(sentences))
                    whisper = SimpleNamespace(transcribe=lambda *a, **kw: {'segments': []})
                    args = ['cut_takes.py', str(root / 'S01.wav'), '--sentences', str(root / 'sentences.json'),
                            '--out', str(root / 'cut')]
                    # One sample-wide search window cannot hold two interior cuts.
                    window = 1 / rate if bounds[0][2] is False else cut.WINDOW
                    before, after = (0, 0) if window < cut.WINDOW else (cut.BEFORE, cut.AFTER)
                    with patch.dict(sys.modules, {'mlx_whisper': whisper}), patch.object(sys, 'argv', args), \
                            patch.object(cut, 'sentence_bounds', return_value=bounds), \
                            patch.object(cut, 'WINDOW', window), patch.object(cut, 'BEFORE', before), \
                            patch.object(cut, 'AFTER', after), patch.object(cut, 'MIN_GAP', 2.0):
                        with self.assertRaises(SystemExit) as stopped, contextlib.redirect_stderr(io.StringIO()) as said:
                            cut.main()
                    self.assertEqual(stopped.exception.code, film.UNCUTTABLE_EXIT)
                    for name in ['S01.wav', 's0', 's1', 's2']:
                        self.assertIn(name, said.getvalue())
                    self.assertEqual(list((root / 'cut').glob('*.wav')), [])


if __name__ == '__main__':
    unittest.main()
