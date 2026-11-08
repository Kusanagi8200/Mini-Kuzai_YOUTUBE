#!/usr/bin/env python3
"""Read-only fhc2 environment audit for Mini-Kuzai YouTube STEP-01."""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"
SAFE_RE = re.compile(r"[^A-Za-z0-9 ._:/@+%(),\[\]=#-]")


def safe(value: object, limit: int = 220) -> str:
    text = str(value).replace("\n", " ").replace("\r", " ").strip()
    text = SAFE_RE.sub("_", text)
    text = re.sub(r"\s+", " ", text)
    return text[:limit]


def cmd(args: list[str], timeout: int = 15) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""
    return result.returncode, result.stdout.strip()


def first_line(args: list[str]) -> str:
    rc, output = cmd(args)
    if rc != 0 or not output:
        return ""
    return output.splitlines()[0].strip()


def os_release() -> dict[str, str]:
    data: dict[str, str] = {}
    path = Path("/etc/os-release")
    if not path.is_file():
        return data
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"')
    return data


def find_first(paths: list[Path], names: tuple[str, ...], executable: bool = False) -> str:
    for base in paths:
        if not base.exists():
            continue
        try:
            for root, dirs, files in os.walk(base):
                rel_depth = len(Path(root).relative_to(base).parts)
                if rel_depth >= 6:
                    dirs[:] = []
                for name in files:
                    if name not in names:
                        continue
                    candidate = Path(root) / name
                    if executable and not os.access(candidate, os.X_OK):
                        continue
                    return str(candidate)
        except OSError:
            continue
    return ""


def find_voice(paths: list[Path]) -> str:
    preferred = ("en_US-lessac-high.onnx", "en_US-lessac-medium.onnx", "en_US-lessac-low.onnx")
    for name in preferred:
        found = find_first(paths, (name,))
        if found:
            return found
    for base in paths:
        if not base.exists():
            continue
        try:
            for root, dirs, files in os.walk(base):
                rel_depth = len(Path(root).relative_to(base).parts)
                if rel_depth >= 6:
                    dirs[:] = []
                for name in files:
                    if name.endswith(".onnx") and "piper" in root.lower():
                        return str(Path(root) / name)
        except OSError:
            continue
    return ""


def main() -> int:
    release = os_release()
    search_roots = [
        Path("/root/Mini-Kuzai"),
        Path("/root/GitHub-Mini-Kuzai"),
        Path("/opt"),
        Path("/usr/local"),
    ]

    python_path = shutil.which("python3") or ""
    ffmpeg_path = shutil.which("ffmpeg") or ""
    ffprobe_path = shutil.which("ffprobe") or ""
    git_path = shutil.which("git") or ""
    gh_path = shutil.which("gh") or ""
    fc_list_path = shutil.which("fc-list") or ""

    piper_path = shutil.which("piper") or find_first(search_roots, ("piper",), executable=True)
    piper_voice = find_voice(search_roots)

    root_usage = shutil.disk_usage("/")
    repo_path = Path("/root/GitHub-Mini-Kuzai/Mini-Kuzai_YOUTUBE")
    repo_usage = shutil.disk_usage(repo_path) if repo_path.exists() else root_usage

    gh_login_ok = 0
    if gh_path:
        rc, _ = cmd(["gh", "api", "user", "--jq", ".login"])
        gh_login_ok = int(rc == 0)

    font_count = 0
    if fc_list_path:
        rc, output = cmd(["fc-list"])
        if rc == 0:
            font_count = len([line for line in output.splitlines() if line.strip()])

    pillow_present = 0
    rc, _ = cmd(["python3", "-c", "import PIL"])
    pillow_present = int(rc == 0)

    values = {
        "STEP_STATUS": "PASS",
        "HOSTNAME": platform.node(),
        "OS_ID": release.get("ID", ""),
        "OS_VERSION": release.get("VERSION_ID", ""),
        "OS_PRETTY": release.get("PRETTY_NAME", ""),
        "KERNEL": platform.release(),
        "ARCH": platform.machine(),
        "PYTHON_PRESENT": int(bool(python_path)),
        "PYTHON_PATH": python_path,
        "PYTHON_VERSION": platform.python_version(),
        "PILLOW_PRESENT": pillow_present,
        "FFMPEG_PRESENT": int(bool(ffmpeg_path)),
        "FFMPEG_PATH": ffmpeg_path,
        "FFMPEG_VERSION_LINE": first_line(["ffmpeg", "-version"]) if ffmpeg_path else "",
        "FFPROBE_PRESENT": int(bool(ffprobe_path)),
        "FFPROBE_PATH": ffprobe_path,
        "FFPROBE_VERSION_LINE": first_line(["ffprobe", "-version"]) if ffprobe_path else "",
        "GIT_PRESENT": int(bool(git_path)),
        "GIT_VERSION_LINE": first_line(["git", "--version"]) if git_path else "",
        "GH_PRESENT": int(bool(gh_path)),
        "GH_LOGIN_OK": gh_login_ok,
        "PIPER_PRESENT": int(bool(piper_path)),
        "PIPER_PATH": piper_path,
        "PIPER_VOICE_PRESENT": int(bool(piper_voice)),
        "PIPER_VOICE_PATH": piper_voice,
        "FC_LIST_PRESENT": int(bool(fc_list_path)),
        "FONT_COUNT": font_count,
        "ROOT_FREE_GIB": root_usage.free // (1024 ** 3),
        "REPO_FREE_GIB": repo_usage.free // (1024 ** 3),
        "MINI_KUZAI_REPO_PRESENT": int(Path("/root/GitHub-Mini-Kuzai/Mini-Kuzai").is_dir()),
        "YOUTUBE_REPO_PRESENT": int(repo_path.is_dir()),
    }

    print(MARKER)
    for key, value in values.items():
        print(f"{key}={safe(value)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
