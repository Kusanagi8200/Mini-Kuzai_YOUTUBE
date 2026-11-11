#!/usr/bin/env python3
"""Mix Piper narration with background music and mux final 60-second media."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUSIC = ROOT / "assets" / "music" / "kuzai-dark-cyberpunk-background-60s.wav"

TARGET_DURATION = 60.0
VOICE_START = 5.0
VOICE_END = 55.0
VOICE_WINDOW = VOICE_END - VOICE_START
MUSIC_VOLUME = 0.20
MIN_SPEED_FACTOR = 0.90
MAX_SPEED_FACTOR = 1.10


def run(args: list[str]) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def duration_seconds(path: Path) -> float:
    output = run([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    return float(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--narration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path)
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

    narration_duration = duration_seconds(args.narration)
    speed_factor = narration_duration / VOICE_WINDOW

    if not MIN_SPEED_FACTOR <= speed_factor <= MAX_SPEED_FACTOR:
        raise RuntimeError(
            "Narration duration is outside the allowed automatic timing range: "
            f"{narration_duration:.3f}s requires atempo={speed_factor:.6f}. "
            f"Allowed range is {MIN_SPEED_FACTOR:.2f} to {MAX_SPEED_FACTOR:.2f}."
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)

    delay_ms = int(round(VOICE_START * 1000))
    filter_complex = (
        "[1:a]aresample=48000,"
        "aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"atempo={speed_factor:.8f},"
        "volume=1.0,"
        f"apad=pad_dur={VOICE_WINDOW:.3f},"
        f"atrim=0:{VOICE_WINDOW:.3f},"
        f"adelay={delay_ms}|{delay_ms}[narr];"
        "[2:a]aresample=48000,"
        "aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"volume={MUSIC_VOLUME:.2f},"
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

    metadata = {
        "schema_version": 1,
        "target_duration_ms": int(TARGET_DURATION * 1000),
        "voice_start_ms": int(VOICE_START * 1000),
        "voice_end_ms": int(VOICE_END * 1000),
        "voice_window_ms": int(VOICE_WINDOW * 1000),
        "narration_source_duration_ms": round(narration_duration * 1000),
        "narration_speed_factor": round(speed_factor, 8),
        "music_volume": MUSIC_VOLUME,
        "narration_volume": 1.0,
    }

    if args.metadata:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(json.dumps(metadata, indent=2) + chr(10), encoding="utf-8")

    print(f"OUTPUT={args.output}")
    print(f"MUSIC_VOLUME={MUSIC_VOLUME:.2f}")
    print("NARRATION_VOLUME=1.00")
    print(f"VOICE_START_SECONDS={VOICE_START:.3f}")
    print(f"VOICE_END_SECONDS={VOICE_END:.3f}")
    print(f"NARRATION_SOURCE_DURATION_SECONDS={narration_duration:.3f}")
    print(f"NARRATION_SPEED_FACTOR={speed_factor:.8f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
