"""Helpers to compute and plot standard DSP characteristics of a FIR filter.

All plotting helpers return ``(fig, axes)`` so callers (notebooks or the
Streamlit app) can either ``plt.show()`` or further customize the figure.
"""
from __future__ import annotations

from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import freqz, spectrogram


def frequency_response(
    taps: np.ndarray, fs: int = 48_000, num_points: int = 4096
) -> Tuple[np.ndarray, np.ndarray]:
    """Return ``(freqs_hz, magnitude_db)`` for a FIR filter."""
    w, h = freqz(taps, worN=num_points, fs=fs)
    eps = 1e-12
    mag_db = 20.0 * np.log10(np.abs(h) + eps)
    return w, mag_db


def plot_frequency_response(
    taps: np.ndarray,
    fs: int = 48_000,
    title: str = "Frequency response",
) -> Tuple[plt.Figure, plt.Axes]:
    freqs, mag_db = frequency_response(taps, fs=fs)
    fig, ax = plt.subplots(figsize=(9, 3.5))
    ax.plot(freqs, mag_db)
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Magnitude [dB]")
    ax.set_title(title)
    ax.set_ylim(-100, 5)
    ax.set_xlim(0, fs / 2)
    ax.grid(True, alpha=0.4)
    fig.tight_layout()
    return fig, ax


def plot_impulse_response(
    taps: np.ndarray, title: str = "Impulse response"
) -> Tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(9, 3.0))
    ax.stem(np.arange(len(taps)), taps, basefmt=" ")
    ax.set_xlabel("Sample n")
    ax.set_ylabel("b[n]")
    ax.set_title(title)
    ax.grid(True, alpha=0.4)
    fig.tight_layout()
    return fig, ax


def plot_spectrogram(
    samples: np.ndarray,
    fs: int = 48_000,
    title: str = "Spectrogram",
    nperseg: int = 1024,
    noverlap: int | None = None,
    f_max: float | None = None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Plot a log-magnitude spectrogram of ``samples``."""
    if noverlap is None:
        noverlap = nperseg // 2
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    f, t, sxx = spectrogram(x, fs=fs, nperseg=nperseg, noverlap=noverlap)
    sxx_db = 10.0 * np.log10(sxx + 1e-12)

    fig, ax = plt.subplots(figsize=(9, 3.5))
    mesh = ax.pcolormesh(t, f, sxx_db, shading="auto", cmap="magma")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Frequency [Hz]")
    ax.set_title(title)
    if f_max is not None:
        ax.set_ylim(0, f_max)
    fig.colorbar(mesh, ax=ax, label="Power [dB]")
    fig.tight_layout()
    return fig, ax


def plot_before_after(
    before: np.ndarray,
    after: np.ndarray,
    fs: int = 48_000,
    title: str = "Filter effect",
    f_max: float | None = None,
) -> plt.Figure:
    """Render two spectrograms (before/after filtering) in a single figure."""
    if f_max is None:
        f_max = fs / 2
    fig, axes = plt.subplots(1, 2, figsize=(14, 3.8), sharey=True)
    for ax, samples, sub in zip(axes, (before, after), ("Before", "After")):
        x = np.asarray(samples, dtype=np.float64)
        if x.ndim > 1:
            x = x.mean(axis=1)
        f, t, sxx = spectrogram(x, fs=fs, nperseg=1024, noverlap=512)
        sxx_db = 10.0 * np.log10(sxx + 1e-12)
        mesh = ax.pcolormesh(t, f, sxx_db, shading="auto", cmap="magma")
        ax.set_xlabel("Time [s]")
        ax.set_title(f"{sub}: {title}")
        ax.set_ylim(0, f_max)
        fig.colorbar(mesh, ax=ax, label="dB")
    axes[0].set_ylabel("Frequency [Hz]")
    fig.tight_layout()
    return fig
