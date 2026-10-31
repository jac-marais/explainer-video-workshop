"""Bounded per-take voice processing; the voice method owns the acceptance rule."""
import math
from pathlib import Path
import subprocess

import soundfile as sf

REVISION = 1
# Bounds constrain tuning, not a claim that every allowed setting suits every voice.
PARAMETERS = {
    'highpass_hz': (70.0, 40.0, 120.0),
    'expander_threshold_dbfs': (-45.0, -70.0, -25.0),
    'expander_ratio': (1.5, 1.0, 3.0),
    'expander_range_db': (-12.0, -24.0, 0.0),
    'expander_attack_ms': (5.0, 1.0, 50.0),
    'expander_release_ms': (100.0, 20.0, 500.0),
    'deesser_intensity': (0.35, 0.0, 0.5),
    'deesser_max': (0.25, 0.0, 0.5),
    'deesser_frequency': (0.5, 0.0, 1.0),
    'presence_hz': (3500.0, 2000.0, 4500.0),
    'presence_gain_db': (0.5, 0.0, 3.0),
    'presence_q': (1.0, 0.5, 2.0),
    'compressor_threshold_dbfs': (-18.0, -30.0, -6.0),
    'compressor_ratio': (1.5, 1.0, 3.0),
    'compressor_attack_ms': (20.0, 5.0, 50.0),
    'compressor_release_ms': (150.0, 50.0, 500.0),
    'limiter_dbfs': (-1.6, -6.0, -1.5),
    'limiter_attack_ms': (5.0, 1.0, 10.0),
    'limiter_release_ms': (50.0, 20.0, 200.0),
}


def resolve(config, spec):
    """Merge workshop defaults, profile settings, then the selected voice override."""
    settings = {'enabled': spec['engine'] in ('qwen3', 'chatterbox'),
                **{key: bounds[0] for key, bounds in PARAMETERS.items()}}
    for override in (config.get('voice_polish', {}), spec.get('voice_polish', {})):
        if not isinstance(override, dict):
            raise ValueError('voice_polish must be an object')
        for key, value in override.items():
            if key == 'enabled':
                if not isinstance(value, bool):
                    raise ValueError('voice_polish.enabled must be boolean')
            elif key not in PARAMETERS:
                raise ValueError(f'Unknown voice_polish parameter: {key}')
            else:
                _, lower, upper = PARAMETERS[key]
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or not lower <= value <= upper):
                    raise ValueError(f'voice_polish.{key} must be finite in [{lower}, {upper}]')
            settings[key] = value
    return settings


def amplitude(decibels):
    return 10 ** (decibels / 20)


def filter_graph(settings, rate):
    """Keep expansion before compression and compensate the oversampled limiter delay."""
    if not settings['enabled']:
        return ''
    if not isinstance(rate, int) or rate < 24000 or rate > 192000:
        raise ValueError('Voice polish requires a sample rate from 24000 to 192000 Hz')
    return ','.join([
        f"highpass=f={settings['highpass_hz']}:p=2",
        f"agate=mode=downward:threshold={amplitude(settings['expander_threshold_dbfs'])}"
        f":ratio={settings['expander_ratio']}:range={amplitude(settings['expander_range_db'])}"
        f":attack={settings['expander_attack_ms']}:release={settings['expander_release_ms']}:makeup=1:detection=rms",
        f"deesser=i={settings['deesser_intensity']}:m={settings['deesser_max']}:f={settings['deesser_frequency']}:s=o",
        f"equalizer=f={settings['presence_hz']}:t=q:w={settings['presence_q']}:g={settings['presence_gain_db']}",
        f"acompressor=mode=downward:threshold={amplitude(settings['compressor_threshold_dbfs'])}"
        f":ratio={settings['compressor_ratio']}:attack={settings['compressor_attack_ms']}"
        f":release={settings['compressor_release_ms']}:makeup=1:detection=rms",
        f'aresample={rate * 4}',
        f"alimiter=limit={amplitude(settings['limiter_dbfs'])}:level=false:latency=true"
        f":attack={settings['limiter_attack_ms']}:release={settings['limiter_release_ms']}",
        f'aresample={rate}',
    ])


def process_take(source, destination, settings):
    """Return the input on bypass; otherwise write verified floating-point PCM separately."""
    source, destination = Path(source), Path(destination)
    if not settings['enabled']:
        return source, {'enabled': False}
    if source.resolve() == destination.resolve():
        raise ValueError('Voice polish must not overwrite its source')
    info = sf.info(source)
    if info.channels != 1 or info.frames == 0:
        raise ValueError('Voice polish requires nonempty mono audio')
    graph = filter_graph(settings, info.samplerate)
    subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-n', '-i', str(source),
                    '-af', graph, '-c:a', 'pcm_f64le', str(destination)],
                   stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True, timeout=120)
    result = sf.info(destination)
    if (result.frames, result.samplerate, result.channels) != (info.frames, info.samplerate, info.channels):
        raise ValueError('Voice polish changed frames, rate or channels; refuse to trim or pad')
    return destination, {'enabled': True, 'revision': REVISION, 'settings': settings,
                         'filter': graph, 'frames_preserved': True}
