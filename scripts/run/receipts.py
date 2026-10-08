#!/usr/bin/env python3
"""Regenerate the measured tables in receipt documents from the files they describe.

  receipts.py FILE.md [FILE.md ...] --audio AUDIO_DIR [--film MP4] [--captions captions.json] [--scenes SCENES.json]
  receipts.py --init FILE.md BLOCK...

Only text between `<!-- receipts:NAME -->` and `<!-- /receipts:NAME -->` is rewritten. An unknown
NAME, an unbalanced marker, or a block whose input was not passed stops the run before any file
changes. `--init` appends empty marked blocks to FILE.md.

Blocks: audio (narration.wav and the counts in timing.json/words.json), scenes (per-scene table
from timing.json), film (--film MP4), sha (SHA-256 of every input passed), captions (--captions).
AUDIO_DIR holds narration.wav, timing.json and words.json. The sha block lists paths relative to the document.
"""
import argparse, hashlib, json, os, re, subprocess, sys

BLOCKS = ("audio", "scenes", "film", "sha", "captions")
MARK = re.compile(r"^<!-- (/?)receipts:(\S+) -->$")
FPS = 30
CH = {1: "mono", 2: "stereo"}


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"{cmd[0]} failed on {cmd[-1]}: {p.stderr.strip()[-300:]}")
    return p.stdout + p.stderr


def probe(path, *args):
    return json.loads(run(["ffprobe", "-v", "error", "-of", "json", *args, path]))


def loudness(path, first_channel=False):
    # A meter adds the power of both channels, so dual-mono reads 3 LU hot unless one channel is measured.
    af = ("pan=mono|c0=c0," if first_channel else "") + "ebur128=peak=true"
    out = run(["ffmpeg", "-nostats", "-i", path, "-map", "0:a:0", "-af", af, "-f", "null", "-"])
    summary = out[out.rindex("Summary:"):]
    return tuple(float(re.search(pat + r":\s+(-?[\d.]+)", summary).group(1)) for pat in ("I", "LRA", "Peak"))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def table(header, rows):
    sep = ["---:" if h.startswith(">") else "---" for h in header]
    head = [h.lstrip(">") for h in header]
    return "\n".join("|" + "|".join(r) + "|" if r is sep else "| " + " | ".join(r) + " |" for r in [head, sep, *rows])


def load_json(path):
    with open(path) as f:
        return json.load(f)


class Inputs:
    def __init__(self, args):
        self.args = args
        self.audio_dir = args.audio

    def need(self, value, flag, block):
        if not value:
            sys.exit(f"block '{block}' needs {flag}")
        return value

    def audio_file(self, name):
        path = os.path.join(self.need(self.audio_dir, "--audio", "audio/scenes/sha"), name)
        if not os.path.isfile(path):
            sys.exit(f"missing {path}")
        return path

    def sha_files(self):
        files = [self.audio_file(n) for n in ("narration.wav", "timing.json", "words.json")]
        files += [f for f in (self.args.film, self.args.captions, self.args.scenes) if f]
        for f in files:
            if not os.path.isfile(f):
                sys.exit(f"missing {f}")
        return files


def audio_block(inp):
    wav = inp.audio_file("narration.wav")
    timing, words = load_json(inp.audio_file("timing.json")), load_json(inp.audio_file("words.json"))
    info = probe(wav, "-show_streams", "-show_format")
    s, dur = info["streams"][0], float(info["format"]["duration"])
    lufs, lra, tp = loudness(wav)
    spoken = sum(len(x["text"].split()) for x in timing["sentences"])
    rows = [
        ("Duration", f"{dur:.3f} s ({round(dur * FPS):,} frames at {FPS} fps)"),
        ("Format", f"{CH.get(s['channels'], s['channels'])}, {int(s['sample_rate']) / 1000:g} kHz, {s['codec_name']}"),
        ("Integrated loudness", f"{lufs:.1f} LUFS"),
        ("Loudness range", f"{lra:.1f} LU"),
        ("True peak", f"{tp:.1f} dBFS"),
        ("Sentences", f"{len(timing['sentences'])}"),
        ("Script words", f"{spoken:,}"),
        ("Measured word intervals", f"{len(words['words']):,}"),
    ]
    return table(["Measure", "Value"], [(a, b) for a, b in rows])


def scenes_block(inp):
    timing = load_json(inp.audio_file("timing.json"))
    rows = []
    for sc in timing["scenes"]:
        own = [x for x in timing["sentences"] if x["scene_id"] == sc["id"]]
        # scenes[] start/end include the gaps around speech, so take the sentence bounds.
        rows.append((sc["id"], sc["title"], f"{min(x['start'] for x in own):.3f}", f"{max(x['end'] for x in own):.3f}", str(len(own))))
    return table(["Scene", "Title", ">Speech start", ">Speech end", ">Sentences"], rows)


def film_block(inp):
    mp4 = inp.need(inp.args.film, "--film", "film")
    info = probe(mp4, "-show_streams", "-show_format")
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    frames = probe(mp4, "-count_packets", "-select_streams", "v:0", "-show_entries", "stream=nb_read_packets")["streams"][0]["nb_read_packets"]
    rows = [
        ("Duration", f"{float(info['format']['duration']):.3f} s"),
        ("Video frames", f"{int(frames):,}"),
        ("Video", f"{v['codec_name']} {v.get('profile', '')}, {v['width']}x{v['height']}, {v['r_frame_rate']} fps".replace(" ,", ",")),
        ("File size", f"{int(info['format']['size']) / 2**20:.1f} MiB"),
        ("Pixel format", v["pix_fmt"]),
        ("Colour matrix tag", v.get("color_space", "untagged")),
    ]
    if a:
        stereo = a["channels"] == 2
        lufs, _, tp = loudness(mp4, first_channel=stereo)
        rows += [("Audio", f"{a['codec_name']}, {CH.get(a['channels'], a['channels'])}, {int(a['sample_rate']) / 1000:g} kHz"),
                 ("Audio loudness" + (" (left channel)" if stereo else ""), f"{lufs:.1f} LUFS integrated, {tp:.1f} dBFS true peak")]
    else:
        rows.append(("Audio", "none"))
    return table(["Measure", "Value"], rows)


def sha_block(inp, doc):
    base = os.path.dirname(os.path.abspath(doc))
    return table(["File", "SHA-256"], [(f"`{os.path.relpath(f, base)}`", f"`{sha256(f)}`") for f in inp.sha_files()])


def captions_block(inp):
    path = inp.need(inp.args.captions, "--captions", "captions")
    return table(["Measure", "Value"], [("Caption cues", f"{len(load_json(path)):,}")])


BUILD = {"audio": audio_block, "scenes": scenes_block, "film": film_block, "sha": None, "captions": captions_block}


def find_blocks(path, lines):
    """Return {name: (open_index, close_index)}; exit on unknown, nested or unbalanced markers."""
    found, open_at = {}, None
    for i, line in enumerate(lines):
        m = MARK.match(line.strip())
        if not m:
            continue
        closing, name = m.group(1) == "/", m.group(2)
        if name not in BUILD:
            sys.exit(f"{path}:{i + 1}: unknown block '{name}' (known: {', '.join(BLOCKS)})")
        if not closing:
            if open_at:
                sys.exit(f"{path}:{i + 1}: '{name}' opens inside '{open_at[0]}'")
            if name in found:
                sys.exit(f"{path}:{i + 1}: block '{name}' appears twice")
            open_at = (name, i)
        else:
            if not open_at or open_at[0] != name:
                sys.exit(f"{path}:{i + 1}: closing '{name}' has no matching open")
            found[name] = (open_at[1], i)
            open_at = None
    if open_at:
        sys.exit(f"{path}:{open_at[1] + 1}: block '{open_at[0]}' is never closed")
    return found


def init(path, names):
    for n in names:
        if n not in BUILD:
            sys.exit(f"unknown block '{n}' (known: {', '.join(BLOCKS)})")
    text = open(path).read() if os.path.exists(path) else ""
    find_blocks(path, text.splitlines())
    for n in names:
        if f"<!-- receipts:{n} -->" in text:
            sys.exit(f"{path}: block '{n}' already exists")
    add = "".join(f"\n<!-- receipts:{n} -->\n<!-- /receipts:{n} -->\n" for n in names)
    with open(path, "w") as f:
        f.write(text + ("" if text.endswith("\n") or not text else "\n") + add)
    print(f"{path}: added {', '.join(names)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", metavar="FILE.md")
    ap.add_argument("--init", action="store_true", help="append empty blocks: --init FILE.md BLOCK...")
    ap.add_argument("--audio", metavar="AUDIO_DIR")
    ap.add_argument("--film", metavar="MP4")
    ap.add_argument("--captions", metavar="captions.json")
    ap.add_argument("--scenes", metavar="SCENES.json")
    args = ap.parse_args()
    if args.init:
        if len(args.files) < 2:
            ap.error("--init needs FILE.md and at least one BLOCK")
        return init(args.files[0], args.files[1:])

    docs = {}
    for path in args.files:
        lines = open(path).read().split("\n")
        docs[path] = (lines, find_blocks(path, lines))
    inp, built = Inputs(args), {}
    for _, blocks in docs.values():
        for name in blocks:
            if name == "sha":
                inp.sha_files()
            elif name not in built:
                built[name] = BUILD[name](inp)
    if args.scenes and args.audio:
        src = load_json(inp.audio_file("timing.json")).get("source_sha256")
        if src and src != sha256(args.scenes):
            print(f"warning: timing.json source_sha256 does not match {args.scenes}", file=sys.stderr)
    for path, (lines, blocks) in docs.items():
        # Rewrite from the bottom so earlier line indexes stay valid.
        for name, (a, b) in sorted(blocks.items(), key=lambda kv: -kv[1][0]):
            body = sha_block(inp, path) if name == "sha" else built[name]
            lines[a + 1:b] = ["", *body.split("\n"), ""]
        new = "\n".join(lines)
        old = open(path).read()
        if new != old:
            with open(path, "w") as f:
                f.write(new)
        print(f"{path}: {len(blocks)} block(s), {'updated' if new != old else 'unchanged'}")


if __name__ == "__main__":
    main()
