#!/usr/bin/env python3
"""Consume verified Mini-Kuzai FINAL receipts and run Short dry-runs.

Safety model:
- separate from Mini-Kuzai DEV-FLOW worker
- read-only access to Mini-Kuzai repository
- requires both repositories clean and synchronized
- accepts only committed Vxx-final Short briefs
- requires matching Mini-Kuzai FINAL receipt with PUBLISHED status
- local idempotence journal outside Git
- current implementation is DRY_RUN_ONLY
- never passes --execute to the YouTube uploader
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MINI_KUZAI = Path("/root/GitHub-Mini-Kuzai/Mini-Kuzai")
BRIEF_DIR = ROOT / "automation" / "dev-flow" / "short-briefs"
PIPELINE = ROOT / "tools" / "dev_flow_short_pipeline.py"
PYTHON = ROOT / ".venv" / "bin" / "python"

STATE_DIR = Path("/root/.local/state/mini-kuzai-youtube")
JOURNAL_FILE = STATE_DIR / "dev-flow-short-worker.json"
LOCK_FILE = Path("/run/lock/mini-kuzai-youtube-dev-flow.lock")

STEP_RE = re.compile(r"V([0-9]+)\Z")


class WorkerError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise WorkerError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(
    args: list[str],
    *,
    cwd: Path,
    timeout: int = 600,
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
        raise WorkerError(f"Command failed to execute: {args[0]}") from exc


def git(repo: Path, *args: str) -> str:
    result = run(["git", *args], cwd=repo, timeout=60)

    if result.returncode != 0:
        fail(f"Git command failed in {repo.name}")

    return result.stdout.strip()


def verify_repo(repo: Path) -> str:
    if not repo.is_dir() or (repo / ".git").is_dir() is False:
        fail(f"Repository unavailable: {repo}")

    if git(repo, "branch", "--show-current") != "main":
        fail(f"{repo.name} is not on main")

    if git(repo, "status", "--porcelain"):
        fail(f"{repo.name} worktree is not clean")

    fetch = run(
        ["git", "fetch", "--no-tags", "origin", "main"],
        cwd=repo,
        timeout=90,
    )

    if fetch.returncode != 0:
        fail(f"{repo.name} fetch failed")

    local = git(repo, "rev-parse", "HEAD")
    remote = git(repo, "rev-parse", "origin/main")

    if local != remote:
        fail(f"{repo.name} is not synchronized with origin/main")

    return local


def load_json(path: Path, label: str) -> dict:
    if path.is_symlink() or not path.is_file():
        fail(f"{label} missing or unsafe")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise WorkerError(f"{label} is invalid JSON") from exc

    if not isinstance(data, dict):
        fail(f"{label} must be a JSON object")

    return data


def ensure_committed_brief(path: Path) -> str:
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise WorkerError("Short brief is outside repository") from exc

    tracked = run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=ROOT,
        timeout=60,
    )

    if tracked.returncode != 0:
        fail(f"Short brief is not committed: {relative}")

    current = path.read_text(encoding="utf-8")
    committed = git(ROOT, "show", f"HEAD:{relative}")

    if current != committed and current.rstrip("\n") != committed:
        fail(f"Short brief differs from committed main: {relative}")

    return relative


def receipt_for(step: str, mini_root: Path) -> Path:
    return (
        mini_root
        / "automation"
        / "dev-flow"
        / "receipts"
        / f"{step}-final.json"
    )


def verify_receipt(step: str, mini_root: Path) -> None:
    path = receipt_for(step, mini_root)
    receipt = load_json(path, "FINAL receipt")

    if receipt.get("schema_version") != 1:
        fail("Unsupported FINAL receipt schema")

    if receipt.get("command") != "FINAL-DEV-FLOW":
        fail("Receipt is not FINAL-DEV-FLOW")

    if receipt.get("step") != step:
        fail("FINAL receipt step mismatch")

    if receipt.get("status") != "PUBLISHED":
        fail("FINAL receipt is not PUBLISHED")

    relative = path.relative_to(mini_root).as_posix()

    tracked = run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=mini_root,
        timeout=60,
    )

    if tracked.returncode != 0:
        fail("FINAL receipt is not committed")


def load_journal(path: Path) -> dict:
    if not path.exists():
        return {
            "schema_version": 1,
            "steps": {},
        }

    data = load_json(path, "Worker journal")

    if data.get("schema_version") != 1:
        fail("Unsupported worker journal schema")

    steps = data.get("steps")
    if not isinstance(steps, dict):
        fail("Invalid worker journal")

    return data


def save_journal(path: Path, journal: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)

    fd, temporary = tempfile.mkstemp(
        prefix=".dev-flow-short-worker.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )

    try:
        os.fchmod(fd, 0o600)

        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(
                journal,
                handle,
                indent=2,
                sort_keys=True,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary, path)
        os.chmod(path, 0o600)

    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def parse_results(output: str) -> dict[str, str]:
    values: dict[str, str] = {}

    for line in output.splitlines():
        if "=" not in line:
            continue

        key, value = line.split("=", 1)

        if re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            values[key] = value.strip()

    return values


def candidates(brief_dir: Path) -> list[Path]:
    if brief_dir.is_symlink() or not brief_dir.is_dir():
        fail("Short brief directory missing or unsafe")

    found: list[tuple[int, Path]] = []

    for path in brief_dir.glob("V*-final.json"):
        match = re.fullmatch(r"V([0-9]+)-final\.json", path.name)

        if match:
            found.append((int(match.group(1)), path))

    return [
        path
        for _, path in sorted(found, key=lambda item: item[0])
    ]


def inspect_candidate(
    path: Path,
    *,
    mini_root: Path,
    journal: dict,
    require_committed: bool,
) -> tuple[str, str, str]:
    brief = load_json(path, "Short brief")

    step = brief.get("step")
    match = STEP_RE.fullmatch(step or "")

    if match is None:
        fail("Invalid Short brief step")

    expected_name = f"{step}-final.json"

    if path.name != expected_name:
        fail("Short brief filename does not match step")

    if brief.get("video_id") != f"VIDEO-{step}-FINAL":
        fail("Short brief video ID does not match step")

    if require_committed:
        relative = ensure_committed_brief(path)
    else:
        relative = path.name

    verify_receipt(step, mini_root)

    digest = sha256_file(path)

    previous = journal["steps"].get(step)

    if previous is not None:
        if previous.get("brief_sha256") != digest:
            fail(f"Conflicting already-processed brief for {step}")

        if previous.get("status") == "DRY_RUN_VERIFIED":
            return step, relative, "ALREADY_VERIFIED"

        fail(f"Unexpected previous worker state for {step}")

    return step, relative, "PENDING"


def process_candidate(
    path: Path,
    *,
    mini_root: Path,
    journal_path: Path,
    pipeline: Path,
    python: Path,
    require_committed: bool = True,
) -> dict[str, str]:
    journal = load_journal(journal_path)

    step, relative, state = inspect_candidate(
        path,
        mini_root=mini_root,
        journal=journal,
        require_committed=require_committed,
    )

    if state == "ALREADY_VERIFIED":
        return {
            "step": step,
            "state": state,
            "processed": "0",
        }

    digest = sha256_file(path)

    result = run(
        [
            str(python),
            str(pipeline),
            "--brief",
            str(path.resolve()),
            "--prefix",
            f"worker-{step.lower()}",
        ],
        cwd=ROOT,
        timeout=900,
    )

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise WorkerError(
            "Short pipeline failed"
            + (f": {detail}" if detail else "")
        )

    values = parse_results(result.stdout)

    if values.get("PIPELINE_ORCHESTRATOR") != "PASS":
        fail("Pipeline orchestrator did not report PASS")

    if values.get("UPLOAD_PERFORMED") != "0":
        fail("Worker dry-run unexpectedly uploaded media")

    if values.get("PUBLICATION") != "DISABLED":
        fail("Worker publication safety invariant failed")

    video_sha256 = values.get("VIDEO_SHA256", "")

    if not re.fullmatch(r"[a-f0-9]{64}", video_sha256):
        fail("Pipeline returned invalid video SHA256")

    journal["steps"][step] = {
        "status": "DRY_RUN_VERIFIED",
        "brief_path": relative,
        "brief_sha256": digest,
        "video_sha256": video_sha256,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    save_journal(journal_path, journal)

    return {
        "step": step,
        "state": "DRY_RUN_VERIFIED",
        "processed": "1",
        "video_sha256": video_sha256,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--brief-dir",
        type=Path,
        default=BRIEF_DIR,
    )

    parser.add_argument(
        "--mini-kuzai-root",
        type=Path,
        default=MINI_KUZAI,
    )

    parser.add_argument(
        "--journal",
        type=Path,
        default=JOURNAL_FILE,
    )

    parser.add_argument(
        "--pipeline",
        type=Path,
        default=PIPELINE,
    )

    parser.add_argument(
        "--python",
        type=Path,
        default=PYTHON,
    )

    parser.add_argument(
        "--skip-repo-checks",
        action="store_true",
        help="Tests only.",
    )

    parser.add_argument(
        "--allow-uncommitted-briefs",
        action="store_true",
        help="Tests only.",
    )

    args = parser.parse_args()

    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOCK_FILE.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)

        print("##### SECTION RESULTS FOR ASSISTANT ######")
        print("WORKER_MODE=DRY_RUN_ONLY")
        print("PUBLICATION=DISABLED")

        if not args.skip_repo_checks:
            youtube_head = verify_repo(ROOT)
            mini_head = verify_repo(args.mini_kuzai_root)

            print(f"YOUTUBE_HEAD={youtube_head}")
            print(f"MINI_KUZAI_HEAD={mini_head}")

        items = candidates(args.brief_dir)
        print(f"BRIEF_CANDIDATES={len(items)}")

        journal = load_journal(args.journal)

        pending: list[Path] = []
        already = 0

        for path in items:
            _, _, state = inspect_candidate(
                path,
                mini_root=args.mini_kuzai_root,
                journal=journal,
                require_committed=not args.allow_uncommitted_briefs,
            )

            if state == "PENDING":
                pending.append(path)
            elif state == "ALREADY_VERIFIED":
                already += 1

        print(f"ALREADY_VERIFIED={already}")
        print(f"PENDING_BRIEFS={len(pending)}")

        if not pending:
            print("WORKER=IDLE")
            return 0

        # One brief per invocation keeps every transaction isolated.
        result = process_candidate(
            pending[0],
            mini_root=args.mini_kuzai_root,
            journal_path=args.journal,
            pipeline=args.pipeline,
            python=args.python,
            require_committed=not args.allow_uncommitted_briefs,
        )

        print(f"SHORT_STEP={result['step']}")
        print(f"PROCESSED={result['processed']}")
        print(f"WORKER_STATE={result['state']}")

        if "video_sha256" in result:
            print(f"VIDEO_SHA256={result['video_sha256']}")

        print("WORKER=PASS")
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkerError as exc:
        print("##### SECTION RESULTS FOR ASSISTANT ######")
        print("WORKER=BLOCKED")
        print(f"ERROR={exc}")
        raise SystemExit(1)
