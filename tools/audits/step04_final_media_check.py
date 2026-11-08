#!/usr/bin/env python3
"""Validate final STEP-04 muxed media."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"
TARGET_DURATION_MS = 60000
TOLERANCE_MS = 100


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("media", type=Path)
    args = parser.parse_args()

    if not args.media.is_file():
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print("MEDIA_PRESENT=0")
        return 1

    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries",
            "format=duration:stream=index,codec_name,codec_type,width,height,pix_fmt,sample_rate,channels",
            "-of", "json",
            str(args.media),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print("MEDIA_PRESENT=1")
        print("FFPROBE_RC=1")
        return 1

    payload = json.loads(result.stdout)
    streams = payload.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    video = video_streams[0] if video_streams else {}
    audio = audio_streams[0] if audio_streams else {}

    duration_ms = round(float(payload.get("format", {}).get("duration", 0)) * 1000)
    delta_ms = abs(duration_ms - TARGET_DURATION_MS)

    checks = {
        "video_count": len(video_streams) == 1,
        "audio_count": len(audio_streams) == 1,
        "video_codec": video.get("codec_name") == "h264",
        "width": video.get("width") == 1080,
        "height": video.get("height") == 1920,
        "pix_fmt": video.get("pix_fmt") == "yuv420p",
        "audio_codec": audio.get("codec_name") == "aac",
        "sample_rate": audio.get("sample_rate") == "48000",
        "channels": audio.get("channels") == 2,
        "duration": delta_ms <= TOLERANCE_MS,
    }
    passed = all(checks.values())

    print(MARKER)
    print(f"STEP_STATUS={'PASS' if passed else 'FAIL'}")
    print("MEDIA_PRESENT=1")
    print("FFPROBE_RC=0")
    print(f"VIDEO_STREAMS={len(video_streams)}")
    print(f"AUDIO_STREAMS={len(audio_streams)}")
    print(f"VIDEO_CODEC={video.get('codec_name', '')}")
    print(f"WIDTH={video.get('width', '')}")
    print(f"HEIGHT={video.get('height', '')}")
    print(f"PIX_FMT={video.get('pix_fmt', '')}")
    print(f"AUDIO_CODEC={audio.get('codec_name', '')}")
    print(f"AUDIO_SAMPLE_RATE={audio.get('sample_rate', '')}")
    print(f"AUDIO_CHANNELS={audio.get('channels', '')}")
    print(f"DURATION_MS={duration_ms}")
    print(f"DURATION_DELTA_MS={delta_ms}")
    print(f"FILE_SIZE_BYTES={args.media.stat().st_size}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
