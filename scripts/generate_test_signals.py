"""Generate the three canonical test WAV files used by the notebooks.

Usage
-----

    python scripts/generate_test_signals.py [--duration 5.0] [--fs 48000]
                                           [--beep-hz 3000] [--out data/]

Outputs (PCM_16, mono):
    data/music.wav       — synthesized "music" surrogate
    data/music_beep.wav  — music + 3 kHz beep (inside the 2.5-3.5 kHz band)
    data/white_noise.wav — uniform white noise
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from filter_anc.signals import (  # noqa: E402
    music_with_beep,
    save_wav,
    synth_music,
    white_noise,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--duration", type=float, default=5.0, help="Seconds")
    parser.add_argument("--fs", type=int, default=48_000, help="Sample rate")
    parser.add_argument("--beep-hz", type=float, default=3_000.0)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "data")
    args = parser.parse_args(argv)

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    music = synth_music(duration_s=args.duration, fs=args.fs)
    music_beep = music_with_beep(
        duration_s=args.duration, fs=args.fs, beep_hz=args.beep_hz
    )
    noise = white_noise(duration_s=args.duration, fs=args.fs)

    save_wav(out_dir / "music.wav", music, fs=args.fs)
    save_wav(out_dir / "music_beep.wav", music_beep, fs=args.fs)
    save_wav(out_dir / "white_noise.wav", noise, fs=args.fs)

    print(f"Wrote 3 WAV files to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
