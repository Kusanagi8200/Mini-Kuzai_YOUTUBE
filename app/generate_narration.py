#!/usr/bin/env python3
"""Generate deterministic Piper narration for Mini-Kuzai YouTube videos."""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
import wave
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPER = Path("/opt/kuzai-tts/piper/venv/bin/piper")
MODEL = Path("/opt/kuzai-tts/piper/models/en_US-lessac-high.onnx")
DEFAULT_TEXT = ROOT / "config" / "video001-intro-narration.txt"

FADE_MS = 12
INTER_SENTENCE_SILENCE_MS = 180


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.strip())
    sentences = [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+", normalized)
        if item.strip()
    ]
    if not sentences:
        raise RuntimeError("No narration sentences found")
    return sentences


def synthesize_sentence(text: str, output: Path) -> None:
    result = subprocess.run(
        [
            str(PIPER),
            "--model", str(MODEL),
            "--output_file", str(output),
            "--length_scale", "1.0",
            "--noise_scale", "0.667",
            "--noise_w", "0.8",
            "--sentence_silence", "0.0",
        ],
        input=text + chr(10),
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())

    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"Piper did not produce a valid chunk: {output}")


def apply_fades(samples: array, sample_rate: int) -> None:
    fade_samples = min(
        len(samples) // 2,
        max(1, round(sample_rate * FADE_MS / 1000)),
    )

    for index in range(fade_samples):
        gain = index / fade_samples
        samples[index] = round(samples[index] * gain)

    for index in range(fade_samples):
        gain = (fade_samples - index - 1) / fade_samples
        sample_index = len(samples) - fade_samples + index
        samples[sample_index] = round(samples[sample_index] * gain)


def concatenate_chunks(chunks: list[Path], output: Path) -> tuple[int, int]:
    reference_params: tuple[int, int, int] | None = None
    combined = array("h")
    sample_rate = 0

    for chunk_index, chunk in enumerate(chunks):
        with wave.open(str(chunk), "rb") as wav:
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()

            if channels != 1 or sample_width != 2:
                raise RuntimeError(
                    f"Unexpected Piper WAV format in {chunk}: "
                    f"channels={channels}, sample_width={sample_width}"
                )

            params = (channels, sample_width, sample_rate)
            if reference_params is None:
                reference_params = params
            elif params != reference_params:
                raise RuntimeError(
                    f"Inconsistent Piper chunk format: {params} != {reference_params}"
                )

            samples = array("h")
            samples.frombytes(wav.readframes(wav.getnframes()))
            apply_fades(samples, sample_rate)
            combined.extend(samples)

        if chunk_index < len(chunks) - 1:
            silence_samples = round(
                sample_rate * INTER_SENTENCE_SILENCE_MS / 1000
            )
            combined.extend(array("h", [0]) * silence_samples)

    if reference_params is None:
        raise RuntimeError("No Piper chunks were generated")

    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(reference_params[0])
        wav.setsampwidth(reference_params[1])
        wav.setframerate(reference_params[2])
        wav.writeframes(combined.tobytes())

    return len(combined), sample_rate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", type=Path, default=DEFAULT_TEXT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--keep-chunks", action="store_true")
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

    sentences = split_sentences(text)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    work_root = ROOT / "work"
    work_root.mkdir(parents=True, exist_ok=True)

    if args.keep_chunks:
        chunk_dir = work_root / "narration-chunks"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        cleanup = False
    else:
        temp = tempfile.TemporaryDirectory(prefix="narration-", dir=work_root)
        chunk_dir = Path(temp.name)
        cleanup = True

    try:
        chunks: list[Path] = []

        for index, sentence in enumerate(sentences, start=1):
            chunk = chunk_dir / f"sentence-{index:02d}.wav"
            synthesize_sentence(sentence, chunk)
            chunks.append(chunk)

        total_samples, sample_rate = concatenate_chunks(chunks, args.output)
    finally:
        if cleanup:
            temp.cleanup()

    duration_seconds = total_samples / sample_rate

    print(f"OUTPUT={args.output}")
    print(f"TEXT_CHARS={len(text)}")
    print(f"SENTENCE_COUNT={len(sentences)}")
    print(f"FADE_MS={FADE_MS}")
    print(f"INTER_SENTENCE_SILENCE_MS={INTER_SENTENCE_SILENCE_MS}")
    print(f"DURATION_SECONDS={duration_seconds:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
