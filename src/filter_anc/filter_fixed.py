"""Fixed-point Q1.15 FIR filter — the candidate for the FPGA port.

Format conventions
------------------

* Coefficients are stored as ``int16`` in Q1.15 format, representing values in
  the range ``[-1, 1)`` with a resolution of ``2**-15 ≈ 30.5e-6``.
* Samples are 16-bit signed integers (``int16``), matching the INMP441 / I2S
  word width described in the project plan.
* Accumulation happens in ``int64`` to provide enough headroom for
  ``num_taps`` multiply-accumulates without overflow.
* The accumulator is shifted right by 15 bits at the end of each sample to
  return to the Q1.15 domain, and is then saturated to ``int16``.

This mirrors what the SystemVerilog FIR module in ``fpga/rtl/fir_filter.sv``
is expected to do, so the Python model can serve as a bit-exact reference
for hardware verification.
"""
from __future__ import annotations

import numpy as np

Q15_SCALE = 1 << 15  # 32768
INT16_MAX = (1 << 15) - 1  # 32767
INT16_MIN = -(1 << 15)  # -32768


def quantize_taps_q15(taps: np.ndarray) -> np.ndarray:
    """Quantize float taps in ``[-1, 1]`` to Q1.15 ``int16``.

    Coefficients are rescaled so that ``max(|b|) <= 0.999`` before quantization
    to avoid the ``+1.0`` corner case which is unrepresentable in Q1.15.
    """
    b = np.asarray(taps, dtype=np.float64)
    peak = float(np.max(np.abs(b)))
    if peak >= 1.0:
        b = b / peak * 0.999
    q = np.round(b * Q15_SCALE).astype(np.int64)
    q = np.clip(q, INT16_MIN, INT16_MAX)
    return q.astype(np.int16)


def apply_filter_fixed_q15(
    taps_q15: np.ndarray, samples_i16: np.ndarray
) -> np.ndarray:
    """Apply a Q1.15 FIR filter to int16 samples.

    Parameters
    ----------
    taps_q15:
        Filter coefficients as ``int16`` in Q1.15 format
        (use :func:`quantize_taps_q15` on the float design).
    samples_i16:
        Mono ``int16`` input samples.

    Returns
    -------
    np.ndarray
        Filtered ``int16`` samples with saturation, same length as input.
    """
    b = np.asarray(taps_q15, dtype=np.int64)
    x = np.asarray(samples_i16, dtype=np.int64)
    if x.ndim != 1:
        raise ValueError("apply_filter_fixed_q15 expects a 1-D int16 array")

    n = x.shape[0]
    # np.convolve preserves int64 arithmetic when both inputs are int64,
    # so this is bit-identical to a manual tap-by-tap MAC loop but ~1000x
    # faster than a Python loop. We take the first ``n`` outputs to match
    # the causal FIR output (the rest is the convolution tail).
    full = np.convolve(x, b, mode="full")[:n]
    rounded = (full + (1 << 14)) >> 15  # round-to-nearest, return to Q1.15
    return np.clip(rounded, INT16_MIN, INT16_MAX).astype(np.int16)
