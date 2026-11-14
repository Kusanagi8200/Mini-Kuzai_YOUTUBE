#!/usr/bin/env python3
"""Consume verified Mini-Kuzai FINAL receipts and publish validated Shorts.

Safety model:
- separate from Mini-Kuzai DEV-FLOW worker
- read-only access to Mini-Kuzai repository
- requires both repositories clean and synchronized
- creates one deterministic committed V81+ brief when a verified FINAL receipt has no brief
- accepts only committed Vxx-final Short briefs
- requires matching Mini-Kuzai FINAL receipt with PUBLISHED status
- local idempotence journal outside Git
- exactly one public upload per immutable brief/media SHA256
- YouTube failure never mutates or invalidates the Mini-Kuzai scientific FINAL
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
WORK_DIR = ROOT / "work"
PIPELINE = ROOT / "tools" / "dev_flow_short_pipeline.py"
GENERATOR = ROOT / "tools" / "generate_dev_flow_short_brief.py"
PYTHON = ROOT / ".venv" / "bin" / "python"

STATE_DIR = Path("/root/.local/state/mini-kuzai-youtube")
JOURNAL_FILE = STATE_DIR / "dev-flow-short-worker.json"
LOCK_FILE = Path("/run/lock/mini-kuzai-youtube-dev-flow.lock")

STEP_RE = re.compile(r"V([0-9]+)\Z")
AUTO_BRIEF_MIN_VERSION = 81


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


def auto_brief_candidates(
    mini_root: Path,
    brief_dir: Path,
) -> list[str]:
    receipt_dir = (
        mini_root
        / "automation"
        / "dev-flow"
        / "receipts"
    )

    if receipt_dir.is_symlink() or not receipt_dir.is_dir():
        fail("FINAL receipt directory missing or unsafe")

    if brief_dir.is_symlink() or not brief_dir.is_dir():
        fail("Short brief directory missing or unsafe")

    found: list[tuple[int, str]] = []

    for path in receipt_dir.glob("V*-final.json"):
        match = re.fullmatch(r"V([0-9]+)-final\.json", path.name)

        if match is None:
            continue

        version = int(match.group(1))
        if version < AUTO_BRIEF_MIN_VERSION:
            continue

        step = f"V{version}"
        target = brief_dir / f"{step}-final.json"

        if target.exists() or target.is_symlink():
            continue

        found.append((version, step))

    return [
        step
        for _, step in sorted(found, key=lambda item: item[0])
    ]


def verify_python_runtime(python: Path) -> None:
    if not python.is_file() or not os.access(python, os.X_OK):
        fail("Project Python unavailable")


def generate_and_commit_brief(
    step: str,
    *,
    mini_root: Path,
    brief_dir: Path,
    generator: Path,
    python: Path,
) -> dict[str, str]:
    match = STEP_RE.fullmatch(step)
    if match is None or int(match.group(1)) < AUTO_BRIEF_MIN_VERSION:
        fail("Automatic brief generation is limited to V81+")

    if generator.is_symlink() or not generator.is_file():
        fail("Short brief generator unavailable")

    verify_python_runtime(python)

    target = brief_dir / f"{step}-final.json"
    if target.exists() or target.is_symlink():
        fail(f"Automatic Short brief already exists for {step}")

    source_head = git(ROOT, "rev-parse", "HEAD")
    remote_before = git(
        ROOT,
        "ls-remote",
        "origin",
        "refs/heads/main",
    ).split()

    if len(remote_before) != 2 or remote_before[0] != source_head:
        fail("Remote main changed before automatic brief generation")

    result = run(
        [
            str(python),
            str(generator),
            "--step",
            step,
            "--mini-kuzai-root",
            str(mini_root),
            "--output",
            str(target),
        ],
        cwd=ROOT,
        timeout=180,
    )

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise WorkerError(
            "Automatic Short brief generation failed"
            + (f": {detail}" if detail else "")
        )

    values = parse_results(result.stdout)

    if values.get("BRIEF_GENERATOR") != "PASS":
        fail("Automatic brief generator did not report PASS")
    if values.get("STEP") != step:
        fail("Automatic brief generator returned wrong step")
    if values.get("PUBLICATION_PERFORMED") != "0":
        fail("Automatic brief generator performed an external publication")

    try:
        relative = target.relative_to(ROOT).as_posix()
    except ValueError as exc:
        if target.exists():
            target.unlink()
        raise WorkerError("Generated brief is outside repository") from exc

    status = git(
        ROOT,
        "status",
        "--porcelain",
        "--untracked-files=all",
    ).splitlines()
    expected = f"?? {relative}"

    if status != [expected]:
        if target.exists():
            target.unlink()
        fail("Unexpected worktree changes after automatic brief generation")

    remote_now = git(
        ROOT,
        "ls-remote",
        "origin",
        "refs/heads/main",
    ).split()

    if len(remote_now) != 2 or remote_now[0] != source_head:
        target.unlink()
        fail("Remote main changed during automatic brief generation")

    git(ROOT, "add", "--", relative)

    staged = git(
        ROOT,
        "diff",
        "--cached",
        "--name-only",
    ).splitlines()
    if staged != [relative]:
        run(["git", "reset"], cwd=ROOT, timeout=60)
        if target.exists():
            target.unlink()
        fail("Unexpected staged paths for automatic brief")

    git(
        ROOT,
        "commit",
        "-m",
        f"media-flow: generate {step} FINAL brief",
    )
    commit = git(ROOT, "rev-parse", "HEAD")

    pushed = run(
        ["git", "push", "origin", "HEAD:main"],
        cwd=ROOT,
        timeout=90,
    )

    if pushed.returncode != 0:
        run(
            ["git", "reset", "--hard", source_head],
            cwd=ROOT,
            timeout=60,
        )
        run(
            ["git", "fetch", "--no-tags", "origin", "main"],
            cwd=ROOT,
            timeout=90,
        )
        fail("Automatic brief push failed")

    remote_after = git(
        ROOT,
        "ls-remote",
        "origin",
        "refs/heads/main",
    ).split()

    if len(remote_after) != 2 or remote_after[0] != commit:
        fail("Automatic brief remote verification failed")

    if git(ROOT, "status", "--porcelain"):
        fail("Worktree not clean after automatic brief commit")

    return {
        "step": step,
        "brief": relative,
        "commit": commit,
    }


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

        if previous.get("status") in {"DRY_RUN_VERIFIED", "PUBLIC_PUBLISHED"}:
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

    if values.get("UPLOAD_PERFORMED") != "1":
        fail("Worker expected exactly one YouTube upload")

    if values.get("UPLOAD_PRIVACY") != "public":
        fail("Worker expected public YouTube visibility")

    if values.get("PUBLICATION") != "PUBLIC":
        fail("Worker public publication invariant failed")

    youtube_video_id = values.get("YOUTUBE_VIDEO_ID", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,32}", youtube_video_id):
        fail("Pipeline returned invalid YouTube video ID")

    video_sha256 = values.get("VIDEO_SHA256", "")

    if not re.fullmatch(r"[a-f0-9]{64}", video_sha256):
        fail("Pipeline returned invalid video SHA256")

    final_video_value = values.get("FINAL_VIDEO", "")
    if not final_video_value:
        fail("Pipeline returned no FINAL_VIDEO path")

    final_video = Path(final_video_value).resolve()
    work_root = WORK_DIR.resolve()

    if final_video.is_symlink() or not final_video.is_file():
        fail("Pipeline FINAL_VIDEO is missing or unsafe")

    if final_video.suffix.lower() != ".mp4":
        fail("Pipeline FINAL_VIDEO is not an MP4")

    try:
        final_video.relative_to(work_root)
    except ValueError as exc:
        raise WorkerError("Pipeline FINAL_VIDEO is outside work directory") from exc

    final_video_sha256 = sha256_file(final_video)
    if final_video_sha256 != video_sha256:
        fail("Pipeline FINAL_VIDEO SHA256 does not match publication SHA256")

    final_video_relative = final_video.relative_to(ROOT).as_posix()

    journal["steps"][step] = {
        "status": "PUBLIC_PUBLISHED",
        "brief_path": relative,
        "brief_sha256": digest,
        "video_sha256": video_sha256,
        "final_video_path": final_video_relative,
        "youtube_video_id": youtube_video_id,
        "privacy_status": "public",
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    save_journal(journal_path, journal)

    return {
        "step": step,
        "state": "PUBLIC_PUBLISHED",
        "processed": "1",
        "video_sha256": video_sha256,
        "final_video_path": final_video_relative,
        "youtube_video_id": youtube_video_id,
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
        "--generator",
        type=Path,
        default=GENERATOR,
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
        print("WORKER_MODE=PUBLIC_UPLOAD")
        print("PUBLICATION=PUBLIC")

        if not args.skip_repo_checks:
            youtube_head = verify_repo(ROOT)
            mini_head = verify_repo(args.mini_kuzai_root)

            print(f"YOUTUBE_HEAD={youtube_head}")
            print(f"MINI_KUZAI_HEAD={mini_head}")

        if not args.skip_repo_checks and not args.allow_uncommitted_briefs:
            auto_steps = auto_brief_candidates(
                args.mini_kuzai_root,
                args.brief_dir,
            )
            print(f"AUTO_BRIEF_CANDIDATES={len(auto_steps)}")

            if auto_steps:
                generated = generate_and_commit_brief(
                    auto_steps[0],
                    mini_root=args.mini_kuzai_root,
                    brief_dir=args.brief_dir,
                    generator=args.generator,
                    python=args.python,
                )
                print("AUTO_BRIEF_GENERATED=1")
                print(f"AUTO_BRIEF_STEP={generated['step']}")
                print(f"AUTO_BRIEF_PATH={generated['brief']}")
                print(f"AUTO_BRIEF_COMMIT={generated['commit']}")
                print("PROCESSED=0")
                print("WORKER=BRIEF_GENERATED")
                return 0
        else:
            print("AUTO_BRIEF_CANDIDATES=0")

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
        if "youtube_video_id" in result:
            print(f"YOUTUBE_VIDEO_ID={result['youtube_video_id']}")
        if "final_video_path" in result:
            print(f"FINAL_VIDEO_PATH={result['final_video_path']}")

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
