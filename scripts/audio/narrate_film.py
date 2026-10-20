"""Turn a scenes file into film narration: sentence WAVs, narration.wav, timing.json and words.json, then check the audio.

  narrate_film.py SCENES.json --voice NAME --out AUDIO_DIR [--spoken RESPELLINGS.json] [--reuse OLD_AUDIO_DIR] [--strict]
                  [--language CODE]
  narrate_film.py --check-only AUDIO_DIR [--out DIR] [--language CODE]

--language (default en) selects Whisper, number matching, Stanza's sentence splitter and the eSpeak voice that estimates take
lengths; the voice's own language is set in voice.json. Run it with scripts/run/py, which has Stanza and eSpeak's bindings.

SCENES.json is a list of scenes with id, title, visual, claim_ids and narration, split into sentences by text_tokens.py.
Sentences of one scene from the same take join without an added gap after the edge silence cap
described in methods/voice-explainer-video.md; the other gaps are in assemble(). RESPELLINGS.json maps a regex to the text the voice reads
instead (use (?i) for case-insensitive); it applies in order, a later rule leaves an earlier rule's pin whole,
and it never changes the captioned text.

Kokoro voices are synthesized one sentence at a time, because the model does not drift over a long text. Every other voice
is voiced in bounded runs (templates/voice/plan_runs.py), one take per run ending in a throwaway sentence, and cut
into sentences by templates/voice/cut_takes.py. A take longer than twice its estimate, or one the cutter cannot cut in order,
has looped and is re-voiced, at most twice.
Sentence WAVs are keyed by voice config and spoken text, and takes.json records each sentence's original take id.
--reuse and reruns follow the canonical take-level reuse rule in methods/voice-explainer-video.md#take-level-reuse.
words.json holds one row per whitespace word or Han/Kana character of the script, timed by aligning Whisper's transcript of narration.wav to it.
Number matching supports fr/pt/es/hi/zh/ko integers below a million (pt and es in either gender), decimals and percents, also inside a heard word (12층); English cardinals/years stay unchanged.
Sentences with fallback words are re-transcribed once from narration.wav, merging adjacent sentences and padding
0.15 s at each end (clamped to the file). In non-English narration, spans with Latin-script fallbacks are also heard
in English, replacing words between matched neighbours. A span's words replace the long-form ones only when fewer words
fall back, and the result feeds both alignment and difference checks, including --check-only; audio-checks stats record
retranscribed_spans and english_retranscribed_spans when nonzero. Fully aligned runs are unchanged.
A word Whisper still did not time is interpolated and listed in audio-checks.json; --strict exits non-zero if there is one.
audio-checks.json lists only failures. --check-only runs the same checks on finished audio (timing.json and narration.wav)
and exits non-zero on any flag; it writes audio-checks.json only if --out is given."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import difflib
import functools
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
import unicodedata
import uuid
from pathlib import Path

# Whisper must come from the local cache; nothing here downloads.
os.environ["HF_HUB_OFFLINE"] = "1"

from text_tokens import norm as letters, tokenize, normalized_tokens, sentences
from number_readings import LANGUAGES, spoken_numbers

import numpy as np
import soundfile as sf

WS = Path(__file__).resolve().parents[2]
TOOLS_DIR = WS / "templates/voice"
VOICE_DIR = WS / "local/voice"
WHISPER = "mlx-community/whisper-large-v3-turbo"
if sys.platform == "linux":
    from linux_whisper import MODEL as WHISPER
RATE = 24000
LEAD_IN, SENTENCE_PAUSE, SCENE_PAUSE, EXPLICIT_PAUSE, TAIL = 0.35, 0.22, 0.50, 3.0, 0.45
LOUDNORM = "I=-16:TP=-1.5:LRA=11"
ESPEAK = Path("/opt/homebrew/opt/espeak-ng")
# The slowest language's measured rate, because an overestimate only shortens a take but an underestimate can exceed MAX_TAKE_SECONDS.
PHONEMES_PER_SECOND = 9.0
MAX_TAKE_SECONDS = 120
TAKE_RESERVE_SECONDS = 10
# A take lands near its estimate, while a looping generation often runs several times longer.
RUNAWAY_FACTOR, RUNAWAY_RETRIES = 2.0, 2
UNCUTTABLE_EXIT = 3  # cut_takes.py's exit code for a take whose sentences it cannot cut in order
THROWAWAY = "That's all for now."
# Thresholds are set so the Kokoro audio of the v4 reference film raises nothing (its largest values are in parentheses).
LEVEL_DEV_DB = 3.0  # a sentence's level from the film median (1.2)
SCENE_JUMP_DB = 2.5  # the level change across a scene boundary (0.7)
TAIL_ABOVE_FLOOR_DB = 20.0  # the last 60 ms above the film's noise floor (14.0)
LUFS_TOLERANCE, TRUE_PEAK_MAX = 1.0, -1.0  # v4 measures -16.3 LUFS and -1.47 dBTP
TAIL_S = 0.06
FRAME_S = 0.01
SENTENCE_MATCH_DB = 1.2
SENTENCE_GAIN_CAP_DB = 8.0
SENTENCE_PEAK_DBFS = -2.0
EDGE_SILENCE_S = 0.3  # Some voices leave long silent edges between sentences.
SMOOTH = 5
FLOOR_PCT = 5
ALIGN_SLACK_S = 0.6  # a match this far outside its sentence is a false match
SIMILAR = 0.8  # letter similarity at which an ASR difference counts as spelling


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()



def load_scenes(path: Path, language: str) -> list[dict]:
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
        scenes.append({**scene, "_sentences": [part for item in narration for part in sentences(item, language)]})
    return scenes


# A pin an earlier rule wrote, [word](/phonemes/) or [text](language), which later rules leave whole.
PIN = re.compile(r"(\[[^\]]+\]\([^)]*\))")


def respell(text: str, rules: list[tuple[re.Pattern, str]]) -> str:
    """Apply each rule in order to the text outside earlier rules' pins."""
    for pattern, replacement in rules:
        text = "".join(part if k % 2 else pattern.sub(replacement, part) for k, part in enumerate(PIN.split(text)))
    return text


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
    identity = {"voice": name, "spec": spec, "refs": refs}
    # CPU Qwen is a different generation backend; retain legacy Mac and Kokoro cache keys.
    if sys.platform == "linux" and spec["engine"] in ("qwen3", "qwen3-preset"):
        identity["backend"] = "qwen-tts-cpu-float32-v1"
    return spec, sha256(json.dumps(identity, sort_keys=True).encode())


def cache_key(identity: str, spoken: str) -> str:
    return sha256(f"{identity}\n{spoken}".encode())


@dataclass
class ReuseSource:
    directory: Path
    hashes: dict[str, str]
    takes: dict[str, str] | None
    scenes: dict[str, str]
    audio: dict[str, Path]
    unclean: list[dict] = field(default_factory=list)
    manifests: dict[str, dict] = field(default_factory=dict)


@dataclass
class ReuseDecision:
    audio: dict[str, Path] = field(default_factory=dict)
    takes: dict[str, str] = field(default_factory=dict)
    unclean: list[dict] = field(default_factory=list)
    manifests: dict[str, dict] = field(default_factory=dict)


def load_reuse_sources(directories: list[Path | None], engine: str) -> list[ReuseSource]:
    sources, seen = [], set()
    for directory in directories:
        if directory is None or directory.resolve() in seen or not (directory / "sentence-hashes.json").is_file():
            continue
        seen.add(directory.resolve())
        takes_path = directory / "takes.json"
        if engine != "kokoro" and not takes_path.is_file():
            log(f"reuse skipped: {directory} has no takes.json")
            continue
        hashes = json.loads((directory / "sentence-hashes.json").read_text())
        takes = json.loads(takes_path.read_text()) if takes_path.is_file() else None
        timing_path, checks_path, manifest_path = (directory / name for name in ("timing.json", "audio-checks.json", "take-manifest.json"))
        timing = json.loads(timing_path.read_text()) if timing_path.is_file() else {}
        checks = json.loads(checks_path.read_text()) if checks_path.is_file() else {}
        manifests = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
        sources.append(ReuseSource(directory, hashes, takes,
                                   {s["id"]: s["scene_id"] for s in timing.get("sentences", [])},
                                   {sid: directory / "sentences" / f"{sid}.wav" for sid in hashes
                                    if (directory / "sentences" / f"{sid}.wav").is_file()},
                                   [flag for flag in checks.get("flags", []) if flag.get("check") == "unclean_cut"], manifests))
    return sources


def decide_reuse(rows: list[dict], engine: str, sources: list[ReuseSource]) -> ReuseDecision:
    """Select complete takes atomically, with later sources winning; Kokoro selects individual matching sentences."""
    result = ReuseDecision()
    if engine == "kokoro":
        known = {}
        for source in sources:
            for sid, key in source.hashes.items():
                if sid in source.audio:
                    take = source.takes.get(sid) if source.takes else None
                    known[key] = (source, sid, take or f"legacy-{sha256(str(source.directory.resolve()).encode())[:16]}-{sid}")
        for row in rows:
            if row["key"] in known:
                source, sid, take = known[row["key"]]
                result.audio[row["id"]] = source.audio[sid]
                result.takes[row["id"]] = take
                if take in source.manifests:
                    result.manifests[take] = source.manifests[take]
        return result

    current = {row["id"]: row for row in rows}
    by_scene: dict[str, set[str]] = {}
    for row in rows:
        by_scene.setdefault(row["scene_id"], set()).add(row["id"])
    selected_scenes = set()
    for source in reversed(sources):
        by_take: dict[str, set[str]] = {}
        for sid, take in (source.takes or {}).items():
            by_take.setdefault(take, set()).add(sid)
        for take, members in by_take.items():
            if any(sid not in source.scenes for sid in members):
                continue
            covered = {source.scenes[sid] for sid in members}
            if not covered <= by_scene.keys() or covered & selected_scenes:
                continue
            needed = set().union(*(by_scene[scene] for scene in covered))
            source_order = [sid for sid in source.scenes if sid in members]
            current_order = [row["id"] for row in rows if row["scene_id"] in covered]
            manifest = source.manifests.get(take)
            if source_order != current_order or (manifest is not None and
                    (manifest.get("sentences") != source_order or set(manifest.get("scenes", [])) != covered)):
                continue
            if members != needed or any(sid not in source.audio or source.hashes.get(sid) != current[sid]["key"]
                                        or source.scenes[sid] != current[sid]["scene_id"] for sid in needed):
                continue
            for sid in needed:
                result.audio[sid] = source.audio[sid]
                result.takes[sid] = take
            selected_scenes.update(covered)
            result.unclean.extend(flag for flag in source.unclean if flag.get("take") == take)
            if take in source.manifests:
                result.manifests[take] = source.manifests[take]
    return result


def run_tool(script: str, args: list[str], capture: bool = False, soft_exit: int | None = None) -> str | None:
    """Run a voice tool and return its captured output, or None when it exits with soft_exit."""
    result = subprocess.run([sys.executable, str(TOOLS_DIR / script), *map(str, args)], text=True,
                            stdout=subprocess.PIPE if capture else None, stderr=None if not capture else subprocess.PIPE)
    if soft_exit is not None and result.returncode == soft_exit:
        print(result.stderr or "", end="", file=sys.stderr)
        return None
    if result.returncode:
        raise SystemExit(f"{script} failed (exit {result.returncode})\n{(result.stderr or '')[-2000:]}")
    if capture and result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.stdout or ""


def run_voice(name: str, texts: list[Path], work: Path) -> None:
    # voice.py must read the same profile that voice_identity hashes into the cache key.
    run_tool("voice.py", [*texts, "--out-dir", work, "--voice", name, "--profile", VOICE_DIR])


def read_audio(path: Path) -> np.ndarray:
    samples, rate = sf.read(path, dtype="float32")
    if rate != RATE or samples.ndim != 1 or not len(samples):
        raise SystemExit(f"{path} must be non-empty mono {RATE} Hz audio")
    return samples


@functools.cache
def espeak(language: str):
    """eSpeak's first choice of voice, with one library wrapper per requested language."""
    from espeak_backend import CachedEspeakBackend, espeak_wrapper
    from phonemizer.backend.espeak.wrapper import EspeakWrapper
    if sys.platform == "linux":
        from linux_speech import espeak_paths
        lib, data = espeak_paths()
        EspeakWrapper.set_library(str(lib))
        EspeakWrapper.set_data_path(str(data))
    else:
        EspeakWrapper.set_library(str(ESPEAK / "lib/libespeak-ng.dylib"))
        EspeakWrapper.set_data_path(str(ESPEAK / "share/espeak-ng-data"))
    # eSpeak ranks its voices for the language, and the phonemizer reads only its own voices, not MBROLA's.
    wrapper = espeak_wrapper(language)
    supported = {voice.language for voice in wrapper.available_voices()}
    voice = next((voice.language for voice in wrapper.available_voices(language) if voice.language in supported), None)
    if not voice:
        raise SystemExit(f"eSpeak has no voice for {language!r}")
    return CachedEspeakBackend(voice, cache_language=language, language_switch="remove-flags")


def estimate_seconds(texts: list[str], language: str) -> list[float]:
    """Each text's estimated speech time, from the phonemes eSpeak reads in it."""
    from phonemizer.separator import Separator
    phones = espeak(language).phonemize(texts, separator=Separator(phone="|", word=" "), strip=True)
    return [len(phone.replace("|", " ").split()) / PHONEMES_PER_SECOND for phone in phones]


def check_scene_lengths(seconds: dict[str, float]) -> None:
    limit = MAX_TAKE_SECONDS - TAKE_RESERVE_SECONDS
    for scene, duration in seconds.items():
        if duration > limit:
            raise SystemExit(f"scene {scene} estimates {duration:.1f} s, above the {limit:g} s take text limit; split its narration into smaller scenes")


def bound_runs(runs: list[list[str]], seconds: dict[str, float]) -> list[list[str]]:
    """Keep whole scenes together while reserving headroom for pauses and the throwaway."""
    limit = MAX_TAKE_SECONDS - TAKE_RESERVE_SECONDS
    bounded = []
    for run in runs:
        current, duration = [], 0.0
        for scene in run:
            if current and duration + seconds[scene] > limit:
                bounded.append(current)
                current, duration = [], 0.0
            current.append(scene)
            duration += seconds[scene]
        if current:
            bounded.append(current)
    return bounded


def plan_runs(seconds: dict[str, float], work: Path) -> list[list[str]]:
    check_scene_lengths(seconds)
    if len(seconds) > 18:
        raise SystemExit("plan_runs.py tries every grouping, so it handles at most 18 scenes with sentences to voice")
    empty = work / "plan-receipts"
    empty.mkdir(exist_ok=True)
    out = run_tool("plan_runs.py", [empty, "--max", str(MAX_TAKE_SECONDS - TAKE_RESERVE_SECONDS),
                                  "--seconds", *(f"{k}={v:.1f}" for k, v in seconds.items())], capture=True)
    best = next(line for line in out.splitlines() if " || violation" in line)
    ids = list(seconds)
    runs = []
    for part in best.split("  ||")[0].split(" | "):
        first, _, last = part.split()[0].partition("-")
        runs.append(ids[ids.index(first):ids.index(last or first) + 1])
    runs = bound_runs(runs, seconds)
    log("runs: " + " | ".join(f"{'-'.join(run)} {sum(seconds[s] for s in run):.1f} s" for run in runs))
    return runs


def voice_takes(name: str, spec: dict, pending: list[dict], work: Path, language: str = "en") -> tuple[dict[str, np.ndarray], dict[str, str], list[dict], dict[str, dict]]:
    """Voice pending rows and return samples, original take ids, unclean cuts and raw take receipts."""
    work.mkdir(parents=True, exist_ok=True)
    generation = uuid.uuid4().hex
    origins, manifests = {}, {}

    def record_take(stem: str, members: list[dict]) -> str:
        take = f"{generation}:{stem}"
        for row in members:
            origins[row["id"]] = take
        wav, receipt = work / f"{stem}.wav", work / f"{stem}.json"
        manifests[take] = {"scenes": list(dict.fromkeys(row["scene_id"] for row in members)),
                           "sentences": [row["id"] for row in members], "wav": str(wav.resolve()),
                           "sha256": sha256(wav.read_bytes()), "receipt": str(receipt.resolve()),
                           "receipt_sha256": sha256(receipt.read_bytes())}
        return take

    if spec["engine"] == "kokoro":
        for row in pending:
            (work / f"{row['id']}.txt").write_text(row["spoken"])
        run_voice(name, [work / f"{row['id']}.txt" for row in pending], work)
        for row in pending:
            record_take(row["id"], [row])
        return {row["id"]: read_audio(work / f"{row['id']}.wav") for row in pending}, origins, [], manifests
    units: dict[str, list[dict]] = {}
    seconds: dict[str, float] = {}
    # The authored text, because eSpeak would read a respelling's phoneme markup letter by letter.
    for row, estimate in zip(pending, estimate_seconds([row["text"] for row in pending], language)):
        units.setdefault(row["alias"], []).append(row)
        seconds[row["alias"]] = seconds.get(row["alias"], 0.0) + estimate
    takes, take_members, planned = [], {}, {}
    for run in plan_runs(seconds, work):
        stem = run[0] if len(run) == 1 else f"{run[0]}-{run[-1]}"
        (work / f"{stem}.txt").write_text(" ".join(r["spoken"] for alias in run for r in units[alias]) + " " + THROWAWAY)
        takes.append(work / f"{stem}.txt")
        take_members[stem] = [r for alias in run for r in units[alias]]
        planned[stem] = sum(seconds[alias] for alias in run)
    run_voice(name, takes, work)
    (work / "sentences.json").write_text(json.dumps([{"id": r["id"], "scene": r["alias"], "text": r["spoken"]} for r in pending]))
    cut, lines, todo = work / "cut", [], takes
    # A looping generation runs past its text, often far past it, and the cutter then cannot place its sentences in order.
    for attempt in range(RUNAWAY_RETRIES + 1):
        runaway = {}
        for t in todo:
            seconds_voiced = sf.info(t.with_suffix(".wav")).duration
            if seconds_voiced > RUNAWAY_FACTOR * planned[t.stem]:
                runaway[t] = f"{seconds_voiced:.0f} s for {planned[t.stem]:.0f} s planned"
                continue
            out = run_tool("cut_takes.py", [t.with_suffix(".wav"), "--sentences", work / "sentences.json", "--out", cut,
                                            "--throwaway", THROWAWAY, "--language", language],
                           capture=True, soft_exit=UNCUTTABLE_EXIT)
            if out is None:
                runaway[t] = "cannot be cut in order"
            else:
                lines += [json.loads(line) for line in out.splitlines() if line.startswith("{")]
        if not runaway:
            break
        report = ", ".join(f"{t.stem} {why}" for t, why in runaway.items())
        if attempt == RUNAWAY_RETRIES:
            raise SystemExit(f"takes still run away after {RUNAWAY_RETRIES} retries: {report}")
        log(f"re-voicing runaway takes: {report}")
        run_voice(name, list(runaway), work)
        todo = list(runaway)
    take_ids = {stem: record_take(stem, members) for stem, members in take_members.items()}
    unclean = [{"check": "unclean_cut", "take": take_ids[r["take"]], "after": r["after"], "gap_s": r["gap_s"]}
               for r in lines if r.get("clean") is False]
    return {row["id"]: read_audio(cut / f"{row['id']}.wav") for row in pending}, origins, unclean, manifests


def frame_power(samples: np.ndarray, rate: int) -> np.ndarray:
    n = int(rate * FRAME_S)
    return np.mean(samples[: len(samples) // n * n].reshape(-1, n) ** 2, axis=1)


def cap_edge_silence(samples: np.ndarray) -> np.ndarray:
    power = frame_power(samples, RATE)
    if not len(power):
        return samples
    sound = np.flatnonzero(power > power.max() * 1e-4)
    if not len(sound):
        return samples
    frame = int(RATE * FRAME_S)
    keep = int(EDGE_SILENCE_S / FRAME_S)
    start = max(0, int(sound[0]) - keep) * frame
    end = min(len(samples), (int(sound[-1]) + 1 + keep) * frame)
    if start == 0 and end == len(samples):
        return samples
    return samples[start:end]


def sentence_level_db(power: np.ndarray) -> float:
    active = power[power > power.max() * 1e-3] if len(power) else power
    return float(10 * np.log10(max(float(active.mean()) if len(active) else 0, 1e-18)))


def calculate_take_gains(audio: dict[str, np.ndarray], takes: dict[str, str]) -> tuple[float, dict[str, float]]:
    """Match each take's median sentence level to the median of all raw sentence levels."""
    levels: dict[str, list[float]] = {}
    for sid, samples in audio.items():
        levels.setdefault(takes[sid], []).append(sentence_level_db(frame_power(samples, RATE)))
    target = statistics.median(level for take in levels.values() for level in take)
    return target, {take: target - statistics.median(values) for take, values in levels.items()}


def match_sentence_levels(audio: dict[str, np.ndarray]) -> tuple[dict[str, np.ndarray], float, dict[str, float]]:
    """Match separate generations without changing cached samples or sentence durations."""
    levels = {sid: sentence_level_db(frame_power(samples, RATE)) for sid, samples in audio.items()}
    target = statistics.median(levels.values())
    gains = {}
    for sid, samples in audio.items():
        gain = target - levels[sid]
        gain = max(-SENTENCE_GAIN_CAP_DB, min(SENTENCE_GAIN_CAP_DB, gain)) if abs(gain) > SENTENCE_MATCH_DB else 0.0
        peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
        # A boost stops at the peak ceiling, because clipping would distort the sentence.
        headroom = SENTENCE_PEAK_DBFS - 20 * np.log10(peak) if peak > 0 else SENTENCE_GAIN_CAP_DB
        gains[sid] = float(min(gain, max(0.0, headroom)))
    matched = {sid: samples * 10 ** (gains[sid] / 20) for sid, samples in audio.items()}
    return matched, target, gains


def assemble(scenes: list[dict], rows: dict[str, dict], audio: dict[str, np.ndarray],
             takes: dict[str, str] | None = None, take_gain_db: dict[str, float] | None = None,
             run_on: set[str] | None = None) -> tuple[np.ndarray, list[dict], list[dict], float]:
    """Join the sentences; return the audio, the scene rows, the sentence rows and the duration.

    Two sentences of one scene from the same take join with no added gap, preserving breaths after the edge silence
    cap described in methods/voice-explainer-video.md. SENTENCE_PAUSE separates only sentences from separate
    generations, such as Kokoro's. Scenes get SCENE_PAUSE.
    run_on holds the sentences whose cut after them is unclean. The next sentence follows with no added gap, because the
    voice ran on there and a gap would split the next word. A [pause] still gets its gap."""
    parts, scene_rows, sentence_rows = [np.zeros(int(LEAD_IN * RATE), dtype="float32")], [], []
    cursor, previous, previous_id = LEAD_IN, None, None
    for scene in scenes:
        scene_start = cursor
        for index, sentence in enumerate(scene["_sentences"], 1):
            explicit = sentence["pause_before"]
            row = rows[f"{scene['id']}-{index:02d}"]
            same_take = takes is not None and previous_id is not None and takes.get(row["id"]) == takes.get(previous_id)
            gap = EXPLICIT_PAUSE if explicit else (0 if previous is None or previous_id in (run_on or ()) else
                                                   SCENE_PAUSE if previous != scene["id"] else
                                                   0 if same_take else SENTENCE_PAUSE)
            if gap:
                parts.append(np.zeros(int(gap * RATE), dtype="float32"))
                cursor += gap
            samples = audio[row["id"]]
            if take_gain_db:
                samples = samples * 10 ** (take_gain_db[takes[row["id"]]] / 20)
            start, end = cursor, cursor + len(samples) / RATE
            sentence_rows.append({"id": row["id"], "scene_id": scene["id"], "text": row["text"], "spoken_text": row["spoken"],
                                  "pause_before": explicit, "start": round(start, 3), "end": round(end, 3),
                                  "audio": f"sentences/{row['id']}.wav"})
            parts.append(samples)
            cursor, previous, previous_id = end, scene["id"], row["id"]
        scene_rows.append({"id": scene["id"], "title": scene["title"], "visual": scene["visual"],
                           "claim_ids": scene["claim_ids"], "start": round(scene_start, 3), "end": round(cursor, 3)})
    parts.append(np.zeros(int(TAIL * RATE), dtype="float32"))
    return np.concatenate(parts), scene_rows, sentence_rows, cursor + TAIL


def ffmpeg(args: list[str]) -> str:
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True).stderr


def measure_loudness(path: Path) -> dict:
    log_text = ffmpeg(["-i", str(path), "-af", f"loudnorm={LOUDNORM}:print_format=json", "-f", "null", "-"])
    return json.JSONDecoder().raw_decode(log_text[log_text.rfind("{"):])[0]


def normalize(raw: Path, final: Path, preserve_take_levels: bool = False) -> float | None:
    """Write 48 kHz, 24-bit mono with a common peak-capped gain, or Kokoro's two-pass loudnorm."""
    m = measure_loudness(raw)
    if preserve_take_levels:
        gain = min(-16 - float(m["input_i"]), -1.5 - float(m["input_tp"]))
        log(f"global normalization gain: {gain:+.2f} dB")
        ffmpeg(["-y", "-i", str(raw), "-af", f"volume={gain:.8f}dB:precision=double", "-ar", "48000", "-ac", "1",
                "-c:a", "pcm_s24le", str(final)])
        return gain
    apply = (f"loudnorm={LOUDNORM}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
             f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    ffmpeg(["-y", "-i", str(raw), "-af", apply, "-ar", "48000", "-ac", "1", "-c:a", "pcm_s24le", str(final)])


def transcribe_words(audio: str | np.ndarray, language: str) -> list[dict]:
    if sys.platform == "linux":
        import linux_whisper as mlx_whisper
    else:
        import mlx_whisper

    result = mlx_whisper.transcribe(audio, path_or_hf_repo=WHISPER, language=language, word_timestamps=True,
                                    condition_on_previous_text=False)
    return [{"word": w["word"], "start": float(w["start"]), "end": float(w["end"])} for seg in result["segments"] for w in seg["words"]]


def transcribe(path: Path, language: str = "en") -> tuple[list[dict], str]:
    from huggingface_hub import snapshot_download

    log("transcribing narration.wav")
    words = transcribe_words(str(path), language)
    if not words:
        raise SystemExit("Whisper returned zero words")
    return words, snapshot_download(WHISPER, local_files_only=True)


def align_words(sents: list[dict], asr: list[dict], language: str = "en") -> tuple[list[list[dict]], list[dict]]:
    """Time each script token from Whisper's pieces, matched by Unicode letters/marks/numbers so a respelled or merged word still lines up."""
    script = [(k, token) for k, s in enumerate(sents) for token in tokenize(s["text"])]
    ref, ref_word = "", []
    for i, (_, token) in enumerate(script):
        ref += letters(token)
        ref_word += [i] * len(letters(token))
    hyp, hyp_time = "", []
    for w in asr:
        chars = letters(w["word"])
        if language in LANGUAGES:
            chars = letters(spoken_word(w["word"], language, ref))
        elif chars.isdecimal() and readings(chars):
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


def latin_fallback_windows(sents: list[dict], rows: list[list[dict]], fallbacks: list[dict]) -> list[tuple[float, float]]:
    """Bound fallback runs containing Latin letters by their nearest matched neighbours, as in take cutting."""
    missing = {(w["sentence"], w["word"], w["start"]) for w in fallbacks}
    windows = []
    for sentence, words in zip(sents, rows):
        i = 0
        while i < len(words):
            start = i
            latin = False
            while i < len(words) and (sentence["id"], words[i]["text"], words[i]["start"]) in missing:
                latin |= any(unicodedata.name(c, "").startswith("LATIN ") for c in letters(words[i]["text"]))
                i += 1
            if i == start:
                i += 1
                continue
            if latin:
                left = words[start - 1]["end"] if start else sentence["start"]
                right = words[i]["start"] if i < len(words) else sentence["end"]
                if left < right:
                    windows.append((left, right))
    return windows


def align_with_repairs(path: Path, sents: list[dict], asr: list[dict], language: str = "en", *,
                       stats: dict | None = None
                       ) -> tuple[list[dict], list[list[dict]], list[dict], int]:
    """Retry fallback spans, also in English for Latin letters; leave clean alignments untouched."""
    rows, fallbacks = align_words(sents, asr, language)
    if not fallbacks:
        return asr, rows, fallbacks, 0
    english_sentences = {w["sentence"] for w in fallbacks
                         if any(unicodedata.name(c, "").startswith("LATIN ") for c in letters(w["word"]))
                         } if language != "en" else set()

    if sys.platform == "linux":
        from linux_whisper import SAMPLE_RATE, load_audio
    else:
        from mlx_whisper.audio import SAMPLE_RATE, load_audio

    # Decode/resample once for all repair spans, using Whisper's own audio loader.
    samples = load_audio(str(path))
    failed = {word["sentence"] for word in fallbacks}
    spans = []
    previous_failed = False
    for sentence in sents:
        if sentence["id"] not in failed:
            previous_failed = False
            continue
        start = max(0, min(len(samples), round((sentence["start"] - 0.15) * SAMPLE_RATE)))
        end = max(0, min(len(samples), round((sentence["end"] + 0.15) * SAMPLE_RATE)))
        if end <= start:
            previous_failed = False
            continue
        # Also merge overlapping padding so no audio is replaced twice.
        if spans and (previous_failed or start <= spans[-1][1]):
            spans[-1][1] = max(spans[-1][1], end)
            spans[-1][2] |= sentence["id"] in english_sentences
        else:
            spans.append([start, end, sentence["id"] in english_sentences])
        previous_failed = True

    best, english_spans = (asr, rows, fallbacks), 0

    def replace_span(words, replacement, start, end):
        candidate = [word for word in words if not start <= (word["start"] + word["end"]) / 2 < end]
        candidate.extend(replacement)
        candidate.sort(key=lambda word: (word["start"] + word["end"]) / 2)
        return candidate, *align_words(sents, candidate, language)

    for start, end, rehear_english in spans:
        offset, stop = start / SAMPLE_RATE, end / SAMPLE_RATE
        replacement = transcribe_words(samples[start:end], language)
        previous = best
        retried = replace_span(best[0],
                               [{**w, "start": w["start"] + offset, "end": w["end"] + offset} for w in replacement],
                               offset, stop)
        # A short clip can swap homophones or hallucinate, so keep only strict improvements.
        if len(retried[2]) < len(best[2]):
            best = retried
        if rehear_english:
            english = transcribe_words(samples[start:end], "en")
            english_spans += 1
            heard = [{**w, "start": w["start"] + offset, "end": w["end"] + offset} for w in english]
            # Try both native transcripts so a retry cannot trade good native words for English matches.
            for source in (previous, retried):
                for left, right in latin_fallback_windows(sents, source[1], source[2]):
                    left, right = max(left, offset), min(right, stop)
                    if left < right:
                        trial = replace_span(source[0],
                                             [w for w in heard if left <= (w["start"] + w["end"]) / 2 < right],
                                             left, right)
                        if len(trial[2]) < len(source[2]):
                            source = trial
                if len(source[2]) < len(best[2]):
                    best = source
    if stats is not None and english_spans:
        stats["english_retranscribed_spans"] = english_spans
    return *best, len(spans)


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def say(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + (ONES[n % 10] if n % 10 else "")
    unit, big = (100, "hundred") if n < 1000 else (1000, "thousand")
    return say(n // unit) + big + (say(n % unit) if n % unit else "")


def readings(digits: str, language: str = "en") -> set[str]:
    """Normalized readings: legacy English cardinals/years; fr/pt/es/hi/zh/ko decimals and percents too."""
    if language in LANGUAGES:
        return {letters(form) for form in spoken_numbers(digits, language)}
    n = int(digits)
    found = {say(n)} if n < 10**6 else set()
    if 1100 <= n < 10000 and n % 100:
        found.add(say(n // 100) + say(n % 100))
    return found


NUMBER = re.compile(r"\d+(?:\.\d+)?%?")


def spoken_word(word: str, language: str, reference: str) -> str:
    """Swap each number in an ASR word, such as 12층, for the reading the script uses; unsupported languages pass through."""
    def swap(match: re.Match) -> str:
        return next((form for form in sorted(spoken_numbers(match[0], language)) if letters(form) in reference), match[0])
    return NUMBER.sub(swap, word)


def asr_differences(sents: list[dict], asr: list[dict], language: str = "en") -> list[dict]:
    """Words Whisper heard that the script does not say, ignoring spelling, spacing and the spoken respelling."""
    script = [(k, t) for k, s in enumerate(sents) for t in tokenize(s["text"]) if letters(t)]
    reference = "".join(letters(t) for _, t in script)
    heard = []
    for w in asr:
        heard.extend(normalized_tokens(spoken_word(w["word"], language, reference)))
    spoken = [letters(s["spoken_text"]) for s in sents]
    found = []
    ops = difflib.SequenceMatcher(None, [letters(t) for _, t in script], heard, autojunk=False).get_opcodes()
    for tag, a1, a2, b1, b2 in ops:
        if tag == "equal":
            continue
        want, got = "".join(letters(t) for _, t in script[a1:a2]), "".join(heard[b1:b2])
        k = script[min(a1, len(script) - 1)][0]
        if b2 - b1 == 1 and heard[b1].isdecimal() and want in readings(heard[b1], language):
            continue
        if want == got or (got and got in spoken[k]) or difflib.SequenceMatcher(None, want, got).ratio() >= SIMILAR:
            continue
        found.append({"check": "asr_difference", "sentence": sents[k]["id"],
                      "script": " ".join(t for _, t in script[a1:a2]), "heard": " ".join(heard[b1:b2])})
    return found


def level_flags(sents: list[dict], scenes: list[str], samples: np.ndarray, rate: int,
                run_on: set[str] = frozenset()) -> tuple[list[dict], dict]:
    power = frame_power(samples, rate)
    smooth = 10 * np.log10(np.convolve(power, np.ones(SMOOTH) / SMOOTH, mode="same") + 1e-18)
    floor = float(np.percentile(smooth[power > 0], FLOOR_PCT))
    levels, tails = [], []
    for s in sents:
        a, b = round(s["start"] / FRAME_S), round(s["end"] / FRAME_S)
        frames = power[a:b]
        levels.append(sentence_level_db(frames))
        tails.append(float(10 * np.log10(power[max(a, b - round(TAIL_S / FRAME_S)):b].mean() + 1e-18)))
    median = statistics.median(levels)
    # A run-on sentence's audio carries straight into the next one, so its last 60 ms is mid-speech, not an end.
    ends = {s["id"]: tail for s, tail in zip(sents, tails) if s["id"] not in run_on}
    flags = []
    for s, level, tail in zip(sents, levels, tails):
        if abs(level - median) > LEVEL_DEV_DB:
            flags.append({"check": "loudness_outlier", "sentence": s["id"], "db_from_median": round(level - median, 1)})
        if s["id"] in ends and tail > floor + TAIL_ABOVE_FLOOR_DB:
            flags.append({"check": "word_cut_short", "sentence": s["id"], "tail_db_above_floor": round(tail - floor, 1)})
    for i in range(len(sents) - 1):
        if scenes[i] != scenes[i + 1] and abs(levels[i + 1] - levels[i]) > SCENE_JUMP_DB:
            flags.append({"check": "scene_jump", "between": [sents[i]["id"], sents[i + 1]["id"]], "db": round(levels[i + 1] - levels[i], 1)})
    return flags, {"median_sentence_db": round(median, 1), "max_dev_db": round(max(abs(v - median) for v in levels), 1),
                   "noise_floor_db": round(floor, 1), "max_tail_above_floor_db": round(max(ends.values(), default=floor) - floor, 1)}


def audio_checks(timing: dict, wav: Path, asr: list[dict], unclean: list[dict], language: str = "en") -> tuple[list[dict], dict]:
    samples, rate = sf.read(wav, dtype="float32")
    sents = timing["sentences"]
    flags = list(unclean)
    run_on = set(timing.get("pauses", {}).get("none_after", []))
    level, stats = level_flags(sents, [s["scene_id"] for s in sents], samples, rate, run_on)
    flags += level
    flags += asr_differences(sents, asr, language)
    loud = measure_loudness(wav)
    stats.update({"integrated_lufs": float(loud["input_i"]), "true_peak_dbtp": float(loud["input_tp"])})
    if abs(stats["integrated_lufs"] + 16) > LUFS_TOLERANCE or stats["true_peak_dbtp"] > TRUE_PEAK_MAX:
        flags.append({"check": "loudness_target", "lufs": stats["integrated_lufs"], "true_peak_dbtp": stats["true_peak_dbtp"]})
    wav_s = len(samples) / rate
    if abs(wav_s - timing["duration"]) > 0.01:
        flags.append({"check": "duration_mismatch", "wav_s": round(wav_s, 3), "timing_s": timing["duration"]})
    stats["duration_s"] = round(wav_s, 3)
    stats.update({key: timing[key] for key in ("take_gain_db", "take_target_sentence_db", "normalization_gain_db",
                                             "final_take_target_sentence_db", "sentence_gain_db", "sentence_target_db",
                                             "sentence_peak_dbfs") if key in timing})
    return flags, stats


def report(flags: list[dict], stats: dict, fallbacks: list[dict], out: Path | None) -> dict:
    result = {"ok": not flags, "flags": flags, "stats": stats, "fallback_words": fallbacks}
    if out:
        (out / "audio-checks.json").write_text(json.dumps(result, indent=2) + "\n")
    for flag in flags:
        print("FLAG " + json.dumps(flag))
    print(json.dumps({"ok": result["ok"], "flags": len(flags), "fallback_words": len(fallbacks), **stats}))
    return result


def check_only(audio_dir: Path, out: Path | None, language: str = "en") -> None:
    timing = json.loads((audio_dir / "timing.json").read_text())
    asr, _ = transcribe(audio_dir / "narration.wav", language)
    repair_stats = {}
    asr, _, fallbacks, repaired_spans = align_with_repairs(audio_dir / "narration.wav", timing["sentences"], asr,
                                                       language, stats=repair_stats)
    flags, stats = audio_checks(timing, audio_dir / "narration.wav", asr, [], language)
    stats.update(repair_stats)
    if repaired_spans:
        stats["retranscribed_spans"] = repaired_spans
    if out:
        out.mkdir(parents=True, exist_ok=True)
    result = report(flags, stats, fallbacks, out)
    sys.exit(0 if result["ok"] else 1)


def narrate(args: argparse.Namespace) -> None:
    started = time.perf_counter()
    scenes = load_scenes(args.scenes, args.language)
    respellings = load_respellings(args.spoken)
    spec, identity = voice_identity(args.voice)
    rows: dict[str, dict] = {}
    for number, scene in enumerate(scenes, 1):
        for index, sentence in enumerate(scene["_sentences"], 1):
            spoken = respell(sentence["text"], respellings)
            sid = f"{scene['id']}-{index:02d}"
            rows[sid] = {"id": sid, "scene_id": scene["id"], "alias": f"S{number:02d}", "text": sentence["text"],
                         "spoken": spoken, "key": cache_key(identity, spoken)}

    out = args.out
    reuse = decide_reuse(list(rows.values()), spec["engine"], load_reuse_sources([args.reuse, out], spec["engine"]))
    audio = {sid: read_audio(path) for sid, path in reuse.audio.items()}
    take_origins, manifests = dict(reuse.takes), dict(reuse.manifests)
    reused = len(audio)
    pending = [row for row in rows.values() if row["id"] not in audio]
    log(f"{reused} sentences reused, {len(pending)} to voice with {args.voice}")
    log("takes reused: " + (", ".join(sorted(set(reuse.takes.values()))) or "none"))
    log("scenes to voice: " + (", ".join(dict.fromkeys(row["scene_id"] for row in pending)) or "none"))
    unclean = list(reuse.unclean)
    voiced_takes = 0
    out.mkdir(parents=True, exist_ok=True)
    if pending:
        voiced, origins, cut_flags, generated = voice_takes(args.voice, spec, pending, out / "takes" / uuid.uuid4().hex, args.language)
        audio.update(voiced)
        take_origins.update(origins)
        manifests.update(generated)
        unclean.extend(cut_flags)
        voiced_takes = len(set(origins.values()))

    audio = {sid: cap_edge_silence(samples) for sid, samples in audio.items()}
    take_target, take_gain_db = None, {}
    assembly_audio, sentence_target, sentence_gain_db = audio, None, {}
    if spec["engine"] == "kokoro":
        assembly_audio, sentence_target, sentence_gain_db = match_sentence_levels(audio)
    else:
        take_target, take_gain_db = calculate_take_gains(audio, take_origins)
        log(f"take level target: {take_target:.2f} dB; take_gain_db: {json.dumps(take_gain_db)}")
        for take, gain in take_gain_db.items():
            if abs(gain) > 3:
                log(f"take gain exceeds 3 dB: {take} {gain:+.2f} dB")
    run_on = {flag["after"] for flag in unclean}
    samples, scene_rows, sentence_rows, duration = assemble(scenes, rows, assembly_audio, take_origins, take_gain_db, run_on)
    shutil.rmtree(out / "sentences", ignore_errors=True)
    (out / "sentences").mkdir()
    for sid, data in audio.items():
        sf.write(out / "sentences" / f"{sid}.wav", data, RATE, subtype="PCM_16")
    (out / "sentence-hashes.json").write_text(json.dumps({sid: rows[sid]["key"] for sid in audio}, indent=1) + "\n")
    (out / "takes.json").write_text(json.dumps(take_origins, indent=2) + "\n")
    (out / "take-manifest.json").write_text(json.dumps(manifests, indent=2) + "\n")
    sf.write(out / "narration-raw.wav", samples, RATE, subtype="PCM_16")
    normalization_gain = normalize(out / "narration-raw.wav", out / "narration.wav", preserve_take_levels=spec["engine"] != "kokoro")
    final_take_target = take_target + normalization_gain if take_target is not None and normalization_gain is not None else None
    timing = {"source_sha256": sha256(args.scenes.read_bytes()), "voice": args.voice, "speed": spec.get("speed"),
              "sample_rate": RATE, "duration": round(duration, 3), "frames_30fps": round(duration * 30),
              "scenes": scene_rows, "sentences": sentence_rows,
              "take_gain_db": take_gain_db, "take_target_sentence_db": take_target,
              "normalization_gain_db": normalization_gain, "final_take_target_sentence_db": final_take_target,
              "sentence_gain_db": sentence_gain_db, "sentence_target_db": sentence_target,
              "sentence_peak_dbfs": SENTENCE_PEAK_DBFS if sentence_target is not None else None,
              "pauses": {"lead_in": LEAD_IN, "between_sentences": SENTENCE_PAUSE, "between_scenes": SCENE_PAUSE,
                         "explicit": EXPLICIT_PAUSE, "tail": TAIL, "none_after": sorted(run_on)}}
    if sys.platform == "linux" and spec["engine"] == "kokoro":
        from linux_levels import correct_file
        timing["linux_level_correction"] = correct_file(
            out / "narration.wav", sentence_rows, frame_power=frame_power,
            sentence_level_db=sentence_level_db, frame_s=FRAME_S,
            level_dev_db=LEVEL_DEV_DB, scene_jump_db=SCENE_JUMP_DB, scratch_dir=out)
    (out / "timing.json").write_text(json.dumps(timing, indent=2) + "\n")

    asr, model_path = transcribe(out / "narration.wav", args.language)
    repair_stats = {}
    asr, word_rows, fallbacks, repaired_spans = align_with_repairs(out / "narration.wav", sentence_rows, asr,
                                                               args.language, stats=repair_stats)
    words = [w for sentence in word_rows for w in sentence]
    (out / "words.json").write_text(json.dumps({
        "model": "faster-whisper large-v3-turbo" if sys.platform == "linux" else "mlx-whisper large-v3-turbo", "model_path": model_path, "language": args.language, "language_probability": 1,
        "duration": timing["duration"], "word_count": len(words),
        "segments": [{"text": s["text"], "start": w[0]["start"], "end": w[-1]["end"]} for s, w in zip(sentence_rows, word_rows)],
        "words": words}, indent=2) + "\n")

    flags, stats = audio_checks(timing, out / "narration.wav", asr, unclean, args.language)
    stats.update(repair_stats)
    if repaired_spans:
        stats["retranscribed_spans"] = repaired_spans
    stats.update({"sentences": len(rows), "reused": reused, "voiced": len(pending), "reused_takes": len(set(reuse.takes.values())),
                  "voiced_takes": voiced_takes, "take_gain_db": take_gain_db, "take_target_sentence_db": take_target,
                  "normalization_gain_db": normalization_gain, "final_take_target_sentence_db": final_take_target,
                  "sentence_gain_db": sentence_gain_db, "sentence_target_db": sentence_target,
                  "sentence_peak_dbfs": timing["sentence_peak_dbfs"],
                  "wall_s": round(time.perf_counter() - started, 1)})
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
    parser.add_argument("--language", default="en", help="narration language code for Whisper, Stanza and eSpeak, such as pt (default: en)")
    args = parser.parse_args()
    if args.check_only:
        return check_only(args.check_only, args.out, args.language)
    if not (args.scenes and args.voice and args.out):
        parser.error("provide SCENES.json, --voice and --out (or --check-only)")
    narrate(args)


if __name__ == "__main__":
    main()
