"""FIR bandpass filter design.

Wraps :func:`scipy.signal.firwin` with sensible defaults for the active
noise cancellation project: a linear-phase FIR with a Hamming window,
configurable cutoff frequencies and a default sample rate of 48 kHz
(matches the INMP441 microphone and PCM5102 DAC used on the target FPGA).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.signal import firwin


WindowName = Literal[
    "hamming", "hann", "blackman", "blackmanharris", "bartlett", "boxcar"
]


@dataclass(frozen=True)
class FilterSpec:
    """Parameters that fully describe a bandpass FIR filter design."""

    f_low: float
    f_high: float
    num_taps: int = 101
    fs: int = 48_000
    window: WindowName = "hamming"

    def __post_init__(self) -> None:
        if self.f_low <= 0 or self.f_high <= 0:
            raise ValueError("f_low and f_high must be positive Hz values")
        if self.f_low >= self.f_high:
            raise ValueError("f_low must be strictly less than f_high")
        if self.f_high >= self.fs / 2:
            raise ValueError("f_high must be below Nyquist (fs/2)")
        if self.num_taps < 3:
            raise ValueError("num_taps must be >= 3")
        # firwin requires odd length for a Type I linear-phase bandpass.
        if self.num_taps % 2 == 0:
            raise ValueError("num_taps must be odd for a bandpass FIR")


def design_bandpass(spec: FilterSpec) -> np.ndarray:
    """Design a linear-phase FIR bandpass filter and return its taps.

    Parameters
    ----------
    spec:
        Filter specification (passband edges, length, sample rate, window).

    Returns
    -------
    np.ndarray
        ``num_taps`` float64 coefficients (the ``b`` array, a.k.a. ``b_taps``).
    """
    taps = firwin(
        numtaps=spec.num_taps,
        cutoff=[spec.f_low, spec.f_high],
        pass_zero=False,
        window=spec.window,
        fs=spec.fs,
    )
    return np.asarray(taps, dtype=np.float64)
