#!/usr/bin/env python3
"""Verify the canonical Mini-Kuzai YouTube background music asset."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"
ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / "assets" / "music" / "kuzai-dark-cyberpunk-background-60s.wav"
EXPECTED_GIT_BLOB = "a756651fdae861cda8aeb247a7f81cbf84fa697f"
TARGET_DURATION_MS = 60000
DURATION_TOLERANCE_MS = 50


def run(args: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return result.returncode, result.stdout.strip()


def git_blob(path: Path) -> str:
    rc, out = run(["git", "hash-object", str(path)])
    return out if rc == 0 else ""


def main() -> int:
    if not ASSET.is_file():
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print("ASSET_PRESENT=0")
        return 1

    data = ASSET.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    blob = git_blob(ASSET)

    rc, out = run([
        "ffprobe", "-v", "error",
        "-show_entries",
        "format=duration,bit_rate,format_name:stream=codec_name,codec_type,sample_rate,channels,channel_layout,bits_per_sample",
        "-of", "json",
        str(ASSET),
    ])
    if rc != 0:
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print("ASSET_PRESENT=1")
        print("FFPROBE_RC=1")
        return 1

    payload = json.loads(out)
    fmt = payload.get("format", {})
    streams = [s for s in payload.get("streams", []) if s.get("codec_type") == "audio"]
    audio = streams[0] if streams else {}

    duration = float(fmt.get("duration", "0") or 0)
    duration_ms = round(duration * 1000)
    duration_delta_ms = abs(duration_ms - TARGET_DURATION_MS)
    duration_valid = duration_delta_ms <= DURATION_TOLERANCE_MS
    blob_valid = blob == EXPECTED_GIT_BLOB
    passed = bool(audio and blob_valid and duration_valid)

    values = {
        "STEP_STATUS": "PASS" if passed else "FAIL",
        "ASSET_PRESENT": 1,
        "FFPROBE_RC": 0,
        "FORMAT": fmt.get("format_name", ""),
        "CODEC": audio.get("codec_name", ""),
        "SAMPLE_RATE": audio.get("sample_rate", ""),
        "CHANNELS": audio.get("channels", ""),
        "CHANNEL_LAYOUT": audio.get("channel_layout", ""),
        "BITS_PER_SAMPLE": audio.get("bits_per_sample", ""),
        "BIT_RATE": fmt.get("bit_rate", ""),
        "DURATION_MS": duration_ms,
        "DURATION_DELTA_MS": duration_delta_ms,
        "DURATION_60S_VALID": int(duration_valid),
        "FILE_SIZE_BYTES": len(data),
        "SHA256": sha256,
        "GIT_BLOB": blob,
        "GIT_BLOB_MATCH": int(blob_valid),
    }

    print(MARKER)
    for key, value in values.items():
        print(f"{key}={value}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
