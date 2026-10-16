#!/usr/bin/env python3
"""Check that storyboard.py places shots on the right phrases and fails on a cue the narrator never says."""
import tempfile, unittest
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

The sun warms the sea, and the water rises again.

**Visual.**

On "the water rises", vapour lifts off the waves.
"""


def run(script):
    """The page, the errors and the phrase-group count for an invented script."""
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "script.md"
        src.write_text(script)
        return build(src, None, "en")


class StoryboardTest(unittest.TestCase):
    def test_groups_follow_cues(self):
        page, errors, groups = run(SCRIPT)
        self.assertEqual(errors, [])
        # Scene 1 splits at "runs downhill" and "to the sea"; scene 2's only shot takes the whole scene.
        self.assertEqual(groups, 4)
        self.assertIn('data-g="0" tabindex="0">Rain falls on the hills. It </span>', page)
        self.assertIn('data-g="1" tabindex="0">runs downhill into the river. </span>', page)
        self.assertIn('<img src="frames/stream.jpg" alt="stream"', page)
        self.assertIn("a stream forms. The stream widens as it goes.", page)
        self.assertIn("No cue · follows the shot above", page)
        self.assertIn("Not drawn yet", page)

    def test_unmatched_cue_fails(self):
        _, errors, _ = run(SCRIPT.replace('On "runs downhill"', 'On "flows uphill"'))
        self.assertIn('scene 1: cue not in narration: "flows uphill"', errors)



if __name__ == "__main__":
    unittest.main()
