#!/usr/bin/env python3
"""Validate STEP-04 Piper narration output."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"
MAX_DURATION_MS = 55000


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path)
    args = parser.parse_args()

    if not args.audio.is_file():
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print("AUDIO_PRESENT=0")
        return 1

    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries",
            "format=duration,bit_rate,format_name:stream=codec_name,codec_type,sample_rate,channels,channel_layout",
            "-of", "json",
            str(args.audio),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print("AUDIO_PRESENT=1")
        print("FFPROBE_RC=1")
        return 1

    payload = json.loads(result.stdout)
    streams = [s for s in payload.get("streams", []) if s.get("codec_type") == "audio"]
    audio = streams[0] if streams else {}
    fmt = payload.get("format", {})
    duration_ms = round(float(fmt.get("duration", 0)) * 1000)

    checks = {
        "stream": bool(streams),
        "codec": audio.get("codec_name") in {"pcm_s16le", "pcm_s24le", "pcm_s32le"},
        "duration": 1000 < duration_ms <= MAX_DURATION_MS,
        "sample_rate": int(audio.get("sample_rate", 0) or 0) > 0,
        "channels": int(audio.get("channels", 0) or 0) >= 1,
    }
    passed = all(checks.values())

    print(MARKER)
    print(f"STEP_STATUS={'PASS' if passed else 'FAIL'}")
    print("AUDIO_PRESENT=1")
    print("FFPROBE_RC=0")
    print(f"FORMAT={fmt.get('format_name', '')}")
    print(f"CODEC={audio.get('codec_name', '')}")
    print(f"SAMPLE_RATE={audio.get('sample_rate', '')}")
    print(f"CHANNELS={audio.get('channels', '')}")
    print(f"CHANNEL_LAYOUT={audio.get('channel_layout', '')}")
    print(f"DURATION_MS={duration_ms}")
    print(f"DURATION_LE_55S={int(duration_ms <= MAX_DURATION_MS)}")
    print(f"FILE_SIZE_BYTES={args.audio.stat().st_size}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
