#!/usr/bin/env python3
"""Final-film checks on an exact MP4. Prints failures only, then a one-line summary; exits 1 on any failure.

  check_film.py FILM.mp4 [--timing timing.json] [--captions captions.json] [--narration WAV]
                [--holds S-E,...] [--tail S] [--uncaptioned ID,...] [--caption-band x,y,w,h] [--sheet OUT_DIR]

Checks: container, codecs, size, fps, pix_fmt and a full decode; colour tags set and equal in the
MP4 `colr` box and the H.264 bitstream; dual-mono stereo AAC (left minus right at least 30 dB below
the signal); integrated loudness of one channel within 1 LU of -16 LUFS (the workshop measures the
mono narration that way) and true peak at most -1 dBTP; frame count against duration x fps; blank
black (over --max-black) pictures, and pictures frozen above the caption band (over --max-still), outside
the declared holds, plus the share of runtime spent still.
With --narration: duration against the narration (plus --tail if given), the loudness delta, and
silence edges within one frame of the master's. With --captions: each cue is visible in the caption
band and the band changes within one frame of its start and end, except --uncaptioned cues such as title cards. With --sheet and --timing: one
contact sheet per scene with a frame 0.1 s before each sentence ends, plus OUT_DIR/check_film.json
with every measurement.

Tags cannot show which matrix the pixels were encoded with; check a known brand colour for that.
Needs ffmpeg/ffprobe and the standard library; --sheet also needs Pillow.
"""
import argparse, json, math, mmap, re, subprocess, sys
from pathlib import Path

TARGET_LUFS, LUFS_TOL, MAX_TP = -16.0, 1.0, -1.0
EDGE = 1  # frames of slack at hold and duration edges


def run(cmd, check=True, text=True):
    r = subprocess.run(cmd, capture_output=True, text=text)
    if check and r.returncode:
        err = r.stderr if text else r.stderr.decode(errors="replace")
        sys.exit(f"command failed: {' '.join(map(str, cmd))}\n{err[-2000:]}")
    return r


def probe(path):
    out = run(["ffprobe", "-v", "error", "-count_packets", "-show_streams", "-show_format", "-of", "json", str(path)]).stdout
    return json.loads(out)


def stream(info, kind):
    return next((s for s in info["streams"] if s["codec_type"] == kind), None)


def rate(s):
    n, d = s["r_frame_rate"].split("/")
    return int(n) / int(d)


def loudness(path, channel=0):
    """Integrated LUFS and true peak (dBTP) of one channel."""
    err = run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-vn", "-af",
               f"pan=mono|c0=c{channel},ebur128=peak=true", "-f", "null", "-"]).stderr
    tail = err[err.rfind("Summary:"):]
    i = float(re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", tail)[1])
    tp = float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail)[1])
    return i, tp


def channel_difference(path):
    """RMS level (dBFS) of left minus right, and of the left channel; the first is -inf for identical channels."""
    def rms(pan):
        err = run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-vn", "-af",
                   f"pan=mono|c0={pan},astats=measure_overall=RMS_level:measure_perchannel=none", "-f", "null", "-"]).stderr
        return float(re.findall(r"RMS level dB:\s+(-?[\d.]+|-inf)", err)[-1])
    return rms("c0-c1"), rms("c0")


def silences(path, channel=0):
    err = run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-vn", "-af",
               f"pan=mono|c0=c{channel},silencedetect=n=-50dB:d=0.15", "-f", "null", "-"]).stderr
    return [float(x) for x in re.findall(r"silence_(?:start|end): (-?[\d.]+)", err)]


def colr_box(path):
    """(primaries, transfer, matrix, full_range) from the MP4 colr/nclx box, or None."""
    with open(path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
        i = data.find(b"colrnclx")
        if i < 0:
            return None
        p, t, m = (int.from_bytes(data[i + 8 + 2 * k:i + 10 + 2 * k], "big") for k in range(3))
        return p, t, m, data[i + 14] >> 7


H264_CODES = {"bt709": 1, "unknown": 2, "bt470bg": 5, "smpte170m": 6, "bt2020nc": 9, "bt2020": 9}


def video_scan(path, picture_h):
    """One decode pass: decode errors, black stretches, and frozen stretches of the picture above the captions."""
    err = run(["ffmpeg", "-nostats", "-hide_banner", "-loglevel", "level+info", "-i", str(path), "-an", "-filter_complex",
               "[0:v]split[a][b];"
               # A frame counts as black only when every pixel is dark, so line art on black is not black.
               "[a]blackdetect=d=0.1:pic_th=1.0:pix_th=0.10[ao];"
               # Caption changes would otherwise end every freeze, hiding a picture that holds for a whole paragraph.
               # The -60 dB floor (about 0.26 luma levels) is above the 0.01-0.08 level refresh that x264 keyframes add to a still picture.
               f"[b]crop=iw:{picture_h}:0:0,freezedetect=n=-60dB:d=1[bo]",
               "-map", "[ao]", "-f", "null", "-", "-map", "[bo]", "-f", "null", "-"], check=False).stderr
    errors = [l for l in err.splitlines() if re.search(r"\[(error|fatal|panic)\]", l)]
    black = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", err)]
    return errors, black, list(zip(starts, ends + [None] * (len(starts) - len(ends))))


def outside(span, holds, fps):
    """Longest part of span that lies outside every hold."""
    a, b = span
    pieces = [(a, b)]
    for h0, h1 in holds:
        h0, h1 = h0 - EDGE / fps, h1 + EDGE / fps
        pieces = [q for x, y in pieces for q in ((x, min(y, h0)), (max(x, h1), y)) if q[1] - q[0] > 1e-6]
    return max((y - x for x, y in pieces), default=0.0)


def select_frames(path, frames, vf, pix_fmt, size):
    """Raw frames for the given frame numbers, in one decode pass, keyed by frame number."""
    want = sorted(set(frames))

    def any_of(ns):
        # A balanced sum, because ffmpeg's expression parser runs out of depth on a long flat chain.
        return f"eq(n,{ns[0]})" if len(ns) == 1 else f"({any_of(ns[:len(ns) // 2])}+{any_of(ns[len(ns) // 2:])})"
    sel = any_of(want)
    raw = run(["ffmpeg", "-v", "error", "-i", str(path), "-an", "-vf", f"select='{sel}',{vf}", "-fps_mode", "passthrough",
               "-f", "rawvideo", "-pix_fmt", pix_fmt, "-"], text=False).stdout
    got = [raw[k * size:(k + 1) * size] for k in range(len(raw) // size)]
    if len(got) != len(want):
        sys.exit(f"asked for {len(want)} frames, decoded {len(got)}")
    return dict(zip(want, got))


DARK = bytes(range(161))


def bright(b):
    return len(b.translate(None, DARK))


def diff(a, b):
    return sum(abs(p - q) for p, q in zip(a[::3], b[::3])) / (len(a) / 3)


def caption_checks(path, cues, fps, nframes, crop):
    """For each cue: visible mid-cue, and the band changes within one frame of its start and its end."""
    def f(t):
        return min(max(round(t * fps), 0), nframes - 1)
    plan = []
    for k, c in enumerate(cues):
        s, e = f(c["start"]), f(c["end"])
        nxt = cues[k + 1]["start"] if k + 1 < len(cues) else None
        ends_alone = nxt is None or nxt - c["end"] > 6 / fps
        plan.append((c, s, e, ends_alone))
    need = []
    for _, s, e, alone in plan:
        need += [(s + e) // 2, s - 4, s - 2, s + 1, s + 3]
        if alone:
            need += [e - 4, e - 2, e + 1, e + 3]
    x, y, w, h = crop
    img = select_frames(path, [min(max(n, 0), nframes - 1) for n in need], f"crop={w}:{h}:{x}:{y}", "gray", w * h)

    def g(n):
        return img[min(max(n, 0), nframes - 1)]

    def step(n):
        """Change across frames n-2..n+1 against the change just before and just after."""
        jump = diff(g(n - 2), g(n + 1))
        calm = max(diff(g(n - 4), g(n - 2)), diff(g(n + 1), g(n + 3)))
        return jump, calm, jump > 0.5 and jump > 2 * calm

    rows, fails = [], []
    for c, s, e, alone in plan:
        mid = bright(g((s + e) // 2))
        on = step(s)
        off = step(e) if alone else None
        row = {"id": c.get("id"), "start": c["start"], "end": c["end"], "mid_bright_px": mid,
               "onset_jump": round(on[0], 2), "onset_calm": round(on[1], 2),
               "end_jump": off and round(off[0], 2), "end_calm": off and round(off[1], 2)}
        rows.append(row)
        text = c["text"].replace("\n", " / ")[:60]
        if mid < 200:
            fails.append(f"caption {c.get('id')} at {c['start']:.2f}s not visible mid-cue ({mid} bright px): {text!r}")
        elif not on[2]:
            fails.append(f"caption {c.get('id')} onset {c['start']:.2f}s: no change within a frame (jump {on[0]:.2f}, calm {on[1]:.2f}): {text!r}")
        if mid >= 200 and off and not off[2]:
            fails.append(f"caption {c.get('id')} end {c['end']:.2f}s: no change within a frame (jump {off[0]:.2f}, calm {off[1]:.2f}): {text!r}")
    return rows, fails


def contact_sheets(path, timing, fps, nframes, out_dir):
    from PIL import Image, ImageDraw, ImageFont
    W, H, COLS, LABEL = 640, 360, 3, 30
    font = ImageFont.load_default(size=22)
    sents = timing["sentences"]
    frames = [min(max(math.floor((s["end"] - 0.1) * fps), 0), nframes - 1) for s in sents]
    raw = select_frames(path, frames, f"scale={W}:{H}:flags=area", "rgb24", W * H * 3)
    img = {n: Image.frombytes("RGB", (W, H), b) for n, b in raw.items()}
    titles = {sc["id"]: sc.get("title", "") for sc in timing.get("scenes", [])}
    written = []
    for scene in dict.fromkeys(s["scene_id"] for s in sents):
        items = [(s, n) for s, n in zip(sents, frames) if s["scene_id"] == scene]
        rows = math.ceil(len(items) / COLS)
        sheet = Image.new("RGB", (COLS * W, LABEL + rows * (H + LABEL)), (40, 40, 40))
        d = ImageDraw.Draw(sheet)
        d.text((8, 4), f"{scene}  {titles.get(scene, '')}  ({path.name}, frame at sentence end - 0.1 s)", fill=(255, 255, 255), font=font)
        for k, (s, n) in enumerate(items):
            x, y = (k % COLS) * W, LABEL + (k // COLS) * (H + LABEL)
            d.text((x + 8, y + 4), f"{s['id']}  {n / fps:.2f}s  (ends {s['end']:.2f})", fill=(255, 210, 120), font=font)
            sheet.paste(img[n], (x, y + LABEL))
        p = out_dir / f"sheet-{scene}.png"
        sheet.save(p)
        written.append(str(p))
    return written


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("film", type=Path)
    ap.add_argument("--timing", type=Path)
    ap.add_argument("--captions", type=Path)
    ap.add_argument("--narration", type=Path)
    ap.add_argument("--holds", default="", help="declared still/black/silent stretches, S-E,S-E in film seconds")
    ap.add_argument("--tail", type=float, help="seconds the film should run past the narration")
    ap.add_argument("--sheet", type=Path, help="directory for the sentence-end contact sheets and check_film.json")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--max-still", type=float, default=6.0, help="longest allowed frozen picture outside holds, s")
    ap.add_argument("--max-black", type=float, default=0.5, help="longest allowed blank black picture outside holds, s")
    ap.add_argument("--caption-band", default="360,860,1200,170", help="x,y,w,h of the burnt-in caption area")
    ap.add_argument("--uncaptioned", default="", help="cue ids the film shows without burnt-in captions, such as title cards, id,id")
    a = ap.parse_args()
    if a.sheet and not a.timing:
        ap.error("--sheet needs --timing")
    holds = [tuple(map(float, h.split("-"))) for h in a.holds.split(",") if h]
    fails, rep = [], {"film": str(a.film.resolve()), "holds": holds}

    info = probe(a.film)
    v, au = stream(info, "video"), stream(info, "audio")
    fmt = info["format"]
    if v is None:
        sys.exit("no video stream")
    fps = rate(v)
    dur = float(v["duration"])
    nframes = int(v["nb_read_packets"])
    rep["video"] = {k: v.get(k) for k in ("codec_name", "profile", "width", "height", "pix_fmt", "r_frame_rate", "nb_frames",
                                          "nb_read_packets", "duration", "color_range", "color_space", "color_primaries",
                                          "color_transfer", "field_order", "sample_aspect_ratio")}
    rep["format"] = {k: fmt.get(k) for k in ("format_name", "duration", "size", "bit_rate")}

    def need(ok, msg):
        if not ok:
            fails.append(msg)

    need("mp4" in fmt["format_name"], f"container {fmt['format_name']}, want mp4")
    need(v["codec_name"] == "h264", f"video codec {v['codec_name']}, want h264")
    need(f"{v['width']}x{v['height']}" == a.size, f"size {v['width']}x{v['height']}, want {a.size}")
    need(abs(fps - a.fps) < 1e-6 and v["r_frame_rate"] == v["avg_frame_rate"], f"fps {v['r_frame_rate']} (avg {v['avg_frame_rate']}), want constant {a.fps:g}")
    need(v["pix_fmt"] == "yuv420p", f"pix_fmt {v['pix_fmt']}, want yuv420p")
    need(v.get("sample_aspect_ratio", "1:1") in ("1:1", "0:1"), f"sample aspect {v.get('sample_aspect_ratio')}, want 1:1")
    need(v.get("field_order", "progressive") == "progressive", f"field order {v.get('field_order')}, want progressive")

    # ffprobe's stream fields mirror the colr box when there is one, so read the bitstream tags from a decoded frame.
    frame = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "v", "-read_intervals", "%+#1", "-show_entries",
                            "frame=color_range,color_space,color_primaries,color_transfer", "-of", "json", str(a.film)]).stdout)["frames"][0]
    box = colr_box(a.film)
    rep["colour"] = {"bitstream": frame, "colr_box": box and dict(zip(("primaries", "transfer", "matrix", "full_range"), box))}
    tags = [frame.get(k, "unknown") for k in ("color_primaries", "color_transfer", "color_space")]
    need("unknown" not in tags and frame.get("color_range") == "tv", f"colour tags incomplete in the bitstream: {frame}")
    if box is None:
        fails.append("no colr box in the MP4, so players guess the colour matrix")
    else:
        sps = tuple(H264_CODES.get(t, -1) for t in tags) + (0,)
        need(box == sps, f"colour tags disagree: colr box (primaries, transfer, matrix, full) {box}, bitstream {tags} range {frame.get('color_range')}")

    errors, black, frozen = video_scan(a.film, int(a.caption_band.split(",")[1]))
    rep["decode_errors"] = errors[:20]
    need(not errors, f"{len(errors)} decode errors, first: {errors[:1]}")
    expect_n = round(dur * fps)
    rep["frames"] = {"packets": nframes, "nb_frames": v.get("nb_frames"), "duration_x_fps": dur * fps}
    need(abs(nframes - expect_n) <= EDGE and str(nframes) == str(v.get("nb_frames", nframes)),
         f"frame count {nframes} packets (header {v.get('nb_frames')}) vs duration {dur:.3f}s x {fps:g} = {dur * fps:.1f}")

    frozen = [(s, e if e is not None else dur) for s, e in frozen]
    rep["black"] = [{"start": s, "end": e, "outside_holds": round(outside((s, e), holds, fps), 3)} for s, e in black]
    rep["frozen"] = [{"start": s, "end": e, "outside_holds": round(outside((s, e), holds, fps), 3)} for s, e in frozen]
    for x in rep["black"]:
        need(x["outside_holds"] < a.max_black, f"blank black picture {x['start']:.2f}-{x['end']:.2f}s, {x['outside_holds']:.2f}s outside holds")
    for x in rep["frozen"]:
        need(x["outside_holds"] < a.max_still, f"frozen picture {x['start']:.2f}-{x['end']:.2f}s, {x['outside_holds']:.2f}s outside holds")
    rep["longest_still_outside_holds"] = max((x["outside_holds"] for x in rep["frozen"]), default=0)
    rep["still_share"] = round(sum(e - s for s, e in frozen) / dur, 3) if dur else 0

    if au is None:
        fails.append("no audio stream")
    else:
        rep["audio"] = {k: au.get(k) for k in ("codec_name", "profile", "channels", "channel_layout", "sample_rate", "duration", "bit_rate")}
        need(au["codec_name"] == "aac" and au["channels"] == 2 and au["sample_rate"] == "48000",
             f"audio {au['codec_name']} {au['channels']} ch {au['sample_rate']} Hz, want AAC stereo 48 kHz")
        if au["channels"] == 2:
            d, signal = channel_difference(a.film)
            rep["audio"].update(left_minus_right_rms_db=d, channel_rms_db=signal)
            # The native AAC encoder's noise substitution makes identical inputs differ slightly on sibilants.
            need(d <= signal - 30, f"channels differ (left minus right RMS {d} dB against {signal} dB), want dual mono")
        i, tp = loudness(a.film)
        rep["audio"].update(integrated_lufs=i, true_peak_dbtp=tp)
        need(abs(i - TARGET_LUFS) <= LUFS_TOL, f"integrated loudness {i} LUFS, want {TARGET_LUFS} +/- {LUFS_TOL}")
        need(tp <= MAX_TP, f"true peak {tp} dBTP, want <= {MAX_TP}")
        need(abs(float(au["duration"]) - dur) <= 2 / fps, f"audio runs {float(au['duration']):.3f}s, video {dur:.3f}s")

    if a.narration:
        nd = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(a.narration)]).stdout)
        ni, ntp = loudness(a.narration)
        rep["narration"] = {"path": str(a.narration.resolve()), "duration": nd, "integrated_lufs": ni, "true_peak_dbtp": ntp}
        need(dur >= nd - EDGE / fps, f"film {dur:.3f}s is shorter than the narration {nd:.3f}s")
        if a.tail is not None:
            need(abs(dur - (nd + a.tail)) <= EDGE / fps + 1e-6, f"film {dur:.3f}s, want narration {nd:.3f}s + tail {a.tail}s = {nd + a.tail:.3f}s")
        if au is not None:
            delta = rep["audio"]["integrated_lufs"] - ni
            rep["narration"]["loudness_delta_lu"] = round(delta, 2)
            need(abs(delta) <= 0.5, f"film audio is {delta:+.2f} LU from the narration master")
            ms, fs = silences(a.narration), silences(a.film)
            offs = [min((f - m for f in fs), key=abs, default=1e9) for m in ms if m < nd - 0.1]
            # An edge further than 0.1 s away is a pause that sits at the detector threshold in only one file.
            near = [abs(o) for o in offs if abs(o) <= 0.1]
            lost = len(offs) - len(near)
            worst = max(near, default=0)
            rep["narration"]["silence_edges"] = {"master": len(offs), "unmatched": lost, "worst_offset_s": round(worst, 4)}
            need(not offs or (near and lost <= max(2, len(offs) // 50) and worst <= EDGE / fps),
                 f"silence edges: {lost} of {len(offs)} master edges unmatched, worst matched offset {worst * 1000:.0f} ms (want <= 1 frame)")

    if a.captions:
        skip = set(filter(None, a.uncaptioned.split(",")))
        cues = sorted((c for c in json.loads(a.captions.read_text()) if c.get("id") not in skip), key=lambda c: c["start"])
        crop = tuple(map(int, a.caption_band.split(",")))
        rep["captions"], cfails = caption_checks(a.film, cues, fps, nframes, crop)
        fails += cfails

    if a.sheet:
        a.sheet.mkdir(parents=True, exist_ok=True)
        timing = json.loads(a.timing.read_text())
        rep["sheets"] = contact_sheets(a.film, timing, fps, nframes, a.sheet)

    rep["failures"] = fails
    if a.sheet:
        (a.sheet / "check_film.json").write_text(json.dumps(rep, indent=1))
    for f in fails:
        print("FAIL", f)
    au_s = f", {rep['audio']['integrated_lufs']} LUFS, TP {rep['audio']['true_peak_dbtp']}" if "audio" in rep else ""
    print(f"{'FAIL' if fails else 'PASS'} {a.film.name}: {len(fails)} failures; {dur:.3f}s, {nframes} frames{au_s}, "
          f"longest still outside holds {rep['longest_still_outside_holds']:.2f}s, stills {rep['still_share']:.0%} of runtime" + (f"; sheets in {a.sheet}" if a.sheet else ""))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
