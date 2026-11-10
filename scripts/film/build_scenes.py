#!/usr/bin/env python3
"""Assemble a composition from scenes/sNN.js and optional sNN.css and sNN.html.

  build_scenes.py --project DIR --template FILE [s03 s04 ...]

The template supplies {{CSS}}, {{JS}}, {{SCENES}} and {{DURATION}}; CSS and JS
markers can be comment-wrapped as /*{{CSS}}*/ and //{{JS}}. Duration comes
unchanged from DIR/data.js. Every scene gets a section with a 1920x1080 SVG,
and each included script runs in a closure with const SC = "sNN".
Full builds write DIR/index.html. Selected builds leave other sections empty
and write DIR/index-s03-s04.html in argument order, preserving other builds.
"""
import argparse
import json
from pathlib import Path
import sys


def build_scenes(project: Path, template: Path, selected_scene_ids: list[str]) -> Path:
    scene_ids = sorted(path.stem for path in (project / "scenes").glob("s[0-9][0-9].js"))
    if not scene_ids:
        raise ValueError(f"{project / 'scenes'} has no sNN.js scene fragments")
    included_scene_ids = selected_scene_ids or scene_ids
    unknown_scene_ids = [scene_id for scene_id in included_scene_ids if scene_id not in scene_ids]
    if unknown_scene_ids:
        raise ValueError(f"unknown scene ids {unknown_scene_ids}; the film has {scene_ids[0]}..{scene_ids[-1]}")
    template_text = template.read_text()
    missing_placeholders = [name for name in ("CSS", "JS", "SCENES", "DURATION")
                            if "{{" + name + "}}" not in template_text]
    if missing_placeholders:
        raise ValueError(f"template missing placeholders: {', '.join(missing_placeholders)}")
    scene_sections, scene_styles, scene_scripts = [], [], []
    for scene_id in scene_ids:
        fragment = project / "scenes" / scene_id
        html_fragment = fragment.with_suffix(".html")
        html = html_fragment.read_text() if scene_id in included_scene_ids and html_fragment.exists() else ""
        scene_sections.append(f'<section id="{scene_id}" class="scene"><svg class="plate" viewBox="0 0 1920 1080" width="1920" height="1080"></svg>{html}</section>')
        if scene_id in included_scene_ids:
            css_fragment = fragment.with_suffix(".css")
            if css_fragment.exists():
                scene_styles.append(f"/* {scene_id} */\n" + css_fragment.read_text())
            scene_scripts.append(f"// ===== {scene_id} =====\n(() => {{\nconst SC = \"{scene_id}\";\n"
                                 + fragment.with_suffix(".js").read_text() + "\n})();")
    data_text = (project / "data.js").read_text()
    duration = json.loads(data_text[data_text.index("{"):data_text.rindex("}") + 1])["duration"]
    output_text = template_text.replace("{{DURATION}}", str(duration)).replace("{{SCENES}}", "\n".join(scene_sections))
    css_placeholder = "/*{{CSS}}*/" if "/*{{CSS}}*/" in template_text else "{{CSS}}"
    js_placeholder = "//{{JS}}" if "//{{JS}}" in template_text else "{{JS}}"
    output_text = output_text.replace(css_placeholder, "\n".join(scene_styles)).replace(js_placeholder, "\n".join(scene_scripts))
    output_name = "index-" + "-".join(selected_scene_ids) + ".html" if selected_scene_ids else "index.html"
    output = project / output_name
    output.write_text(output_text)
    print(f"{output_name}: {len(included_scene_ids)} scene fragments, {duration} s")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, required=True, help="Read scene fragments and data.js from this composition folder.")
    parser.add_argument("--template", type=Path, required=True, help="Read the page template from this file.")
    parser.add_argument("scene_ids", nargs="*", metavar="sNN", help="Include these scenes; the default includes every scene.")
    args = parser.parse_args()
    build_scenes(args.project, args.template, args.scene_ids)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as exc:
        sys.exit(str(exc))
