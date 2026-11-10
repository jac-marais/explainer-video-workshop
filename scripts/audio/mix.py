#!/usr/bin/env python3
"""Synthesize music and sound events under mono narration into one WAV.

  scripts/run/py scripts/audio/mix.py --project DIR --events STILLS/sfx.json --out MIX.wav
      [--narration WAV] [--timing JSON] [--stems DIR]

Narration and timing default to DIR/audio/narration.wav and DIR/audio/timing.json.
Timing has a nonempty scenes list with finite, strictly increasing start times;
scene IDs do not select the music: programs cycle in scene order.
Events are {name, t, gain, pitch}; gain defaults to 1 and pitch to 0 semitones.
Everything is synthesized with numpy/scipy, with no samples or downloads. Stems
are music.wav and effects.wav after ducking, before the master limiter.
The narration is added at unity gain; only the master true-peak limiter changes
its peaks. The 24-bit output must retain its sample count, stay at or below
-1.5 dBTP, and move no more than 1 LU from its integrated loudness, or exit 1.
Empty, silent, nonfinite, stereo, sub-20-ms or below-24-kHz narration fails clearly.
Sound events may be empty; their times must fall within the narration, gains
must be nonnegative, and pitches must be within +/-120 semitones.
"""
import argparse
import json
import math
import zlib
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d

TEMPO_BPM = 120.0
SIXTEENTH_SECONDS = 60.0 / TEMPO_BPM / 4
BAR_SECONDS = 16 * SIXTEENTH_SECONDS
CHORD_SECONDS = 4 * BAR_SECONDS
FINAL_CHORD_SECONDS = 8.0
MUSIC_FADE_IN_SECONDS = 4.0
MUSIC_FADE_OUT_SECONDS = 2.5

MUSIC_UNDER_SPEECH_DB = -20.0  # music RMS relative to speech RMS while the voice is talking
MUSIC_DUCK_DEPTH_DB = 9.0  # how far the music rises back up in a clear gap
EFFECTS_REFERENCE_DB = 0.0  # peak of a trim-0, gain-1 effect relative to speech RMS
EFFECTS_DUCK_DEPTH_DB = 3.0
TRUE_PEAK_CEILING_DBTP = -1.7  # 0.2 dB under the -1.5 dBTP spec for margin
TRUE_PEAK_SPEC_DBTP = -1.5
LOUDNESS_TOLERANCE_LU = 1.0

THIN_WINDOW_SECONDS = 0.100
THIN_MAX_EVENTS_PER_WINDOW = 3
REPEAT_WINDOW_SECONDS = 0.400
REPEAT_ATTENUATION = 0.8
REPEAT_GAIN_FLOOR = 0.5
SAME_NAME_MIN_SPACING_SECONDS = 0.030

NOTE_BASE_MIDI = 74  # D5: `note` pitch 0 is the tonic of D major
DING_BASE_MIDI = 81  # A5: `ding` pitch 0 is the fifth of D major

# Key of D major; each chord has a bass note, pad voicing and five arpeggio tones (MIDI numbers).
CHORDS = {
    "Dmaj9": dict(bass=38, pad=[50, 57, 64, 66, 73], arp=[62, 66, 69, 73, 76]),
    "Dadd9": dict(bass=38, pad=[50, 57, 62, 64, 66], arp=[62, 64, 66, 69, 74]),
    "Bm9": dict(bass=35, pad=[47, 54, 61, 62, 66], arp=[59, 62, 66, 69, 73]),
    "Gmaj9": dict(bass=43, pad=[55, 59, 62, 66, 69], arp=[62, 66, 67, 69, 71]),
    "Em9": dict(bass=40, pad=[52, 59, 62, 66], arp=[59, 62, 64, 66, 71]),
    "A6sus": dict(bass=45, pad=[57, 62, 64, 66], arp=[64, 66, 69, 71, 74]),
    "F#m7": dict(bass=42, pad=[54, 57, 61, 64], arp=[61, 64, 66, 69, 73]),
}

SCENE_PROGRAMS = (
    dict(chords=["Dmaj9", "Gmaj9"], arp_a=0.5, arp_b=0.0, pulse=0.0, mallet=0.0, level=0.8),
    dict(chords=["Bm9", "Em9"], arp_a=0.7, arp_b=0.5, pulse=0.5, mallet=0.0, level=0.9),
    dict(chords=["Gmaj9", "A6sus"], arp_a=0.8, arp_b=0.7, pulse=0.7, mallet=0.5, level=1.0),
    dict(chords=["F#m7", "Bm9"], arp_a=0.6, arp_b=0.8, pulse=0.5, mallet=0.6, level=0.9),
)
FINAL_PROGRAM = dict(chords=["Dadd9"], arp_a=0.35, arp_b=0.2, pulse=0.0, mallet=0.3, level=0.8)

# Downbeats first, so a lower density keeps the strongest steps of the bar.
STEP_PRIORITY = [0, 8, 4, 12, 2, 10, 6, 14, 3, 11, 7, 15, 1, 9, 5, 13]
ARP_A_PATTERN = [0, 2, 1, 3, 2, 4, 3, 1]
ARP_B_PATTERN = [4, 2, 3, 1]
MALLET_PATTERN = [4, 2, 3, 0]

# Designer trims (dB) so every peak-normalized effect lands at a similar perceived level.
EFFECT_TRIM_DB = {
    "key": -9, "tick": -14, "click": -10, "pop": -8, "thump": -4, "thud": -4, "slam": -1,
    "whoosh": -9, "swish": -12, "ding": -9, "note": -8, "spring": -11, "riser": -8,
}


def k_weighting_coefficients(sample_rate):
    """BS.1770-4 K-weighting as two biquads, in the libebur128 form that reproduces the published 48 kHz values."""
    f0, gain_db, q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    k = np.tan(np.pi * f0 / sample_rate)
    vh = 10 ** (gain_db / 20)
    vb = vh ** 0.4996667741545416
    a0 = 1 + k / q + k * k
    shelf_b = np.array([(vh + vb * k / q + k * k) / a0, 2 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0])
    shelf_a = np.array([1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0])
    f0, q = 38.13547087602444, 0.5003270373238773
    k = np.tan(np.pi * f0 / sample_rate)
    a0 = 1 + k / q + k * k
    highpass_b = np.array([1.0, -2.0, 1.0])
    highpass_a = np.array([1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0])
    return shelf_b, shelf_a, highpass_b, highpass_a


def integrated_loudness_lufs(audio, sample_rate):
    shelf_b, shelf_a, highpass_b, highpass_a = k_weighting_coefficients(sample_rate)
    weighted = signal.lfilter(highpass_b, highpass_a, signal.lfilter(shelf_b, shelf_a, audio))
    if len(weighted) < int(round(0.4 * sample_rate)):
        weighted = np.pad(weighted, (0, int(round(0.4 * sample_rate)) - len(weighted)))
    block = int(round(0.4 * sample_rate))
    hop = block // 4
    cumulative = np.concatenate([[0.0], np.cumsum(weighted ** 2)])
    starts = np.arange(0, len(weighted) - block + 1, hop)
    block_power = (cumulative[starts + block] - cumulative[starts]) / block
    block_power = block_power[block_power > 10 ** ((-70 + 0.691) / 10)]
    if not len(block_power):
        return float("-inf")
    relative_gate = -0.691 + 10 * np.log10(block_power.mean()) - 10
    block_power = block_power[-0.691 + 10 * np.log10(block_power) > relative_gate]
    return -0.691 + 10 * np.log10(block_power.mean())


def true_peak_per_sample(audio):
    """Absolute peak of each sample and its three 4x-oversampled neighbours."""
    oversampled = signal.resample_poly(audio, 4, 1)[: len(audio) * 4]
    return np.maximum(np.abs(audio), np.abs(oversampled).reshape(-1, 4).max(axis=1))


def true_peak_dbtp(audio):
    return 20 * np.log10(true_peak_per_sample(audio).max() + 1e-12)


def db(value):
    return 20 * np.log10(value + 1e-12)


def rms(audio):
    return np.sqrt(np.mean(audio ** 2)) if len(audio) else 0.0



class SpeechAnalysis:
    """20 ms frame levels of the narration, speech/gap masks and the sidechain ducking curve."""

    FRAME_SECONDS = 0.020

    def __init__(self, narration, sample_rate):
        self.sample_rate = sample_rate
        frame = int(self.FRAME_SECONDS * sample_rate)
        frame_count = len(narration) // frame
        frames = narration[: frame_count * frame].reshape(frame_count, frame)
        self.frame_db = db(np.sqrt(np.mean(frames ** 2, axis=1)))
        reference_db = np.percentile(self.frame_db, 90)
        self.speech_mask = self.frame_db > reference_db - 20
        self.gap_mask = self.frame_db < reference_db - 40
        self.speech_rms = rms(frames[self.speech_mask].ravel())
        if self.speech_rms <= 1e-10:
            raise ValueError("narration has no measurable speech-level signal")
        self.frame_samples = frame
        self.reference_db = reference_db

    def ducking_gain(self, narration, depth_db, length):
        """Sidechain gain from the narration: 0 dB in clear gaps, -depth_db under speech."""
        control_rate = 1000
        step = self.sample_rate // control_rate
        # The running mean can round a hair below zero over digital silence, and sqrt of that is NaN.
        mean_square = np.maximum(uniform_filter1d(narration ** 2, size=int(0.030 * self.sample_rate)), 0)
        envelope = np.sqrt(mean_square[::step])
        envelope_db = db(envelope)
        presence = np.clip((envelope_db - (self.reference_db - 38)) / 14, 0, 1)
        # Hold 150 ms so word gaps do not pump; look ahead 60 ms so the dip starts before the syllable.
        presence = maximum_filter1d(presence, size=150, origin=-15)
        smoothed = np.empty_like(presence)
        level = presence[0]
        attack, release = 1 - np.exp(-1 / 40), 1 - np.exp(-1 / 250)
        for index, target in enumerate(presence):
            level += (target - level) * (attack if target > level else release)
            smoothed[index] = level
        gain_db = -depth_db * smoothed
        control_times = np.arange(len(gain_db)) * step
        return 10 ** (np.interp(np.arange(length), control_times, gain_db) / 20)



def midi_to_hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


class Instruments:
    """Cached synthesized notes; a few seeded variants per pitch so repeats are not identical."""

    VARIANTS = 3

    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self.cache = {}

    def note(self, instrument, midi, variant):
        key = (instrument, midi, variant % self.VARIANTS)
        if key not in self.cache:
            rng = np.random.default_rng([zlib.crc32(instrument.encode()), midi, key[2]])
            self.cache[key] = getattr(self, "_" + instrument)(midi, rng)
        return self.cache[key]

    def _time(self, seconds):
        return np.arange(int(seconds * self.sample_rate)) / self.sample_rate

    def _attack(self, t, seconds):
        return np.clip(t / seconds, 0, 1)

    def _pluck(self, midi, rng):
        """Felt-piano-like pluck: harmonic partials, upper ones fade faster."""
        t = self._time(1.6)
        frequency = midi_to_hz(midi) * 2 ** (rng.uniform(-3, 3) / 1200)
        wave = np.zeros_like(t)
        for harmonic in range(1, 7):
            amplitude = 0.42 ** (harmonic - 1) / harmonic
            decay = 3.2 * (1 + 0.9 * (harmonic - 1)) * rng.uniform(0.9, 1.1)
            wave += amplitude * np.sin(2 * np.pi * frequency * harmonic * t + rng.uniform(0, 2 * np.pi)) * np.exp(-decay * t)
        wave *= self._attack(t, 0.004)
        return wave / np.abs(wave).max()

    def _bell(self, midi, rng):
        """Higher, glassier pluck for the interlocking second voice."""
        t = self._time(1.8)
        frequency = midi_to_hz(midi) * 2 ** (rng.uniform(-3, 3) / 1200)
        partials = [(1.0, 1.0, 2.2), (2.0, 0.25, 4.0), (3.0, 0.08, 6.0), (4.07, 0.06, 9.0)]
        wave = np.zeros_like(t)
        for ratio, amplitude, decay in partials:
            wave += amplitude * np.sin(2 * np.pi * frequency * ratio * t) * np.exp(-decay * rng.uniform(0.9, 1.1) * t)
        wave *= self._attack(t, 0.003)
        return wave / np.abs(wave).max()

    def _mallet(self, midi, rng):
        """Soft marimba-like mallet with the 4x and 10x bar partials."""
        t = self._time(1.4)
        frequency = midi_to_hz(midi) * 2 ** (rng.uniform(-3, 3) / 1200)
        wave = np.sin(2 * np.pi * frequency * t) * np.exp(-3.0 * t)
        wave += 0.18 * np.sin(2 * np.pi * frequency * 3.99 * t) * np.exp(-14 * t)
        wave += 0.05 * np.sin(2 * np.pi * frequency * 9.9 * t) * np.exp(-30 * t)
        wave *= self._attack(t, 0.002)
        return wave / np.abs(wave).max()

    def _pulse(self, midi, rng):
        """Muted low pulse: fundamental plus octave so small speakers still hear the beat."""
        t = self._time(0.45)
        frequency = midi_to_hz(midi + 12)
        wave = np.sin(2 * np.pi * frequency * t) + 0.35 * np.sin(4 * np.pi * frequency * t) * np.exp(-12 * t)
        wave *= np.exp(-9 * t * rng.uniform(0.95, 1.05)) * self._attack(t, 0.008)
        return wave / np.abs(wave).max()


def add_at(buffer, start_sample, sound, gain):
    if start_sample >= len(buffer) or start_sample + len(sound) <= 0:
        return
    sound_start = max(0, -start_sample)
    start_sample = max(0, start_sample)
    end = min(len(buffer), start_sample + len(sound) - sound_start)
    buffer[start_sample:end] += gain * sound[sound_start : sound_start + end - start_sample]


def final_chord_start(total_seconds):
    return total_seconds - min(FINAL_CHORD_SECONDS, total_seconds / 4)


def chord_timeline(scenes, total_seconds):
    """List of (start, end, chord name, program) sections; scene boundaries change the harmony."""
    sections = []
    final_start = final_chord_start(total_seconds)
    for index, scene in enumerate(scenes):
        scene_start = 0.0 if index == 0 else scene["start"]
        scene_end = scenes[index + 1]["start"] if index + 1 < len(scenes) else total_seconds
        program = SCENE_PROGRAMS[index % len(SCENE_PROGRAMS)]
        scene_end = min(scene_end, final_start)
        chord_start = scene_start
        chord_index = 0
        while chord_start < scene_end - 1e-6:
            chord_end = min(chord_start + CHORD_SECONDS, scene_end)
            sections.append((chord_start, chord_end, program["chords"][chord_index % len(program["chords"])], program))
            chord_start = chord_end
            chord_index += 1
    sections.append((final_start, total_seconds, FINAL_PROGRAM["chords"][0], FINAL_PROGRAM))
    return sections


def section_at(sections, time_seconds):
    for section in sections:
        if section[0] <= time_seconds < section[1]:
            return section
    return sections[-1]


def synthesize_pad(sections, sample_rate, length):
    """Warm detuned additive pad, rendered at a quarter rate then upsampled; crossfades at each chord change."""
    pad_rate = sample_rate // 4
    pad_length = length // 4 + 1
    pad = np.zeros(pad_length)
    crossfade = 1.2
    rng = np.random.default_rng(7)
    for start, end, chord_name, program in sections:
        segment_start = max(0.0, start - crossfade / 2)
        segment_end = min(length / sample_rate, end + crossfade / 2)
        t = np.arange(int((segment_end - segment_start) * pad_rate)) / pad_rate
        absolute_t = t + segment_start
        wave = np.zeros_like(t)
        for midi in CHORDS[chord_name]["pad"]:
            for detune_cents in (-6, 0, 7):
                frequency = midi_to_hz(midi) * 2 ** (detune_cents / 1200)
                for harmonic in range(1, 5):
                    wave += (0.35 ** (harmonic - 1) / harmonic) * np.sin(
                        2 * np.pi * frequency * harmonic * absolute_t + rng.uniform(0, 2 * np.pi))
        breathing = 1 + 0.15 * np.sin(2 * np.pi * 0.07 * absolute_t + rng.uniform(0, 2 * np.pi))
        fade_in = np.clip((absolute_t - segment_start) / crossfade, 0, 1) if segment_start > 0 else 1.0
        fade_out = np.clip((segment_end - absolute_t) / crossfade, 0, 1) if segment_end < length / sample_rate else 1.0
        envelope = np.sin(0.5 * np.pi * fade_in) * np.sin(0.5 * np.pi * fade_out)
        start_index = int(segment_start * pad_rate)
        segment = wave * breathing * envelope * program["level"] / len(CHORDS[chord_name]["pad"])
        pad[start_index : start_index + len(segment)] += segment[: pad_length - start_index]
    return signal.resample_poly(pad, 4, 1)[:length]


def synthesize_music(scenes, sample_rate, length):
    total_seconds = length / sample_rate
    sections = chord_timeline(scenes, total_seconds)
    instruments = Instruments(sample_rate)
    music = 0.55 * synthesize_pad(sections, sample_rate, length)
    rng = np.random.default_rng(102)
    step_count = int(total_seconds / SIXTEENTH_SECONDS)
    arp_entry_seconds = 2 * BAR_SECONDS  # pad alone for two bars, then the first voice enters
    for step in range(step_count):
        time_seconds = step * SIXTEENTH_SECONDS
        _, _, chord_name, program = section_at(sections, time_seconds)
        chord = CHORDS[chord_name]
        level = program["level"]
        step_in_bar = step % 16
        start_sample = int(round(time_seconds * sample_rate))
        humanize_db = rng.normal(0, 1.0)
        accent = 1.0 if step_in_bar % 4 == 0 else 0.8
        # Voice A: sixteenth-note arpeggio; density keeps the highest-priority steps of each bar.
        if time_seconds >= arp_entry_seconds and step_in_bar in STEP_PRIORITY[: round(program["arp_a"] * 16)]:
            midi = chord["arp"][ARP_A_PATTERN[step % len(ARP_A_PATTERN)]]
            add_at(music, start_sample, instruments.note("pluck", midi, step), 0.16 * accent * level * 10 ** (humanize_db / 20))
        # Voice B: dotted-eighth cycle an octave up, so it phases against voice A every three bars.
        if program["arp_b"] > 0 and step % 3 == 1:
            midi = chord["arp"][ARP_B_PATTERN[(step // 3) % len(ARP_B_PATTERN)]] + 12
            add_at(music, start_sample, instruments.note("bell", midi, step), 0.07 * program["arp_b"] * level * 10 ** (humanize_db / 20))
        # Pulse: quarter notes on the chord root, softer on the off-beats.
        if program["pulse"] > 0 and step_in_bar % 4 == 0:
            beat_gain = 1.0 if step_in_bar in (0, 8) else 0.6
            add_at(music, start_sample, instruments.note("pulse", chord["bass"], step), 0.22 * program["pulse"] * beat_gain * level)
        # Mallet: a slow four-note line on beats 1 and 3.
        if program["mallet"] > 0 and step_in_bar in (0, 8):
            midi = chord["arp"][MALLET_PATTERN[(step // 8) % len(MALLET_PATTERN)]] + 12
            add_at(music, start_sample, instruments.note("mallet", midi, step), 0.10 * program["mallet"] * level)
    # Chapter mark: a low mallet bloom on the root at every scene boundary after the first.
    for scene in scenes[1:]:
        chord = CHORDS[section_at(sections, scene["start"] + 0.01)[2]]
        add_at(music, int(scene["start"] * sample_rate), instruments.note("mallet", chord["bass"] + 24, 0), 0.30)
    # Resolution: the final tonic rings out from the last chord change.
    final_start = final_chord_start(total_seconds)
    add_at(music, int(final_start * sample_rate), instruments.note("mallet", 62, 1), 0.30)
    t = np.arange(length) / sample_rate
    fade_in = np.clip(t / MUSIC_FADE_IN_SECONDS, 0, 1) ** 2
    fade_out = np.clip((total_seconds - t) / MUSIC_FADE_OUT_SECONDS, 0, 1)
    return music * fade_in * np.sin(0.5 * np.pi * fade_out), sections



class Effects:
    """Each effect is a function of (rng, pitch) returning a peak-normalized mono sound."""

    def __init__(self, sample_rate):
        self.sample_rate = sample_rate

    def render(self, name, rng, pitch):
        synthesizer = getattr(self, "_" + name, None)
        if synthesizer is None:
            raise SystemExit(f"unknown sound event name {name!r}")
        sound = synthesizer(rng, pitch)
        tail = int(0.004 * self.sample_rate)
        sound[-tail:] *= np.linspace(1, 0, tail)
        return sound / (np.abs(sound).max() + 1e-12)

    def _time(self, seconds):
        return np.arange(int(seconds * self.sample_rate)) / self.sample_rate

    def _band_noise(self, rng, count, low_hz, high_hz, order=2):
        nyquist = self.sample_rate / 2
        high_hz = min(high_hz, nyquist * 0.95)
        sos = signal.butter(order, [low_hz / nyquist, high_hz / nyquist], btype="band", output="sos")
        return signal.sosfilt(sos, rng.standard_normal(count))

    def _low_noise(self, rng, count, cutoff_hz):
        sos = signal.butter(2, cutoff_hz / (self.sample_rate / 2), output="sos")
        return signal.sosfilt(sos, rng.standard_normal(count))

    def _sweep_sine(self, t, start_hz, end_hz, sweep_seconds):
        frequency = end_hz + (start_hz - end_hz) * np.exp(-t / sweep_seconds)
        return np.sin(2 * np.pi * np.cumsum(frequency) / self.sample_rate)

    def _key(self, rng, pitch):
        """Light, weighted typewriter tick: a bright strike, a small body and the key bottoming out."""
        t = self._time(0.07)
        variation = rng.uniform(0.85, 1.15)
        strike = self._band_noise(rng, len(t), 1800 * variation, 6500 * variation) * np.exp(-t / (0.004 * variation))
        body = 0.6 * np.sin(2 * np.pi * 190 * variation * t) * np.exp(-t / 0.014)
        bottom_delay = int(rng.uniform(0.008, 0.014) * self.sample_rate)
        bottom = np.zeros_like(t)
        bottom[bottom_delay:] = 0.35 * self._band_noise(rng, len(t) - bottom_delay, 900, 3500) * np.exp(-t[: len(t) - bottom_delay] / 0.003)
        return (strike / (np.abs(strike).max() + 1e-12) + body + bottom) * np.clip(t / 0.0005, 0, 1)

    def _tick(self, rng, pitch):
        t = self._time(0.03)
        frequency = rng.uniform(2600, 3400)
        return np.sin(2 * np.pi * frequency * t) * np.exp(-t / 0.0035) + 0.3 * self._band_noise(rng, len(t), 3000, 9000) * np.exp(-t / 0.002)

    def _click(self, rng, pitch):
        t = self._time(0.06)
        sound = self._band_noise(rng, len(t), 2000, 8000) * np.exp(-t / 0.0015)
        release_delay = int(rng.uniform(0.022, 0.030) * self.sample_rate)
        sound[release_delay:] += 0.55 * self._band_noise(rng, len(t) - release_delay, 2500, 9000) * np.exp(-t[: len(t) - release_delay] / 0.0012)
        return sound

    def _pop(self, rng, pitch):
        t = self._time(0.09)
        start_hz = rng.uniform(280, 340)
        wave = self._sweep_sine(t, start_hz, start_hz * 2.3, 0.012)
        return wave * np.exp(-t / 0.022) * np.clip(t / 0.001, 0, 1)

    def _thump(self, rng, pitch):
        t = self._time(0.35)
        variation = rng.uniform(0.9, 1.1)
        body = self._sweep_sine(t, 95 * variation, 50 * variation, 0.03) * np.exp(-t / 0.09)
        body += 0.25 * self._sweep_sine(t, 190 * variation, 100 * variation, 0.03) * np.exp(-t / 0.04)
        noise = self._low_noise(rng, len(t), 350) * np.exp(-t / 0.025)
        return (body + 0.4 * noise / (np.abs(noise).max() + 1e-12)) * np.clip(t / 0.002, 0, 1)

    def _thud(self, rng, pitch):
        t = self._time(0.3)
        variation = rng.uniform(0.9, 1.1)
        body = self._sweep_sine(t, 150 * variation, 75 * variation, 0.025) * np.exp(-t / 0.07)
        noise = self._low_noise(rng, len(t), 900) * np.exp(-t / 0.03)
        return (body + 0.5 * noise / (np.abs(noise).max() + 1e-12)) * np.clip(t / 0.0015, 0, 1)

    def _slam(self, rng, pitch):
        """Low impact with metallic resonance and delayed clicks."""
        t = self._time(2.4)
        variation = rng.uniform(0.95, 1.05)
        boom = self._sweep_sine(t, 70, 36, 0.08) * np.exp(-t / 0.45)
        impact = self._low_noise(rng, len(t), 450) * np.exp(-t / 0.12)
        impact /= np.abs(impact).max() + 1e-12
        clank = np.zeros_like(t)
        for ratio, amplitude, decay_seconds in [(1.0, 0.5, 0.9), (2.29, 0.35, 0.6), (3.76, 0.25, 0.4), (5.68, 0.15, 0.25), (8.3, 0.08, 0.15)]:
            clank += amplitude * np.sin(2 * np.pi * 178 * variation * ratio * t) * np.exp(-t / decay_seconds)
        room = self._low_noise(rng, len(t), 1200) * np.exp(-t / 0.5)
        room = 0.08 * room / (np.abs(room).max() + 1e-12)
        sound = boom + 0.7 * impact + 0.45 * clank + room
        for delay_seconds, amplitude in [(0.11, 0.35), (0.33, 0.22), (0.38, 0.15)]:
            delay = int(delay_seconds * variation * self.sample_rate)
            latch = self._band_noise(rng, len(t) - delay, 1000, 5000) * np.exp(-t[: len(t) - delay] / 0.006)
            sound[delay:] += amplitude * latch / (np.abs(latch).max() + 1e-12)
        return sound * np.clip(t / 0.002, 0, 1)

    def _air(self, rng, seconds, bands_hz, peak_fraction):
        """Filtered-noise sweep: band envelopes peak one after another, so the colour rises then falls."""
        t = self._time(seconds)
        sound = np.zeros_like(t)
        for index, (low_hz, high_hz) in enumerate(bands_hz):
            centre = seconds * (peak_fraction * (0.6 + 0.8 * index / max(1, len(bands_hz) - 1)))
            width = seconds * 0.28
            band = self._band_noise(rng, len(t), low_hz, high_hz)
            sound += band / (np.abs(band).max() + 1e-12) * np.exp(-0.5 * ((t - centre) / width) ** 2)
        return sound * np.sin(np.pi * np.clip(t / seconds, 0, 1)) ** 1.5

    def _whoosh(self, rng, pitch):
        variation = rng.uniform(0.9, 1.1)
        return self._air(rng, 0.6 * variation, [(250, 700), (600, 1600), (1400, 3500), (3000, 7000)], 0.5)

    def _swish(self, rng, pitch):
        variation = rng.uniform(0.9, 1.1)
        return self._air(rng, 0.28 * variation, [(1200, 3000), (2500, 6000), (5000, 11000)], 0.45)

    def _ding(self, rng, pitch):
        t = self._time(1.6)
        frequency = midi_to_hz(DING_BASE_MIDI + pitch) * 2 ** (rng.uniform(-4, 4) / 1200)
        sound = np.zeros_like(t)
        for ratio, amplitude, decay_seconds in [(1.0, 1.0, 0.9), (2.0, 0.2, 0.5), (2.76, 0.3, 0.35), (5.4, 0.12, 0.15)]:
            sound += amplitude * np.sin(2 * np.pi * frequency * ratio * t) * np.exp(-t / decay_seconds)
        return sound * np.clip(t / 0.001, 0, 1)

    def _note(self, rng, pitch):
        """Soft mallet pluck in D major; pitch is semitones above D5."""
        t = self._time(0.9)
        frequency = midi_to_hz(NOTE_BASE_MIDI + pitch) * 2 ** (rng.uniform(-4, 4) / 1200)
        decay = rng.uniform(0.9, 1.1)
        sound = np.sin(2 * np.pi * frequency * t) * np.exp(-t / (0.35 * decay))
        sound += 0.2 * np.sin(2 * np.pi * frequency * 2 * t) * np.exp(-t / 0.12)
        sound += 0.12 * np.sin(2 * np.pi * frequency * 3.99 * t) * np.exp(-t / 0.04)
        return sound * np.clip(t / 0.0015, 0, 1)

    def _spring(self, rng, pitch):
        t = self._time(0.45)
        base_hz = rng.uniform(240, 290)
        wobble = 1 + 0.22 * np.exp(-t / 0.12) * np.sin(2 * np.pi * rng.uniform(12, 15) * t)
        phase = 2 * np.pi * np.cumsum(base_hz * wobble) / self.sample_rate
        return (np.sin(phase) + 0.2 * np.sin(2 * phase)) * np.exp(-t / 0.13) * np.clip(t / 0.002, 0, 1)

    def _riser(self, rng, pitch):
        """Gentle ~1 s swell: rising filtered air and a soft D-A-E chord, with a short tail."""
        seconds = 1.0 * rng.uniform(0.95, 1.05)
        tail_seconds = 0.25
        t = self._time(seconds + tail_seconds)
        swell = np.where(t < seconds, (t / seconds) ** 2.2, np.exp(-(t - seconds) / 0.07))
        air = np.zeros_like(t)
        for index, (low_hz, high_hz) in enumerate([(400, 1200), (1000, 3000), (2500, 7000)]):
            band = self._band_noise(rng, len(t), low_hz, high_hz)
            air += band / (np.abs(band).max() + 1e-12) * np.clip(t / seconds, 0, 1) ** (index + 1)
        chord = sum(np.sin(2 * np.pi * midi_to_hz(midi) * (1 + 0.01 * t) * t) for midi in (62, 69, 76)) / 3
        return (0.5 * air + chord) * swell


def thin_events(events):
    """Drop events beyond the per-window cap and soften close repeats of the same sound."""
    kept = []
    for event in sorted(events, key=lambda item: item["t"]):
        recent = [other for other in kept if event["t"] - other["t"] < THIN_WINDOW_SECONDS]
        if len(recent) >= THIN_MAX_EVENTS_PER_WINDOW:
            continue
        same_name = [other for other in kept if other["name"] == event["name"] and event["t"] - other["t"] < REPEAT_WINDOW_SECONDS]
        if same_name and event["t"] - same_name[-1]["t"] < SAME_NAME_MIN_SPACING_SECONDS:
            continue
        attenuation = max(REPEAT_GAIN_FLOOR, REPEAT_ATTENUATION ** len(same_name))
        kept.append(dict(event, gain=float(event.get("gain", 1.0)) * attenuation))
    return kept


def synthesize_effects(events, sample_rate, length):
    effects = Effects(sample_rate)
    bus = np.zeros(length)
    for event in events:
        rng = np.random.default_rng([zlib.crc32(event["name"].encode()), int(round(event["t"] * 1000))])
        sound = effects.render(event["name"], rng, float(event.get("pitch", 0)))
        trim = 10 ** ((EFFECT_TRIM_DB[event["name"]] + rng.normal(0, 0.8)) / 20)
        add_at(bus, int(round(event["t"] * sample_rate)), sound, trim * event["gain"])
    return bus



def true_peak_limit(audio, ceiling_dbtp, sample_rate):
    """Lookahead true-peak limiter; returns the limited audio and the maximum gain reduction in dB."""
    ceiling = 10 ** (ceiling_dbtp / 20)
    width = int(0.010 * sample_rate)
    total_reduction = np.ones_like(audio)
    for _ in range(4):
        peaks = true_peak_per_sample(audio * total_reduction)
        if peaks.max() <= ceiling:
            break
        required = np.minimum(1.0, ceiling / (peaks + 1e-12)) * 0.999
        gain = uniform_filter1d(minimum_filter1d(required, size=width), size=width)
        total_reduction *= gain
    return audio * total_reduction, -db(total_reduction.min())


def finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def validate_inputs(timing, events, total_seconds):
    scenes = timing.get("scenes") if isinstance(timing, dict) else None
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("timing needs a nonempty scenes list")
    previous_start = -1.0
    for scene in scenes:
        if not isinstance(scene, dict):
            raise ValueError("each scene must be an object with a start")
        start = finite_number(scene.get("start"), "scene start")
        if not 0 <= start < total_seconds or start <= previous_start:
            raise ValueError("scene starts must increase strictly within the narration")
        previous_start = start
    if not isinstance(events, list):
        raise ValueError("sound events must be a list (empty is allowed)")
    validated_events = []
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("name"), str) or event["name"] not in EFFECT_TRIM_DB:
            raise ValueError(f"unknown or missing sound event name: {event.get('name') if isinstance(event, dict) else event!r}")
        time = finite_number(event.get("t"), "event t")
        gain = finite_number(event.get("gain", 1), "event gain")
        pitch = finite_number(event.get("pitch", 0), "event pitch")
        if not 0 <= time < total_seconds or gain < 0 or abs(pitch) > 120:
            raise ValueError("event t must be inside narration, gain >= 0 and pitch within +/-120 semitones")
        validated_events.append(dict(event, t=time, gain=gain, pitch=pitch))
    return scenes, validated_events


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, type=Path, help="run composition folder")
    parser.add_argument("--narration", type=Path, help="default: PROJECT/audio/narration.wav")
    parser.add_argument("--timing", type=Path, help="default: PROJECT/audio/timing.json")
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--stems", type=Path, help="directory for music-only and effects-only WAVs")
    arguments = parser.parse_args()

    arguments.narration = arguments.narration or arguments.project / "audio" / "narration.wav"
    arguments.timing = arguments.timing or arguments.project / "audio" / "timing.json"
    input_paths = [arguments.narration, arguments.timing, arguments.events]
    output_paths = [arguments.out]
    if arguments.stems:
        output_paths += [arguments.stems / "music.wav", arguments.stems / "effects.wav"]
    resolved_outputs = [path.resolve() for path in output_paths]
    if len(set(resolved_outputs)) != len(resolved_outputs) or set(resolved_outputs) & {path.resolve() for path in input_paths}:
        raise ValueError("mix and stems must have distinct paths separate from the inputs")
    narration, sample_rate = sf.read(arguments.narration, dtype="float64", always_2d=True)
    if narration.shape[1] != 1:
        raise SystemExit(f"expected mono narration, got {narration.shape[1]} channels")
    narration = narration[:, 0]
    length = len(narration)
    if not length:
        raise ValueError("narration is empty")
    if sample_rate < 24000:
        raise ValueError("narration sample rate must be at least 24000 Hz")
    if length < int(SpeechAnalysis.FRAME_SECONDS * sample_rate):
        raise ValueError("narration must be at least 20 ms long")
    if not np.isfinite(narration).all():
        raise ValueError("narration samples must be finite")
    if np.max(np.abs(narration)) <= 1e-10:
        raise ValueError("narration is silent")
    timing = json.loads(arguments.timing.read_text())
    events = json.loads(arguments.events.read_text())
    scenes, events = validate_inputs(timing, events, length / sample_rate)

    speech = SpeechAnalysis(narration, sample_rate)
    speech_samples = np.repeat(speech.speech_mask, speech.frame_samples)
    speech_samples = np.concatenate([speech_samples, np.zeros(length - len(speech_samples), bool)])
    gap_samples = np.repeat(speech.gap_mask, speech.frame_samples)
    gap_samples = np.concatenate([gap_samples, np.zeros(length - len(gap_samples), bool)])

    music, sections = synthesize_music(scenes, sample_rate, length)
    music *= speech.ducking_gain(narration, MUSIC_DUCK_DEPTH_DB, length)
    music_rms = rms(music[speech_samples])
    if music_rms <= 1e-12:
        raise ValueError("music has no measurable signal during narration")
    music *= speech.speech_rms * 10 ** (MUSIC_UNDER_SPEECH_DB / 20) / music_rms

    kept_events = thin_events(events)
    effects = synthesize_effects(kept_events, sample_rate, length)
    effects *= speech.speech_rms * 10 ** (EFFECTS_REFERENCE_DB / 20)
    effects *= speech.ducking_gain(narration, EFFECTS_DUCK_DEPTH_DB, length)

    mix, limiter_reduction_db = true_peak_limit(narration + music + effects, TRUE_PEAK_CEILING_DBTP, sample_rate)

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(arguments.out, mix, sample_rate, subtype="PCM_24")
    if arguments.stems:
        arguments.stems.mkdir(parents=True, exist_ok=True)
        sf.write(arguments.stems / "music.wav", music, sample_rate, subtype="PCM_24")
        sf.write(arguments.stems / "effects.wav", effects, sample_rate, subtype="PCM_24")

    written, _ = sf.read(arguments.out, dtype="float64")
    narration_lufs = integrated_loudness_lufs(narration, sample_rate)
    mix_lufs = integrated_loudness_lufs(written, sample_rate)
    mix_true_peak = true_peak_dbtp(written)
    speech_db = db(speech.speech_rms)
    print(f"length: {len(written)} samples = {len(written) / sample_rate:.3f} s at {sample_rate} Hz (narration {length} samples)")
    print(f"loudness: narration {narration_lufs:.2f} LUFS, mix {mix_lufs:.2f} LUFS, delta {mix_lufs - narration_lufs:+.2f} LU")
    print(f"true peak: narration {true_peak_dbtp(narration):.2f} dBTP, mix {mix_true_peak:.2f} dBTP, limiter max reduction {limiter_reduction_db:.2f} dB")
    print(f"events: {len(events)} in, {len(kept_events)} kept, {len(events) - len(kept_events)} thinned")
    print(f"music re speech RMS: under speech {db(rms(music[speech_samples])) - speech_db:+.1f} dB, in gaps {db(rms(music[gap_samples])) - speech_db:+.1f} dB")
    print(f"effects bus peak re speech RMS: {db(np.abs(effects).max()) - speech_db:+.1f} dB")
    print(f"chord sections: {len(sections)}; scenes: {len(timing['scenes'])}")

    failures = []
    if len(written) != length:
        failures.append("length differs from narration")
    if mix_true_peak > TRUE_PEAK_SPEC_DBTP:
        failures.append(f"true peak {mix_true_peak:.2f} dBTP is above {TRUE_PEAK_SPEC_DBTP} dBTP")
    if not math.isfinite(mix_lufs) or not math.isfinite(narration_lufs):
        failures.append("integrated loudness cannot be measured")
    elif abs(mix_lufs - narration_lufs) > LOUDNESS_TOLERANCE_LU:
        failures.append(f"loudness moved {mix_lufs - narration_lufs:+.2f} LU from the narration")
    if failures:
        raise SystemExit("FAILED: " + "; ".join(failures))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, RuntimeError) as error:
        raise SystemExit(str(error)) from error
