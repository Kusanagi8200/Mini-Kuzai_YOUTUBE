#!/usr/bin/env python3
"""Validate the STEP-03 renderer output with ffprobe."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"
TARGET_DURATION_MS = 60000
DURATION_TOLERANCE_MS = 100


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    args = parser.parse_args()

    if not args.video.is_file():
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print("VIDEO_PRESENT=0")
        return 1

    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries",
            "format=duration:stream=codec_name,codec_type,width,height,pix_fmt,avg_frame_rate",
            "-of", "json",
            str(args.video),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print("VIDEO_PRESENT=1")
        print("FFPROBE_RC=1")
        return 1

    payload = json.loads(result.stdout)
    streams = payload.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    video = video_streams[0] if video_streams else {}
    duration_ms = round(float(payload.get("format", {}).get("duration", 0)) * 1000)
    duration_delta = abs(duration_ms - TARGET_DURATION_MS)

    checks = {
        "codec": video.get("codec_name") == "h264",
        "width": video.get("width") == 1080,
        "height": video.get("height") == 1920,
        "pix_fmt": video.get("pix_fmt") == "yuv420p",
        "duration": duration_delta <= DURATION_TOLERANCE_MS,
        "audio": len(audio_streams) == 0,
    }
    passed = bool(video_streams) and all(checks.values())

    print(MARKER)
    print(f"STEP_STATUS={'PASS' if passed else 'FAIL'}")
    print("VIDEO_PRESENT=1")
    print("FFPROBE_RC=0")
    print(f"CODEC={video.get('codec_name', '')}")
    print(f"WIDTH={video.get('width', '')}")
    print(f"HEIGHT={video.get('height', '')}")
    print(f"PIX_FMT={video.get('pix_fmt', '')}")
    print(f"AVG_FRAME_RATE={video.get('avg_frame_rate', '')}")
    print(f"DURATION_MS={duration_ms}")
    print(f"DURATION_DELTA_MS={duration_delta}")
    print(f"AUDIO_STREAMS={len(audio_streams)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
