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
from unittest.mock import patch

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
        for relative in ['templates/voice/cut_takes.py', 'local/voice/cut_takes.py']:
            path = ROOT / relative
            if not path.exists():
                continue  # Local voice profiles are not shipped with the public repository.
            spec = importlib.util.spec_from_file_location('cut_test', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            yield module

    def test_unicode_matching(self):
        for cut in self.modules():
            for first, second in [('फूल', 'खिला'), ('꽃이', '피어'), ('小花', '开放'), ('A-M-S', 'done')]:
                sentences = [{'text': first}, {'text': second}]
                words = [{'word': norm(first), 'start': 0, 'end': 1}, {'word': second, 'start': 2, 'end': 3}]
                self.assertEqual(cut.sentence_bounds(sentences, words, 4), [(1, 2, True)])
            self.assertEqual(cut.letters('Ａ É क़ 가'), norm('Ａ É क़ 가'))

    def test_cut_logs_unmatched_as_unclean_and_forwards_language(self):
        for cut in self.modules():
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                sf.write(root / 'S01.wav', np.full(24000, .1), 24000)
                (root / 'sentences.json').write_text(json.dumps([
                    {'id': 'a', 'scene': 'S01', 'text': '花'},
                    {'id': 'b', 'scene': 'S01', 'text': 'Goodbye.'}]))
                whisper = SimpleNamespace(transcribe=lambda *a, **kw: None)
                args = ['cut_takes.py', str(root / 'S01.wav'), '--sentences', str(root / 'sentences.json'),
                        '--out', str(root / 'cut'), '--language', 'zh']
                stdout = io.StringIO()
                with patch.dict(sys.modules, {'mlx_whisper': whisper}), patch.object(sys, 'argv', args), \
                        patch.object(whisper, 'transcribe', return_value={'segments': [{'words': [
                            {'word': '花', 'start': .1, 'end': .3}]}]}) as transcribe, \
                        contextlib.redirect_stdout(stdout):
                    cut.main()
                self.assertEqual(transcribe.call_args.kwargs['language'], 'zh')
                logs = [json.loads(line) for line in stdout.getvalue().splitlines()]
                self.assertEqual(logs[0]['unclean_cuts'], ['a'])
                self.assertFalse(next(row for row in logs if 'clean' in row)['clean'])

    def test_missing_middle_edges_and_all(self):
        for cut in self.modules():
            sentences = [{'text': text} for text in ['花', 'twenty', '开']]
            words = [{'word': word, 'start': i, 'end': i + .5} for i, word in enumerate(['花', '20', '开'])]
            self.assertEqual(cut.sentence_bounds(sentences, words, 3), [(0.5, 2, False), (0.5, 2, False)])
            self.assertEqual(cut.sentence_bounds([{'text': '花'}, {'text': 'Goodbye.'}], words[:1], 3), [(0.5, 3, False)])
            self.assertEqual(cut.sentence_bounds([{'text': '!'}, {'text': '花'}], words[:1], 3), [(0, 0, False)])
            self.assertEqual(cut.sentence_bounds(sentences, [], 3), [(0, 3, False), (0, 3, False)])


if __name__ == '__main__':
    unittest.main()
