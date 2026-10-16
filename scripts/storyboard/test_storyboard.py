#!/usr/bin/env python3
"""Check that storyboard.py places shots on the right phrases, fails on a cue the narrator never says, and plays only current clips."""
import json, re, tempfile, unittest, wave
from pathlib import Path

from storyboard import build

SCRIPT = """# A test film

## Scene 1: Water

**Narration**

Rain falls on the hills. It runs downhill into the river.

The river carries it to the sea.

**Visual**

1. Clouds over hills.
2. On "runs downhill", a stream forms. ![stream](frames/stream.jpg)
   The stream widens as it goes.
3. A boat drifts past, with no cue.
- **"to the sea"**: the river mouth opens.

## Scene 2: Sun

**Narration.**

The sun warms the sea, and the water rises again. Then clouds form over the hills once more.

**Visual.**

On "the water rises", vapour lifts off the waves.
"""


def run(script, voicing=None, frames=("frames/stream.jpg",)):
    """The page, the errors, the phrase-group count and the readings for an invented script.

    voicing, when given, writes an audio folder into the script's folder and returns its path."""
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "script.md"
        src.write_text(script)
        for frame in frames:
            (Path(d) / frame).parent.mkdir(parents=True, exist_ok=True)
            (Path(d) / frame).write_bytes(b"")
        return build(src, None, "en", audio=voicing(Path(d)) if voicing else None)


def audio_folder(rows):
    """A writer for an audio folder like narrate_film.py's: one timing row of 2 s per (ID, text, clip seconds or None)."""
    def write(root):
        audio = root / "production" / "audio"
        (audio / "sentences").mkdir(parents=True)
        timing, start = [], 0.35
        for sid, text, seconds in rows:
            timing.append({"id": sid, "scene_id": sid[:3], "text": text, "start": start, "end": round(start + 2, 3),
                           "audio": f"sentences/{sid}.wav"})
            if seconds is not None:
                with wave.open(str(audio / "sentences" / f"{sid}.wav"), "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(24000)
                    w.writeframes(b"\0\0" * round(seconds * 24000))
            start += 2.22
        (audio / "timing.json").write_text(json.dumps({"sentences": timing}))
        return audio
    return write


def embedded(page):
    return json.loads(re.search(r'<script type="application/json" id="said">(.*?)</script>', page, re.S)[1])


class StoryboardTest(unittest.TestCase):
    def test_groups_follow_cues(self):
        page, errors, groups, _ = run(SCRIPT)
        self.assertEqual(errors, [])
        # Scene 1 splits at "runs downhill" and "to the sea"; scene 2's only shot takes the whole scene.
        self.assertEqual(groups, 4)
        # Spans also split at sentences, so a click knows its sentence, and each cue's words carry the faint mark.
        self.assertIn('<p><span class="g" data-g="0" data-s="s01-01" tabindex="0">Rain falls on the hills. </span>'
                      '<span class="g" data-g="0" data-s="s01-02">It </span>'
                      '<span class="g" data-g="1" data-s="s01-02" tabindex="0"><span class="k">runs downhill</span> into the river.</span></p>', page)
        self.assertIn('<p><span class="g" data-g="1" data-s="s01-03">The river carries it </span>'
                      '<span class="g" data-g="2" data-s="s01-03" tabindex="0"><span class="k">to the sea.</span></span></p>', page)
        self.assertIn('<img src="frames/stream.jpg" alt="stream"', page)
        self.assertIn("a stream forms. The stream widens as it goes.", page)
        self.assertIn("Shot 1 of 4 opens the scene, with no cue", page)
        self.assertIn("Shot 3 of 4 follows the shot above, with no cue", page)
        self.assertIn("Not drawn yet", page)
        # The strip lists every shot of the scene in script order, each pointing at its phrase group.
        strip = re.search(r'<section class="strip" data-scene="1".*?</section>', page)[0]
        self.assertEqual(re.findall(r'<button type="button" data-g="(\d+)">', strip), ["0", "1", "1", "2"])

    def test_a_missing_frame_shows_as_not_drawn(self):
        page, _, _, _ = run(SCRIPT, frames=())
        self.assertNotIn("<img", page)
        self.assertIn('<figure><span class="todo label">Not drawn yet</span><figcaption class="label">stream</figcaption></figure>', page)

    def test_a_scene_without_shots_says_so(self):
        page, errors, _, _ = run(SCRIPT.split("**Visual.**")[0])
        self.assertEqual(errors, [])
        self.assertIn('<p class=label>Scene 2 has no shots yet.</p>', page)
        self.assertNotIn('data-scene="2" aria-label', page)

    def test_cue_marks_stop_at_the_next_cue(self):
        script = SCRIPT.replace('On "runs downhill"', 'On "falls on the hills"').replace('3. A boat', '3. On "the hills. It", a boat')
        page, errors, _, _ = run(script)
        self.assertEqual(errors, [])
        self.assertIn('<span class="k">falls on</span> </span><span class="g" data-g="2" data-s="s01-01" tabindex="0">'
                      '<span class="k">the hills. </span></span><span class="g" data-g="2" data-s="s01-02"><span class="k">It</span>', page)

    def test_unmatched_cue_fails(self):
        _, errors, _, _ = run(SCRIPT.replace('On "runs downhill"', 'On "flows uphill"'))
        self.assertIn('scene 1: cue not in narration: "flows uphill"', errors)

    def test_without_audio_a_system_voice_reads_every_sentence(self):
        page, _, _, said = run(SCRIPT)
        self.assertEqual(len(said), 5)
        self.assertEqual(said["s02-02"], {"text": "Then clouds form over the hills once more."})
        self.assertEqual(embedded(page), said)
        self.assertIn("A system voice reads each sentence.", page)

    def test_audio_folder_before_voicing(self):
        page, _, _, said = run(SCRIPT, lambda root: root / "production" / "audio")
        self.assertEqual({s["why"] for s in said.values()}, {"it is not voiced yet"})
        self.assertNotIn('"src"', json.dumps(said))
        self.assertIn("No sentence has a narration clip that matches the script yet", page)

    def test_only_clips_that_match_the_script_play(self):
        page, _, _, said = run(SCRIPT, audio_folder([
            ("s01-01", "Rain falls on the hills.", 2),
            ("s01-02", "It runs uphill into the river.", 2),
            ("s01-03", "The river carries it to the sea.", 2.4),
            ("s02-01", "The sun warms the sea, and the water rises again.", None),
        ]))
        self.assertEqual(said["s01-01"], {"text": "Rain falls on the hills.", "src": "production/audio/sentences/s01-01.wav", "seconds": 2})
        self.assertEqual(said["s01-02"]["why"], "it changed since it was voiced")
        self.assertEqual(said["s01-03"]["why"], "its clip is missing or unlike timing.json")
        self.assertEqual(said["s02-01"]["why"], "its clip is missing or unlike timing.json")
        self.assertEqual(said["s02-02"]["why"], "it is not voiced yet")
        self.assertTrue(all("src" not in said[sid] for sid in ("s01-02", "s01-03", "s02-01", "s02-02")))
        self.assertEqual(embedded(page), said)
        self.assertIn("The film&#x27;s narration reads 1 of 5 sentences. A system voice reads the other 4, which have no clip", page)


if __name__ == "__main__":
    unittest.main()
