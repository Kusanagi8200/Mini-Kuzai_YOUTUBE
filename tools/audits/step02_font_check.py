#!/usr/bin/env python3
"""Select a deterministic installed font for the Mini-Kuzai Short renderer."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"
SAFE_RE = re.compile(r"[^A-Za-z0-9 ._:/@+%(),\[\]=#-]")

CANDIDATES = [
    "Ubuntu Sans:style=Bold",
    "Ubuntu:style=Bold",
    "DejaVu Sans:style=Bold",
    "Liberation Sans:style=Bold",
    "Noto Sans:style=Bold",
]


def safe(value: object, limit: int = 220) -> str:
    text = str(value).replace("\n", " ").replace("\r", " ").strip()
    text = SAFE_RE.sub("_", text)
    text = re.sub(r"\s+", " ", text)
    return text[:limit]


def fc_match(pattern: str) -> tuple[str, str, str]:
    result = subprocess.run(
        ["fc-match", "-f", "%{file}\n%{family}\n%{style}\n", pattern],
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    if result.returncode != 0:
        return "", "", ""
    lines = result.stdout.splitlines()
    if len(lines) < 3:
        return "", "", ""
    return lines[0].strip(), lines[1].strip(), lines[2].strip()


def main() -> int:
    if not shutil.which("fc-match"):
        print(MARKER)
        print("STEP_STATUS=FAIL")
        print("FC_MATCH_PRESENT=0")
        return 1

    selected_pattern = ""
    selected_path = ""
    selected_family = ""
    selected_style = ""

    for pattern in CANDIDATES:
        path, family, style = fc_match(pattern)
        if path and Path(path).is_file() and "bold" in style.lower():
            selected_pattern = pattern
            selected_path = path
            selected_family = family
            selected_style = style
            break

    passed = bool(selected_path)
    values = {
        "STEP_STATUS": "PASS" if passed else "FAIL",
        "FC_MATCH_PRESENT": 1,
        "FONT_SELECTED": int(passed),
        "FONT_PATTERN": selected_pattern,
        "FONT_PATH": selected_path,
        "FONT_FAMILY": selected_family,
        "FONT_STYLE": selected_style,
    }

    print(MARKER)
    for key, value in values.items():
        print(f"{key}={safe(value)}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
