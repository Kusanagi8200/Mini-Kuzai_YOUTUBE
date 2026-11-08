#!/usr/bin/env python3
"""Verify FFmpeg/ffprobe availability for Mini-Kuzai YouTube STEP-02."""

from __future__ import annotations

import re
import shutil
import subprocess

MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"
SAFE_RE = re.compile(r"[^A-Za-z0-9 ._:/@+%(),\[\]=#-]")


def safe(value: object, limit: int = 220) -> str:
    text = str(value).replace("\n", " ").replace("\r", " ").strip()
    text = SAFE_RE.sub("_", text)
    text = re.sub(r"\s+", " ", text)
    return text[:limit]


def first_line(args: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""
    output = result.stdout.strip() or result.stderr.strip()
    return result.returncode, output.splitlines()[0].strip() if output else ""


def main() -> int:
    ffmpeg = shutil.which("ffmpeg") or ""
    ffprobe = shutil.which("ffprobe") or ""
    ffmpeg_rc, ffmpeg_line = first_line(["ffmpeg", "-version"]) if ffmpeg else (127, "")
    ffprobe_rc, ffprobe_line = first_line(["ffprobe", "-version"]) if ffprobe else (127, "")

    passed = bool(ffmpeg and ffprobe and ffmpeg_rc == 0 and ffprobe_rc == 0)

    values = {
        "STEP_STATUS": "PASS" if passed else "FAIL",
        "FFMPEG_PRESENT": int(bool(ffmpeg)),
        "FFMPEG_PATH": ffmpeg,
        "FFMPEG_VERSION_LINE": ffmpeg_line,
        "FFMPEG_RC": ffmpeg_rc,
        "FFPROBE_PRESENT": int(bool(ffprobe)),
        "FFPROBE_PATH": ffprobe,
        "FFPROBE_VERSION_LINE": ffprobe_line,
        "FFPROBE_RC": ffprobe_rc,
    }

    print(MARKER)
    for key, value in values.items():
        print(f"{key}={safe(value)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
