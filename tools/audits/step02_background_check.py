#!/usr/bin/env python3
"""Verify the canonical Mini-Kuzai Short master background."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from PIL import Image

MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"
ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / "assets" / "backgrounds" / "mini-kuzai-short-master.png"
EXPECTED_GIT_BLOB = "6b40e546b3d0d68840c23c8f30d0faf9fba04076"
EXPECTED_WIDTH = 1080
EXPECTED_HEIGHT = 1920


def git_blob(path: Path) -> str:
    result = subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def main() -> int:
    if not ASSET.is_file():
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print("ASSET_PRESENT=0")
        return 1

    data = ASSET.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    blob = git_blob(ASSET)

    try:
        with Image.open(ASSET) as image:
            image_format = image.format or ""
            image_mode = image.mode
            width, height = image.size
            image.verify()
    except Exception:
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print("ASSET_PRESENT=1")
        print("IMAGE_VALID=0")
        return 1

    valid = (
        image_format.upper() == "PNG"
        and width == EXPECTED_WIDTH
        and height == EXPECTED_HEIGHT
        and blob == EXPECTED_GIT_BLOB
    )

    print(MARKER)
    print(f"STEP_STATUS={'PASS' if valid else 'FAIL'}")
    print("ASSET_PRESENT=1")
    print("IMAGE_VALID=1")
    print(f"IMAGE_FORMAT={image_format}")
    print(f"IMAGE_MODE={image_mode}")
    print(f"IMAGE_WIDTH={width}")
    print(f"IMAGE_HEIGHT={height}")
    print(f"FILE_SIZE_BYTES={len(data)}")
    print(f"SHA256={sha256}")
    print(f"GIT_BLOB={blob}")
    print(f"GIT_BLOB_MATCH={int(blob == EXPECTED_GIT_BLOB)}")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
