#!/usr/bin/env python3
"""Generate deterministic Piper narration for Mini-Kuzai YouTube videos."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPER = Path("/opt/kuzai-tts/piper/venv/bin/piper")
MODEL = Path("/opt/kuzai-tts/piper/models/en_US-lessac-high.onnx")
DEFAULT_TEXT = ROOT / "config" / "video001-intro-narration.txt"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", type=Path, default=DEFAULT_TEXT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not PIPER.is_file():
        raise RuntimeError(f"Piper not found: {PIPER}")
    if not MODEL.is_file():
        raise RuntimeError(f"Piper model not found: {MODEL}")
    if not args.text_file.is_file():
        raise RuntimeError(f"Narration text not found: {args.text_file}")

    text = args.text_file.read_text(encoding="utf-8").strip()
    if not text:
        raise RuntimeError("Narration text is empty")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            str(PIPER),
            "--model", str(MODEL),
            "--output_file", str(args.output),
            "--length_scale", "1.0",
            "--noise_scale", "0.667",
            "--noise_w", "0.8",
            "--sentence_silence", "0.25",
        ],
        input=text + "
",
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())

    if not args.output.is_file() or args.output.stat().st_size == 0:
        raise RuntimeError("Piper did not produce a valid output file")

    print(f"OUTPUT={args.output}")
    print(f"TEXT_CHARS={len(text)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
