#!/usr/bin/env python3
"""Write narration scenes JSON from a workshop script.

  scenes_json.py --script SCRIPT.md --out SCENES.json

Each ## Scene N: Title has **Narration.** followed by **Visual.**, with inline
or multiline text; the periods are optional. Output entries contain id, title,
visual, claim_ids and narration, as read by narrate_film.py and validated
against the script by make_film.py. claim_ids stays empty because the scene
plan owns claim IDs. A scene gets "starts_fresh_take": true when the line "This
scene starts a fresh voice take." comes before its Narration, so a regenerated
file keeps the voice method's fresh-take marks.
"""
import argparse
import json
from pathlib import Path
import re
import sys


def scenes_from_script(script: Path) -> list[dict]:
    script_text = script.read_text()
    scene_rows, scene_ids = [], set()
    for match in re.finditer(r"^## Scene (\d+): (.+?)\n(.*?)(?=^## Scene |\Z)", script_text, re.S | re.M):
        scene_id = f"s{int(match.group(1)):02d}"
        if scene_id in scene_ids:
            raise ValueError(f"duplicate scene id: {scene_id}")
        scene_ids.add(scene_id)
        body = match.group(3)
        parts = re.search(r"\*\*Narration\.?\*\*\s*(.+?)\s*\*\*Visual\.?\*\*\s*(.*)", body, re.S)
        if not parts:
            raise ValueError(f"Scene {match.group(1)} needs a **Narration.** part followed by a **Visual.** part")
        narration, visual = parts.group(1).strip(), parts.group(2).strip()
        title = match.group(2).strip()
        for field_name, value in (("title", title), ("narration", narration), ("visual", visual)):
            if not value:
                raise ValueError(f"scene {scene_id} needs a non-empty {field_name}")
        scene = {"id": scene_id, "title": title, "visual": visual, "claim_ids": [], "narration": narration}
        if "This scene starts a fresh voice take." in re.split(r"\*\*Narration\.?\*\*", body, maxsplit=1)[0]:
            scene["starts_fresh_take"] = True
        scene_rows.append(scene)
    if not scene_rows:
        raise ValueError("script has no scenes")
    return scene_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--script", type=Path, required=True, help="Read the authored scenes from this Markdown file.")
    parser.add_argument("--out", type=Path, required=True, help="Write scenes JSON to this file.")
    args = parser.parse_args()
    scene_rows = scenes_from_script(args.script)
    args.out.write_text(json.dumps(scene_rows, indent=1, ensure_ascii=False) + "\n")
    print(len(scene_rows), "scenes")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as exc:
        sys.exit(str(exc))
