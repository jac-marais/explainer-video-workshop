"""Check the template's Kokoro frontend without loading or running a speech model."""
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(importlib.util.find_spec("kokoro_onnx"), "run with scripts/run/py, whose environment has kokoro-onnx")
class VoiceFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from kokoro_onnx import EspeakConfig
        from kokoro_onnx.tokenizer import Tokenizer

        module = importlib.util.spec_from_file_location("voice_frontend", ROOT / "templates/voice/voice.py")
        cls.voice = importlib.util.module_from_spec(module)
        module.loader.exec_module(cls.voice)
        prefix = Path("/opt/homebrew/opt/espeak-ng")
        cls.tokenizer = Tokenizer(EspeakConfig(str(prefix / "lib/libespeak-ng.dylib"), str(prefix / "share/espeak-ng-data")))

    def phones(self, text, lang="en-us"):
        return self.voice.phonemize_kokoro(text, self.tokenizer, lang)

    def test_language_switch_flags_are_removed_without_losing_the_word(self):
        for lang, text in [("fr-fr", "Le football est simple."), ("hi", "यह football है.")]:
            with self.subTest(lang=lang):
                kokoro = self.tokenizer.phonemize(text, lang)
                self.assertIn("(en)", kokoro)
                self.assertEqual(self.phones(text, lang), re.sub(r"\((?:en|fr|hi)\)", "", kokoro))

    def test_text_without_a_language_switch_matches_kokoros_tokenizer(self):
        for lang, text in [("en-us", "  The (red) cup is full.\n\nThe blue cup is empty!  "),
                           ("fr-fr", "  Le (chat) dort. Le chien joue!  "),
                           ("pt-br", "  O (gato) dorme. O copo está cheio!  "),
                           ("hi", "  यह (घर) है. हर घर नया है!  "),
                           ("en-us", " \n\n ")]:
            with self.subTest(lang=lang, text=text):
                self.assertEqual(self.phones(text, lang), self.tokenizer.phonemize(text, lang))

    def test_terminators_kokoro_lacks_become_its_nearest_stop(self):
        for lang, text, stops in [("en-us", "Is it full? Yes! It is.", "Is it full? Yes! It is."),
                                  ("hi", "यह घर है। वह नया है॥", "यह घर है. वह नया है."),
                                  ("cmn", "他来了。你好吗？好！", "他来了.你好吗?好!")]:
            with self.subTest(lang=lang):
                self.assertEqual(self.phones(text, lang), self.tokenizer.phonemize(stops, lang))

    def test_flaps_take_the_tap_in_both_unicode_forms_and_real_stops_survive(self):
        for flap, aspirated in [("ड़", "ढ़"), ("ड़", "ढ़")]:
            for stop in [".", "।"]:
                with self.subTest(flap=flap, stop=stop):
                    text = f"ल{flap}का ब{aspirated}ता है{stop} हर{stop} वह प{aspirated}{stop}"
                    self.assertIn("r.", self.tokenizer.phonemize(text, "hi"))
                    self.assertEqual(self.phones(text, "hi"), "lˈʌɾkˌaː bˈʌɾhətˌaː hɛː. hˈʌɾ. ʋˌəh pˈʌɾh.")

    def test_espeak_symbols_never_reach_kokoro_as_punctuation(self):
        for lang, text, phones in [("bn", "বড় পড়া।", "bˈɔɾ pˈɔɾ."), ("cmn", "我知道这是什么", "wˈo tsitˈɑu tsˈo sˈi sˈəɜn mˈo")]:
            with self.subTest(lang=lang):
                self.assertIn(".", self.tokenizer.phonemize(text.rstrip("।"), lang))
                self.assertEqual(self.phones(text, lang), phones)

    def test_pins_replace_their_words_in_place(self):
        for lang, text, phones in [("en-us", "The [cup](/bˈʌɡ/) and [mug](/kˈʌp/) are here.", "ðə bˈʌɡ ænd kˈʌp ɑːɹ hˈɪɹ."),
                                   ("fr-fr", "L’[objet](/ɔbʒˈɛ/) arrive.", "lɔbʒˈɛ aʁˈiv."),
                                   ("fr-fr", "L'[objet](/ɔbʒˈɛ/) arrive.", "lɔbʒˈɛ aʁˈiv."),
                                   ("hi", "यह [घर](/mˈʌkaːn/) है।", "jˌəh mˈʌkaːn hɛː.")]:
            with self.subTest(text=text):
                self.assertEqual(self.phones(text, lang), phones)

    def test_language_pins_take_that_languages_phonemes(self):
        quote = "I see a red cup."
        english = self.phones(quote, "en-us")
        self.assertNotEqual(english, self.phones(quote, "pt-br"))
        for lang, text in [("pt-br", f'Ela disse "[{quote}](en-us)" hoje.'), ("fr-fr", f"L’[{quote}](en-us) arrive.")]:
            with self.subTest(lang=lang):
                self.assertEqual(self.phones(text, lang), self.phones(text.replace("(en-us)", f"(/{english}/)"), lang))
                self.assertIn(english, self.phones(text, lang))

    def test_engines_without_phonemes_read_the_pinned_words(self):
        self.assertEqual(self.voice.unpinned("The [cup](/kˈʌp/) and [the tea](en-us) are here."), "The cup and the tea are here.")

    def test_pins_with_symbols_kokoro_lacks_fail_instead_of_vanishing(self):
        self.assertNotIn("ɝ", self.tokenizer.vocab)
        with self.assertRaisesRegex(SystemExit, "cannot say the pinned phonemes ɝ"):
            self.phones("The [bird](/bˈɝd/) sings.")
        self.assertIn("bˈɜɹd", self.phones("The [bird](/bˈɜɹd/) sings."))

    def test_ambiguous_pin_placement_fails_instead_of_guessing(self):
        with self.assertRaisesRegex(SystemExit, "could not place pinned phonemes"):
            self.phones(self.voice.ELIDING_STAND_IN + " and [cup](/kˈʌp/).")

    def load_with_mock_model(self, spec):
        model = SimpleNamespace(tokenizer=self.tokenizer,
                                create=Mock(return_value=(self.voice.np.zeros(1), 24000)))
        with patch("kokoro_onnx.Kokoro", return_value=model), \
                patch.object(self.voice.Path, "exists", return_value=True), \
                patch.object(self.voice, "sha256_file", return_value="model-digest"):
            synthesize, identity = self.voice.load_kokoro(spec, seed=0)
        return synthesize, identity, model

    def test_frontend_key_selects_the_phonemizer(self):
        frontend = self.voice.KOKORO_FRONTEND
        for lang, plain, pinned in [("en-us", "The red cup is full.", "The [cup](/kˈʌp/) is full."),
                                    ("fr-fr", "Le football est simple.", "Le [chat](/ʃˈa/) dort."),
                                    ("hi", "लड़का है।", "यह [घर](/ɡʰˈʌɾ/) है."),
                                    ("pt-br", "O copo está cheio.", "O [cup](en-us) está cheio.")]:
            for key in [None, frontend]:
                for text in [plain, pinned]:
                    with self.subTest(lang=lang, frontend=key, text=text):
                        settings = {"voice": "test-voice", "speed": 0.92, "lang": lang}
                        spec = {"engine": "kokoro", **settings, **({"frontend": key} if key else {})}
                        synthesize, identity, model = self.load_with_mock_model(spec)
                        samples, rate, extra = synthesize(text)
                        if key:
                            phonemes = self.phones(text, lang)
                        elif text == pinned:
                            kokoro = lambda value: self.tokenizer.phonemize(value, lang)
                            expanded = text.replace("(en-us)", f"(/{self.tokenizer.phonemize('cup', 'en-us')}/)")
                            phonemes = self.voice.place_pins(expanded, kokoro, self.voice.STAND_IN)
                        else:
                            phonemes = None
                        if phonemes:
                            model.create.assert_called_once_with(phonemes, **settings, is_phonemes=True)
                            self.assertEqual(extra, {"phonemes": phonemes})
                        else:
                            model.create.assert_called_once_with(text, **settings)
                            self.assertEqual(extra, {})
                        self.assertEqual(identity["settings"], {**settings, **({"frontend": key} if key else {})})
                        self.assertEqual(samples.dtype.name, "float32")
                        self.assertEqual(rate, 24000)
        with self.assertRaisesRegex(SystemExit, f"Unknown Kokoro frontend {frontend - 1}"):
            self.load_with_mock_model({"engine": "kokoro", "voice": "test-voice", "speed": 0.92, "frontend": frontend - 1})

    def test_template_kokoro_voice_opts_in(self):
        config = json.loads((ROOT / "templates/voice/voice.json").read_text())
        for spec in config["voices"].values():
            if spec["engine"] == "kokoro":
                self.assertEqual(spec["frontend"], self.voice.KOKORO_FRONTEND)


if __name__ == "__main__":
    unittest.main()
