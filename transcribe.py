"""Transcribe all .ogg voice notes in the current directory using faster-whisper.

Writes per-file transcripts to transcripts/<name>.txt and a combined file
transcripts/_combined.md ordered by filename.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from faster_whisper import WhisperModel


def main() -> int:
    root = Path(__file__).parent
    out_dir = root / "transcripts"
    out_dir.mkdir(exist_ok=True)

    files = sorted(p for p in root.iterdir() if p.suffix.lower() == ".ogg")
    if not files:
        print("No .ogg files found", file=sys.stderr)
        return 1

    print(f"Loading Whisper model (small, CPU int8)...", flush=True)
    model = WhisperModel("small", device="cpu", compute_type="int8")

    combined_path = out_dir / "_combined.md"
    combined_lines: list[str] = ["# Combined voice transcripts\n"]

    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f.name} ...", flush=True)
        segments, info = model.transcribe(
            str(f),
            language="ru",
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        text_parts: list[str] = []
        for seg in segments:
            text_parts.append(seg.text.strip())
        full = " ".join(p for p in text_parts if p).strip()

        per_path = out_dir / f"{f.stem}.txt"
        per_path.write_text(full + "\n", encoding="utf-8")

        combined_lines.append(f"\n## {f.name}\n\n{full}\n")
        print(f"   duration={info.duration:.1f}s lang={info.language} chars={len(full)}", flush=True)

    combined_path.write_text("".join(combined_lines), encoding="utf-8")
    print(f"\nDone. Combined transcript: {combined_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
