// -----------------------------------------------------------------------------
// inverter.sv -- sample-by-sample multiplication by -1, with saturation for
//                the -32768 corner case (since +32768 is not representable in
//                int16).
//
// Pure combinational. Pipeline upstream/downstream if timing requires it.
// -----------------------------------------------------------------------------
`default_nettype none

module inverter (
    input  wire signed [15:0] in_sample,
    output reg  signed [15:0] out_sample
);
    always_comb begin
        if (in_sample == 16'sh8000)
            out_sample = 16'sh7FFF;        // saturate -32768 -> +32767
        else
            out_sample = -in_sample;
    end
endmodule

`default_nettype wire
