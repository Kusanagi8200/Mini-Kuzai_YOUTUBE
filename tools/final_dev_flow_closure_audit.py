#!/usr/bin/env python3
"""Read-only end-to-end audit for one completed Mini-Kuzai FINAL media flow."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MINI_KUZAI = Path("/root/GitHub-Mini-Kuzai/Mini-Kuzai")
PYTHON = ROOT / ".venv" / "bin" / "python"
LINKEDIN = ROOT / "tools" / "linkedin_video_handoff.py"
GITHUB_MEDIA = ROOT / "tools" / "github_media_fallback.py"
DEFAULT_JOURNAL = Path(
    "/root/.local/state/mini-kuzai-youtube/dev-flow-short-worker.json"
)

STEP_RE = re.compile(r"V([0-9]+)\Z")

sys.path.insert(0, str(ROOT / "tools"))
from cross_channel_media_orchestrator import (  # noqa: E402
    local_state,
    validate_existing_receipt,
)


class ClosureAuditError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ClosureAuditError(message)


def run(
    args: list[str],
    *,
    cwd: Path = ROOT,
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ClosureAuditError(
            f"Command failed to execute: {args[0]}"
        ) from exc


def parse_results(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            values[key] = value.strip()
    return values


def load_json(path: Path, label: str) -> dict:
    if path.is_symlink() or not path.is_file():
        fail(f"{label} missing or unsafe")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ClosureAuditError(f"{label} is invalid JSON") from exc
    if not isinstance(data, dict):
        fail(f"{label} must be a JSON object")
    return data


def git(repo: Path, *args: str) -> str:
    result = run(["git", *args], cwd=repo, timeout=60)
    if result.returncode != 0:
        fail(f"Git command failed in {repo.name}")
    return result.stdout.strip()


def verify_scientific_final(step: str, media_receipt: dict) -> None:
    source = media_receipt.get("source")
    if not isinstance(source, dict):
        fail("Media receipt source metadata missing")

    relative = source.get("scientific_final_receipt")
    expected = f"automation/dev-flow/receipts/{step}-final.json"
    if relative != expected:
        fail("Scientific FINAL receipt path mismatch")

    final_path = MINI_KUZAI / relative
    final_receipt = load_json(final_path, "Scientific FINAL receipt")

    tracked = run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=MINI_KUZAI,
        timeout=60,
    )
    if tracked.returncode != 0:
        fail("Scientific FINAL receipt is not committed")

    if final_receipt.get("schema_version") != 1:
        fail("Scientific FINAL receipt schema invalid")
    if final_receipt.get("command") != "FINAL-DEV-FLOW":
        fail("Scientific FINAL command mismatch")
    if final_receipt.get("step") != step:
        fail("Scientific FINAL step mismatch")
    if final_receipt.get("status") != "PUBLISHED":
        fail("Scientific FINAL is not published")
    if final_receipt.get("source_commit") != source.get("scientific_source_commit"):
        fail("Scientific FINAL source commit mismatch")


def child(tool: Path, step: str, journal: Path) -> dict[str, str]:
    result = run(
        [
            str(PYTHON),
            str(tool),
            "--step",
            step,
            "--journal",
            str(journal),
        ],
        timeout=240,
    )
    if result.returncode != 0:
        fail(f"{tool.name} verification failed")
    return parse_results(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", required=True)
    parser.add_argument("--journal", type=Path, default=DEFAULT_JOURNAL)
    args = parser.parse_args()

    match = STEP_RE.fullmatch(args.step)
    if match is None or int(match.group(1)) < 81:
        fail("FINAL closure audit is limited to V81+")

    state = local_state(args.step, args.journal)
    media_receipt = validate_existing_receipt(args.step, state)
    if media_receipt is None:
        fail("Committed cross-channel media receipt missing")

    verify_scientific_final(args.step, media_receipt)

    linkedin = child(LINKEDIN, args.step, args.journal)
    if linkedin.get("HANDOFF_PREFLIGHT") != "PASS":
        fail("LinkedIn handoff preflight failed")
    if linkedin.get("EXISTING_PUBLICATION") != "1":
        fail("LinkedIn native video publication is not recorded")
    if linkedin.get("PUBLICATION_PERFORMED") != "0":
        fail("LinkedIn audit unexpectedly published")

    github = child(GITHUB_MEDIA, args.step, args.journal)
    if github.get("GITHUB_MEDIA_PREFLIGHT") != "PASS":
        fail("GitHub media preflight failed")
    if github.get("PUBLICATION_STATE") != "EXISTS_IDENTICAL":
        fail("GitHub media comment is not verified identical")
    if github.get("PUBLICATION_PERFORMED") != "0":
        fail("GitHub audit unexpectedly published")

    receipt_linkedin = media_receipt.get("linkedin") or {}
    receipt_github = media_receipt.get("github") or {}
    receipt_youtube = media_receipt.get("youtube") or {}

    if receipt_youtube.get("video_id") != state["youtube_video_id"]:
        fail("YouTube receipt identity mismatch")
    if github.get("MEDIA_COMMENT_URL") != receipt_github.get("comment_url"):
        fail("GitHub media comment receipt mismatch")
    if receipt_linkedin.get("status") != "PUBLISHED":
        fail("LinkedIn receipt status invalid")

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print("FINAL_FLOW=PASS")
    print(f"STEP={args.step}")
    print("SCIENTIFIC_FINAL=PASS")
    print("YOUTUBE=PASS")
    print(f"YOUTUBE_VIDEO_ID={state['youtube_video_id']}")
    print("LINKEDIN=PASS")
    print("GITHUB=PASS")
    print("MEDIA_RECEIPT=PASS")
    print(f"MEDIA_SHA256={state['video_sha256']}")
    print("PUBLICATION_PERFORMED=0")
    print("TRAINING_ALLOWED=0")
    print("BLIND_ACCESS=0")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ClosureAuditError as exc:
        print("##### SECTION RESULTS FOR ASSISTANT ######")
        print("FINAL_FLOW=BLOCKED")
        print(f"ERROR={exc}")
        raise SystemExit(1)
