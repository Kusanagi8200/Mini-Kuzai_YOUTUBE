#!/usr/bin/env python3
"""Preflight or publish a Mini-Kuzai GitHub media fallback comment.

The canonical scientific FINAL remains authoritative. This tool only appends
one media comment to the already-existing canonical Vxx Discussion after a
verified public YouTube publication.

Default mode is read-only. Live publication requires both --publish and
KUZAI_GITHUB_MEDIA_PUBLISHER_ENABLED=YES.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MINI_KUZAI = Path("/root/GitHub-Mini-Kuzai/Mini-Kuzai")
DEFAULT_JOURNAL = Path(
    "/root/.local/state/mini-kuzai-youtube/dev-flow-short-worker.json"
)

OWNER = "Kusanagi8200"
REPOSITORY = "Mini-Kuzai"
STEP_RE = re.compile(r"V([0-9]+)\Z")
YOUTUBE_ID_RE = re.compile(r"[A-Za-z0-9_-]{6,32}\Z")
SHA256_RE = re.compile(r"[a-f0-9]{64}\Z")
FINAL_URL_RE = re.compile(
    r"https://github\.com/Kusanagi8200/Mini-Kuzai/discussions/"
    r"([1-9][0-9]*)#discussioncomment-[1-9][0-9]*\Z"
)
MEDIA_MARKER_RE = re.compile(
    r"^MEDIA PUBLICATION // (V[0-9]+) FINAL$",
    re.MULTILINE,
)

DISCUSSION_QUERY = """
query($owner: String!, $repo: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    discussion(number: $number) {
      id
      number
      url
      comments(first: 100, after: $after) {
        totalCount
        pageInfo { hasNextPage endCursor }
        nodes { id body url }
      }
    }
  }
}
"""

ADD_COMMENT = """
mutation($discussion: ID!, $body: String!, $client: String!) {
  addDiscussionComment(input: {
    discussionId: $discussion,
    body: $body,
    clientMutationId: $client
  }) {
    comment { id body url }
  }
}
"""


class GitHubMediaError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise GitHubMediaError(message)


def run(
    args: list[str],
    *,
    cwd: Path = ROOT,
    timeout: int = 60,
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
        raise GitHubMediaError(
            f"Command failed to execute: {args[0]}"
        ) from exc


def git(repo: Path, *args: str) -> str:
    result = run(["git", *args], cwd=repo, timeout=60)
    if result.returncode != 0:
        fail(f"Git command failed in {repo.name}")
    return result.stdout.strip()


def verify_repo(repo: Path) -> str:
    if repo.is_symlink() or not repo.is_dir() or not (repo / ".git").is_dir():
        fail(f"Repository unavailable or unsafe: {repo}")

    if git(repo, "branch", "--show-current") != "main":
        fail(f"{repo.name} must be on main")
    if git(repo, "status", "--porcelain"):
        fail(f"{repo.name} worktree must be clean")

    fetched = run(
        ["git", "fetch", "--no-tags", "origin", "main"],
        cwd=repo,
        timeout=90,
    )
    if fetched.returncode != 0:
        fail(f"{repo.name} fetch failed")

    local = git(repo, "rev-parse", "HEAD")
    remote = git(repo, "rev-parse", "origin/main")
    if local != remote:
        fail(f"{repo.name} must be synchronized with origin/main")
    return local


def load_json(path: Path, label: str) -> dict:
    if path.is_symlink() or not path.is_file():
        fail(f"{label} missing or unsafe")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GitHubMediaError(f"{label} is invalid JSON") from exc
    if not isinstance(data, dict):
        fail(f"{label} must be a JSON object")
    return data


def github_actor() -> str:
    result = run(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            "query=query { viewer { login } }",
            "--jq",
            ".data.viewer.login",
        ],
        timeout=60,
    )
    if result.returncode != 0:
        fail("Unable to verify GitHub CLI identity")
    actor = result.stdout.strip()
    if actor != OWNER:
        fail("GitHub CLI identity is not the approved publisher")
    return actor


def graphql(query: str, **fields: str) -> dict:
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in fields.items():
        args.extend(["-F", f"{key}={value}"])

    result = run(args, timeout=90)
    if result.returncode != 0:
        fail("GitHub GraphQL request failed")

    try:
        payload = json.loads(result.stdout)
    except ValueError as exc:
        raise GitHubMediaError("GitHub GraphQL returned invalid JSON") from exc

    data = payload.get("data")
    if not isinstance(data, dict):
        fail("GitHub GraphQL response has no data")
    return data


def validate_state(
    step: str,
    journal_path: Path,
    mini_root: Path,
) -> dict[str, str]:
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
        fail("YouTube publication is not PUBLIC_PUBLISHED")

    youtube_id = row.get("youtube_video_id", "")
    video_sha = row.get("video_sha256", "")

    if not YOUTUBE_ID_RE.fullmatch(youtube_id):
        fail("Invalid YouTube video ID")
    if not SHA256_RE.fullmatch(video_sha):
        fail("Invalid media SHA256")

    receipt_rel = f"automation/dev-flow/receipts/{step}-final.json"
    receipt_path = mini_root / receipt_rel
    receipt = load_json(receipt_path, "FINAL receipt")

    tracked = run(
        ["git", "ls-files", "--error-unmatch", "--", receipt_rel],
        cwd=mini_root,
        timeout=60,
    )
    if tracked.returncode != 0:
        fail("FINAL receipt is not committed")

    committed = git(mini_root, "show", f"HEAD:{receipt_rel}")
    if receipt_path.read_text(encoding="utf-8").rstrip("\n") != committed:
        fail("FINAL receipt differs from committed HEAD")

    if receipt.get("schema_version") != 1:
        fail("Unsupported FINAL receipt schema")
    if receipt.get("command") != "FINAL-DEV-FLOW":
        fail("Receipt is not FINAL-DEV-FLOW")
    if receipt.get("step") != step:
        fail("FINAL receipt step mismatch")
    if receipt.get("status") != "PUBLISHED":
        fail("FINAL receipt is not PUBLISHED")

    github_url = receipt.get("github_url", "")
    match = FINAL_URL_RE.fullmatch(github_url)
    if match is None:
        fail("FINAL receipt GitHub URL is invalid")

    discussion_number = match.group(1)
    youtube_url = f"https://www.youtube.com/watch?v={youtube_id}"

    return {
        "discussion_number": discussion_number,
        "youtube_video_id": youtube_id,
        "youtube_url": youtube_url,
        "video_sha256": video_sha,
    }


def media_body(step: str, state: dict[str, str]) -> str:
    footer = (
        "##### **"
        + chr(96)
        + "THE KUZ NETWORK - KUSANAGI8200 - @2026"
        + chr(96)
        + "**"
    )
    return (
        f"MEDIA PUBLICATION // {step} FINAL\n\n"
        "The verified FINAL media package is now available publicly.\n\n"
        f"YouTube Short: {state['youtube_url']}\n\n"
        f"Media SHA256: {state['video_sha256']}\n\n"
        "GitHub media mode: YOUTUBE_PUBLIC_LINK_FALLBACK\n\n"
        "This media publication is downstream communication only. "
        "It does not alter the scientific FINAL, authorize training, "
        "open BLIND evaluation, or establish semantic competence.\n\n"
        "---\n\n"
        + footer
    )


def discussion_comments(number: str) -> tuple[str, str, list[dict]]:
    collected: list[dict] = []
    cursor = None
    total = None
    discussion_id = ""
    discussion_url = ""

    while True:
        fields = {
            "owner": OWNER,
            "repo": REPOSITORY,
            "number": number,
        }
        if cursor:
            fields["after"] = cursor

        data = graphql(DISCUSSION_QUERY, **fields)
        repo = data.get("repository")
        if not isinstance(repo, dict):
            fail("GitHub repository unavailable")
        discussion = repo.get("discussion")
        if not isinstance(discussion, dict):
            fail("Canonical Discussion unavailable")

        if str(discussion.get("number")) != number:
            fail("Canonical Discussion number mismatch")

        if not discussion_id:
            discussion_id = discussion.get("id", "")
            discussion_url = discussion.get("url", "")
        elif discussion.get("id") != discussion_id:
            fail("Discussion identity changed during pagination")

        comments = discussion.get("comments")
        if not isinstance(comments, dict):
            fail("Discussion comments unavailable")

        if total is None:
            total = comments.get("totalCount")

        nodes = comments.get("nodes")
        if not isinstance(nodes, list):
            fail("Discussion comment nodes unavailable")
        collected.extend(nodes)

        page = comments.get("pageInfo")
        if not isinstance(page, dict):
            fail("Discussion pagination unavailable")
        if not page.get("hasNextPage"):
            break

        cursor = page.get("endCursor")
        if not isinstance(cursor, str) or not cursor:
            fail("Discussion pagination cursor invalid")

    if not isinstance(total, int) or len(collected) != total:
        fail("Incomplete Discussion comment inventory")
    if not discussion_id or not discussion_url:
        fail("Canonical Discussion identity missing")

    return discussion_id, discussion_url, collected


def existing_media_comment(
    comments: list[dict],
    step: str,
    body: str,
) -> dict | None:
    matches = []
    for comment in comments:
        text = comment.get("body")
        if not isinstance(text, str):
            continue

        found = MEDIA_MARKER_RE.search(text)
        if found and found.group(1) == step:
            matches.append(comment)

    if len(matches) > 1:
        fail("Multiple GitHub media comments found for the same step")

    if not matches:
        return None

    existing = matches[0]
    if existing.get("body", "").strip() != body.strip():
        fail("Existing GitHub media comment conflicts with expected body")
    if not existing.get("id") or not existing.get("url"):
        fail("Existing GitHub media comment missing identity")
    return existing


def publish(
    step: str,
    state: dict[str, str],
    *,
    allow_publish: bool,
) -> dict[str, str]:
    actor = github_actor()
    discussion_id, discussion_url, comments = discussion_comments(
        state["discussion_number"]
    )
    body = media_body(step, state)
    existing = existing_media_comment(comments, step, body)

    if existing is not None:
        return {
            "state": "EXISTS_IDENTICAL",
            "discussion_url": discussion_url,
            "comment_url": existing["url"],
            "actor": actor,
        }

    if not allow_publish:
        return {
            "state": "READY_TO_COMMENT",
            "discussion_url": discussion_url,
            "comment_url": "",
            "actor": actor,
        }

    if os.environ.get("KUZAI_GITHUB_MEDIA_PUBLISHER_ENABLED") != "YES":
        fail("GitHub media publication gate is disabled")

    result = graphql(
        ADD_COMMENT,
        discussion=discussion_id,
        body=body,
        client=f"mini-kuzai-{step.lower()}-media",
    )
    created = (result.get("addDiscussionComment") or {}).get("comment")
    if not isinstance(created, dict) or not created.get("id"):
        fail("GitHub media comment creation returned no identity")

    _id, checked_url, checked_comments = discussion_comments(
        state["discussion_number"]
    )
    verified = existing_media_comment(checked_comments, step, body)

    if verified is None or verified.get("id") != created.get("id"):
        fail("GitHub media comment post-write verification failed")

    return {
        "state": "PUBLISHED",
        "discussion_url": checked_url,
        "comment_url": verified["url"],
        "actor": actor,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", required=True)
    parser.add_argument("--journal", type=Path, default=DEFAULT_JOURNAL)
    parser.add_argument(
        "--mini-kuzai-root",
        type=Path,
        default=MINI_KUZAI,
    )
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    match = STEP_RE.fullmatch(args.step)
    if match is None or int(match.group(1)) < 81:
        fail("GitHub media publication is limited to V81+")

    youtube_head = verify_repo(ROOT)
    mini_head = verify_repo(args.mini_kuzai_root)
    state = validate_state(
        args.step,
        args.journal,
        args.mini_kuzai_root,
    )
    result = publish(
        args.step,
        state,
        allow_publish=args.publish,
    )

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print("GITHUB_MEDIA_PREFLIGHT=PASS")
    print(f"STEP={args.step}")
    print(f"YOUTUBE_HEAD={youtube_head}")
    print(f"MINI_KUZAI_HEAD={mini_head}")
    print(f"GITHUB_ACTOR={result['actor']}")
    print(f"DISCUSSION_URL={result['discussion_url']}")
    print(f"YOUTUBE_VIDEO_ID={state['youtube_video_id']}")
    print(f"VIDEO_SHA256={state['video_sha256']}")
    print("MEDIA_MODE=YOUTUBE_PUBLIC_LINK_FALLBACK")
    print(f"PUBLICATION_STATE={result['state']}")
    print(f"PUBLISH_REQUESTED={int(args.publish)}")

    if result["comment_url"]:
        print(f"MEDIA_COMMENT_URL={result['comment_url']}")

    performed = int(result["state"] == "PUBLISHED")
    print(f"PUBLICATION_PERFORMED={performed}")
    print("GITHUB_MEDIA=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GitHubMediaError as exc:
        print("##### SECTION RESULTS FOR ASSISTANT ######")
        print("GITHUB_MEDIA=BLOCKED")
        print(f"ERROR={exc}")
        raise SystemExit(1)
