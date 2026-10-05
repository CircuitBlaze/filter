"""Floating-point (float64) reference implementation of the FIR filter.

This is the *gold model* against which the quantized variants in
:mod:`filter_anc.filter_fixed` and :mod:`filter_anc.filter_int` are compared.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import lfilter


def apply_filter_float(taps: np.ndarray, samples: np.ndarray) -> np.ndarray:
    """Apply a FIR filter using float64 arithmetic.

    Parameters
    ----------
    taps:
        Filter coefficients (``b``).
    samples:
        1-D or 2-D input signal. For stereo input, each channel is filtered
        independently.

    Returns
    -------
    np.ndarray
        Filtered signal, same shape as ``samples``, dtype ``float64``.
    """
    b = np.asarray(taps, dtype=np.float64)
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim == 1:
        return lfilter(b, [1.0], x)
    return np.stack([lfilter(b, [1.0], x[..., c]) for c in range(x.shape[-1])], axis=-1)
