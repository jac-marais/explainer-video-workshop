#!/usr/bin/env python3
"""Render a HyperFrames composition to a new MP4 with the known fixes applied.

  render.py --hf HYPERFRAMES_CLI_OR_HF_SH --project DIR COMPOSITION -o OUT.mp4 [--narration WAV]
            [--expect-seconds S] [--relabel-601] [--mark RUN_STATE.md PHASE SESSION...] [-- extra hyperframes args]
  render.py --skip-render INPUT.mp4 -o OUT.mp4 [same options]

COMPOSITION is passed to `hyperframes render DIR -c COMPOSITION`; use `.` for DIR/index.html.
The render runs on host Chrome with the GPU (HYPERFRAMES_BROWSER_PATH if set, else Google Chrome on macOS or the
first of google-chrome, chromium and chromium-browser on PATH elsewhere, as scripts/run/setup_check.sh finds it)
and one worker unless the extra args set --workers, and with
HF_DE_VERIFY=0 unless the environment sets it; it fails if the log shows a whole-film fallback to screenshot
capture (see both bottom-band traps in methods/renderer-traps.md). Telemetry, update checks and auto-install
are off and the Gemini/Google keys unset. OUT is never overwritten: if it exists, the run stops before rendering
and names the next free OUT.vN.mp4. Work happens in a temporary folder beside OUT.

--narration replaces the render's audio with the approved master as dual-mono stereo AAC (video is
stream-copied), padded with silence to the video length, and fails if its integrated loudness moves
more than 0.5 LU. --expect-seconds fails unless the frame count is within one frame of S x fps.
--relabel-601 retags the colour matrix as BT.601 in the bitstream and the MP4 box, without
re-encoding. Use it only for a render whose pixels measure as BT.601: a Docker image built
on ffmpeg 5.1 writes BT.601 pixels under a BT.709 tag, while the host CLI with ffmpeg 9.0.2 writes true
BT.709, so a host render must not be relabelled. --mark runs `runlog.py mark` after success.
Run check_film.py on OUT afterwards.

encoded_true_peak(WAV) is for a caller that mixes its own master: AAC can raise the true peak above the WAV's, so
measure the master as --narration will encode it before it reaches check_film.py's ceiling.
"""
import argparse, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_film import loudness, probe, rate, stream  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LINUX_BROWSERS = ("google-chrome", "chromium", "chromium-browser")


def host_browser():
    """The host Chrome or Chromium executable, or None to leave the choice to HyperFrames."""
    if sys.platform == "darwin":
        return CHROME if Path(CHROME).exists() else None
    return next((path for name in LINUX_BROWSERS if (path := shutil.which(name))), None)


def narration_filter(video_seconds=None):
    """The --narration audio filter: dual-mono 48 kHz, padded in whole AAC frames to the video length if given."""
    f = "aresample=48000,pan=stereo|c0=c0|c1=c0"
    return f + f",apad=whole_len={int(video_seconds * 48000) // 1024 * 1024}" if video_seconds is not None else f


def encoded_true_peak(wav):
    """True peak (dBTP) of a mono master after the AAC encoding that --narration applies."""
    with tempfile.TemporaryDirectory() as d:
        encoded = Path(d) / "encoded.m4a"
        subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", Path(wav).resolve(), "-af", narration_filter()] + aac_args()
                       + [encoded], stdin=subprocess.DEVNULL, check=True, capture_output=True)
        return loudness(encoded)[1]


def next_free(out):
    m = re.fullmatch(r"(.*)\.v(\d+)", out.stem)
    base, n = (m[1], int(m[2]) + 1) if m else (out.stem, 2)
    while (out.parent / f"{base}.v{n}{out.suffix}").exists():
        n += 1
    return out.parent / f"{base}.v{n}{out.suffix}"


def sh(cmd, **kw):
    print("+", " ".join(map(str, cmd)), flush=True)
    if subprocess.run(cmd, stdin=subprocess.DEVNULL, **kw).returncode:
        raise SystemExit(f"failed: {cmd[0]}")


def aac_args():
    encoders = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], stdin=subprocess.DEVNULL, capture_output=True, text=True).stdout
    if re.search(r"\baac_at\b", encoders):
        return ["-c:a", "aac_at", "-b:a", "192k"]
    # Noise substitution fills each channel with its own noise, which breaks identical channels.
    return ["-c:a", "aac", "-b:a", "192k", "-aac_pns", "0"]


def main():
    argv = sys.argv[1:]
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    argv = argv[:argv.index("--")] if "--" in argv else argv
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("composition", nargs="?")
    ap.add_argument("--hf", type=Path)
    ap.add_argument("--project", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--skip-render", type=Path, metavar="INPUT.mp4", help="post-process an existing render instead")
    ap.add_argument("--narration", type=Path)
    ap.add_argument("--expect-seconds", type=float)
    ap.add_argument("--relabel-601", action="store_true")
    ap.add_argument("--mark", nargs="+", metavar="ARG", help="RUN_STATE.md PHASE SESSION...")
    a = ap.parse_args(argv)
    if a.skip_render is None and not (a.hf and a.project and a.composition):
        ap.error("give --hf, --project and COMPOSITION, or --skip-render INPUT.mp4")
    if a.mark and len(a.mark) < 3:
        ap.error("--mark needs RUN_STATE.md PHASE SESSION...")
    out = a.out.resolve()
    if out.exists():
        sys.exit(f"{out} exists and is never overwritten; use {next_free(out)}")
    if a.narration:
        ch = stream(probe(a.narration), "audio")["channels"]
        if ch != 1:
            sys.exit(f"narration has {ch} channels; the master must be mono")

    out.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f".{out.stem}.", dir=out.parent))
    try:
        if a.skip_render:
            raw = a.skip_render.resolve()
        else:
            raw = work / "render.mp4"
            env = dict(os.environ, HYPERFRAMES_NO_TELEMETRY="1", DO_NOT_TRACK="1",
                       HYPERFRAMES_NO_UPDATE_CHECK="1", HYPERFRAMES_NO_AUTO_INSTALL="1")
            # The snapshot command sends frames to Gemini when a key is set.
            for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                env.pop(k, None)
            if "HYPERFRAMES_BROWSER_PATH" not in env and (browser := host_browser()):
                env["HYPERFRAMES_BROWSER_PATH"] = browser
            hf = [a.hf.resolve()] if a.hf.suffix != ".sh" else ["sh", a.hf.resolve()]
            # With more than one worker, host Chrome can drop the bottom 87 px of frames.
            if not any(x in ("-w", "--workers") or x.startswith(("-w=", "--workers=")) for x in extra):
                extra = ["--workers", "1"] + extra
            # Screenshot capture also drops the bottom 87 px, and a failed drawElement self-verify switches the whole film to it.
            env.setdefault("HF_DE_VERIFY", "0")
            cmd = hf + ["render", a.project.resolve(), "-c", a.composition, "-o", raw, "--browser-gpu"] + extra
            print("+", " ".join(map(str, cmd)), flush=True)
            proc = subprocess.Popen(cmd, env=env, cwd=a.project, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            fallback = False
            for line in proc.stdout:
                print(line, end="", flush=True)
                fallback = fallback or "re-rendering via screenshot" in line
            if proc.wait():
                raise SystemExit(f"failed: {cmd[0]}")
            if fallback:
                raise SystemExit("the render fell back to screenshot capture, which blanks the bottom 87 px; see methods/renderer-traps.md")

        final = work / "final.mp4"
        cmd = ["ffmpeg", "-v", "error", "-nostdin", "-i", raw]
        if a.narration:
            vdur = float(stream(probe(raw), "video")["duration"])
            ndur = float(probe(a.narration)["format"]["duration"])
            if ndur > vdur + 0.02:
                sys.exit(f"narration {ndur:.3f}s is longer than the video {vdur:.3f}s")
            cmd += ["-i", a.narration.resolve(), "-map", "0:v:0", "-map", "1:a:0",
                    # Whole AAC frames only, so the audio cannot outrun the picture.
                    "-af", narration_filter(vdur)] + aac_args()
        else:
            cmd += ["-map", "0", "-c:a", "copy"]
        cmd += ["-c:v", "copy", "-movflags", "+faststart"]
        if a.relabel_601:
            # Primaries and transfer stay BT.709 because the browser's pixels are sRGB; only the matrix was BT.601.
            cmd += ["-bsf:v", "h264_metadata=matrix_coefficients=6:colour_primaries=1:transfer_characteristics=1",
                    "-colorspace", "smpte170m", "-color_primaries", "bt709", "-color_trc", "bt709"]
        sh(cmd + [final])

        if a.narration:
            master, film = loudness(a.narration)[0], loudness(final)[0]
            delta = film - master
            print(f"loudness: master {master} LUFS, MP4 {film} LUFS, delta {delta:+.2f} LU")
            if abs(delta) > 0.5:
                sys.exit(f"loudness moved {delta:+.2f} LU (limit 0.5)")

        v = stream(probe(final), "video")
        fps, frames = rate(v), int(v["nb_read_packets"])
        print(f"frames: {frames} at {fps:g} fps = {frames / fps:.3f}s")
        if a.expect_seconds is not None and abs(frames - a.expect_seconds * fps) > 1:
            sys.exit(f"frame count {frames}, expected {a.expect_seconds} s x {fps:g} = {a.expect_seconds * fps:.1f}")

        # A hard link fails if OUT appeared meanwhile, so nothing is ever replaced.
        try:
            os.link(final, out)
        except FileExistsError:
            sys.exit(f"{out} appeared during the run; use {next_free(out)}")
        shutil.rmtree(work)
    except BaseException:
        if work.exists():
            print(f"left the work folder {work} for inspection", file=sys.stderr)
        raise
    print(f"wrote {out}")

    if a.mark:
        sh([sys.executable, Path(__file__).resolve().parent.parent / "run" / "runlog.py", "mark", *a.mark, "--note", out.name])


if __name__ == "__main__":
    main()
