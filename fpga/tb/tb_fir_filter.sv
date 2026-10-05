// -----------------------------------------------------------------------------
// tb_fir_filter.sv -- self-checking testbench for fir_filter.sv.
//
// Reads input samples from input_samples.hex (one signed 16-bit hex value per
// line, two's complement) and expected outputs from expected_samples.hex.
// Both files are produced by the Python reference:
//
//   python -m filter_anc.tb_export   # see helper script under scripts/
//
// The testbench drives one sample per clock with in_valid = 1, then compares
// out_sample with the expected value. The DUT is bit-exact with the Python
// fixed-point model.
// -----------------------------------------------------------------------------
`default_nettype none

`timescale 1ns/1ps

import fir_coeffs_pkg::*;

module tb_fir_filter;

    localparam int N_SAMPLES = 4096;

    reg                       clk = 1'b0;
    reg                       rst_n = 1'b0;
    reg                       in_valid = 1'b0;
    reg  signed [15:0]        in_sample = '0;
    wire                      out_valid;
    wire signed [15:0]        out_sample;

    // 50 MHz simulation clock (period chosen arbitrarily for the TB).
    always #10 clk = ~clk;

    fir_filter #(.N_TAPS(N_TAPS)) dut (
        .clk        (clk),
        .rst_n      (rst_n),
        .in_valid   (in_valid),
        .in_sample  (in_sample),
        .out_valid  (out_valid),
        .out_sample (out_sample)
    );

    reg signed [15:0] in_mem  [0:N_SAMPLES-1];
    reg signed [15:0] exp_mem [0:N_SAMPLES-1];
    integer i;
    integer mismatches = 0;

    initial begin
        $readmemh("input_samples.hex", in_mem);
        $readmemh("expected_samples.hex", exp_mem);

        // Reset.
        #25 rst_n = 1'b1;

        for (i = 0; i < N_SAMPLES; i = i + 1) begin
            @(negedge clk);
            in_sample = in_mem[i];
            in_valid  = 1'b1;
            @(posedge clk);
            #1;
            if (out_valid && out_sample !== exp_mem[i]) begin
                $display("MISMATCH @ %0d: dut=%0d exp=%0d",
                         i, out_sample, exp_mem[i]);
                mismatches = mismatches + 1;
            end
        end

        in_valid = 1'b0;

        if (mismatches == 0)
            $display("PASS: %0d samples matched the Python reference", N_SAMPLES);
        else
            $display("FAIL: %0d / %0d samples mismatched", mismatches, N_SAMPLES);

        $finish;
    end

endmodule

`default_nettype wire
