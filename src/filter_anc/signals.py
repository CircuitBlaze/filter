"""Generators and I/O helpers for test signals used in the experiments.

The three canonical experiments from the project plan are:

* **Music** — a clean reference track.
* **Music + beep** — same music with a sinusoidal whistle inside the filter
  passband (used to demonstrate that the bandpass removes the beep).
* **Uniform / white noise** — random samples spanning the full spectrum.

For unit tests and quick demos we synthesize a "music" surrogate so the
project remains self-contained without copyrighted audio files.
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import soundfile as sf


INT16_MAX = 32_767


def synth_music(duration_s: float = 5.0, fs: int = 48_000, seed: int = 7) -> np.ndarray:
    """Synthesize a chord-like "music" surrogate (sum of harmonics + slow LFO).

    This is intentionally simple: a fundamental at A4 (440 Hz) plus a few
    harmonics, amplitude-modulated by a slow tremolo. It is *not* musical art
    — it merely provides a reproducible, royalty-free stand-in for a real
    track during automated tests and notebook demos.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(int(duration_s * fs)) / fs

    fundamentals = [220.0, 330.0, 440.0, 660.0]
    amps = [0.35, 0.25, 0.20, 0.10]
    phases = rng.uniform(0.0, 2 * np.pi, size=len(fundamentals))

    signal = np.zeros_like(t)
    for f0, a, ph in zip(fundamentals, amps, phases):
        signal += a * np.sin(2 * np.pi * f0 * t + ph)

    tremolo = 0.85 + 0.15 * np.sin(2 * np.pi * 1.5 * t)
    signal *= tremolo

    peak = np.max(np.abs(signal)) or 1.0
    return (signal / peak * 0.7).astype(np.float64)


def beep(
    duration_s: float = 5.0, fs: int = 48_000, freq_hz: float = 3_000.0, amp: float = 0.4
) -> np.ndarray:
    """Sinusoidal tone (whistle/beep) at ``freq_hz``."""
    t = np.arange(int(duration_s * fs)) / fs
    return amp * np.sin(2 * np.pi * freq_hz * t)


def white_noise(duration_s: float = 5.0, fs: int = 48_000, amp: float = 0.5, seed: int = 42) -> np.ndarray:
    """Uniform white noise scaled to ``[-amp, amp]``."""
    rng = np.random.default_rng(seed)
    return amp * (rng.random(int(duration_s * fs)) * 2.0 - 1.0)


def music_with_beep(
    duration_s: float = 5.0,
    fs: int = 48_000,
    beep_hz: float = 3_000.0,
    beep_amp: float = 0.3,
    seed: int = 7,
) -> np.ndarray:
    """Music surrogate mixed with a beep inside the target passband."""
    base = synth_music(duration_s=duration_s, fs=fs, seed=seed)
    tone = beep(duration_s=duration_s, fs=fs, freq_hz=beep_hz, amp=beep_amp)
    out = base + tone
    peak = np.max(np.abs(out)) or 1.0
    if peak > 0.95:
        out = out / peak * 0.95
    return out


def to_int16(samples: np.ndarray) -> np.ndarray:
    """Convert float samples in ``[-1, 1]`` to int16 with saturation."""
    x = np.asarray(samples, dtype=np.float64)
    clipped = np.clip(x * INT16_MAX, -INT16_MAX - 1, INT16_MAX)
    return clipped.astype(np.int16)


def from_int16(samples: np.ndarray) -> np.ndarray:
    """Convert int16 samples back to float in ``[-1, 1]``."""
    return np.asarray(samples, dtype=np.float64) / INT16_MAX


def save_wav(path: str | Path, samples: np.ndarray, fs: int = 48_000) -> None:
    """Write samples (float in ``[-1, 1]`` or int16) to a 16-bit PCM WAV."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if samples.dtype == np.int16:
        sf.write(str(p), samples, fs, subtype="PCM_16")
    else:
        sf.write(str(p), to_int16(samples), fs, subtype="PCM_16")


def load_wav(path: str | Path) -> Tuple[np.ndarray, int]:
    """Load a WAV file. Returns ``(samples_float, fs)`` with mono averaging."""
    data, fs = sf.read(str(path), always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data.astype(np.float64), int(fs)
