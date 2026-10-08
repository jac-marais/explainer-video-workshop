# /// script
# requires-python = "==3.12.*"
# dependencies = [
#   "numpy==2.5.3",
#   "soundfile==0.14.0",
#   "kokoro-onnx==0.4.7",
#   "mlx-audio==0.5.8; sys_platform == 'darwin' and platform_machine == 'arm64'",
# ]
# ///
"""Turn text files into loudness-normalized narration WAVs with the voices listed in voice.json."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import secrets
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
RATE = 24000
LOUDNORM = "I=-16:TP=-1.5:LRA=11"
KOKORO_LANG = "en-us"
QWEN3_LANG = "english"
# These match the mlx_audio.tts.generate CLI defaults.
MLX_SAMPLING = {"temperature": 0.7, "top_p": 0.9, "top_k": 50, "repetition_penalty": 1.1}
# A single pass stops at 4096 tokens (about 330 s) and slows as text grows.
QWEN3_CHUNK_WORDS = 400
CHUNK_PAUSE = 0.25


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_config() -> dict:
    path = HERE / "voice.json"
    if not path.is_file():
        raise SystemExit(f"Missing voice config: {path}")
    config = json.loads(path.read_text())
    if config.get("default") not in config.get("voices", {}):
        raise SystemExit(f"{path}: default voice is not listed under voices")
    return config


def split_chunks(text: str, max_words: int) -> list[str]:
    chunks: list[list[str]] = [[]]
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if chunks[-1] and len(chunks[-1]) + len(sentence.split()) > max_words:
            chunks.append([])
        chunks[-1].extend(sentence.split())
    return [" ".join(words) for words in chunks]


def load_kokoro(spec: dict, seed: int) -> tuple[callable, dict]:
    from kokoro_onnx import EspeakConfig, Kokoro

    cache = Path(os.environ.get("KOKORO_TTS_CACHE", Path.home() / ".cache/hyperframes/tts"))
    model_path = cache / "models/kokoro-v1.0.onnx"
    voices_path = cache / "voices/voices-v1.0.bin"
    prefix = Path("/opt/homebrew/opt/espeak-ng")
    lib_path = prefix / "lib/libespeak-ng.dylib"
    data_path = prefix / "share/espeak-ng-data"
    missing = [str(path) for path in (model_path, voices_path, lib_path, data_path) if not path.exists()]
    if missing:
        raise SystemExit("Missing local speech assets: " + ", ".join(missing))
    model = Kokoro(str(model_path), str(voices_path), espeak_config=EspeakConfig(str(lib_path), str(data_path)))

    def synthesize(text: str) -> tuple[np.ndarray, int, dict]:
        samples, rate = model.create(text, voice=spec["voice"], speed=spec["speed"], lang=KOKORO_LANG)
        return samples.astype("float32", copy=False), rate, {}

    identity = {
        "model": {"id": "kokoro-v1.0", "onnx_sha256": sha256_file(model_path)},
        "settings": {"voice": spec["voice"], "speed": spec["speed"], "lang": KOKORO_LANG},
        "packages": {name: version(name) for name in ("kokoro-onnx", "onnxruntime")},
    }
    return synthesize, identity


def require_mlx() -> None:
    if not (platform.system() == "Darwin" and platform.machine() == "arm64"):
        raise SystemExit("MLX voices need an Apple Silicon Mac")


def reference_paths(spec: dict) -> dict[str, Path]:
    paths = {key: HERE / spec[key] for key in ("ref_audio", "ref_text") if key in spec}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise SystemExit("Missing reference files: " + ", ".join(missing))
    return paths


def load_snapshot(model_id: str) -> Path:
    from huggingface_hub import snapshot_download
    from huggingface_hub.errors import LocalEntryNotFoundError
    from mlx_audio.utils import get_model_path

    try:
        return Path(snapshot_download(model_id, local_files_only=True))
    except LocalEntryNotFoundError:
        return get_model_path(model_id)


def mlx_identity(spec: dict, snapshot: Path, refs: dict[str, Path], settings: dict) -> dict:
    return {
        "model": {"id": spec["model"], "snapshot_revision": snapshot.name},
        "settings": settings,
        **{f"{key}_sha256": sha256_file(path) for key, path in refs.items()},
        "packages": {name: version(name) for name in ("mlx-audio", "mlx")},
    }


def load_qwen3(spec: dict, seed: int, max_words: int = QWEN3_CHUNK_WORDS) -> tuple[callable, dict]:
    require_mlx()
    refs = reference_paths(spec)
    import mlx.core as mx
    from mlx_audio.tts.utils import load
    from mlx_audio.utils import load_audio

    snapshot = load_snapshot(spec["model"])
    model = load(snapshot)
    settings = {"lang": QWEN3_LANG, **MLX_SAMPLING, "seed": seed, "max_words_per_chunk": max_words, "chunk_pause_s": CHUNK_PAUSE}
    if refs:
        voice = {"ref_audio": load_audio(str(refs["ref_audio"]), sample_rate=model.sample_rate), "ref_text": refs["ref_text"].read_text().strip()}
    else:
        speaker = spec["speaker"]
        if speaker.lower() not in (name.lower() for name in model.supported_speakers):
            raise SystemExit(f"Unknown speaker '{speaker}'; this model has: {', '.join(model.supported_speakers)}")
        voice = {"voice": speaker}
        settings["speaker"] = speaker

    def synthesize(text: str) -> tuple[np.ndarray, int, dict]:
        pieces, chunks = [], split_chunks(text, max_words)
        for index, chunk in enumerate(chunks):
            if index:
                pieces.append(np.zeros(int(CHUNK_PAUSE * model.sample_rate), dtype="float32"))
            # Seeding per chunk makes each chunk reproducible on its own.
            mx.random.seed(seed + index)
            results = model.generate(text=chunk, lang_code=QWEN3_LANG, **voice, **MLX_SAMPLING)
            pieces.extend(np.array(result.audio, dtype="float32") for result in results)
        return np.concatenate(pieces), model.sample_rate, {"chunks": len(chunks), "chunk_words": [len(c.split()) for c in chunks]}

    return synthesize, mlx_identity(spec, snapshot, refs, settings)


def load_chatterbox(spec: dict, seed: int) -> tuple[callable, dict]:
    require_mlx()
    refs = reference_paths(spec)
    import mlx.core as mx
    from mlx_audio.tts.utils import load

    snapshot = load_snapshot(spec["model"])
    model = load(snapshot)

    def synthesize(text: str) -> tuple[np.ndarray, int, dict]:
        mx.random.seed(seed)
        # The model splits long text at sentence boundaries itself.
        results = list(model.generate(text=text, ref_audio=str(refs["ref_audio"]), **MLX_SAMPLING))
        return np.concatenate([np.array(result.audio, dtype="float32") for result in results]), model.sample_rate, {"segments": len(results)}

    return synthesize, mlx_identity(spec, snapshot, refs, {**MLX_SAMPLING, "seed": seed})


LOADERS = {"kokoro": load_kokoro, "qwen3": load_qwen3, "qwen3-preset": load_qwen3, "chatterbox": load_chatterbox}


def ffmpeg_loudnorm(raw: Path, final: Path) -> None:
    def run(args: list[str]) -> str:
        return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True, check=True).stderr

    log = run(["-i", str(raw), "-af", f"loudnorm={LOUDNORM}:print_format=json", "-f", "null", "-"])
    m, _ = json.JSONDecoder().raw_decode(log[log.rfind("{"):])
    apply = (f"loudnorm={LOUDNORM}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
             f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample={RATE}")
    run(["-y", "-i", str(raw), "-af", apply, "-ac", "1", "-ar", str(RATE), "-c:a", "pcm_s16le", str(final)])


def read_texts(paths: list[Path]) -> list[tuple[Path, str]]:
    texts = []
    for path in paths:
        if not path.is_file():
            raise SystemExit(f"Text file not found: {path}")
        raw = path.read_text()
        if not raw.strip():
            raise SystemExit(f"Text file is empty: {path}")
        texts.append((path, raw))
    stems = [path.stem for path, _ in texts]
    if len(set(stems)) != len(stems):
        raise SystemExit("Text files must have distinct names (the output is named after the file stem)")
    return texts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("texts", nargs="*", type=Path, metavar="TEXT_FILE")
    parser.add_argument("--out-dir", type=Path, help="Directory for <stem>.wav and <stem>.json")
    parser.add_argument("--voice", help="Voice name from voice.json (default: the file's default)")
    parser.add_argument("--seed", type=int, help="Sampling seed for MLX voices (default: random, recorded in the receipt)")
    parser.add_argument("--max-words", type=int, default=QWEN3_CHUNK_WORDS,
                        help=f"Qwen3 voices only: split longer text into separate takes (default: {QWEN3_CHUNK_WORDS})")
    parser.add_argument("--list", action="store_true", help="List voices and exit")
    args = parser.parse_args()

    config = load_config()
    voices = config["voices"]
    if args.list:
        for name, spec in voices.items():
            print(f"{name}\t{spec['engine']}" + ("\t(default)" if name == config["default"] else ""))
        return
    if not args.texts or not args.out_dir:
        parser.error("provide TEXT_FILE... and --out-dir (or use --list)")
    name = args.voice or config["default"]
    if name not in voices:
        raise SystemExit(f"Unknown voice '{name}'; available: {', '.join(voices)}")
    spec = voices[name]
    engine = spec["engine"]
    if engine not in LOADERS:
        raise SystemExit(f"Voice '{name}' has unknown engine '{engine}'")
    texts = read_texts(args.texts)

    started = time.perf_counter()
    seed = args.seed if args.seed is not None else secrets.randbelow(2**31)
    options = {"max_words": args.max_words} if LOADERS[engine] is load_qwen3 else {}
    synthesize, identity = LOADERS[engine](spec, seed, **options)
    load_s = time.perf_counter() - started
    identity["packages"].update({"soundfile": version("soundfile"), "numpy": version("numpy")})
    identity["packages"]["ffmpeg"] = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.split("\n")[0]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for path, raw in texts:
        file_started = time.perf_counter()
        samples, rate, extra = synthesize(" ".join(raw.split()))
        wav = args.out_dir / f"{path.stem}.wav"
        with tempfile.TemporaryDirectory() as tmp:
            raw_wav = Path(tmp) / "raw.wav"
            sf.write(raw_wav, samples, rate)
            ffmpeg_loudnorm(raw_wav, wav)
        info = sf.info(wav)
        receipt = {
            "voice": name,
            "engine": engine,
            **identity,
            **extra,
            "input_sha256": sha256(raw.encode()),
            "input_text": raw,
            "duration_s": round(info.duration, 3),
            "sample_rate": info.samplerate,
            "wall_s": round(time.perf_counter() - file_started, 2),
            "model_load_s": round(load_s, 2),
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        wav.with_suffix(".json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"{wav}  {receipt['duration_s']}s  wall {receipt['wall_s']}s", file=sys.stderr)


if __name__ == "__main__":
    main()
