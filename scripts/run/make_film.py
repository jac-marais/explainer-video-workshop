#!/usr/bin/env python3
"""Build one language of a prepared HyperFrames film; restart with --from STEP."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS / "film"))
from build_data import scenes, cue_keys, sentences, sentence_time

STEPS = ("narrate", "captions", "cues", "data", "render", "check")


def execute(command, heavy=False):
    command = [str(item) for item in command]
    if heavy:
        command = [str(SCRIPTS / "run/heavy"), *command]
    print("+", shlex.join(command), flush=True)
    subprocess.run(command, check=True)


def validate_inputs(args):
    script = list(scenes(args.script))
    if not script:
        raise ValueError("script has no scenes")
    for num, text, names in script:
        rows = [{"id": f"s{num:02d}-{i:02d}", "start": 0, "end": 1} for i, _ in enumerate(sentences(text), 1)]
        for name in names:
            sentence_time(name, f"s{num:02d}", rows)
    source = json.loads(args.scenes.read_text())
    expected = {f"s{num:02d}": [s["text"] for s in sentences(text)] for num, text, _ in script}
    actual = {}
    for scene in source:
        text = scene["narration"]
        actual[scene["id"]] = [s["text"] for part in ([text] if isinstance(text, str) else text) for s in sentences(part)]
    if len(actual) != len(source) or actual != expected:
        raise ValueError("scenes JSON must match the script's scene IDs, sentences and narration")
    if args.key_script:
        cue_keys(args.script, args.key_script)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("script", "scenes", "project", "hf", "out"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--audio", type=Path, help="defaults to PROJECT/audio")
    parser.add_argument("--from", dest="start", choices=STEPS, default="narrate")
    parser.add_argument("--composition", default=".")
    for name in ("key-script", "strings", "spoken", "reuse", "aliases"):
        parser.add_argument(f"--{name}", type=Path)
    parser.add_argument("--embed", action="append", default=[])
    parser.add_argument("--tail", type=float, default=0)
    parser.add_argument("--pacing", choices=("measured", "fast"), default="measured")
    parser.add_argument("--holds", default="")
    parser.add_argument("--uncaptioned", default="")
    parser.add_argument("--caption-band", default="360,860,1200,170")
    parser.add_argument("--size", default="1920x1080")
    parser.add_argument("--fps", type=float, default=30)
    args = parser.parse_args()
    validate_inputs(args)
    audio = (args.audio or args.project / "audio").resolve()
    timing, words = audio / "timing.json", audio / "words.json"
    captions, cues = audio / "captions.json", audio / "cues.json"
    narration = audio / "narration.wav"
    if STEPS.index(args.start) <= STEPS.index("render") and args.out.exists():
        raise ValueError(f"{args.out} exists; choose a new --out before rerendering")
    if not (args.project / "index.html").is_file():
        raise ValueError("project needs an existing index.html composition")
    for step in STEPS[STEPS.index(args.start):]:
        print(f"[{step}]", flush=True)
        if step == "narrate":
            command = ["uv", "run", SCRIPTS / "audio/narrate_film.py", args.scenes, "--voice", args.voice,
                       "--language", args.language, "--out", audio, "--strict"]
            for name in ("spoken", "reuse"):
                if getattr(args, name):
                    command += [f"--{name}", getattr(args, name)]
            execute(command, heavy=True)
            report = json.loads((audio / "audio-checks.json").read_text())
            if report.get("flags") or report.get("fallback_words"):
                raise ValueError(f"resolve audio flags in {audio / 'audio-checks.json'} before continuing")
        elif step == "captions":
            execute([sys.executable, SCRIPTS / "audio/captions.py", timing, words,
                     "--output", audio / "captions.vtt", "--json-output", captions])
        elif step == "cues":
            command = [sys.executable, SCRIPTS / "audio/cues.py", args.script, words, timing, "--out", cues, "--strict"]
            for name in ("aliases", "key_script"):
                if getattr(args, name):
                    command += ["--" + name.replace("_", "-"), getattr(args, name)]
            execute(command)
        elif step == "data":
            command = [sys.executable, SCRIPTS / "film/build_data.py", "--script", args.script,
                       "--project", args.project, "--audio", audio, "--tail", args.tail]
            for name in ("strings", "key_script"):
                if getattr(args, name):
                    command += ["--" + name.replace("_", "-"), getattr(args, name)]
            for embed in args.embed:
                command += ["--embed", embed]
            execute(command)
        elif step == "render":
            duration = json.loads(timing.read_text())["duration"] + args.tail
            execute([sys.executable, SCRIPTS / "film/render.py", "--hf", args.hf, "--project", args.project,
                     args.composition, "--out", args.out, "--narration", narration, "--expect-seconds", duration], heavy=True)
        elif step == "check":
            execute([sys.executable, SCRIPTS / "film/check_film.py", args.out, "--timing", timing,
                     "--captions", captions, "--narration", narration, "--tail", args.tail,
                     "--pacing", args.pacing, "--holds", args.holds, "--uncaptioned", args.uncaptioned,
                     "--caption-band", args.caption_band, "--size", args.size, "--fps", args.fps], heavy=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
