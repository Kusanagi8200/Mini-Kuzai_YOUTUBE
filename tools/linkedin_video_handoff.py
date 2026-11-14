#!/usr/bin/env python3
"""Preflight or publish one verified Mini-Kuzai FINAL MP4 through KUZ-DIN.

Default mode is read-only preflight. Live handoff requires both --publish and
KUZAI_LINKEDIN_HANDOFF_ENABLED=YES.

The script:
- reads the Mini-Kuzai_YOUTUBE worker journal
- verifies the committed FINAL brief and local MP4 SHA256
- verifies the KUZ-DIN runtime over SSH
- on explicit live authorization, copies the exact MP4 + text payload
- invokes KUZ-DIN's guarded native LinkedIn video runner with a transient gate

It never authorizes training, BLIND access, or scientific execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JOURNAL = Path(
    "/root/.local/state/mini-kuzai-youtube/dev-flow-short-worker.json"
)
DEFAULT_HOST = "83.228.192.116"
DEFAULT_SSH_KEY = Path("/root/.ssh/id_ed25519_kuzdin")
DEFAULT_REMOTE_ROOT = "/opt/kuz-din"
DEFAULT_REMOTE_MEDIA_ROOT = "/var/lib/kuz-din/mini-kuzai-media"

STEP_RE = re.compile(r"V([0-9]+)\Z")
VIDEO_ID_RE = re.compile(r"[A-Za-z0-9_-]{6,32}\Z")
SHA256_RE = re.compile(r"[a-f0-9]{64}\Z")
URN_RE = re.compile(r"urn:li:(?:video|share|ugcPost):[A-Za-z0-9_-]{5,256}\Z")


class HandoffError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise HandoffError(message)


def run(
    args: list[str],
    *,
    cwd: Path = ROOT,
    timeout: int = 120,
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
        raise HandoffError(
            f"Command failed to execute: {args[0]}"
        ) from exc


def git(*args: str) -> str:
    result = run(["git", *args], timeout=60)
    if result.returncode != 0:
        fail("Git command failed")
    return result.stdout.strip()


def verify_local_repo() -> str:
    if git("branch", "--show-current") != "main":
        fail("Handoff requires main branch")
    if git("status", "--porcelain"):
        fail("Handoff requires a clean worktree")

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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> dict:
    if path.is_symlink() or not path.is_file():
        fail(f"{label} missing or unsafe")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HandoffError(f"{label} is invalid JSON") from exc
    if not isinstance(data, dict):
        fail(f"{label} must be a JSON object")
    return data


def parse_results(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            values[key] = value.strip()
    return values


def brief_for(step: str) -> Path:
    return ROOT / "automation" / "dev-flow" / "short-briefs" / f"{step}-final.json"


def validate_local_state(step: str, journal_path: Path) -> dict[str, str]:
    journal = load_json(journal_path, "YouTube worker journal")
    if journal.get("schema_version") != 1:
        fail("Unsupported worker journal schema")

    steps = journal.get("steps")
    if not isinstance(steps, dict):
        fail("Worker journal steps missing")

    row = steps.get(step)
    if not isinstance(row, dict):
        fail(f"No worker journal entry for {step}")
    if row.get("status") != "PUBLIC_PUBLISHED":
        fail("YouTube worker state is not PUBLIC_PUBLISHED")

    video_sha = row.get("video_sha256", "")
    youtube_id = row.get("youtube_video_id", "")
    final_rel = row.get("final_video_path", "")

    if not SHA256_RE.fullmatch(video_sha):
        fail("Invalid journal video SHA256")
    if not VIDEO_ID_RE.fullmatch(youtube_id):
        fail("Invalid journal YouTube video ID")
    if not isinstance(final_rel, str) or not final_rel.startswith("work/"):
        fail("Invalid journal final media path")

    video = (ROOT / final_rel).resolve()
    work_root = (ROOT / "work").resolve()

    if video.is_symlink() or not video.is_file() or video.suffix.lower() != ".mp4":
        fail("Final MP4 missing or unsafe")
    try:
        video.relative_to(work_root)
    except ValueError as exc:
        raise HandoffError("Final MP4 outside work directory") from exc

    if sha256_file(video) != video_sha:
        fail("Local MP4 SHA256 does not match worker journal")

    brief_path = brief_for(step)
    brief = load_json(brief_path, "FINAL Short brief")

    relative = brief_path.relative_to(ROOT).as_posix()
    tracked = run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        timeout=60,
    )
    if tracked.returncode != 0:
        fail("FINAL Short brief is not committed")

    committed = git("show", f"HEAD:{relative}")
    if brief_path.read_text(encoding="utf-8").rstrip("\n") != committed:
        fail("FINAL Short brief differs from committed HEAD")

    if brief.get("step") != step:
        fail("Short brief step mismatch")
    if brief.get("video_id") != f"VIDEO-{step}-FINAL":
        fail("Short brief video ID mismatch")

    youtube = brief.get("youtube")
    if not isinstance(youtube, dict):
        fail("Short brief YouTube metadata missing")

    title = youtube.get("title")
    description = youtube.get("description")
    if not isinstance(title, str) or not title.strip():
        fail("Short brief title missing")
    if not isinstance(description, str) or not description.strip():
        fail("Short brief description missing")

    linkedin_title = title.strip()[:200]
    linkedin_text = (
        f"MINI-KUZAI // LLM FROM SCRATCH\n"
        f"FLOW {step} OK\n\n"
        f"{description.strip()}\n\n"
        "#MiniKuzai #LocalAI #LLMFromScratch #OpenSource #TheKuzNetwork"
    )
    if len(linkedin_text) > 2800:
        fail("Derived LinkedIn commentary exceeds 2800 characters")

    return {
        "video": str(video),
        "video_sha256": video_sha,
        "youtube_video_id": youtube_id,
        "linkedin_title": linkedin_title,
        "linkedin_text": linkedin_text,
        "publication_id": f"MINI-KUZAI-{step}-FINAL",
    }


def ssh_base(host: str, key: Path) -> list[str]:
    if not re.fullmatch(r"[A-Za-z0-9.-]{1,255}", host):
        fail("Unsafe KUZ-DIN host")
    if key.is_symlink() or not key.is_file():
        fail("KUZ-DIN SSH key missing or unsafe")
    if key.stat().st_mode & 0o077:
        fail("KUZ-DIN SSH key permissions are too open")

    return [
        "ssh",
        "-i",
        str(key),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        "ConnectTimeout=10",
        f"root@{host}",
    ]


def scp_base(host: str, key: Path) -> list[str]:
    if not re.fullmatch(r"[A-Za-z0-9.-]{1,255}", host):
        fail("Unsafe KUZ-DIN host")
    return [
        "scp",
        "-q",
        "-i",
        str(key),
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        "ConnectTimeout=10",
    ]


def remote_preflight(
    host: str,
    key: Path,
    remote_root: str,
) -> dict[str, str]:
    command = (
        "set -eu; "
        f"cd {shlex.quote(remote_root)}; "
        "test \"$(git branch --show-current)\" = main; "
        "test -z \"$(git status --porcelain)\"; "
        "git fetch --no-tags origin main >/dev/null 2>&1; "
        "LOCAL=$(git rev-parse HEAD); "
        "REMOTE=$(git rev-parse origin/main); "
        "SYNC=UNCHANGED; "
        "BACKUP=NONE; "
        "if [ \"$LOCAL\" != \"$REMOTE\" ]; then "
        "git merge-base --is-ancestor \"$LOCAL\" \"$REMOTE\"; "
        "BACKUP=backup/auto-media-pre-sync-$LOCAL; "
        "git show-ref --verify --quiet refs/heads/$BACKUP || git branch \"$BACKUP\" \"$LOCAL\"; "
        "git merge --ff-only \"$REMOTE\" >/dev/null; "
        "SYNC=FAST_FORWARD; "
        "fi; "
        "LOCAL=$(git rev-parse HEAD); "
        "test \"$LOCAL\" = \"$REMOTE\"; "
        "test -z \"$(git status --porcelain)\"; "
        "test -x .venv/bin/python; "
        "test -f tools/linkedin_video_post.py; "
        "test -f /var/lib/kuz-din/linkedin-video-publications.json; "
        "test \"$(stat -c %a /var/lib/kuz-din/linkedin-video-publications.json)\" = 600; "
        "printf 'REMOTE_PREFLIGHT=PASS\\n'; "
        "printf 'REMOTE_SYNC=%s\\n' \"$SYNC\"; "
        "printf 'REMOTE_BACKUP=%s\\n' \"$BACKUP\"; "
        "printf 'REMOTE_HEAD=%s\\n' \"$LOCAL\""
    )
    result = run(
        [*ssh_base(host, key), command],
        timeout=90,
    )
    if result.returncode != 0:
        fail("KUZ-DIN remote preflight failed")

    values = parse_results(result.stdout)
    if values.get("REMOTE_PREFLIGHT") != "PASS":
        fail("KUZ-DIN remote preflight did not report PASS")
    if values.get("REMOTE_SYNC") not in {"UNCHANGED", "FAST_FORWARD"}:
        fail("KUZ-DIN remote synchronization state invalid")
    return values


def remote_existing_publication(
    host: str,
    key: Path,
    publication_id: str,
    media_sha256: str,
    remote_root: str,
) -> dict[str, str] | None:
    script = (
        "import json,pathlib; "
        "p=pathlib.Path('/var/lib/kuz-din/linkedin-video-publications.json'); "
        "d=json.loads(p.read_text()); "
        f"pid={publication_id!r}; sha={media_sha256!r}; "
        "rows=[r for r in d.get('publications',[]) "
        "if r.get('publication_id')==pid or r.get('media_sha256')==sha]; "
        "r=rows[0] if rows else None; "
        "print('EXISTING_PUBLICATION='+('1' if r else '0')); "
        "print('EXISTING_MATCH='+('1' if r and r.get('publication_id')==pid "
        "and r.get('media_sha256')==sha else '0')); "
        "print('LINKEDIN_VIDEO_URN='+(r.get('linkedin_video_urn','') if r else '')); "
        "print('LINKEDIN_POST_URN='+(r.get('linkedin_post_urn','') if r else ''))"
    )
    command = (
        f"{shlex.quote(remote_root)}/.venv/bin/python "
        f"-c {shlex.quote(script)}"
    )
    result = run(
        [*ssh_base(host, key), command],
        timeout=60,
    )
    if result.returncode != 0:
        fail("Unable to inspect KUZ-DIN video journal")

    values = parse_results(result.stdout)
    if values.get("EXISTING_PUBLICATION") != "1":
        return None
    if values.get("EXISTING_MATCH") != "1":
        fail("KUZ-DIN journal contains a conflicting publication")

    video_urn = values.get("LINKEDIN_VIDEO_URN", "")
    post_urn = values.get("LINKEDIN_POST_URN", "")
    if not URN_RE.fullmatch(video_urn) or not URN_RE.fullmatch(post_urn):
        fail("KUZ-DIN existing publication has invalid URNs")
    return values


def publish(
    step: str,
    state: dict[str, str],
    *,
    host: str,
    key: Path,
    remote_root: str,
    remote_media_root: str,
) -> dict[str, str]:
    if os.environ.get("KUZAI_LINKEDIN_HANDOFF_ENABLED") != "YES":
        fail("Local LinkedIn handoff gate is disabled")

    existing = remote_existing_publication(
        host,
        key,
        state["publication_id"],
        state["video_sha256"],
        remote_root,
    )
    if existing is not None:
        return {
            "state": "ALREADY_PUBLISHED",
            "linkedin_video_urn": existing["LINKEDIN_VIDEO_URN"],
            "linkedin_post_urn": existing["LINKEDIN_POST_URN"],
        }

    remote_dir = f"{remote_media_root}/{step}"
    remote_video = f"{remote_dir}/{state['publication_id']}.mp4"
    remote_text = f"{remote_dir}/{state['publication_id']}.txt"

    mkdir_command = (
        f"install -d -m 750 {shlex.quote(remote_dir)}"
    )
    made = run(
        [*ssh_base(host, key), mkdir_command],
        timeout=60,
    )
    if made.returncode != 0:
        fail("Unable to create KUZ-DIN media handoff directory")

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{step.lower()}-linkedin-",
        suffix=".txt",
        text=True,
    )
    temp_text = Path(temp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(state["linkedin_text"])
            handle.write("\n")

        copied_video = run(
            [
                *scp_base(host, key),
                state["video"],
                f"root@{host}:{remote_video}",
            ],
            timeout=180,
        )
        if copied_video.returncode != 0:
            fail("MP4 handoff to KUZ-DIN failed")

        copied_text = run(
            [
                *scp_base(host, key),
                str(temp_text),
                f"root@{host}:{remote_text}",
            ],
            timeout=60,
        )
        if copied_text.returncode != 0:
            fail("LinkedIn text handoff to KUZ-DIN failed")
    finally:
        temp_text.unlink(missing_ok=True)

    verify_command = (
        f"chmod 600 {shlex.quote(remote_video)} {shlex.quote(remote_text)}; "
        f"printf 'REMOTE_SHA256=%s\\n' "
        f"\"$(sha256sum {shlex.quote(remote_video)} | awk '{{print $1}}')\""
    )
    verified = run(
        [*ssh_base(host, key), verify_command],
        timeout=60,
    )
    if verified.returncode != 0:
        fail("KUZ-DIN media SHA256 verification failed")

    remote_values = parse_results(verified.stdout)
    if remote_values.get("REMOTE_SHA256") != state["video_sha256"]:
        fail("KUZ-DIN media SHA256 mismatch")

    runner = (
        "env KUZDIN_VIDEO_PUBLISHER_ENABLED=YES "
        f"{shlex.quote(remote_root)}/.venv/bin/python "
        f"{shlex.quote(remote_root)}/tools/linkedin_video_post.py "
        f"--publication-id {shlex.quote(state['publication_id'])} "
        f"--video {shlex.quote(remote_video)} "
        f"--text-file {shlex.quote(remote_text)} "
        f"--title {shlex.quote(state['linkedin_title'])} "
        "--publish"
    )
    result = run(
        [*ssh_base(host, key), runner],
        timeout=300,
    )

    values = parse_results(result.stdout)
    if result.returncode != 0:
        fail("KUZ-DIN LinkedIn video runner failed")
    if values.get("STATE") != "PUBLISHED":
        fail("KUZ-DIN LinkedIn runner did not report PUBLISHED")
    if values.get("UPLOAD_PERFORMED") != "1":
        fail("KUZ-DIN LinkedIn upload was not performed")

    video_urn = values.get("LINKEDIN_VIDEO_URN", "")
    post_urn = values.get("LINKEDIN_POST_URN", "")
    if not URN_RE.fullmatch(video_urn) or not URN_RE.fullmatch(post_urn):
        fail("KUZ-DIN LinkedIn runner returned invalid URNs")

    cleanup = run(
        [
            *ssh_base(host, key),
            f"rm -f {shlex.quote(remote_video)} {shlex.quote(remote_text)}",
        ],
        timeout=60,
    )
    if cleanup.returncode != 0:
        fail("LinkedIn published but remote handoff cleanup failed")

    return {
        "state": "PUBLISHED",
        "linkedin_video_urn": video_urn,
        "linkedin_post_urn": post_urn,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", required=True)
    parser.add_argument("--journal", type=Path, default=DEFAULT_JOURNAL)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--ssh-key", type=Path, default=DEFAULT_SSH_KEY)
    parser.add_argument("--remote-root", default=DEFAULT_REMOTE_ROOT)
    parser.add_argument(
        "--remote-media-root",
        default=DEFAULT_REMOTE_MEDIA_ROOT,
    )
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    match = STEP_RE.fullmatch(args.step)
    if match is None or int(match.group(1)) < 81:
        fail("LinkedIn handoff is limited to V81+")

    head = verify_local_repo()
    state = validate_local_state(args.step, args.journal)
    remote = remote_preflight(
        args.host,
        args.ssh_key,
        args.remote_root,
    )

    existing = remote_existing_publication(
        args.host,
        args.ssh_key,
        state["publication_id"],
        state["video_sha256"],
        args.remote_root,
    )

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print("HANDOFF_PREFLIGHT=PASS")
    print(f"STEP={args.step}")
    print(f"LOCAL_HEAD={head}")
    print(f"REMOTE_HEAD={remote.get('REMOTE_HEAD', '')}")
    print(f"REMOTE_SYNC={remote.get('REMOTE_SYNC', '')}")
    print(f"REMOTE_BACKUP={remote.get('REMOTE_BACKUP', '')}")
    print(f"PUBLICATION_ID={state['publication_id']}")
    print(f"VIDEO_SHA256={state['video_sha256']}")
    print(f"YOUTUBE_VIDEO_ID={state['youtube_video_id']}")
    print(f"EXISTING_PUBLICATION={int(existing is not None)}")
    print(f"PUBLISH_REQUESTED={int(args.publish)}")

    if not args.publish:
        print("PUBLICATION_PERFORMED=0")
        print("HANDOFF=DRY_RUN_PASS")
        return 0

    result = publish(
        args.step,
        state,
        host=args.host,
        key=args.ssh_key,
        remote_root=args.remote_root,
        remote_media_root=args.remote_media_root,
    )

    print(f"HANDOFF_STATE={result['state']}")
    print(f"LINKEDIN_VIDEO_URN={result['linkedin_video_urn']}")
    print(f"LINKEDIN_POST_URN={result['linkedin_post_urn']}")
    print("PUBLICATION_PERFORMED=1")
    print("HANDOFF=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HandoffError as exc:
        print("##### SECTION RESULTS FOR ASSISTANT ######")
        print("HANDOFF=BLOCKED")
        print(f"ERROR={exc}")
        raise SystemExit(1)
