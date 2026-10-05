"""Unit tests for the FIR filter package.

We cover three angles:
* Filter design produces a sensible bandpass (attenuation in stop bands,
  near-unity gain in the passband).
* The Q1.15 fixed-point implementation tracks the float64 reference within
  the expected quantization error.
* The Verilog exporter produces the expected snippet shape.
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy.signal import freqz

from filter_anc import (
    FilterSpec,
    apply_filter_fixed_q15,
    apply_filter_float,
    apply_filter_int,
    design_bandpass,
    quantize_taps_int,
    quantize_taps_q15,
    taps_to_verilog,
)
from filter_anc.signals import from_int16, music_with_beep, to_int16


FS = 48_000


@pytest.fixture(scope="module")
def spec() -> FilterSpec:
    return FilterSpec(f_low=2_500, f_high=3_500, num_taps=101, fs=FS, window="hamming")


@pytest.fixture(scope="module")
def taps(spec: FilterSpec) -> np.ndarray:
    return design_bandpass(spec)


def _gain_db_at(taps: np.ndarray, hz: float, fs: int = FS) -> float:
    w, h = freqz(taps, worN=8192, fs=fs)
    idx = int(np.argmin(np.abs(w - hz)))
    return float(20.0 * np.log10(np.abs(h[idx]) + 1e-12))


class TestDesign:
    def test_length_and_symmetry(self, taps: np.ndarray, spec: FilterSpec) -> None:
        assert taps.shape == (spec.num_taps,)
        assert np.allclose(taps, taps[::-1])

    def test_passband_gain(self, taps: np.ndarray) -> None:
        gain = _gain_db_at(taps, hz=3_000.0)
        assert gain > -1.0, f"Passband gain too low: {gain:.2f} dB"

    def test_stopband_attenuation(self, taps: np.ndarray) -> None:
        gain_low = _gain_db_at(taps, hz=500.0)
        gain_high = _gain_db_at(taps, hz=12_000.0)
        assert gain_low < -40.0, f"Low stopband not attenuated: {gain_low:.2f} dB"
        assert gain_high < -40.0, f"High stopband not attenuated: {gain_high:.2f} dB"

    def test_rejects_invalid_spec(self) -> None:
        with pytest.raises(ValueError):
            FilterSpec(f_low=100, f_high=50, num_taps=51, fs=FS)
        with pytest.raises(ValueError):
            FilterSpec(f_low=100, f_high=200, num_taps=50, fs=FS)
        with pytest.raises(ValueError):
            FilterSpec(f_low=100, f_high=30_000, num_taps=51, fs=FS)


class TestQuantization:
    def test_q15_round_trip(self, taps: np.ndarray) -> None:
        q = quantize_taps_q15(taps)
        assert q.dtype == np.int16
        back = q.astype(np.float64) / 2**15
        assert np.max(np.abs(back - taps)) < 2.0 / 2**15

    def test_int_round_trip(self, taps: np.ndarray) -> None:
        q, sb = quantize_taps_int(taps, scale_bits=15)
        assert sb == 15
        back = q.astype(np.float64) / 2**15
        assert np.max(np.abs(back - taps)) < 2.0 / 2**15


class TestEquivalence:
    """The Q1.15 / integer outputs must track the float reference closely."""

    @pytest.fixture(scope="class")
    def signal(self) -> np.ndarray:
        return music_with_beep(duration_s=1.0, fs=FS, beep_hz=3_000.0)

    def test_float_vs_q15(self, taps: np.ndarray, signal: np.ndarray) -> None:
        b_q15 = quantize_taps_q15(taps)
        x_i16 = to_int16(signal)
        y_float = apply_filter_float(taps, signal)
        y_q15 = from_int16(apply_filter_fixed_q15(b_q15, x_i16))

        corr = float(np.corrcoef(y_float, y_q15)[0, 1])
        rmse = float(np.sqrt(np.mean((y_float - y_q15) ** 2)))
        assert corr > 0.99, f"Correlation too low: {corr}"
        assert rmse < 0.01, f"RMSE too high: {rmse}"

    def test_float_vs_int(self, taps: np.ndarray, signal: np.ndarray) -> None:
        b_int, sb = quantize_taps_int(taps, scale_bits=15)
        x_i16 = to_int16(signal)
        y_float = apply_filter_float(taps, signal)
        y_int = from_int16(apply_filter_int(b_int, x_i16, scale_bits=sb))
        corr = float(np.corrcoef(y_float, y_int)[0, 1])
        assert corr > 0.99, f"Integer correlation too low: {corr}"

    def test_q15_no_overflow(self, taps: np.ndarray, signal: np.ndarray) -> None:
        b_q15 = quantize_taps_q15(taps)
        y = apply_filter_fixed_q15(b_q15, to_int16(signal))
        assert y.dtype == np.int16
        assert -32768 <= int(y.min()) <= int(y.max()) <= 32767


class TestVerilogExport:
    def test_systemverilog_snippet(self, taps: np.ndarray) -> None:
        text = taps_to_verilog(
            taps[:8], fs=FS, f_low=2_500, f_high=3_500, columns=4
        )
        assert "localparam logic signed [15:0] B_TAPS [0:7]" in text
        assert "// FIR bandpass filter coefficients (Q1.15, 8 taps)" in text
        assert "// Passband:    2500 - 3500 Hz" in text
        assert text.rstrip().endswith("};")
        hex_count = text.count("16'h")
        assert hex_count == 8

    def test_custom_name(self, taps: np.ndarray) -> None:
        text = taps_to_verilog(taps[:4], name="FIR_COEFFS", columns=4)
        assert "FIR_COEFFS" in text

    def test_accepts_int16_input(self, taps: np.ndarray) -> None:
        q = quantize_taps_q15(taps[:4])
        text = taps_to_verilog(q, columns=4)
        assert "16'h" in text
