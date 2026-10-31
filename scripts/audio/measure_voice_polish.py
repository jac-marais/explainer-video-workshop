"""Offline stock narration trial; writes only synthetic audio under the chosen output folder.

Run with scripts/run/heavy scripts/run/py scripts/audio/measure_voice_polish.py OUT.
Requires cached Kokoro and production Whisper assets; downloads nothing.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

import narrate_film as film
from linux_levels import correct_file
from text_tokens import normalized_tokens
from voice_polish import process_take, resolve

TEXTS = [
    'The small sensor measures the pressure inside the sealed chamber.',
    'As the air warms up, the pressure slowly starts to rise.',
    'The safety switch opens a valve before the pressure gets too high.',
    'Some air escapes through the valve, and the pressure falls again.',
    'The system closes the valve once the sensor reports a safe pressure.',
    'This simple cycle keeps the chamber steady as the temperature changes.',
]


def word_errors(expected, heard):
    previous = list(range(len(heard) + 1))
    for index, word in enumerate(expected, 1):
        current = [index]
        for offset, other in enumerate(heard, 1):
            current.append(min(current[-1] + 1, previous[offset] + 1,
                               previous[offset - 1] + (word != other)))
        previous = current
    return previous[-1]


def measure(output):
    output.mkdir(parents=True, exist_ok=True)
    module = importlib.util.spec_from_file_location('trial_voice', film.TOOLS_DIR / 'voice.py')
    voice = importlib.util.module_from_spec(module)
    module.loader.exec_module(voice)
    synthesize, identity = voice.load_kokoro(
        {'voice': 'af_heart', 'speed': .92, 'frontend': 3}, 0, {})
    rate = 24000
    parts, rows, quiet, speech = [np.zeros(rate // 2)], [], [], []
    cursor = rate // 2
    for index, text in enumerate(TEXTS):
        samples, actual_rate, _ = synthesize(text)
        if actual_rate != rate:
            raise ValueError('Unexpected synthesis rate')
        start = cursor
        parts.extend([samples, np.zeros(rate // 2)])
        cursor += len(samples) + rate // 2
        rows.append({'id': f's{index}', 'scene_id': f'scene{index // 2}', 'text': text, 'spoken_text': text,
                     'start': start / rate, 'end': cursor / rate})
        quiet.append(((cursor - int(.25 * rate)) / rate, (cursor - int(.05 * rate)) / rate))
        speech.append((start / rate, (start + len(samples)) / rate))
    parts.append(np.zeros(round(film.TAIL * rate)))
    clean = np.concatenate(parts)
    settings = resolve({'voice_polish': {'enabled': True}}, {'engine': 'kokoro'})
    results = {'fixture': 'Invented sensor passage; stock Kokoro af_heart, frontend 3, speed 0.92',
               'synthesis': identity, 'settings': settings,
               'ffmpeg': subprocess.run(['ffmpeg', '-version'], stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                        check=True).stdout.splitlines()[0],
               'duration_s': len(clean) / rate, 'quiet_intervals_s': quiet,
               'speech_intervals_s': speech, 'variants': {}}
    random = np.random.default_rng(41)
    noise = .0015 * random.normal(size=len(clean)) + .004 * np.sin(2 * np.pi * 35 * np.arange(len(clean)) / rate)
    for variant, samples in [('clean', clean), ('added_noise', clean + noise)]:
        folder = output / variant
        folder.mkdir(exist_ok=True)
        source = folder / 'source.wav'
        sf.write(source, samples, rate, subtype='DOUBLE')
        pair = {}
        for enabled in (False, True):
            name = 'after' if enabled else 'before'
            destination = folder / f'{name}-polish.wav'
            destination.unlink(missing_ok=True)
            processed, receipt = process_take(source, destination, {**settings, 'enabled': enabled})
            take, final = folder / f'{name}-take.wav', folder / f'{name}.wav'
            voice.ffmpeg_loudnorm(processed, take)
            correction = {}
            film.normalize(take, final, preserve_take_levels=True, correction=correction)
            level_correction = correct_file(final, rows, frame_power=film.frame_power,
                sentence_level_db=film.sentence_level_db, frame_s=film.FRAME_S,
                level_dev_db=film.LEVEL_DEV_DB, scene_jump_db=film.SCENE_JUMP_DB)
            asr, _ = film.transcribe(final)
            repaired, _, fallbacks, _ = film.align_with_repairs(final, rows, asr)
            timing = {'sentences': rows, 'duration': len(clean) / rate}
            flags, stats = film.audio_checks(timing, final, repaired, [])
            data, final_rate = sf.read(final)
            quiet_samples = np.concatenate([data[round(a * final_rate):round(b * final_rate)] for a, b in quiet])
            band = sosfilt(butter(4, [4000, 10000], btype='bandpass', fs=final_rate, output='sos'), data)
            band_samples = np.concatenate([band[round(a * final_rate):round(b * final_rate)] for a, b in speech])
            loudness = film.measure_loudness(final)
            expected = normalized_tokens(' '.join(TEXTS))
            heard = normalized_tokens(' '.join(word['word'] for word in asr))
            pair[name] = {'quiet_rms_dbfs': float(10 * np.log10(np.mean(quiet_samples ** 2) + 1e-18)),
                          'speech_4_10khz_dbfs': float(10 * np.log10(np.mean(band_samples ** 2) + 1e-18)),
                          'loudness_range_lu': float(loudness['input_lra']),
                          'asr_word_errors': word_errors(expected, heard),
                          'reference_words': len(expected), 'heard': ' '.join(word['word'] for word in asr),
                          'fallback_words': len(fallbacks), 'flags': flags, 'stats': stats,
                          'frames': len(data), 'polish': receipt,
                          'loudness_correction': correction, 'level_correction': level_correction}
            (folder / f'{name}-checks.json').write_text(json.dumps(pair[name], indent=2) + '\n')
            print(variant, name, json.dumps({key: pair[name][key] for key in
                  ('quiet_rms_dbfs', 'speech_4_10khz_dbfs', 'loudness_range_lu', 'asr_word_errors', 'fallback_words', 'flags')}), flush=True)
        results['variants'][variant] = pair
    (output / 'measurements.json').write_text(json.dumps(results, indent=2) + '\n')
    for pair in results['variants'].values():
        if any(row['flags'] or row['fallback_words'] for row in pair.values()):
            raise SystemExit('Existing gates failed; inspect measurements.json')
        if pair['after']['asr_word_errors'] != pair['before']['asr_word_errors']:
            raise SystemExit('Recognition word error count changed; inspect measurements.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    measure(parser.parse_args().output)
