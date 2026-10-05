"""Integer-only FIR filter variant.

Coefficients are scaled to integers by a power-of-two factor ``scale_bits``
(default 15, equivalent to Q1.15 but kept as a free parameter so callers can
trade resolution for headroom). The accumulator is ``int64`` and the result
is right-shifted by ``scale_bits`` at the end. Unlike :mod:`filter_fixed`,
this variant exposes the scale explicitly and does not normalize the taps
to ``[-1, 1)`` before quantization, which makes it useful for filters with
gains different from unity.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np


def quantize_taps_int(
    taps: np.ndarray, scale_bits: int = 15
) -> Tuple[np.ndarray, int]:
    """Quantize float taps to integers using a power-of-two scale.

    Returns ``(int_taps, scale_bits)``. The taps are stored in the smallest
    signed type that can hold them; for ``scale_bits=15`` and coefficients in
    ``[-1, 1)`` this fits in ``int16``.
    """
    if scale_bits < 1 or scale_bits > 30:
        raise ValueError("scale_bits must be in [1, 30]")
    b = np.asarray(taps, dtype=np.float64)
    scale = 1 << scale_bits
    q = np.round(b * scale).astype(np.int64)
    dtype: np.dtype = np.int32 if np.max(np.abs(q)) >= (1 << 15) else np.int16
    return q.astype(dtype), scale_bits


def apply_filter_int(
    taps_int: np.ndarray, samples_i16: np.ndarray, scale_bits: int = 15
) -> np.ndarray:
    """Apply an integer FIR filter and return int16 output with saturation."""
    b = np.asarray(taps_int, dtype=np.int64)
    x = np.asarray(samples_i16, dtype=np.int64)
    if x.ndim != 1:
        raise ValueError("apply_filter_int expects a 1-D int16 array")

    n = x.shape[0]
    rounding = 1 << (scale_bits - 1)
    full = np.convolve(x, b, mode="full")[:n]
    out = (full + rounding) >> scale_bits
    return np.clip(out, -32768, 32767).astype(np.int16)
