#!/usr/bin/env python3
"""Read-only probe of the installed Piper runtime for STEP-04."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"
PIPER = Path("/opt/kuzai-tts/piper/venv/bin/piper")
MODEL = Path("/opt/kuzai-tts/piper/models/en_US-lessac-high.onnx")
MODEL_JSON = Path(str(MODEL) + ".json")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    piper_present = PIPER.is_file()
    model_present = MODEL.is_file()
    config_present = MODEL_JSON.is_file()

    help_rc = 127
    help_text = ""
    if piper_present:
        result = subprocess.run(
            [str(PIPER), "--help"],
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        help_rc = result.returncode
        help_text = (result.stdout or "") + "\n" + (result.stderr or "")

    flags = {
        "FLAG_MODEL": "--model",
        "FLAG_OUTPUT_FILE": "--output_file",
        "FLAG_OUTPUT_RAW": "--output_raw",
        "FLAG_SPEAKER": "--speaker",
        "FLAG_LENGTH_SCALE": "--length_scale",
        "FLAG_NOISE_SCALE": "--noise_scale",
        "FLAG_NOISE_W": "--noise_w",
        "FLAG_SENTENCE_SILENCE": "--sentence_silence",
    }

    passed = piper_present and model_present and help_rc == 0

    print(MARKER)
    print(f"STEP_STATUS={'PASS' if passed else 'FAIL'}")
    print(f"PIPER_PRESENT={int(piper_present)}")
    print(f"MODEL_PRESENT={int(model_present)}")
    print(f"MODEL_CONFIG_PRESENT={int(config_present)}")
    print(f"PIPER_HELP_RC={help_rc}")
    if piper_present:
        print(f"PIPER_SHA256={sha256(PIPER)}")
    if model_present:
        print(f"MODEL_SHA256={sha256(MODEL)}")
    if config_present:
        print(f"MODEL_CONFIG_SHA256={sha256(MODEL_JSON)}")
    for key, flag in flags.items():
        print(f"{key}={int(flag in help_text)}")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
