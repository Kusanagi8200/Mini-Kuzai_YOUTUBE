#!/usr/bin/env python3
"""Mix Piper narration with the canonical background track and mux final media."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUSIC = ROOT / "assets" / "music" / "kuzai-dark-cyberpunk-background-60s.wav"
TARGET_DURATION = 60.0


def run(args: list[str]) -> None:
    result = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--narration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found")
    if not args.video.is_file():
        raise RuntimeError(f"Video not found: {args.video}")
    if not args.narration.is_file():
        raise RuntimeError(f"Narration not found: {args.narration}")
    if not MUSIC.is_file():
        raise RuntimeError(f"Music not found: {MUSIC}")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    filter_complex = (
        "[1:a]aresample=48000,"
        "aformat=sample_fmts=fltp:channel_layouts=stereo,"
        "volume=1.0,"
        "apad=pad_dur=60,"
        "atrim=0:60[narr];"
        "[2:a]aresample=48000,"
        "aformat=sample_fmts=fltp:channel_layouts=stereo,"
        "volume=0.10,"
        "afade=t=in:st=0:d=1.5,"
        "afade=t=out:st=56:d=4,"
        "atrim=0:60[music];"
        "[music][narr]amix=inputs=2:duration=longest:dropout_transition=0,"
        "alimiter=limit=0.95,"
        "atrim=0:60[aout]"
    )

    run([
        ffmpeg, "-y",
        "-i", str(args.video),
        "-i", str(args.narration),
        "-i", str(MUSIC),
        "-filter_complex", filter_complex,
        "-map", "0:v:0",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-ac", "2",
        "-t", f"{TARGET_DURATION:.3f}",
        "-movflags", "+faststart",
        str(args.output),
    ])

    print(f"OUTPUT={args.output}")
    print("MUSIC_VOLUME=0.10")
    print("NARRATION_VOLUME=1.0")
    print("TARGET_DURATION_SECONDS=60")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
