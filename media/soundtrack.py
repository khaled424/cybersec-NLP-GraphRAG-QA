"""Synthesised soundtrack: a 96 BPM tech-electronic bed plus sound effects placed on the timeline cues.

Everything is generated with NumPy/SciPy (no samples, no licences): soft synth pads, sub bass, kick,
crisp hi-hats, then a whoosh on each hard cut, a click + shimmer on button presses, keyboard ticks
while text types, glassy pops for tiles, an airy reverse swell into each hero star and a warm
rising chime with a sub hit on the end card. The music stops its drums on the end card and the pad
resolves and rings out.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44_100
BPM = 96
BEAT = 60 / BPM
RNG = np.random.default_rng(7)

# A minor progression, 2 bars per chord: Am(add9) – Fmaj7 – C(add9) – G6
CHORDS = [(45, [57, 60, 64, 67, 71]), (41, [53, 57, 60, 64, 69]), (48, [55, 60, 64, 67, 74]), (43, [55, 59, 62, 64, 71])]


def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


def band(signal: np.ndarray, low: float | None, high: float | None, order: int = 2) -> np.ndarray:
    if low and high:
        sos = butter(order, [low, high], btype="bandpass", fs=SR, output="sos")
    elif low:
        sos = butter(order, low, btype="highpass", fs=SR, output="sos")
    else:
        sos = butter(order, high, btype="lowpass", fs=SR, output="sos")
    return sosfilt(sos, signal)


def env(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.exp(-np.maximum(0, t - attack) / max(decay, 1e-4))


def add(track: np.ndarray, sound: np.ndarray, at: float, gain: float = 1.0) -> None:
    start = int(at * SR)
    if start >= len(track):
        return
    if start < 0:
        sound, start = sound[-start:], 0
    end = min(len(track), start + len(sound))
    track[start:end] += gain * sound[: end - start]


def reverb(signal: np.ndarray, seconds: float = 2.2, wet: float = 0.25) -> np.ndarray:
    n = int(seconds * SR)
    ir = RNG.standard_normal(n) * np.exp(-np.arange(n) / SR * 3.2)
    ir = band(ir, 200, 7000)
    tail = fftconvolve(signal, ir)[: len(signal)]
    return (1 - wet) * signal + wet * tail / (np.abs(tail).max() + 1e-9) * np.abs(signal).max()


# ------------------------------------------------------------------ music bed
def pad_note(freq: float, seconds: float, detune: float) -> np.ndarray:
    t = np.arange(int(seconds * SR)) / SR
    wave_ = sum(np.sin(2 * np.pi * k * freq * (1 + detune) * t + k) / k ** 1.3 for k in range(1, 7))
    return wave_ * np.minimum(1, t / 0.9) * np.minimum(1, (seconds - t) / 0.8)


def music(duration: float, drums_until: float) -> tuple[np.ndarray, np.ndarray]:
    n = int(duration * SR) + SR
    left, right = np.zeros(n), np.zeros(n)
    bar = 4 * BEAT
    span = 2 * bar
    k, t0 = 0, 0.0
    while t0 < duration:
        root, notes = CHORDS[k % len(CHORDS)]
        last = t0 + span >= drums_until  # the chord under the end card rings out
        length = (duration - t0 + 1.2) if last else span + 0.9
        for m in notes:
            add(left, pad_note(hz(m), length, -0.004), t0, 0.05)
            add(right, pad_note(hz(m), length, +0.004), t0, 0.05)
        # sub bass pulse on eighth notes, ducked like a sidechain
        for i in range(int(span / (BEAT / 2))):
            at = t0 + i * BEAT / 2
            if at >= min(duration, drums_until):
                break
            seg = int(BEAT / 2 * SR)
            tt = np.arange(seg) / SR
            bass = np.tanh(2.2 * np.sin(2 * np.pi * hz(root) * tt)) * env(seg, 0.01, 0.16)
            add(left, bass, at, 0.11); add(right, bass, at, 0.11)
        if last:
            add(left, pad_note(hz(root + 12), length, 0), t0, 0.06)
            add(right, pad_note(hz(root + 12), length, 0), t0, 0.06)
            break
        t0 += span
        k += 1
    mono = band((left + right) / 2, None, 2600)
    left, right = band(left, None, 2600), band(right, None, 2600)
    # drums
    beat_t = 0.0
    while beat_t < min(duration, drums_until) - 1e-6:
        i = round(beat_t / BEAT)
        intro = beat_t < 1.25
        if not intro:
            add(left, kick(), beat_t, 0.42); add(right, kick(), beat_t, 0.42)
            if i % 2 == 1:
                c = clap()
                add(left, c, beat_t, 0.13); add(right, c, beat_t + 0.008, 0.13)
        for j, g in ((0, 0.05), (0.5, 0.11), (0.25, 0.03), (0.75, 0.04)):  # crisp hats
            h = hat()
            add(left if j in (0.25, 0.5) else right, h, beat_t + j * BEAT, g * (0.5 if intro else 1))
        beat_t += BEAT
    del mono
    return left[: int(duration * SR)], right[: int(duration * SR)]


def kick() -> np.ndarray:
    n = int(0.32 * SR)
    t = np.arange(n) / SR
    freq = 45 + 85 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 11)


def clap() -> np.ndarray:
    n = int(0.18 * SR)
    return band(RNG.standard_normal(n), 900, 3200) * env(n, 0.002, 0.06)


def hat() -> np.ndarray:
    n = int(0.05 * SR)
    return band(RNG.standard_normal(n), 7500, None, 4) * env(n, 0.001, 0.014)


# ------------------------------------------------------------------ sound effects
def whoosh() -> tuple[np.ndarray, float]:
    """Noise sweep peaking on the cut; returns (sound, offset before the cut)."""
    pre, post = 0.32, 0.22
    n = int((pre + post) * SR)
    t = np.arange(n) / SR
    noise = RNG.standard_normal(n)
    bands = [band(noise, f * 0.7, f * 1.4) for f in (400, 900, 2000, 4500)]
    pos = np.clip(t / pre, 0, 1) * 3
    mix = sum(b * np.clip(1 - np.abs(pos - i), 0, 1) for i, b in enumerate(bands))
    shape = np.where(t < pre, (t / pre) ** 2.2, np.exp(-(t - pre) / 0.07))
    return mix * shape, pre


def click() -> np.ndarray:
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2400 * t) * 0.6 + band(RNG.standard_normal(n), 2000, None)) * env(n, 0.0005, 0.008)


def shimmer() -> np.ndarray:
    n = int(1.1 * SR)
    out = np.zeros(n)
    for i, m in enumerate((84, 88, 91, 95, 98)):
        seg = n - int(i * 0.045 * SR)
        tt = np.arange(seg) / SR
        out[n - seg:] += np.sin(2 * np.pi * hz(m) * tt) * env(seg, 0.004, 0.32) * 0.5
    return out


def tick(rng: np.random.Generator) -> np.ndarray:
    n = int(0.018 * SR)
    t = np.arange(n) / SR
    return (band(rng.standard_normal(n), 2500, 9000) + 0.4 * np.sin(2 * np.pi * rng.uniform(1500, 2100) * t)) * env(n, 0.0005, 0.004)


def pop(rng: np.random.Generator) -> np.ndarray:
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    f = rng.uniform(1300, 2100) * (1 + 0.25 * np.exp(-t * 40))
    phase = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(phase) + 0.35 * np.sin(2.76 * phase)) * env(n, 0.002, 0.05)


def swell() -> tuple[np.ndarray, float]:
    pre = 0.7
    n = int((pre + 0.15) * SR)
    t = np.arange(n) / SR
    air = band(RNG.standard_normal(n), 1500, 9000)
    tone = sum(np.sin(2 * np.pi * hz(m) * t) for m in (69, 76, 81)) / 3
    shape = np.where(t < pre, (t / pre) ** 3, np.exp(-(t - pre) / 0.05))
    return (0.6 * air + 0.5 * tone) * shape, pre


def chime() -> np.ndarray:
    n = int(3.2 * SR)
    out = np.zeros(n)
    for i, m in enumerate((69, 72, 76, 81)):  # warm rising arpeggio
        seg = n - int(i * 0.09 * SR)
        tt = np.arange(seg) / SR
        bell = sum(a * np.sin(2 * np.pi * hz(m) * r * tt) * np.exp(-tt * d) for r, a, d in ((1, 1, 1.4), (2, 0.4, 2.4), (2.76, 0.22, 3.5)))
        out[n - seg:] += bell * np.minimum(1, tt / 0.004) * 0.35
    tt = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (42 + 20 * np.exp(-tt * 9)) * tt) * np.exp(-tt * 2.2)
    return out + 0.9 * sub


# ------------------------------------------------------------------ assembly
def render_soundtrack(cues: list[dict], duration: float, path: Path, drums_until: float | None = None,
                      music_gain: float = 1.0) -> Path:
    chime_at = next((c["t"] for c in cues if c["type"] == "chime"), None)
    drums_until = drums_until or chime_at or duration
    left, right = music(duration, drums_until)
    fx = np.zeros_like(left)
    rng = np.random.default_rng(3)
    for c in cues:
        t = c["t"]
        if c["type"] == "whoosh":
            s, pre = whoosh(); add(fx, s, t - pre, 0.22)
        elif c["type"] == "click":
            add(fx, click(), t, 0.5); add(fx, shimmer(), t + 0.01, 0.12)
        elif c["type"] == "type":
            at = t
            while at < t + c["dur"]:
                add(fx, tick(rng), at, rng.uniform(0.18, 0.32))
                at += rng.uniform(0.035, 0.07)
        elif c["type"] == "pop":
            add(fx, pop(rng), t, 0.16)
        elif c["type"] == "swell":
            s, pre = swell(); add(fx, s, t - pre, 0.16)
        elif c["type"] == "chime":
            add(fx, chime(), t, 0.5)
    fx = reverb(fx, 1.6, 0.18)
    left, right = music_gain * reverb(left, 2.4, 0.3) + fx, music_gain * reverb(right, 2.4, 0.3) + fx
    stereo = np.stack([left, right], axis=1)
    stereo /= np.abs(stereo).max() + 1e-9
    stereo = np.tanh(stereo * 1.4) / np.tanh(1.4) * 0.89
    fade = int(0.35 * SR)
    stereo[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
    pcm = (stereo * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(SR)
        out.writeframes(pcm.tobytes())
    return path
