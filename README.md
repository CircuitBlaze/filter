# FIR Bandpass Filter — Active Noise Cancellation

End-to-end study project for a FIR bandpass filter used as the core of an
**active noise cancellation** (ANC) pipeline. Combines a Python reference
model, two Jupyter notebooks, an interactive Streamlit designer and a
SystemVerilog skeleton ready to be dropped into the
[`basics-graphics-music`](https://github.com/yuri-panchul/basics-graphics-music)
FPGA project.

```
microphone (INMP441, I2S 16-bit) -> FIR bandpass -> inverter (x -1) -> speaker (PCM5102)
                                  |                                          |
                                  +-- "extracts the noise band"              +-- "plays the anti-phase to cancel it"
```

Default filter spec: bandpass **2500–3500 Hz** at **48 kHz**, **101 taps**,
Hamming window. The cutoff frequencies and number of taps are parametric and
can be re-tuned interactively from the Streamlit UI.

## Repository layout

```
filter/
  notebooks/
    1_1_fir_filter.ipynb         # 1.1  -- float64 reference + experiments
    1_2_fir_filter_16bit.ipynb   # 1.2  -- 16-bit fixed-point / integer
  app/
    streamlit_app.py             # 1.3  -- interactive designer + Verilog export
  fpga/
    rtl/{fir_filter,inverter,top,coeffs}.sv
    tb/tb_fir_filter.sv          # 1.4  -- FPGA skeleton (bonus)
  src/filter_anc/                # Python package (design + 3 implementations)
  scripts/generate_test_signals.py
  tests/test_filter.py
  transcripts/_combined.md       # reference voice notes (Russian)
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# or: pip install -e ".[notebooks,app,dev]"

# (optional) generate the three test WAV files used by the notebooks
python scripts/generate_test_signals.py

# 1.1 + 1.2 -- run the notebooks
jupyter notebook notebooks/

# 1.3 -- interactive UI
streamlit run app/streamlit_app.py

# tests
python -m pytest -q
```

## What each piece does

### 1.1 — `notebooks/1_1_fir_filter.ipynb`
Synthesizes a FIR bandpass with `scipy.signal.firwin`, plots the magnitude /
impulse responses, and runs the **three canonical experiments** on
*(I)* music, *(II)* music + 3 kHz beep, *(III)* white noise — six
before/after spectrograms and inline audio players.

### 1.2 — `notebooks/1_2_fir_filter_16bit.ipynb`
Repeats the same flow with three 16-bit variants of the filter
(`float16`, **Q1.15 fixed-point** and integer-only). Verifies that the
quantized magnitude response keeps the right bandpass shape and that the
Q1.15 implementation is correlated >0.99 with the float reference. This is
the variant that ships to the FPGA.

### 1.3 — `app/streamlit_app.py`
Interactive designer. Two number inputs (`f_low`, `f_high`), a button to
recalculate, and live updates of every plot from 1.1 / 1.2. At the bottom
of the page, a read-only code block renders the **Verilog `localparam`**
with the Q1.15 coefficients — copy-paste ready for the FPGA project.

### 1.4 — `fpga/`
SystemVerilog skeleton for the on-board version:
`mic_driver -> fir_filter -> inverter -> spk_driver`. The drivers come from
`basics-graphics-music`. The FIR module is bit-exact with
`filter_anc.filter_fixed.apply_filter_fixed_q15`, so the Python model is
a golden reference for `fpga/tb/tb_fir_filter.sv`.

## Source modules

| Module | Purpose |
|--------|---------|
| `src/filter_anc/design.py`       | `FilterSpec` + `design_bandpass` (firwin wrapper) |
| `src/filter_anc/characteristics.py` | `freqz`, impulse response, spectrogram helpers |
| `src/filter_anc/filter_float.py` | Float64 reference implementation |
| `src/filter_anc/filter_fixed.py` | Q1.15 fixed-point implementation (FPGA-grade) |
| `src/filter_anc/filter_int.py`   | Integer-only implementation (configurable scale) |
| `src/filter_anc/signals.py`      | Synthetic music / beep / noise generators + WAV I/O |
| `src/filter_anc/verilog_export.py` | Format Q1.15 taps as Verilog `localparam` or `.hex` |

## Why "active noise cancellation"?

From the project conversation (preserved in
[`transcripts/_combined.md`](transcripts/_combined.md)): the demo idea is
to feed a microphone signal into a FIR bandpass that isolates the noise
band, invert it (×−1) and play it through a co-located speaker. The
anti-phase signal acoustically cancels the original noise in that band.
The 2.5–3.5 kHz default is a placeholder — the Streamlit UI lets you pick
any band that you want to cancel.

## License

MIT — see `pyproject.toml`.
