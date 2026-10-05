// -----------------------------------------------------------------------------
// top.sv -- top-level wiring for the active noise cancellation pipeline.
//
//   INMP441 -- I2S --> mic_driver --> fir_filter --> inverter --> spk_driver
//                                                                       |
//                                                                  I2S to PCM5102
//
// `mic_driver` and `spk_driver` are taken from the basics-graphics-music
// repository. Their port lists differ slightly per board, so wiring below
// uses placeholders -- adjust to match the BSP of the chosen target.
// -----------------------------------------------------------------------------
`default_nettype none

import fir_coeffs_pkg::*;

module top (
    input  wire        clk,         // board clock (e.g. 27 MHz on Tang Nano)
    input  wire        rst_n,       // active-low reset

    // INMP441 I2S microphone
    output wire        mic_sck,
    output wire        mic_ws,
    input  wire        mic_sd,

    // PCM5102 I2S DAC
    output wire        dac_bck,
    output wire        dac_lrck,
    output wire        dac_sd
);

    // -------------------------------------------------------------------------
    // I2S microphone driver: emits one int16 sample per WS edge with in_valid.
    // Provided by basics-graphics-music (instance name kept generic here).
    // -------------------------------------------------------------------------
    wire        mic_valid;
    wire signed [15:0] mic_sample;

    /* verilator lint_off PINMISSING */
    mic_driver_inmp441 u_mic_driver (
        .clk        (clk),
        .rst_n      (rst_n),
        .i2s_sck    (mic_sck),
        .i2s_ws     (mic_ws),
        .i2s_sd     (mic_sd),
        .sample_valid (mic_valid),
        .sample     (mic_sample)
    );
    /* verilator lint_on PINMISSING */

    // -------------------------------------------------------------------------
    // FIR bandpass filter (Q1.15 coefficients from fir_coeffs_pkg).
    // -------------------------------------------------------------------------
    wire        fir_valid;
    wire signed [15:0] fir_sample;

    fir_filter #(
        .N_TAPS (N_TAPS)
    ) u_fir (
        .clk        (clk),
        .rst_n      (rst_n),
        .in_valid   (mic_valid),
        .in_sample  (mic_sample),
        .out_valid  (fir_valid),
        .out_sample (fir_sample)
    );

    // -------------------------------------------------------------------------
    // Inverter (x -1) -- this is the active cancellation step.
    // -------------------------------------------------------------------------
    wire signed [15:0] anti_sample;
    inverter u_inv (
        .in_sample  (fir_sample),
        .out_sample (anti_sample)
    );

    // -------------------------------------------------------------------------
    // I2S speaker driver to PCM5102.
    // -------------------------------------------------------------------------
    /* verilator lint_off PINMISSING */
    spk_driver_pcm5102 u_spk_driver (
        .clk        (clk),
        .rst_n      (rst_n),
        .sample_valid (fir_valid),
        .sample     (anti_sample),
        .i2s_bck    (dac_bck),
        .i2s_lrck   (dac_lrck),
        .i2s_sd     (dac_sd)
    );
    /* verilator lint_on PINMISSING */

endmodule

`default_nettype wire
