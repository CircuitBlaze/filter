// -----------------------------------------------------------------------------
// fir_filter.sv -- parameterized Q1.15 FIR direct-form filter.
//
// Implements the same arithmetic as
//   filter_anc.filter_fixed.apply_filter_fixed_q15
// so the Python model can be used as a bit-exact reference in
// tb_fir_filter.sv.
//
// Math:
//   acc[i] = sum_{k=0..N-1} ( x[i-k] * b[k] )            -- int64 MAC
//   y[i]   = saturate_i16( (acc[i] + (1 << 14)) >>> 15 ) -- Q1.15 -> int16
//
// Coefficients come from fir_coeffs_pkg (see coeffs.sv).
// -----------------------------------------------------------------------------
`default_nettype none

import fir_coeffs_pkg::*;

module fir_filter #(
    parameter int N_TAPS    = fir_coeffs_pkg::N_TAPS,
    parameter int ACC_WIDTH = 40   // generous headroom over 16x16 MAC
)(
    input  wire                       clk,
    input  wire                       rst_n,
    input  wire                       in_valid,
    input  wire  signed [15:0]        in_sample,
    output reg                        out_valid,
    output reg   signed [15:0]        out_sample
);

    // Shift-register of the most recent N_TAPS input samples.
    reg signed [15:0] shift_reg [0:N_TAPS-1];

    // Combinational MAC over the shift register.
    integer k;
    reg  signed [ACC_WIDTH-1:0] acc;
    reg  signed [ACC_WIDTH-1:0] rounded;
    reg  signed [16:0]          shifted;  // 17 bits to detect saturation

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (k = 0; k < N_TAPS; k = k + 1)
                shift_reg[k] <= '0;
            out_valid  <= 1'b0;
            out_sample <= '0;
        end else begin
            out_valid <= 1'b0;

            if (in_valid) begin
                for (k = N_TAPS-1; k > 0; k = k - 1)
                    shift_reg[k] <= shift_reg[k-1];
                shift_reg[0] <= in_sample;

                acc = '0;
                for (k = 0; k < N_TAPS; k = k + 1) begin
                    acc = acc + $signed(shift_reg[k]) * $signed(B_TAPS[k]);
                end

                rounded = acc + (1 <<< 14);
                shifted = rounded >>> 15;

                if (shifted >  17'sd32767) out_sample <=  16'sd32767;
                else if (shifted < -17'sd32768) out_sample <= -16'sd32768;
                else                            out_sample <= shifted[15:0];

                out_valid <= 1'b1;
            end
        end
    end

endmodule

`default_nettype wire
