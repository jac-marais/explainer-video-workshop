# /// script
# requires-python = "==3.12.*"
# dependencies = ["numpy==2.5.3", "soundfile==0.14.0", "mlx-whisper==0.4.3"]
# ///
"""Turn a scenes file into film narration: sentence WAVs, narration.wav, timing.json and words.json, then check the audio.

  narrate_film.py SCENES.json --voice NAME --out AUDIO_DIR [--spoken RESPELLINGS.json] [--reuse OLD_AUDIO_DIR] [--strict]
  narrate_film.py --check-only AUDIO_DIR [--out DIR]

SCENES.json is a list of scenes with id, title, visual, claim_ids and narration. The sentence split, the [pause] marker,
the gaps and the timing.json schema are those of narrate.py. RESPELLINGS.json maps a regex to the text the voice reads
instead (use (?i) for case-insensitive); it applies in order and never changes the captioned text.

Kokoro voices are synthesized one sentence at a time, because the model does not drift over a long text. Every other voice
is voiced in runs of about 60 to 120 s (local/voice/plan_runs.py), one take per run ending in a throwaway sentence, and cut
into sentences by local/voice/cut_takes.py.
Each sentence WAV is cached under a hash of the voice config and the spoken text, so --reuse (or a rerun into the same
AUDIO_DIR) voices only the sentences that changed.
words.json holds one row per word of the script, timed by aligning Whisper's transcript of narration.wav to it.
A word Whisper did not time is interpolated and listed in audio-checks.json; --strict exits non-zero if there is one.
audio-checks.json lists only failures. --check-only runs the same checks on finished audio (timing.json and narration.wav)
and exits non-zero on any flag; it writes audio-checks.json only if --out is given."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Whisper must come from the local cache; nothing here downloads.
os.environ["HF_HUB_OFFLINE"] = "1"

import numpy as np
import soundfile as sf

WS = Path(__file__).resolve().parents[2]
VOICE_DIR = WS / "local/voice"
WHISPER = "mlx-community/whisper-large-v3-turbo"
RATE = 24000
LEAD_IN, SENTENCE_PAUSE, SCENE_PAUSE, EXPLICIT_PAUSE, TAIL = 0.35, 0.22, 0.50, 3.0, 0.45
LOUDNORM = "I=-16:TP=-1.5:LRA=11"
WPM = 165
THROWAWAY = "That's all for now."
# Thresholds are set so the Kokoro audio of the v4 reference film raises nothing (its largest values are in parentheses).
LEVEL_DEV_DB = 3.0  # a sentence's level from the film median (1.2)
SCENE_JUMP_DB = 2.5  # the level change across a scene boundary (0.7)
TAIL_ABOVE_FLOOR_DB = 20.0  # the last 60 ms above the film's noise floor (14.0)
LUFS_TOLERANCE, TRUE_PEAK_MAX = 1.0, -1.0  # v4 measures -16.3 LUFS and -1.47 dBTP
TAIL_S = 0.06
FRAME_S = 0.01
SMOOTH = 5
FLOOR_PCT = 5
ALIGN_SLACK_S = 0.6  # a match this far outside its sentence is a false match
SIMILAR = 0.8  # letter similarity at which an ASR difference counts as spelling


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def letters(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def sentences(text: str) -> list[dict]:
    """Same split as production/scripts/narrate.py."""
    normalized = " ".join(text.split())
    if not normalized:
        raise ValueError("scene narration must not be empty")
    marker = "␞PAUSE␞"
    normalized = re.sub(r"\s*\[pause\]\s*", f" {marker} ", normalized, flags=re.IGNORECASE)
    result = []
    for part in re.split(r"(?<=[.!?])\s+", normalized):
        pause_before = marker in part
        clean = " ".join(part.replace(marker, " ").split())
        if clean:
            result.append({"text": clean, "pause_before": pause_before})
    return result


def load_scenes(path: Path) -> list[dict]:
    source = json.loads(path.read_text())
    if not isinstance(source, list) or not source:
        raise SystemExit("scenes file must contain a non-empty array of scene objects")
    ids, scenes = set(), []
    for index, scene in enumerate(source, 1):
        scene_id = scene.get("id") if isinstance(scene, dict) else None
        if not isinstance(scene_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", scene_id):
            raise SystemExit(f"scene {index} needs a filesystem-safe string id")
        if scene_id in ids:
            raise SystemExit(f"duplicate scene id: {scene_id}")
        ids.add(scene_id)
        for key in ("title", "visual"):
            if not isinstance(scene.get(key), str) or not scene[key].strip():
                raise SystemExit(f"scene {scene_id} needs a non-empty {key}")
        if not isinstance(scene.get("claim_ids"), list) or not all(isinstance(item, str) for item in scene["claim_ids"]):
            raise SystemExit(f"scene {scene_id} needs claim_ids as an array of strings")
        narration = scene.get("narration")
        if isinstance(narration, str):
            narration = [narration]
        if not (isinstance(narration, list) and narration and all(isinstance(item, str) for item in narration)):
            raise SystemExit(f"scene {scene_id} narration must be a string or a non-empty array of strings")
        scenes.append({**scene, "_sentences": [part for item in narration for part in sentences(item)]})
    return scenes


def load_respellings(path: Path | None) -> list[tuple[re.Pattern, str]]:
    if path is None:
        return []
    mapping = json.loads(path.read_text())
    if not isinstance(mapping, dict):
        raise SystemExit(f"{path} must be a JSON object of regex to replacement")
    return [(re.compile(pattern), replacement) for pattern, replacement in mapping.items()]


def voice_identity(name: str) -> tuple[dict, str]:
    config = json.loads((VOICE_DIR / "voice.json").read_text())
    if name not in config["voices"]:
        raise SystemExit(f"Unknown voice '{name}'; available: {', '.join(config['voices'])}")
    spec = config["voices"][name]
    refs = {key: sha256((VOICE_DIR / spec[key]).read_bytes()) for key in ("ref_audio", "ref_text") if key in spec}
    return spec, sha256(json.dumps({"voice": name, "spec": spec, "refs": refs}, sort_keys=True).encode())


def cache_key(identity: str, spoken: str) -> str:
    return sha256(f"{identity}\n{spoken}".encode())


def run_uv(script: str, args: list[str], capture: bool = False) -> str:
    result = subprocess.run(["uv", "run", "--offline", str(VOICE_DIR / script), *map(str, args)], text=True,
                            stdout=subprocess.PIPE if capture else None, stderr=None if not capture else subprocess.PIPE)
    if result.returncode:
        raise SystemExit(f"{script} failed (exit {result.returncode})\n{(result.stderr or '')[-2000:]}")
    if capture and result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.stdout or ""


def read_audio(path: Path) -> np.ndarray:
    samples, rate = sf.read(path, dtype="float32")
    if rate != RATE or samples.ndim != 1 or not len(samples):
        raise SystemExit(f"{path} must be non-empty mono {RATE} Hz audio")
    return samples


def plan_runs(seconds: dict[str, float], work: Path) -> list[list[str]]:
    if len(seconds) > 18:
        raise SystemExit("plan_runs.py tries every grouping, so it handles at most 18 scenes with sentences to voice")
    empty = work / "plan-receipts"
    empty.mkdir(exist_ok=True)
    out = run_uv("plan_runs.py", [empty, "--seconds", *(f"{k}={v:.1f}" for k, v in seconds.items())], capture=True)
    best = next(line for line in out.splitlines() if " || violation" in line)
    ids = list(seconds)
    runs = []
    for part in best.split("  ||")[0].split(" | "):
        first, _, last = part.split()[0].partition("-")
        runs.append(ids[ids.index(first):ids.index(last or first) + 1])
    log("runs: " + best)
    return runs


def voice_takes(name: str, spec: dict, pending: list[dict], work: Path) -> tuple[dict[str, np.ndarray], list[dict]]:
    """Voice the pending sentences; return their samples by id and the cuts that were not clean."""
    work.mkdir(parents=True, exist_ok=True)
    if spec["engine"] == "kokoro":
        for row in pending:
            (work / f"{row['id']}.txt").write_text(row["spoken"])
        run_uv("voice.py", [*(work / f"{row['id']}.txt" for row in pending), "--out-dir", work, "--voice", name])
        return {row["id"]: read_audio(work / f"{row['id']}.wav") for row in pending}, []
    units: dict[str, list[dict]] = {}
    for row in pending:
        units.setdefault(row["alias"], []).append(row)
    seconds = {alias: sum(len(r["spoken"].split()) for r in rows) / WPM * 60 for alias, rows in units.items()}
    takes = []
    for run in plan_runs(seconds, work):
        stem = run[0] if len(run) == 1 else f"{run[0]}-{run[-1]}"
        (work / f"{stem}.txt").write_text(" ".join(r["spoken"] for alias in run for r in units[alias]) + " " + THROWAWAY)
        takes.append(work / f"{stem}.txt")
    run_uv("voice.py", [*takes, "--out-dir", work, "--voice", name])
    (work / "sentences.json").write_text(json.dumps([{"id": r["id"], "scene": r["alias"], "text": r["spoken"]} for r in pending]))
    cut = work / "cut"
    out = run_uv("cut_takes.py", [*(t.with_suffix(".wav") for t in takes), "--sentences", work / "sentences.json", "--out", cut,
                                  "--throwaway", THROWAWAY], capture=True)
    lines = [json.loads(line) for line in out.splitlines() if line.startswith("{")]
    unclean = [{"check": "unclean_cut", "take": r["take"], "after": r["after"], "gap_s": r["gap_s"]}
               for r in lines if r.get("clean") is False]
    return {row["id"]: read_audio(cut / f"{row['id']}.wav") for row in pending}, unclean


def assemble(scenes: list[dict], rows: dict[str, dict], audio: dict[str, np.ndarray]) -> tuple[np.ndarray, list[dict], list[dict], float]:
    """Join the sentences with narrate.py's gaps; return the audio, the scene rows, the sentence rows and the duration."""
    parts, scene_rows, sentence_rows = [np.zeros(int(LEAD_IN * RATE), dtype="float32")], [], []
    cursor, previous = LEAD_IN, None
    for scene in scenes:
        scene_start = cursor
        for index, sentence in enumerate(scene["_sentences"], 1):
            explicit = sentence["pause_before"]
            gap = EXPLICIT_PAUSE if explicit else (0 if previous is None else SCENE_PAUSE if previous != scene["id"] else SENTENCE_PAUSE)
            if gap:
                parts.append(np.zeros(int(gap * RATE), dtype="float32"))
                cursor += gap
            row = rows[f"{scene['id']}-{index:02d}"]
            samples = audio[row["id"]]
            start, end = cursor, cursor + len(samples) / RATE
            sentence_rows.append({"id": row["id"], "scene_id": scene["id"], "text": row["text"], "spoken_text": row["spoken"],
                                  "pause_before": explicit, "start": round(start, 3), "end": round(end, 3),
                                  "audio": f"sentences/{row['id']}.wav"})
            parts.append(samples)
            cursor, previous = end, scene["id"]
        scene_rows.append({"id": scene["id"], "title": scene["title"], "visual": scene["visual"],
                           "claim_ids": scene["claim_ids"], "start": round(scene_start, 3), "end": round(cursor, 3)})
    parts.append(np.zeros(int(TAIL * RATE), dtype="float32"))
    return np.concatenate(parts), scene_rows, sentence_rows, cursor + TAIL


def ffmpeg(args: list[str]) -> str:
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True, check=True).stderr


def measure_loudness(path: Path) -> dict:
    log_text = ffmpeg(["-i", str(path), "-af", f"loudnorm={LOUDNORM}:print_format=json", "-f", "null", "-"])
    return json.JSONDecoder().raw_decode(log_text[log_text.rfind("{"):])[0]


def normalize(raw: Path, final: Path) -> None:
    """Two-pass linear loudnorm as voice.py does, written as narrate.py does: 48 kHz, 24-bit mono."""
    m = measure_loudness(raw)
    apply = (f"loudnorm={LOUDNORM}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
             f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    ffmpeg(["-y", "-i", str(raw), "-af", apply, "-ar", "48000", "-ac", "1", "-c:a", "pcm_s24le", str(final)])


def transcribe(path: Path) -> tuple[list[dict], str]:
    import mlx_whisper
    from huggingface_hub import snapshot_download

    log("transcribing narration.wav")
    result = mlx_whisper.transcribe(str(path), path_or_hf_repo=WHISPER, language="en", word_timestamps=True,
                                    condition_on_previous_text=False)
    words = [{"word": w["word"], "start": float(w["start"]), "end": float(w["end"])} for seg in result["segments"] for w in seg["words"]]
    if not words:
        raise SystemExit("Whisper returned zero words")
    return words, snapshot_download(WHISPER, local_files_only=True)


def align_words(sents: list[dict], asr: list[dict]) -> tuple[list[list[dict]], list[dict]]:
    """Time each word of the script from Whisper's words, matched by letters so a respelled or merged word still lines up."""
    script = [(k, token) for k, s in enumerate(sents) for token in s["text"].split()]
    ref, ref_word = "", []
    for i, (_, token) in enumerate(script):
        ref += letters(token)
        ref_word += [i] * len(letters(token))
    hyp, hyp_time = "", []
    for w in asr:
        chars = letters(w["word"])
        if chars.isdigit() and readings(chars):
            chars = next((r for r in sorted(readings(chars)) if r in ref), chars)
        step = (w["end"] - w["start"]) / max(1, len(chars))
        hyp += chars
        hyp_time += [(w["start"] + step * j, w["start"] + step * (j + 1)) for j in range(len(chars))]
    hits: dict[int, list] = {}
    for a, b, n in difflib.SequenceMatcher(None, ref, hyp, autojunk=False).get_matching_blocks():
        for d in range(n):
            hits.setdefault(ref_word[a + d], []).append(hyp_time[b + d])
    times: list[tuple[float, float] | None] = []
    for i, (k, token) in enumerate(script):
        got = hits.get(i, [])
        span = None
        if got and 2 * len(got) >= len(letters(token)):
            start, end = min(t[0] for t in got), max(t[1] for t in got)
            near = start <= sents[k]["end"] + ALIGN_SLACK_S and end >= sents[k]["start"] - ALIGN_SLACK_S
            # Whisper stretches a sentence's first word back over the pause before it.
            clamped = (max(start, sents[k]["start"]), min(end, sents[k]["end"]))
            span = clamped if near and clamped[0] < clamped[1] else None
        times.append(span)
    fallbacks = []
    for i, (k, token) in enumerate(script):
        if times[i] is not None:
            continue
        lo = i
        while lo > 0 and script[lo - 1][0] == k and times[lo - 1] is None:
            lo -= 1
        hi = i
        while hi + 1 < len(script) and script[hi + 1][0] == k and times[hi + 1] is None:
            hi += 1
        left = times[lo - 1][1] if lo > 0 and script[lo - 1][0] == k else sents[k]["start"]
        right = times[hi + 1][0] if hi + 1 < len(script) and script[hi + 1][0] == k else sents[k]["end"]
        right = max(right, left + 0.05 * (hi - lo + 1))
        weights = [max(1, len(letters(script[j][1]))) for j in range(lo, hi + 1)]
        cursor = left
        for j, weight in zip(range(lo, hi + 1), weights):
            times[j] = (cursor, cursor + (right - left) * weight / sum(weights))
            cursor = times[j][1]
            if letters(script[j][1]):
                fallbacks.append({"sentence": sents[k]["id"], "word": script[j][1], "start": round(times[j][0], 3)})
    rows: list[list[dict]] = [[] for _ in sents]
    for (k, token), (start, end) in zip(script, times):
        rows[k].append({"text": token, "start": round(start, 3), "end": round(end, 3)})
    return rows, fallbacks


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def say(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + (ONES[n % 10] if n % 10 else "")
    unit, big = (100, "hundred") if n < 1000 else (1000, "thousand")
    return say(n // unit) + big + (say(n % unit) if n % unit else "")


def readings(digits: str) -> set[str]:
    """How an integer is read aloud: as a cardinal, and as a year when it looks like one."""
    n = int(digits)
    found = {say(n)} if n < 10**6 else set()
    if 1100 <= n < 10000 and n % 100:
        found.add(say(n // 100) + say(n % 100))
    return found


def asr_differences(sents: list[dict], asr: list[dict]) -> list[dict]:
    """Words Whisper heard that the script does not say, ignoring spelling, spacing and the spoken respelling."""
    script = [(k, t) for k, s in enumerate(sents) for t in s["text"].split() if letters(t)]
    heard = [letters(w["word"]) for w in asr if letters(w["word"])]
    spoken = [letters(s["spoken_text"]) for s in sents]
    found = []
    ops = difflib.SequenceMatcher(None, [letters(t) for _, t in script], heard, autojunk=False).get_opcodes()
    for tag, a1, a2, b1, b2 in ops:
        if tag == "equal":
            continue
        want, got = "".join(letters(t) for _, t in script[a1:a2]), "".join(heard[b1:b2])
        k = script[min(a1, len(script) - 1)][0]
        if b2 - b1 == 1 and heard[b1].isdigit() and want in readings(heard[b1]):
            continue
        if want == got or (got and got in spoken[k]) or difflib.SequenceMatcher(None, want, got).ratio() >= SIMILAR:
            continue
        found.append({"check": "asr_difference", "sentence": sents[k]["id"],
                      "script": " ".join(t for _, t in script[a1:a2]), "heard": " ".join(heard[b1:b2])})
    return found


def level_flags(sents: list[dict], scenes: list[str], samples: np.ndarray, rate: int) -> tuple[list[dict], dict]:
    n = int(rate * FRAME_S)
    power = np.mean(samples[: len(samples) // n * n].reshape(-1, n) ** 2, axis=1)
    smooth = 10 * np.log10(np.convolve(power, np.ones(SMOOTH) / SMOOTH, mode="same") + 1e-18)
    floor = float(np.percentile(smooth[power > 0], FLOOR_PCT))
    levels, tails = [], []
    for s in sents:
        a, b = round(s["start"] / FRAME_S), round(s["end"] / FRAME_S)
        frames = power[a:b]
        levels.append(float(10 * np.log10(frames[frames > frames.max() * 1e-3].mean())))
        tails.append(float(10 * np.log10(power[max(a, b - round(TAIL_S / FRAME_S)):b].mean() + 1e-18)))
    median = statistics.median(levels)
    flags = []
    for s, level, tail in zip(sents, levels, tails):
        if abs(level - median) > LEVEL_DEV_DB:
            flags.append({"check": "loudness_outlier", "sentence": s["id"], "db_from_median": round(level - median, 1)})
        if tail > floor + TAIL_ABOVE_FLOOR_DB:
            flags.append({"check": "word_cut_short", "sentence": s["id"], "tail_db_above_floor": round(tail - floor, 1)})
    for i in range(len(sents) - 1):
        if scenes[i] != scenes[i + 1] and abs(levels[i + 1] - levels[i]) > SCENE_JUMP_DB:
            flags.append({"check": "scene_jump", "between": [sents[i]["id"], sents[i + 1]["id"]], "db": round(levels[i + 1] - levels[i], 1)})
    return flags, {"median_sentence_db": round(median, 1), "max_dev_db": round(max(abs(v - median) for v in levels), 1),
                   "noise_floor_db": round(floor, 1), "max_tail_above_floor_db": round(max(tails) - floor, 1)}


def audio_checks(timing: dict, wav: Path, asr: list[dict], unclean: list[dict]) -> tuple[list[dict], dict]:
    samples, rate = sf.read(wav, dtype="float32")
    sents = timing["sentences"]
    flags = list(unclean)
    level, stats = level_flags(sents, [s["scene_id"] for s in sents], samples, rate)
    flags += level
    flags += asr_differences(sents, asr)
    loud = measure_loudness(wav)
    stats.update({"integrated_lufs": float(loud["input_i"]), "true_peak_dbtp": float(loud["input_tp"])})
    if abs(stats["integrated_lufs"] + 16) > LUFS_TOLERANCE or stats["true_peak_dbtp"] > TRUE_PEAK_MAX:
        flags.append({"check": "loudness_target", "lufs": stats["integrated_lufs"], "true_peak_dbtp": stats["true_peak_dbtp"]})
    wav_s = len(samples) / rate
    if abs(wav_s - timing["duration"]) > 0.01:
        flags.append({"check": "duration_mismatch", "wav_s": round(wav_s, 3), "timing_s": timing["duration"]})
    stats["duration_s"] = round(wav_s, 3)
    return flags, stats


def report(flags: list[dict], stats: dict, fallbacks: list[dict], out: Path | None) -> dict:
    result = {"ok": not flags, "flags": flags, "stats": stats, "fallback_words": fallbacks}
    if out:
        (out / "audio-checks.json").write_text(json.dumps(result, indent=2) + "\n")
    for flag in flags:
        print("FLAG " + json.dumps(flag))
    print(json.dumps({"ok": result["ok"], "flags": len(flags), "fallback_words": len(fallbacks), **stats}))
    return result


def check_only(audio_dir: Path, out: Path | None) -> None:
    timing = json.loads((audio_dir / "timing.json").read_text())
    asr, _ = transcribe(audio_dir / "narration.wav")
    flags, stats = audio_checks(timing, audio_dir / "narration.wav", asr, [])
    _, fallbacks = align_words(timing["sentences"], asr)
    if out:
        out.mkdir(parents=True, exist_ok=True)
    result = report(flags, stats, fallbacks, out)
    sys.exit(0 if result["ok"] else 1)


def narrate(args: argparse.Namespace) -> None:
    started = time.perf_counter()
    scenes = load_scenes(args.scenes)
    respellings = load_respellings(args.spoken)
    spec, identity = voice_identity(args.voice)
    rows: dict[str, dict] = {}
    for number, scene in enumerate(scenes, 1):
        for index, sentence in enumerate(scene["_sentences"], 1):
            spoken = sentence["text"]
            for pattern, replacement in respellings:
                spoken = pattern.sub(replacement, spoken)
            sid = f"{scene['id']}-{index:02d}"
            rows[sid] = {"id": sid, "alias": f"S{number:02d}", "text": sentence["text"], "spoken": spoken, "key": cache_key(identity, spoken)}

    out = args.out
    audio: dict[str, np.ndarray] = {}
    sources = [d for d in (args.reuse, out) if d and (d / "sentence-hashes.json").is_file()]
    known: dict[str, Path] = {}
    for directory in sources:
        for sid, key in json.loads((directory / "sentence-hashes.json").read_text()).items():
            if (directory / "sentences" / f"{sid}.wav").is_file():
                known[key] = directory / "sentences" / f"{sid}.wav"
    for row in rows.values():
        if row["key"] in known:
            audio[row["id"]] = read_audio(known[row["key"]])
    reused = len(audio)
    pending = [row for row in rows.values() if row["id"] not in audio]
    log(f"{reused} sentences reused, {len(pending)} to voice with {args.voice}")
    unclean: list[dict] = []
    out.mkdir(parents=True, exist_ok=True)
    if pending:
        voiced, unclean = voice_takes(args.voice, spec, pending, out / "takes")
        audio.update(voiced)

    samples, scene_rows, sentence_rows, duration = assemble(scenes, rows, audio)
    shutil.rmtree(out / "sentences", ignore_errors=True)
    (out / "sentences").mkdir()
    for sid, data in audio.items():
        sf.write(out / "sentences" / f"{sid}.wav", data, RATE, subtype="PCM_16")
    (out / "sentence-hashes.json").write_text(json.dumps({sid: rows[sid]["key"] for sid in audio}, indent=1) + "\n")
    sf.write(out / "narration-raw.wav", samples, RATE, subtype="PCM_16")
    normalize(out / "narration-raw.wav", out / "narration.wav")
    timing = {"source_sha256": sha256(args.scenes.read_bytes()), "voice": args.voice, "speed": spec.get("speed"),
              "sample_rate": RATE, "duration": round(duration, 3), "frames_30fps": round(duration * 30),
              "scenes": scene_rows, "sentences": sentence_rows,
              "pauses": {"lead_in": LEAD_IN, "between_sentences": SENTENCE_PAUSE, "between_scenes": SCENE_PAUSE,
                         "explicit": EXPLICIT_PAUSE, "tail": TAIL}}
    (out / "timing.json").write_text(json.dumps(timing, indent=2) + "\n")

    asr, model_path = transcribe(out / "narration.wav")
    word_rows, fallbacks = align_words(sentence_rows, asr)
    words = [w for sentence in word_rows for w in sentence]
    (out / "words.json").write_text(json.dumps({
        "model": "mlx-whisper large-v3-turbo", "model_path": model_path, "language": "en", "language_probability": 1,
        "duration": timing["duration"], "word_count": len(words),
        "segments": [{"text": s["text"], "start": w[0]["start"], "end": w[-1]["end"]} for s, w in zip(sentence_rows, word_rows)],
        "words": words}, indent=2) + "\n")

    flags, stats = audio_checks(timing, out / "narration.wav", asr, unclean)
    stats.update({"sentences": len(rows), "reused": reused, "voiced": len(pending), "wall_s": round(time.perf_counter() - started, 1)})
    report(flags, stats, fallbacks, out)
    if args.strict and fallbacks:
        raise SystemExit(f"--strict: {len(fallbacks)} script word(s) have no Whisper time; see fallback_words in audio-checks.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scenes", nargs="?", type=Path, metavar="SCENES.json")
    parser.add_argument("--voice", help="voice name from local/voice/voice.json")
    parser.add_argument("--out", type=Path, metavar="AUDIO_DIR")
    parser.add_argument("--spoken", type=Path, metavar="RESPELLINGS.json")
    parser.add_argument("--reuse", type=Path, metavar="OLD_AUDIO_DIR")
    parser.add_argument("--strict", action="store_true", help="exit non-zero if any script word has no Whisper time")
    parser.add_argument("--check-only", type=Path, metavar="AUDIO_DIR", help="check finished audio and exit")
    args = parser.parse_args()
    if args.check_only:
        return check_only(args.check_only, args.out)
    if not (args.scenes and args.voice and args.out):
        parser.error("provide SCENES.json, --voice and --out (or --check-only)")
    narrate(args)


if __name__ == "__main__":
    main()
