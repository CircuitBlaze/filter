# 1.3 интерактивный UI два ноутбука (1.1 и 1.2) завёрнутые в Streamlit
# запуск: uv run streamlit run app/streamlit_app.py

import sys
from io import BytesIO
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import streamlit as st
from scipy.signal import firwin, freqz, lfilter, spectrogram

from filter_anc.signals import (
    synth_music, music_with_beep, white_noise, load_wav, to_int16, from_int16,
)

FS = 48_000

st.set_page_config(page_title="FIR designer", layout="wide")
st.title("FIR bandpass designer")
st.markdown(
    "Интерактивная версия ноутбуков 1.1 и 1.2. Слева крутишь полосу и длину фильтра, "
    "ниже автоматом пересчитываются АЧХ, спектрограммы и квантованная версия Q1.15. "
    "В самом низу — готовый Verilog-снипет с коэффициентами для FPGA."
)

# ---------- параметры ----------
with st.sidebar:
    st.header("параметры фильтра")
    f_low  = st.number_input("f_low, Hz", 20, FS // 2 - 100, 2_500, step=50)
    f_high = st.number_input("f_high, Hz", int(f_low) + 50, FS // 2 - 50,
                             max(3_500, int(f_low) + 500), step=50)
    n_taps = st.number_input("N taps (нечётное)", 11, 401, 101, step=2)
    if n_taps % 2 == 0:
        n_taps += 1
        st.warning(f"N должно быть нечётным → {n_taps}")
    duration = st.slider("длительность сигналов, с", 1.0, 6.0, 3.0, step=0.5)
    st.button("recalculate", use_container_width=True)

# ---------- дизайн фильтра ----------
b = firwin(int(n_taps), [f_low, f_high], pass_zero=False, window="hamming", fs=FS)
b_q15 = np.round(b * 2**15).astype(np.int16)


def wav_bytes(samples):
    buf = BytesIO()
    data = samples if samples.dtype == np.int16 else to_int16(samples)
    sf.write(buf, data, FS, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def fir_q15(b_q15, x_i16):
    full = np.convolve(x_i16.astype(np.int64), b_q15.astype(np.int64), mode="full")[:len(x_i16)]
    y = (full + (1 << 14)) >> 15
    return np.clip(y, -32768, 32767).astype(np.int16)


def plot_spec(ax, x, title):
    f, t, S = spectrogram(x.astype(np.float64), fs=FS, nperseg=1024, noverlap=512)
    ax.pcolormesh(t, f, 10*np.log10(S+1e-12), shading="auto", cmap="magma")
    ax.set_ylim(0, 8000); ax.set_title(title)
    ax.set_xlabel("s")


# подгружаем эталонные WAV если есть, иначе синтезируем
data = REPO / "data"
if (data / "music.wav").exists():
    music, _ = load_wav(data / "music.wav")
    beep,  _ = load_wav(data / "music_beep.wav")
    noise, _ = load_wav(data / "white_noise.wav")
    music = music[: int(duration * FS)]
    beep  = beep[: int(duration * FS)]
    noise = noise[: int(duration * FS)]
else:
    music = synth_music(duration, FS)
    beep  = music_with_beep(duration, FS, beep_hz=(f_low + f_high) / 2)
    noise = white_noise(duration, FS)

sigs = {"I. music": music, "II. music+beep": beep, "III. noise": noise}


# ==================================================================
# 1.1 — float64
# ==================================================================
st.header("1.1  float64 reference")
st.markdown(
    "Это то, что делает ноутбук `1_1_fir_filter.ipynb`: дизайн через `firwin`, "
    "АЧХ + импульсная, прогон тех же трёх сигналов через `lfilter`."
)

# --- 1.1.2 характеристики ---
st.subheader("1.1.2  характеристики")
w, h = freqz(b, worN=4096, fs=FS)

fig, ax = plt.subplots(1, 2, figsize=(13, 3.5))
ax[0].plot(w, 20*np.log10(np.abs(h)+1e-12))
ax[0].axvspan(f_low, f_high, alpha=0.15, color="g")
ax[0].set_xlim(0, FS/2); ax[0].set_ylim(-100, 5)
ax[0].set_xlabel("Hz"); ax[0].set_ylabel("dB"); ax[0].set_title("АЧХ"); ax[0].grid(alpha=.3)
ax[1].stem(b, basefmt=" ")
ax[1].set_title("impulse response"); ax[1].grid(alpha=.3)
st.pyplot(fig, clear_figure=True)

# --- 1.1.10 эксперименты ---
st.subheader("1.1.10  эксперименты на трёх сигналах")
st.markdown(
    "Три сигнала из ТЗ: чистая музыка (в полосе её почти нет), "
    "музыка с писком в полосе (тот самый шум, который надо вырезать) "
    "и белый шум (равномерный по спектру)."
)

out_f64 = {k: lfilter(b, [1.0], v) for k, v in sigs.items()}

for name, sig in sigs.items():
    st.markdown(f"**{name}**")
    fig, ax = plt.subplots(1, 2, figsize=(13, 3.5), sharey=True)
    plot_spec(ax[0], sig,         f"{name} — до")
    plot_spec(ax[1], out_f64[name], f"{name} — после")
    ax[0].set_ylabel("Hz")
    st.pyplot(fig, clear_figure=True)
    c1, c2 = st.columns(2)
    c1.caption("до"); c1.audio(wav_bytes(sig), format="audio/wav")
    c2.caption("после"); c2.audio(wav_bytes(out_f64[name]), format="audio/wav")


# ==================================================================
# 1.2 — 16-bit / Q1.15
# ==================================================================
st.header("1.2  Q1.15 fixed-point (FPGA-style)")
st.markdown(
    "Тот же фильтр, но коэффициенты квантованы в `int16` (Q1.15), "
    "а сигналы приведены к `int16` через `to_int16` — как с микрофона по I2S. "
    "Это уже репетиция того, что услышит FPGA."
)

# --- 1.2.2 АЧХ float64 vs Q1.15 ---
st.subheader("1.2.2  АЧХ до и после квантования")
fig, ax = plt.subplots(figsize=(11, 3.8))
for name, taps in (("float64", b), ("Q1.15", b_q15.astype(np.float64) / 2**15)):
    w, h = freqz(taps, worN=4096, fs=FS)
    ax.plot(w, 20*np.log10(np.abs(h)+1e-12), label=name, linewidth=1.4)
ax.axvspan(f_low, f_high, alpha=0.1, color="g")
ax.set_xlim(0, FS/2); ax.set_ylim(-100, 5)
ax.set_xlabel("Hz"); ax.set_ylabel("dB"); ax.grid(alpha=.3); ax.legend()
st.pyplot(fig, clear_figure=True)
st.caption("Q1.15 должен лечь почти точно поверх float64 — значит квантование ничего не сломало.")

# --- 1.2.3 те же эксперименты, но через Q1.15 ---
st.subheader("1.2.3  эксперименты на int16")
sigs_i16 = {k: to_int16(v) for k, v in sigs.items()}
out_q15  = {k: fir_q15(b_q15, v) for k, v in sigs_i16.items()}

# короткая количественная сверка с эталоном
rows = []
for k in sigs:
    a = out_f64[k]
    bx = from_int16(out_q15[k])
    rows.append(f"- **{k}** — corr(float64, Q1.15) = {np.corrcoef(a, bx)[0,1]:.5f}")
st.markdown("\n".join(rows))

for name in sigs:
    st.markdown(f"**{name}**")
    fig, ax = plt.subplots(1, 2, figsize=(13, 3.5), sharey=True)
    plot_spec(ax[0], sigs_i16[name], f"{name} — до (int16)")
    plot_spec(ax[1], out_q15[name],  f"{name} — после Q1.15")
    ax[0].set_ylabel("Hz")
    st.pyplot(fig, clear_figure=True)
    c1, c2 = st.columns(2)
    c1.caption("до");    c1.audio(wav_bytes(sigs_i16[name]), format="audio/wav")
    c2.caption("после"); c2.audio(wav_bytes(out_q15[name]),  format="audio/wav")


# ==================================================================
# Verilog
# ==================================================================
st.divider()
st.header("Verilog коэффициенты (Q1.15)")
st.markdown(
    "Готовый `localparam`-массив."
)

def to_hex16(v):
    return f"16'h{(v & 0xFFFF):04X}"

lines = []
for i in range(0, len(b_q15), 8):
    chunk = b_q15[i:i+8]
    s = "    " + ", ".join(to_hex16(int(v)) for v in chunk)
    if i + 8 < len(b_q15):
        s += ","
    lines.append(s)

verilog = (
    f"// FIR bandpass {int(f_low)}-{int(f_high)} Hz, fs={FS}, "
    f"N={len(b_q15)} taps, window=hamming, Q1.15\n"
    f"localparam int N_TAPS = {len(b_q15)};\n"
    f"localparam logic signed [15:0] B_TAPS [0:{len(b_q15)-1}] = '{{\n"
    + "\n".join(lines)
    + "\n};"
)
st.code(verilog, language="verilog")
