// FIR bandpass filter coefficients (Q1.15)
// Sample rate: 48000 Hz
// Passband:    2500 - 3500 Hz
// Window:      hamming, 101 taps
//
// Regenerate this file from app/streamlit_app.py:
//   $ streamlit run app/streamlit_app.py
// then copy the "Verilog coefficients" snippet into this file.

`ifndef FIR_COEFFS_SVH
`define FIR_COEFFS_SVH

package fir_coeffs_pkg;

    // Number of taps must match fir_filter.sv's N_TAPS parameter.
    localparam int N_TAPS = 101;

    // Q1.15 signed coefficients. Placeholder values (low-pass-ish) until the
    // Streamlit app is used to regenerate them for the desired passband.
    localparam logic signed [15:0] B_TAPS [0:N_TAPS-1] = '{
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h7FFF, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000, 16'h0000, 16'h0000, 16'h0000,
        16'h0000
    };

endpackage : fir_coeffs_pkg

`endif // FIR_COEFFS_SVH
