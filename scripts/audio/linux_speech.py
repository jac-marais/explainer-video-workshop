"""CPU speech support; model assets must already be in the shared caches."""
import ctypes.util
import functools
import math
from importlib.metadata import version
from pathlib import Path
import re


def espeak_paths():
    library = ctypes.util.find_library("espeak-ng")
    candidates = [Path("/usr/share/espeak-ng-data"), Path("/usr/lib/espeak-ng-data")]
    candidates.extend(Path("/usr/lib").glob("*/espeak-ng-data"))
    data = next((path for path in candidates if path.is_dir()), None)
    if not library or data is None:
        raise SystemExit("Install espeak-ng and libespeak-ng1 before voicing on Linux")
    # Resolve the SONAME through the loader; existence checks cannot resolve it as a relative file.
    candidates = list(Path("/usr/lib").glob("*/" + library)) + [Path("/usr/lib") / library]
    lib = next((path for path in candidates if path.is_file()), None)
    if lib is None:
        raise SystemExit("Cannot locate the installed eSpeak NG shared library")
    return lib, data


def qwen_model_id(model):
    match = re.fullmatch(r"mlx-community/(Qwen3-TTS-12Hz-(?:0\.6|1\.7)B-(?:Base|CustomVoice))-bf16", model)
    if match:
        return "Qwen/" + match[1]
    if re.fullmatch(r"Qwen/Qwen3-TTS-12Hz-(?:0\.6|1\.7)B-(?:Base|CustomVoice)", model):
        return model
    raise SystemExit("No faithful CPU mapping for this Qwen model; use the matching bf16 release")


class RecentTokenRepetitionPenalty:
    """Public HF logits-processor protocol, using MLX's last 64 generated IDs."""

    def __init__(self, penalty, context_size=64):
        if not math.isfinite(penalty) or penalty <= 0 or context_size <= 0:
            raise ValueError("Repetition penalty and context size must be positive")
        self.penalty = penalty
        self.context_size = context_size
        self.prefix_length = None

    def __call__(self, input_ids, scores):
        import torch

        # HF calls processors before sampling the first token. Embedding-only
        # Qwen prompts start with zero IDs; explicit ID prompts are excluded too.
        if self.prefix_length is None:
            self.prefix_length = input_ids.shape[-1]
        start = max(self.prefix_length, input_ids.shape[-1] - self.context_size)
        recent = input_ids[:, start:]
        if self.penalty == 1 or not recent.numel():
            return scores
        result = scores.clone()
        for row in range(recent.shape[0]):
            tokens = recent[row].unique()
            tokens = tokens[(tokens >= 0) & (tokens < scores.shape[-1])]
            selected = scores[row, tokens]
            result[row, tokens] = torch.where(selected < 0, selected * self.penalty, selected / self.penalty)
        return result


def install_qwen_repetition_window(talker):
    """Adapt this model instance's public generate call without changing HF internals."""
    generate = talker.generate

    @functools.wraps(generate)
    def bounded_generate(*args, **kwargs):
        config = kwargs.get("generation_config") or getattr(talker, "generation_config", None)
        penalty = kwargs.pop("repetition_penalty", getattr(config, "repetition_penalty", 1.0))
        # Disable the built-in full-history penalty; preserve other processors.
        kwargs["repetition_penalty"] = 1.0
        # MLX accepts EOS on the first step; override qwen-tts's two-token floor.
        kwargs["min_new_tokens"] = 0
        processors = list(kwargs.get("logits_processor") or [])
        processors.append(RecentTokenRepetitionPenalty(float(penalty)))
        kwargs["logits_processor"] = processors
        return generate(*args, **kwargs)

    talker.generate = bounded_generate


def load_qwen3(spec, seed, refs, max_words):
    import numpy as np
    import torch
    from huggingface_hub import snapshot_download
    from qwen_tts import Qwen3TTSModel
    from voice import CHUNK_PAUSE, MLX_SAMPLING, QWEN3_LANG, sha256_file, split_chunks

    model_id = qwen_model_id(spec["model"])
    snapshot = Path(snapshot_download(model_id, local_files_only=True))
    model = Qwen3TTSModel.from_pretrained(str(snapshot), device_map="cpu", dtype=torch.float32,
                                        attn_implementation="eager", local_files_only=True)
    install_qwen_repetition_window(model.model.talker)
    language = spec.get("lang", QWEN3_LANG)
    sampling = dict(MLX_SAMPLING)
    if refs:
        # MLX Base cloning uses full-text ICL conditioning and clamps this penalty.
        sampling["repetition_penalty"] = max(1.5, sampling["repetition_penalty"])
    generation = {**sampling, "max_new_tokens": 4096, "non_streaming_mode": bool(refs),
                  "do_sample": True, "subtalker_dosample": True,
                  "subtalker_temperature": sampling["temperature"],
                  "subtalker_top_p": sampling["top_p"], "subtalker_top_k": sampling["top_k"]}
    settings = {"lang": language, **generation, "seed": seed, "max_words_per_chunk": max_words,
                "chunk_pause_s": CHUNK_PAUSE, "device": "cpu", "dtype": "float32",
                "repetition_context_size": 64, "repetition_scope": "generated_tokens", "min_new_tokens": 0}
    if refs:
        voice = {"ref_audio": str(refs["ref_audio"]), "ref_text": refs["ref_text"].read_text().strip(),
                 "x_vector_only_mode": False}
        settings["x_vector_only_mode"] = False
        generate = model.generate_voice_clone
    else:
        speaker = spec["speaker"]
        supported = {name.lower(): name for name in model.get_supported_speakers()}
        if speaker.lower() not in supported:
            raise SystemExit(f"Unknown speaker {speaker!r}; available: {', '.join(supported)}")
        voice = {"speaker": supported[speaker.lower()]}
        settings["speaker"] = speaker
        generate = model.generate_custom_voice

    def synthesize(text):
        pieces, chunks, rate = [], split_chunks(text, max_words), None
        for index, chunk in enumerate(chunks):
            torch.manual_seed(seed + index)
            wavs, current_rate = generate(text=chunk, language=language, **voice, **generation)
            if rate is not None and current_rate != rate:
                raise ValueError("Qwen changed sample rate between chunks")
            rate = current_rate
            if index:
                pieces.append(np.zeros(int(CHUNK_PAUSE * rate), dtype="float32"))
            pieces.append(np.asarray(wavs[0], dtype="float32"))
        return np.concatenate(pieces), rate, {"chunks": len(chunks), "chunk_words": [len(c.split()) for c in chunks]}

    return synthesize, {"model": {"id": model_id, "snapshot_revision": snapshot.name},
                       "settings": settings,
                       **{f"{key}_sha256": sha256_file(path) for key, path in refs.items()},
                       "packages": {name: version(name) for name in ("qwen-tts", "torch")}}
