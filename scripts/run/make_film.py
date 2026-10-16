#!/usr/bin/env python3
"""Build one language of a prepared HyperFrames film.

Run the steps from --from through --to. Arguments after a bare -- go to hyperframes render.
"""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS / "film"))
sys.path.insert(0, str(SCRIPTS / "audio"))
from build_data import scenes, cue_keys, check_sentence_counts, sentence_ref, sentence_time
from text_tokens import short_sentences

STEPS = ("narrate", "captions", "cues", "data", "render", "check")


def execute(command, heavy=False):
    command = [str(item) for item in command]
    if heavy:
        command = [str(SCRIPTS / "run/heavy"), *command]
    print("+", shlex.join(command), flush=True)
    subprocess.run(command, check=True)


def split_sentences(texts):
    """Each (language, text) pair's sentence texts, split by text_tokens.py in the workshop environment."""
    result = subprocess.run([SCRIPTS / "run/heavy", SCRIPTS / "run/py", SCRIPTS / "audio/text_tokens.py"],
                            input=json.dumps(texts), stdout=subprocess.PIPE, text=True)
    if result.returncode:
        raise ValueError(f"text_tokens.py could not split the narration (exit {result.returncode})")
    return [[sentence["text"] for sentence in split] for split in json.loads(result.stdout)]


def validate_inputs(args):
    script = list(scenes(args.script))
    if not script:
        raise ValueError("script has no scenes")
    source = json.loads(args.scenes.read_text())
    parts = [[text] if isinstance(text, str) else text for text in (scene["narration"] for scene in source)]
    key = list(scenes(args.key_script)) if args.key_script else []
    # One process splits every text, because loading Stanza takes seconds.
    split = split_sentences([[args.language, text] for _, text, _ in script]
                            + [[args.language, part] for scene in parts for part in scene]
                            + [[args.key_language, text] for _, text, _ in key])
    expected = dict(zip((f"s{num:02d}" for num, _, _ in script), split))
    for num, _, names in script:
        rows = [{"id": f"s{num:02d}-{i:02d}", "start": 0, "end": 1} for i in range(1, len(expected[f"s{num:02d}"]) + 1)]
        for name in names:
            sentence_time(name, f"s{num:02d}", rows)
    rest = iter(split[len(script):])
    actual = {scene["id"]: [sentence for _ in scene_parts for sentence in next(rest)] for scene, scene_parts in zip(source, parts)}
    if len(actual) != len(source) or actual != expected:
        raise ValueError("scenes JSON must match the script's scene IDs, sentences and narration")
    key_split = {f"s{num:02d}": sentences for (num, _, _), sentences in zip(key, rest)}
    # Sentence counts matter only to sentence cues, so translations of a film cued by quoted words may split differently.
    if key and any(sentence_ref(name) for _, _, names in script + key for name in names):
        check_sentence_counts({num: len(expected[f"s{num:02d}"]) for num, _, _ in script},
                              {num: len(key_split[f"s{num:02d}"]) for num, _, _ in key})
    if args.key_script:
        cue_keys(args.script, args.key_script)
    # A restart after narrate keeps its voiced words, so only a run that voices them must pass the floor.
    if args.start == "narrate":
        # A translation follows its key script's sentences, so the floor holds for the script the writer wrote.
        short = short_sentences(key_split if key else expected)
        if short:
            raise ValueError("rewrite the narration sentences under the word floor in step 3 of "
                             "methods/prepare-explainer-video.md: " + "; ".join(short))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("script", "scenes", "project", "hf", "out"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--key-language", help="the --key-script's language code")
    parser.add_argument("--audio", type=Path, help="defaults to PROJECT/audio")
    parser.add_argument("--from", dest="start", choices=STEPS, default="narrate")
    parser.add_argument("--to", dest="stop", choices=STEPS, default="check")
    parser.add_argument("--composition", default=".")
    for name in ("key-script", "strings", "spoken", "reuse", "aliases"):
        parser.add_argument(f"--{name}", type=Path)
    parser.add_argument("--embed", action="append", default=[])
    parser.add_argument("--tail", type=float, default=0)
    parser.add_argument("--pacing", choices=("measured", "fast"), default="measured")
    parser.add_argument("--holds", default="")
    parser.add_argument("--uncaptioned", default="")
    parser.add_argument("--caption-font", action="append", default=[], metavar="FILE[#INDEX]")
    for name in ("caption-font-size", "caption-font-weight", "caption-line-width"):
        parser.add_argument(f"--{name}", type=float)
    parser.add_argument("--caption-band")
    parser.add_argument("--size", default="1920x1080")
    parser.add_argument("--fps", type=float, default=30)
    parser.add_argument("--mix", type=Path, help="mono mix to mux and check instead of AUDIO/narration.wav")
    argv = sys.argv[1:]
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    argv = argv[:argv.index("--")] if "--" in argv else argv
    args = parser.parse_args(argv)
    if args.key_script and not args.key_language:
        parser.error("--key-script needs --key-language")
    if STEPS.index(args.stop) < STEPS.index(args.start):
        parser.error("--to must not come before --from")
    if args.mix is not None and STEPS.index(args.start) < STEPS.index("render"):
        parser.error("--mix needs --from render or check, because earlier steps change what the mix contains")
    validate_inputs(args)
    audio = (args.audio or args.project / "audio").resolve()
    timing, words = audio / "timing.json", audio / "words.json"
    captions, cues = audio / "captions.json", audio / "cues.json"
    master = args.mix or audio / "narration.wav"
    if STEPS.index(args.start) <= STEPS.index("render") <= STEPS.index(args.stop) and args.out.exists():
        raise ValueError(f"{args.out} exists; choose a new --out before rerendering")
    if not (args.project / "index.html").is_file():
        raise ValueError("project needs an existing index.html composition")
    for step in STEPS[STEPS.index(args.start):STEPS.index(args.stop) + 1]:
        print(f"[{step}]", flush=True)
        if step == "narrate":
            command = [SCRIPTS / "run/py", SCRIPTS / "audio/narrate_film.py", args.scenes, "--voice", args.voice,
                       "--language", args.language, "--out", audio, "--strict"]
            for name in ("spoken", "reuse"):
                if getattr(args, name):
                    command += [f"--{name}", getattr(args, name)]
            execute(command, heavy=True)
            report = json.loads((audio / "audio-checks.json").read_text())
            if report.get("flags") or report.get("fallback_words"):
                raise ValueError(f"resolve audio flags in {audio / 'audio-checks.json'} before continuing")
        elif step == "captions":
            command = [SCRIPTS / "run/py", SCRIPTS / "audio/captions.py", timing, words,
                       "--output", audio / "captions.vtt", "--json-output", captions]
            for font in args.caption_font:
                command += ["--font", font]
            for name in ("font_size", "font_weight", "line_width"):
                if getattr(args, f"caption_{name}") is not None:
                    command += ["--" + name.replace("_", "-"), getattr(args, f"caption_{name}")]
            execute(command, heavy=True)
        elif step == "cues":
            command = [sys.executable, SCRIPTS / "audio/cues.py", args.script, words, timing, "--out", cues, "--strict"]
            if args.aliases:
                command += ["--aliases", args.aliases]
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
            command = [sys.executable, SCRIPTS / "film/render.py", "--hf", args.hf, "--project", args.project,
                       args.composition, "--out", args.out, "--narration", master, "--expect-seconds", duration]
            if extra:
                command += ["--", *extra]
            execute(command, heavy=True)
        elif step == "check":
            # check_film.py owns the default caption band, so pass one only when the user sets it.
            band = ["--caption-band", args.caption_band] if args.caption_band else []
            execute([sys.executable, SCRIPTS / "film/check_film.py", args.out, "--timing", timing,
                     "--captions", captions, "--narration", master, "--tail", args.tail,
                     "--pacing", args.pacing, "--holds", args.holds, "--uncaptioned", args.uncaptioned,
                     *band, "--size", args.size, "--fps", args.fps], heavy=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
