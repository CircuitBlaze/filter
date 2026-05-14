"""Active noise cancellation FIR filter package.

Public API re-exports the main building blocks so that notebooks and the
Streamlit app can keep imports short:

    from filter_anc import (
        design_bandpass,
        apply_filter_float,
        apply_filter_fixed_q15,
        apply_filter_int,
        FilterSpec,
    )
"""
from .design import FilterSpec, design_bandpass
from .filter_float import apply_filter_float
from .filter_fixed import apply_filter_fixed_q15, quantize_taps_q15
from .filter_int import apply_filter_int, quantize_taps_int
from .verilog_export import taps_to_verilog

__all__ = [
    "FilterSpec",
    "design_bandpass",
    "apply_filter_float",
    "apply_filter_fixed_q15",
    "quantize_taps_q15",
    "apply_filter_int",
    "quantize_taps_int",
    "taps_to_verilog",
]
