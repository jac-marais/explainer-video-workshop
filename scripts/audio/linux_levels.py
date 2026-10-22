"""Conditional final-PCM level correction for Linux narration.

Call only from the reviewed Linux dispatch. Inputs/outputs are mono48kHz
PCM24 represented as left-aligned int32. Existing production measurement functions
and constants must be supplied. The caller keeps all ordinary final audio/ASR gates.
"""
from pathlib import Path
import signal
import statistics
import subprocess
import tempfile
import os

import numpy as np

GAIN_CAP_DB = 4.0
MARGIN_DB = .5
MIN_GAIN_STEP_DB = .05
CONTEXT_S = .25
BLEND_S = .005
LIMIT_DBFS = -1.6
FILTER_TIMEOUT_S = 120


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _levels(pcm, rate, sentences, frame_power, sentence_level_db, frame_s):
    # Match production's float32 input and global10ms frame origin exactly.
    power = frame_power(pcm.astype(np.float32) / np.float32(2 ** 31), rate)
    values = []
    for row in sentences:
        a, b = round(row['start'] / frame_s), round(row['end'] / frame_s)
        _require(0 <= a < b <= len(power), 'Sentence has no valid complete measurement frames')
        value = sentence_level_db(power[a:b])
        _require(np.isfinite(value), 'Nonfinite measured sentence level')
        values.append(float(value))
    return values, float(statistics.median(values))


def filter_graph(rate, gain_db):
    """The fixed localized limiter profile; no automatic level or hidden trimming."""
    limit = 10 ** (LIMIT_DBFS / 20)
    return (f'volume={gain_db:.9f}dB:precision=double,'
            f'aresample={rate * 4}:resampler=swr:filter_size=64:phase_shift=10:exact_rational=1,'
            f'alimiter=limit={limit:.12f}:level_in=1:level_out=1:attack=5:release=50'
            ':asc=false:level=false:latency=true,'
            f'aresample={rate}:resampler=swr:filter_size=64:phase_shift=10:exact_rational=1')


def _stop_owned(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _filter_context(samples, rate, gain_db, scratch_dir, ffmpeg):
    import soundfile as sf
    with tempfile.TemporaryDirectory(prefix='linux-levels-', dir=scratch_dir) as name:
        folder = Path(name)
        source, result = folder / 'input.wav', folder / 'output.wav'
        sf.write(source, samples, rate, subtype='DOUBLE')
        with (folder / 'ffmpeg.log').open('w') as log:
            process = subprocess.Popen(
                [str(ffmpeg), '-hide_banner', '-nostats', '-n', '-i', str(source),
                 '-af', filter_graph(rate, gain_db), '-ar', str(rate), '-ac', '1',
                 '-c:a', 'pcm_f64le', str(result)],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                close_fds=False, start_new_session=True)
            try:
                code = process.wait(timeout=FILTER_TIMEOUT_S)
            finally:
                _stop_owned(process)
            if code:
                detail = (folder / 'ffmpeg.log').read_text(errors='replace')[-2000:]
                raise RuntimeError(f'Localized limiter failed (exit{code}): {detail}')
        data, output_rate = sf.read(result, dtype='float64')
        _require(output_rate == rate, 'Limiter changed sample rate')
        return data


def correct_levels(pcm, rate, sentences, *, frame_power, sentence_level_db,
                   frame_s, level_dev_db, scene_jump_db, scratch_dir=None,
                   ffmpeg='ffmpeg', filter_context=None):
    """Capped localized gains; return corrected PCM and measured settings/results.

    Select loudness outliers plus the quieter, below-median endpoint of
    existing failing scene boundaries. Re-measure after blending and retry from
    original PCM until the measured target or total gain cap is reached. The caller
    still runs all final checks. filter_context is injectable for deterministic tests.
    """
    _require(isinstance(pcm, np.ndarray) and pcm.ndim == 1 and pcm.dtype == np.int32,
             'Require mono left-aligned int32 PCM24')
    _require(rate == 48000 and len(pcm) > 0 and len(sentences) > 0, 'Require nonempty48kHz final narration')
    _require(np.all((pcm & 255) == 0), 'Input int32 contains bits below PCM24 precision')
    _require(frame_s > 0 and level_dev_db > MARGIN_DB and scene_jump_db > MARGIN_DB, 'Invalid measurement constants')
    ids, intervals, previous = set(), {}, 0
    for row in sentences:
        start, end = round(row['start'] * rate), round(row['end'] * rate)
        _require(row['id'] not in ids and previous <= start < end <= len(pcm), 'Invalid/overlapping sentence intervals')
        ids.add(row['id']); intervals[row['id']] = (start, end); previous = end
    before, median = _levels(pcm, rate, sentences, frame_power, sentence_level_db, frame_s)
    targets, reasons, neighbors = {}, {}, {}
    for i, value in enumerate(before):
        if value < median - level_dev_db:
            targets[i] = median - level_dev_db + MARGIN_DB
            reasons[i] = ['negative_loudness_outlier']
        elif value > median + level_dev_db:
            targets[i] = median + level_dev_db - MARGIN_DB
            reasons[i] = ['positive_loudness_outlier']
    for i in range(len(sentences) - 1):
        if sentences[i]['scene_id'] == sentences[i + 1]['scene_id'] or abs(before[i + 1] - before[i]) <= scene_jump_db:
            continue
        low, high = (i, i + 1) if before[i] < before[i + 1] else (i + 1, i)
        if before[low] < median:
            neighbor_level = min(before[high], targets.get(high, before[high]))
            targets[low] = max(targets.get(low, before[low]), neighbor_level - scene_jump_db + MARGIN_DB)
            reasons.setdefault(low, []).append('quiet_scene_boundary_endpoint')
            neighbors.setdefault(low, []).append(high)
    output, changed, plan = pcm.copy(), np.zeros(len(pcm), dtype=bool), []
    process = filter_context
    if process is None:
        process = lambda samples, sample_rate, gain: _filter_context(samples, sample_rate, gain, scratch_dir, ffmpeg)
    settings = {}
    directions = {i: 1 if targets[i] > before[i] else -1 for i in targets}
    # Cut loud neighbors before choosing measured gains for quiet endpoints.
    order = sorted(targets, key=lambda i: (directions[i], i))
    for i in order:
        sid = sentences[i]['id']; start, end = intervals[sid]
        left = max(0, start - round(CONTEXT_S * rate))
        right = min(len(pcm), end + round(CONTEXT_S * rate))
        context = pcm[left:right].astype(np.float64) / (2 ** 31)
        original = pcm[start:end].astype(np.float64) / (2 ** 31)
        blend = min(round(BLEND_S * rate), len(original) // 4)
        _require(blend >= 2, 'Sentence too short for the fixed boundary blend')
        weight = np.ones(len(original)); ramp = .5 - .5 * np.cos(np.linspace(0, np.pi, blend))
        weight[:blend] = ramp; weight[-blend:] = ramp[::-1]
        settings[i] = (context, start - left, original, weight)
        plan.append({'id': sid, 'reason': reasons[i], 'gain_db': 0.0,
                     'requested_gain_db': targets[i] - before[i],
                     'gain_cap_reached': False, 'target_db': targets[i],
                     'start_frame': start, 'end_frame': end, 'attempts': []})

    after, after_median = before, median
    while True:
        retried = False
        for i, entry in zip(order, plan):
            # A corrected sentence can move the median or a neighboring target.
            # Revisit earlier entries against the resulting track, retaining at
            # least the original correction even if another change relaxes it.
            direction = directions[i]
            if direction > 0:
                target = max(targets[i], after_median - level_dev_db + MARGIN_DB,
                             *(after[j] - scene_jump_db + MARGIN_DB for j in neighbors.get(i, [])))
            else:
                target = min(targets[i], after_median + level_dev_db - MARGIN_DB)
            entry['target_db'] = target
            entry['target_reached'] = direction * (after[i] - target) >= 0
            if entry['target_reached'] or entry['gain_cap_reached']:
                continue
            residual = direction * (target - after[i])
            # Minimum progress bounds retries even for an unresponsive limiter or
            # a discontinuity in the active-frame gate. gain_db is always TOTAL
            # gain on the original context, never compounded between attempts.
            requested = entry['gain_db'] + direction * (max(MIN_GAIN_STEP_DB, residual) if entry['attempts'] else residual)
            gain = direction * min(GAIN_CAP_DB, direction * requested)
            context, offset, original, weight = settings[i]
            # Attenuation cannot introduce peaks and needs no limiter.
            filtered = context * 10 ** (gain / 20) if gain < 0 else process(context.copy(), rate, gain)
            _require(isinstance(filtered, np.ndarray) and filtered.shape == context.shape,
                     'Limiter changed context frame count; do not trim, pad or compensate silently')
            _require(np.isfinite(filtered).all(), 'Limiter returned nonfinite samples')
            selected = filtered[offset:offset + len(original)]
            mixed = original * (1 - weight) + selected * weight
            quantized = np.rint(mixed * (2 ** 23))
            _require((quantized >= -(2 ** 23)).all() and (quantized < 2 ** 23).all(), 'Correction would clip; refuse rather than clip')
            start, end = entry['start_frame'], entry['end_frame']
            output[start:end] = quantized.astype(np.int32) << 8
            changed[start:end] = True
            after, after_median = _levels(output, rate, sentences, frame_power, sentence_level_db, frame_s)
            entry.update(gain_db=gain, requested_gain_db=requested, gain_cap_reached=abs(gain) >= GAIN_CAP_DB)
            entry['attempts'].append({'gain_db': gain, 'target_db': target, 'after_db': after[i]})
            retried = True
        if not retried:
            break
    _require(len(output) == len(pcm) and np.array_equal(output[~changed], pcm[~changed]), 'Outside-interval PCM or total frames changed')
    after, after_median = _levels(output, rate, sentences, frame_power, sentence_level_db, frame_s)
    return output, {'plan': plan, 'median_before_db': median, 'median_after_db': after_median,
                    'before_db': dict(zip((s['id'] for s in sentences), before)),
                    'after_db': dict(zip((s['id'] for s in sentences), after)),
                    'gain_cap_db': GAIN_CAP_DB, 'target_margin_db': MARGIN_DB,
                    'total_frames_identical': True, 'outside_selected_intervals_pcm_identical': True}


def correct_file(wav, sentences, **settings):
    """Replace a caller-owned final WAV only after exact encoded-PCM verification."""
    import soundfile as sf
    wav = Path(wav)
    before = wav.stat()
    info = sf.info(wav)
    _require(info.channels == 1 and info.samplerate == 48000 and info.subtype == 'PCM_24',
             'Require final mono48kHz PCM24 WAV')
    original, rate = sf.read(wav, dtype='int32')
    output, result = correct_levels(original, rate, sentences, **settings)
    if not result['plan']:
        return result  # Keep already-good file bytes untouched, including its header.
    with tempfile.TemporaryDirectory(prefix='linux-level-final-', dir=wav.parent) as name:
        temporary = Path(name) / 'narration.wav'
        sf.write(temporary, output, rate, format='WAVEX', subtype='PCM_24')
        reread, actual_rate = sf.read(temporary, dtype='int32')
        _require(actual_rate == rate and len(reread) == len(original) and np.array_equal(reread, output),
                 'Encoded final PCM/rate/frame verification failed')
        current = wav.stat()
        _require((before.st_size, before.st_mtime_ns, before.st_ino) ==
                 (current.st_size, current.st_mtime_ns, current.st_ino), 'Final WAV changed concurrently')
        os.replace(temporary, wav)
    return result


def correct_loudness_file(wav, *, measure_loudness, target_lufs, tolerance_lu,
                          peak_ceiling_dbtp, scratch_dir=None, ffmpeg='ffmpeg',
                          filter_context=None):
    """Lift only a failing, peak-bound track with the existing limiter profile.

    Each attempt filters the original normalized PCM with increasing total gain,
    then measures the encoded candidate. Never trim or pad to conceal latency.
    Passing tracks keep their exact file bytes. The caller retains every gate.
    """
    import soundfile as sf
    wav = Path(wav)
    before_stat = wav.stat()
    before = measure_loudness(wav)
    before_lufs, before_peak = float(before['input_i']), float(before['input_tp'])
    _require(tolerance_lu > MARGIN_DB, 'Invalid loudness tolerance')
    if (not np.isfinite([before_lufs, before_peak]).all()
            or before_lufs >= target_lufs - tolerance_lu
            or target_lufs - before_lufs <= peak_ceiling_dbtp - before_peak):
        return None
    info = sf.info(wav)
    _require(info.channels == 1 and info.samplerate == 48000 and info.subtype == 'PCM_24',
             'Require final mono48kHz PCM24 WAV')
    original, rate = sf.read(wav, dtype='int32')
    _require(len(original) > 0, 'Require nonempty final narration')
    samples = original.astype(np.float64) / (2 ** 31)
    target = target_lufs - tolerance_lu + MARGIN_DB
    process = filter_context
    if process is None:
        process = lambda data, sample_rate, gain: _filter_context(data, sample_rate, gain, scratch_dir, ffmpeg)
    gain, after_lufs, after_peak, attempts = 0.0, before_lufs, before_peak, []
    with tempfile.TemporaryDirectory(prefix='loudness-final-', dir=wav.parent) as name:
        temporary = Path(name) / 'narration.wav'
        while after_lufs < target and gain < GAIN_CAP_DB:
            gain = min(GAIN_CAP_DB, gain + max(MIN_GAIN_STEP_DB, target - after_lufs))
            filtered = process(samples.copy(), rate, gain)
            _require(isinstance(filtered, np.ndarray) and filtered.shape == samples.shape,
                     'Limiter changed frame count; do not trim or pad')
            _require(np.isfinite(filtered).all(), 'Limiter returned nonfinite samples')
            quantized = np.rint(filtered * (2 ** 23))
            _require((quantized >= -(2 ** 23)).all() and (quantized < 2 ** 23).all(),
                     'Correction would clip; refuse rather than clip')
            output = quantized.astype(np.int32) << 8
            sf.write(temporary, output, rate, format='WAVEX', subtype='PCM_24')
            reread, actual_rate = sf.read(temporary, dtype='int32')
            _require(actual_rate == rate and len(reread) == len(original) and np.array_equal(reread, output),
                     'Encoded final PCM/rate/frame verification failed')
            after = measure_loudness(temporary)
            after_lufs, after_peak = float(after['input_i']), float(after['input_tp'])
            _require(np.isfinite([after_lufs, after_peak]).all(), 'Nonfinite corrected loudness')
            _require(after_peak <= peak_ceiling_dbtp, 'Correction exceeded true-peak ceiling')
            attempts.append({'gain_db': gain, 'lufs': after_lufs, 'true_peak_dbtp': after_peak})
        current = wav.stat()
        _require((before_stat.st_size, before_stat.st_mtime_ns, before_stat.st_ino) ==
                 (current.st_size, current.st_mtime_ns, current.st_ino), 'Final WAV changed concurrently')
        os.replace(temporary, wav)
    return {'reason': 'peak_bound_loudness', 'before_lufs': before_lufs,
            'before_true_peak_dbtp': before_peak, 'after_lufs': after_lufs,
            'after_true_peak_dbtp': after_peak, 'target_lufs': target,
            'target_margin_db': MARGIN_DB, 'gain_db': gain, 'gain_cap_db': GAIN_CAP_DB,
            'gain_cap_reached': gain >= GAIN_CAP_DB, 'target_reached': after_lufs >= target,
            'filter': filter_graph(rate, gain), 'attempts': attempts,
            'total_frames_identical': True}
