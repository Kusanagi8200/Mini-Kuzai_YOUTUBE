#!/usr/bin/env python3
"""Validate V2 final media and mix timing metadata."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"
TARGET_DURATION_MS = 60000
VOICE_START_MS = 10000
VOICE_END_MS = 50000
VOICE_WINDOW_MS = 40000
MUSIC_VOLUME = 0.20
TOLERANCE_MS = 100


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("media", type=Path)
    parser.add_argument("--mix-metadata", type=Path, required=True)
    args = parser.parse_args()

    if not args.media.is_file() or not args.mix_metadata.is_file():
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print(f"MEDIA_PRESENT={int(args.media.is_file())}")
        print(f"MIX_METADATA_PRESENT={int(args.mix_metadata.is_file())}")
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
        print("FFPROBE_RC=1")
        return 1

    payload = json.loads(result.stdout)
    metadata = json.loads(args.mix_metadata.read_text(encoding="utf-8"))

    streams = payload.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    video = video_streams[0] if video_streams else {}
    audio = audio_streams[0] if audio_streams else {}

    duration_ms = round(float(payload.get("format", {}).get("duration", 0)) * 1000)
    delta_ms = abs(duration_ms - TARGET_DURATION_MS)
    speed_factor = float(metadata.get("narration_speed_factor", 0))

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
        "voice_start": metadata.get("voice_start_ms") == VOICE_START_MS,
        "voice_end": metadata.get("voice_end_ms") == VOICE_END_MS,
        "voice_window": metadata.get("voice_window_ms") == VOICE_WINDOW_MS,
        "music_volume": abs(float(metadata.get("music_volume", 0)) - MUSIC_VOLUME) < 0.0001,
        "speed_factor": 0.90 <= speed_factor <= 1.10,
    }
    passed = all(checks.values())

    print(MARKER)
    print(f"STEP_STATUS={'PASS' if passed else 'FAIL'}")
    print("MEDIA_PRESENT=1")
    print("MIX_METADATA_PRESENT=1")
    print("FFPROBE_RC=0")
    print(f"VIDEO_CODEC={video.get('codec_name', '')}")
    print(f"WIDTH={video.get('width', '')}")
    print(f"HEIGHT={video.get('height', '')}")
    print(f"PIX_FMT={video.get('pix_fmt', '')}")
    print(f"AUDIO_CODEC={audio.get('codec_name', '')}")
    print(f"AUDIO_SAMPLE_RATE={audio.get('sample_rate', '')}")
    print(f"AUDIO_CHANNELS={audio.get('channels', '')}")
    print(f"DURATION_MS={duration_ms}")
    print(f"DURATION_DELTA_MS={delta_ms}")
    print(f"VOICE_START_MS={metadata.get('voice_start_ms', '')}")
    print(f"VOICE_END_MS={metadata.get('voice_end_ms', '')}")
    print(f"VOICE_WINDOW_MS={metadata.get('voice_window_ms', '')}")
    print(f"NARRATION_SOURCE_DURATION_MS={metadata.get('narration_source_duration_ms', '')}")
    print(f"NARRATION_SPEED_FACTOR={metadata.get('narration_speed_factor', '')}")
    print(f"MUSIC_VOLUME_PERCENT={round(float(metadata.get('music_volume', 0)) * 100)}")
    print(f"FILE_SIZE_BYTES={args.media.stat().st_size}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
