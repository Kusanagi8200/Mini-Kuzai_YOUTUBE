#!/usr/bin/env python3
"""Orchestrate verified Mini-Kuzai FINAL media publication after YouTube.

Default mode is preflight-only.

Live mode requires:
- --publish
- KUZAI_CROSS_CHANNEL_MEDIA_ENABLED=YES

The orchestrator reuses the independently guarded LinkedIn and GitHub media
publishers. It records a committed media receipt only after all three sinks are
verified:
- YouTube public
- LinkedIn native video
- GitHub media fallback

Media publication never changes the scientific FINAL and never authorizes
training, BLIND access, checkpoint mutation, or scientific execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MINI_KUZAI = Path("/root/GitHub-Mini-Kuzai/Mini-Kuzai")
DEFAULT_JOURNAL = Path(
    "/root/.local/state/mini-kuzai-youtube/dev-flow-short-worker.json"
)
LINKEDIN = ROOT / "tools" / "linkedin_video_handoff.py"
GITHUB_MEDIA = ROOT / "tools" / "github_media_fallback.py"
PYTHON = ROOT / ".venv" / "bin" / "python"
RECEIPT_DIR = ROOT / "automation" / "publication-receipts"

STEP_RE = re.compile(r"V([0-9]+)\Z")
SHA256_RE = re.compile(r"[a-f0-9]{64}\Z")
YOUTUBE_ID_RE = re.compile(r"[A-Za-z0-9_-]{6,32}\Z")
LINKEDIN_VIDEO_URN_RE = re.compile(
    r"urn:li:video:[A-Za-z0-9_-]{5,256}\Z"
)
LINKEDIN_POST_URN_RE = re.compile(
    r"urn:li:(?:share|ugcPost):[A-Za-z0-9_-]{5,256}\Z"
)
GITHUB_URL_RE = re.compile(
    r"https://github\.com/Kusanagi8200/Mini-Kuzai/discussions/"
    r"[1-9][0-9]*(?:#discussioncomment-[1-9][0-9]*)?\Z"
)


class MediaOrchestratorError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise MediaOrchestratorError(message)


def run(
    args: list[str],
    *,
    cwd: Path = ROOT,
    timeout: int = 180,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaOrchestratorError(
            f"Command failed to execute: {args[0]}"
        ) from exc


def git(*args: str) -> str:
    result = run(["git", *args], timeout=60)
    if result.returncode != 0:
        fail("Git command failed")
    return result.stdout.strip()


def verify_repo() -> str:
    if git("branch", "--show-current") != "main":
        fail("Media orchestrator requires main branch")
    if git("status", "--porcelain"):
        fail("Media orchestrator requires a clean worktree")

    fetched = run(
        ["git", "fetch", "--no-tags", "origin", "main"],
        timeout=90,
    )
    if fetched.returncode != 0:
        fail("Git fetch failed")

    local = git("rev-parse", "HEAD")
    remote = git("rev-parse", "origin/main")
    if local != remote:
        fail("Local main differs from origin/main")
    return local


def load_json(path: Path, label: str) -> dict:
    if path.is_symlink() or not path.is_file():
        fail(f"{label} missing or unsafe")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise MediaOrchestratorError(
            f"{label} is invalid JSON"
        ) from exc
    if not isinstance(data, dict):
        fail(f"{label} must be a JSON object")
    return data


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_results(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            values[key] = value.strip()
    return values


def local_state(step: str, journal_path: Path) -> dict[str, str]:
    journal = load_json(journal_path, "YouTube worker journal")
    if journal.get("schema_version") != 1:
        fail("Unsupported YouTube worker journal schema")

    steps = journal.get("steps")
    if not isinstance(steps, dict):
        fail("YouTube worker journal steps missing")

    row = steps.get(step)
    if not isinstance(row, dict):
        fail(f"No YouTube worker record for {step}")
    if row.get("status") != "PUBLIC_PUBLISHED":
        fail("YouTube state is not PUBLIC_PUBLISHED")

    video_sha = row.get("video_sha256", "")
    youtube_id = row.get("youtube_video_id", "")
    brief_path = row.get("brief_path", "")
    brief_sha = row.get("brief_sha256", "")

    if not SHA256_RE.fullmatch(video_sha):
        fail("Invalid worker media SHA256")
    if not YOUTUBE_ID_RE.fullmatch(youtube_id):
        fail("Invalid worker YouTube video ID")
    if not SHA256_RE.fullmatch(brief_sha):
        fail("Invalid worker brief SHA256")
    if (
        not isinstance(brief_path, str)
        or brief_path != f"automation/dev-flow/short-briefs/{step}-final.json"
    ):
        fail("Unexpected worker brief path")

    brief = ROOT / brief_path
    if brief.is_symlink() or not brief.is_file():
        fail("Committed Short brief missing or unsafe")
    if sha256_file(brief) != brief_sha:
        fail("Short brief SHA256 differs from worker journal")

    tracked = run(
        ["git", "ls-files", "--error-unmatch", "--", brief_path],
        timeout=60,
    )
    if tracked.returncode != 0:
        fail("Short brief is not committed")

    brief_data = load_json(brief, "FINAL Short brief")
    source = brief_data.get("source")
    if not isinstance(source, dict):
        fail("Short brief source metadata missing")

    final_receipt = source.get("final_receipt")
    source_commit = source.get("source_commit")
    report = source.get("gogit_report")

    if final_receipt != f"automation/dev-flow/receipts/{step}-final.json":
        fail("Short brief scientific FINAL receipt mismatch")
    if not isinstance(source_commit, str) or not re.fullmatch(
        r"[a-f0-9]{40}",
        source_commit,
    ):
        fail("Short brief scientific source commit invalid")
    if not isinstance(report, str) or not report.startswith(
        f"reports/assistant-results/history/PHASE03-SMOLTALK-{step}-"
    ):
        fail("Short brief GOGIT report mismatch")

    return {
        "video_sha256": video_sha,
        "youtube_video_id": youtube_id,
        "brief_path": brief_path,
        "brief_sha256": brief_sha,
        "scientific_final_receipt": final_receipt,
        "scientific_source_commit": source_commit,
        "scientific_gogit_report": report,
    }


def receipt_path(step: str) -> Path:
    return RECEIPT_DIR / f"{step}-final.json"


def validate_existing_receipt(
    step: str,
    state: dict[str, str],
) -> dict | None:
    path = receipt_path(step)
    if not path.exists():
        return None

    receipt = load_json(path, "Media publication receipt")
    relative = path.relative_to(ROOT).as_posix()

    tracked = run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        timeout=60,
    )
    if tracked.returncode != 0:
        fail("Existing media receipt is not committed")

    if receipt.get("schema_version") != 1:
        fail("Unsupported media receipt schema")
    if receipt.get("publication_id") != f"MINI-KUZAI-{step}-FINAL":
        fail("Existing media receipt publication ID mismatch")
    if receipt.get("step") != step:
        fail("Existing media receipt step mismatch")

    media = receipt.get("media")
    youtube = receipt.get("youtube")
    linkedin = receipt.get("linkedin")
    github = receipt.get("github")

    if not isinstance(media, dict) or media.get("sha256") != state["video_sha256"]:
        fail("Existing media receipt SHA256 conflict")
    if (
        not isinstance(youtube, dict)
        or youtube.get("status") != "PUBLIC"
        or youtube.get("video_id") != state["youtube_video_id"]
    ):
        fail("Existing media receipt YouTube conflict")
    if not isinstance(linkedin, dict) or linkedin.get("status") != "PUBLISHED":
        fail("Existing media receipt LinkedIn state invalid")
    if not isinstance(github, dict) or github.get("status") != "PUBLISHED":
        fail("Existing media receipt GitHub state invalid")

    return receipt


def child(
    tool: Path,
    step: str,
    *,
    publish: bool,
    gate_name: str | None = None,
    timeout: int = 360,
) -> dict[str, str]:
    if tool.is_symlink() or not tool.is_file():
        fail(f"Media child tool unavailable: {tool.name}")
    if PYTHON.is_symlink() or not PYTHON.is_file():
        fail("Project Python unavailable")

    args = [str(PYTHON), str(tool), "--step", step]
    if publish:
        args.append("--publish")

    env = None
    if publish and gate_name:
        env = os.environ.copy()
        env[gate_name] = "YES"

    result = run(
        args,
        timeout=timeout,
        env=env,
    )
    values = parse_results(result.stdout)

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise MediaOrchestratorError(
            f"{tool.name} failed"
            + (f": {detail}" if detail else "")
        )

    return values


def require_linkedin(
    values: dict[str, str],
    *,
    publish: bool,
) -> dict[str, str]:
    if values.get("HANDOFF_PREFLIGHT") != "PASS":
        fail("LinkedIn handoff preflight did not report PASS")

    if not publish:
        if values.get("PUBLICATION_PERFORMED") != "0":
            fail("LinkedIn preflight unexpectedly published")
        return {}

    if values.get("HANDOFF") != "PASS":
        fail("LinkedIn handoff did not report PASS")

    video_urn = values.get("LINKEDIN_VIDEO_URN", "")
    post_urn = values.get("LINKEDIN_POST_URN", "")

    if not LINKEDIN_VIDEO_URN_RE.fullmatch(video_urn):
        fail("LinkedIn handoff returned invalid video URN")
    if not LINKEDIN_POST_URN_RE.fullmatch(post_urn):
        fail("LinkedIn handoff returned invalid post URN")

    return {
        "video_urn": video_urn,
        "post_urn": post_urn,
    }


def require_github(
    values: dict[str, str],
    *,
    publish: bool,
) -> dict[str, str]:
    if values.get("GITHUB_MEDIA_PREFLIGHT") != "PASS":
        fail("GitHub media preflight did not report PASS")
    if values.get("MEDIA_MODE") != "YOUTUBE_PUBLIC_LINK_FALLBACK":
        fail("Unexpected GitHub media mode")

    state = values.get("PUBLICATION_STATE", "")
    discussion_url = values.get("DISCUSSION_URL", "")

    if not GITHUB_URL_RE.fullmatch(discussion_url):
        fail("GitHub media returned invalid Discussion URL")

    if not publish:
        if values.get("PUBLICATION_PERFORMED") != "0":
            fail("GitHub media preflight unexpectedly published")
        if state not in {"READY_TO_COMMENT", "EXISTS_IDENTICAL"}:
            fail("GitHub media preflight is not ready")
        return {
            "discussion_url": discussion_url,
        }

    if state not in {"PUBLISHED", "EXISTS_IDENTICAL"}:
        fail("GitHub media publication state invalid")

    comment_url = values.get("MEDIA_COMMENT_URL", "")
    if not GITHUB_URL_RE.fullmatch(comment_url):
        fail("GitHub media returned invalid comment URL")

    return {
        "discussion_url": discussion_url,
        "comment_url": comment_url,
    }


def write_receipt(
    step: str,
    state: dict[str, str],
    linkedin: dict[str, str],
    github: dict[str, str],
) -> Path:
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    if RECEIPT_DIR.is_symlink() or not RECEIPT_DIR.is_dir():
        fail("Unsafe publication receipt directory")

    target = receipt_path(step)
    if target.exists() or target.is_symlink():
        fail("Media publication receipt already exists")

    payload = {
        "schema_version": 1,
        "publication_id": f"MINI-KUZAI-{step}-FINAL",
        "step": step,
        "purpose": "SCIENTIFIC_FINAL_DOWNSTREAM_MEDIA_PUBLICATION",
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "scientific_final_receipt": state["scientific_final_receipt"],
            "scientific_source_commit": state["scientific_source_commit"],
            "scientific_gogit_report": state["scientific_gogit_report"],
            "short_brief": state["brief_path"],
            "short_brief_sha256": state["brief_sha256"],
        },
        "media": {
            "sha256": state["video_sha256"],
            "duration_ms": 60000,
        },
        "youtube": {
            "status": "PUBLIC",
            "video_id": state["youtube_video_id"],
        },
        "linkedin": {
            "status": "PUBLISHED",
            "video_urn": linkedin["video_urn"],
            "post_urn": linkedin["post_urn"],
        },
        "github": {
            "status": "PUBLISHED",
            "discussion_url": github["discussion_url"],
            "comment_url": github["comment_url"],
            "media_mode": "YOUTUBE_PUBLIC_LINK_FALLBACK",
        },
        "scientific_boundary": {
            "media_is_scientific_evidence": False,
            "training_authorized": False,
            "blind_access_authorized": False,
        },
    }

    fd, temporary = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=RECEIPT_DIR,
        text=True,
    )
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    return target


def commit_receipt(
    target: Path,
    source_head: str,
    step: str,
) -> str:
    remote = git("ls-remote", "origin", "refs/heads/main").split()
    if len(remote) != 2 or remote[0] != source_head:
        target.unlink(missing_ok=True)
        fail("Remote main changed after media publication; receipt deferred")

    relative = target.relative_to(ROOT).as_posix()
    git("add", "--", relative)

    staged = git("diff", "--cached", "--name-only").splitlines()
    if staged != [relative]:
        run(["git", "reset"], timeout=60)
        target.unlink(missing_ok=True)
        fail("Unexpected staged paths for media receipt")

    git(
        "commit",
        "-m",
        f"media-flow: record {step} cross-channel publication",
    )
    commit = git("rev-parse", "HEAD")

    pushed = run(
        ["git", "push", "origin", "HEAD:main"],
        timeout=90,
    )
    if pushed.returncode != 0:
        fail("Media receipt push failed; local commit preserved")

    remote_after = git(
        "ls-remote",
        "origin",
        "refs/heads/main",
    ).split()
    if len(remote_after) != 2 or remote_after[0] != commit:
        fail("Media receipt remote verification failed")

    return commit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", required=True)
    parser.add_argument("--journal", type=Path, default=DEFAULT_JOURNAL)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    match = STEP_RE.fullmatch(args.step)
    if match is None or int(match.group(1)) < 81:
        fail("Cross-channel media orchestration is limited to V81+")

    source_head = verify_repo()
    state = local_state(args.step, args.journal)

    existing = validate_existing_receipt(args.step, state)
    if existing is not None:
        print("##### SECTION RESULTS FOR ASSISTANT ######")
        print("MEDIA_ORCHESTRATOR=PASS")
        print(f"STEP={args.step}")
        print("STATE=ALREADY_VERIFIED")
        print("PUBLICATION_PERFORMED=0")
        print("RECEIPT_COMMITTED=1")
        return 0

    linkedin_preflight = child(
        LINKEDIN,
        args.step,
        publish=False,
    )
    require_linkedin(linkedin_preflight, publish=False)

    github_preflight = child(
        GITHUB_MEDIA,
        args.step,
        publish=False,
    )
    github_ready = require_github(
        github_preflight,
        publish=False,
    )

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print("MEDIA_ORCHESTRATOR_PREFLIGHT=PASS")
    print(f"STEP={args.step}")
    print(f"SOURCE_HEAD={source_head}")
    print(f"VIDEO_SHA256={state['video_sha256']}")
    print(f"YOUTUBE_VIDEO_ID={state['youtube_video_id']}")
    print("LINKEDIN_PREFLIGHT=PASS")
    print("GITHUB_MEDIA_PREFLIGHT=PASS")
    print(f"GITHUB_DISCUSSION_URL={github_ready['discussion_url']}")
    print(f"PUBLISH_REQUESTED={int(args.publish)}")

    if not args.publish:
        print("PUBLICATION_PERFORMED=0")
        print("RECEIPT_COMMITTED=0")
        print("MEDIA_ORCHESTRATOR=DRY_RUN_PASS")
        return 0

    if os.environ.get("KUZAI_CROSS_CHANNEL_MEDIA_ENABLED") != "YES":
        fail("Cross-channel media live gate is disabled")

    linkedin_live = child(
        LINKEDIN,
        args.step,
        publish=True,
        gate_name="KUZAI_LINKEDIN_HANDOFF_ENABLED",
        timeout=420,
    )
    linkedin = require_linkedin(
        linkedin_live,
        publish=True,
    )

    github_live = child(
        GITHUB_MEDIA,
        args.step,
        publish=True,
        gate_name="KUZAI_GITHUB_MEDIA_PUBLISHER_ENABLED",
        timeout=180,
    )
    github = require_github(
        github_live,
        publish=True,
    )

    target = write_receipt(
        args.step,
        state,
        linkedin,
        github,
    )
    commit = commit_receipt(
        target,
        source_head,
        args.step,
    )

    print(f"LINKEDIN_VIDEO_URN={linkedin['video_urn']}")
    print(f"LINKEDIN_POST_URN={linkedin['post_urn']}")
    print(f"GITHUB_MEDIA_COMMENT_URL={github['comment_url']}")
    print(f"RECEIPT={target.relative_to(ROOT).as_posix()}")
    print(f"RECEIPT_COMMIT={commit}")
    print("PUBLICATION_PERFORMED=1")
    print("RECEIPT_COMMITTED=1")
    print("MEDIA_ORCHESTRATOR=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MediaOrchestratorError as exc:
        print("##### SECTION RESULTS FOR ASSISTANT ######")
        print("MEDIA_ORCHESTRATOR=BLOCKED")
        print(f"ERROR={exc}")
        raise SystemExit(1)
