#!/usr/bin/env python3
"""Post-V83 THE KUZ NETWORK maintenance reconciliation.

Runs from fhc2 after V83 FINAL closure. It fast-forwards only clean main
worktrees, creates recoverable local backup branches before runtime changes,
updates the two VPS clones through the already configured SSH identity, checks
the public Mini-Kuzai page, and emits only sanitized aggregate results.

It never authorizes training, BLIND access, optimizer work or checkpoint writes.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

YOUTUBE = Path("/root/GitHub-Mini-Kuzai/Mini-Kuzai_YOUTUBE")
MINI = Path("/root/GitHub-Mini-Kuzai/Mini-Kuzai")
KUZAICHAT = Path("/root/KUZAI-CHAT")

SSH = [
    "ssh",
    "-i", "/root/.ssh/id_ed25519_kuzdin",
    "-o", "IdentitiesOnly=yes",
    "-o", "BatchMode=yes",
    "-o", "StrictHostKeyChecking=yes",
    "-o", "ConnectTimeout=10",
    "root@83.228.192.116",
]

REMOTE_SCRIPT = r"""
set -euo pipefail
stamp="$1"

sync_repo() {
    label="$1"
    repo="$2"
    cd "$repo"
    test "$(git branch --show-current)" = "main"
    test -z "$(git status --porcelain)"
    old="$(git rev-parse HEAD)"
    git fetch --no-tags origin main >/dev/null 2>&1
    remote="$(git rev-parse origin/main)"
    updated=0
    if [ "$old" != "$remote" ]; then
        git merge-base --is-ancestor "$old" "$remote"
        lower="$(printf '%s' "$label" | tr 'A-Z' 'a-z')"
        git branch "backup/runtime-maj-v83-close-${lower}-${stamp}" "$old"
        git merge --ff-only "$remote" >/dev/null
        updated=1
    fi
    new="$(git rev-parse HEAD)"
    test "$new" = "$remote"
    test -z "$(git status --porcelain)"
    printf '%s_SYNC=PASS\n' "$label"
    printf '%s_UPDATED=%s\n' "$label" "$updated"
    printf '%s_WORKTREE=CLEAN\n' "$label"
}

sync_repo KUZDIN /opt/kuz-din
grep -q 'V83 genuine FINAL native-video result' /opt/kuz-din/README.md
grep -q 'V84 has not started' /opt/kuz-din/README.md
printf 'KUZDIN_V83_DOC=PASS\n'

sync_repo KUZAIORG /var/www/kuzai.org
cd /var/www/kuzai.org
php -l app/mini-kuzai.php >/dev/null
printf 'PHP_LINT=PASS\n'
body="$(mktemp)"
trap 'rm -f "$body"' EXIT
status="$(curl -sS -L -o "$body" -w '%{http_code}' 'https://kuzai.org/index.php?page=mini-kuzai')"
test "$status" = "200"
grep -q 'V83 CLOSED' "$body"
grep -q 'V84' "$body"
printf 'PUBLIC_HTTP=200\n'
printf 'PUBLIC_V83=PASS\n'
printf 'PUBLIC_V84=PASS\n'
"""


class MaintenanceError(RuntimeError):
    pass


def run(
    args: list[str],
    *,
    cwd: Path | None = None,
    input_text: str | None = None,
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MaintenanceError(f"command execution failed: {args[0]}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise MaintenanceError(
            f"command failed: {args[0]}" + (f": {detail}" if detail else "")
        )
    return result


def git(repo: Path, *args: str) -> str:
    return run(["git", *args], cwd=repo).stdout.strip()


def sync_local(label: str, repo: Path, stamp: str) -> dict[str, str]:
    if repo.is_symlink() or not (repo / ".git").exists():
        raise MaintenanceError(f"{label} repository missing or unsafe")
    if git(repo, "branch", "--show-current") != "main":
        raise MaintenanceError(f"{label} is not on main")
    if git(repo, "status", "--porcelain"):
        raise MaintenanceError(f"{label} worktree is not clean")

    old = git(repo, "rev-parse", "HEAD")
    run(["git", "fetch", "--no-tags", "origin", "main"], cwd=repo)
    remote = git(repo, "rev-parse", "origin/main")
    updated = "0"
    if old != remote:
        run(["git", "merge-base", "--is-ancestor", old, remote], cwd=repo)
        branch = f"backup/runtime-maj-v83-close-{label.lower()}-{stamp}"
        run(["git", "branch", branch, old], cwd=repo)
        run(["git", "merge", "--ff-only", remote], cwd=repo)
        updated = "1"

    new = git(repo, "rev-parse", "HEAD")
    if new != remote or git(repo, "status", "--porcelain"):
        raise MaintenanceError(f"{label} synchronization verification failed")

    return {
        f"{label}_SYNC": "PASS",
        f"{label}_UPDATED": updated,
        f"{label}_WORKTREE": "CLEAN",
    }


def parse_remote(output: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in output.splitlines():
        if "=" not in raw:
            continue
        key, value = raw.strip().split("=", 1)
        if not key or key in result:
            raise MaintenanceError("invalid remote result")
        result[key] = value
    required = {
        "KUZDIN_SYNC", "KUZDIN_UPDATED", "KUZDIN_WORKTREE",
        "KUZDIN_V83_DOC", "KUZAIORG_SYNC", "KUZAIORG_UPDATED",
        "KUZAIORG_WORKTREE", "PHP_LINT", "PUBLIC_HTTP",
        "PUBLIC_V83", "PUBLIC_V84",
    }
    if not required <= set(result):
        raise MaintenanceError("incomplete remote maintenance result")
    return result


def verify_local_state() -> dict[str, str]:
    mini_readme = (MINI / "README.md").read_text(encoding="utf-8")
    youtube_readme = (YOUTUBE / "README.md").read_text(encoding="utf-8")
    receipt = YOUTUBE / "automation/publication-receipts/V83-final.json"
    closure = (
        YOUTUBE
        / "reports/assistant-results/history/V83-FINAL-DEV-FLOW-AUTO-VERIFY-001.json"
    )
    if receipt.is_symlink() or not receipt.is_file():
        raise MaintenanceError("V83 media receipt missing")
    if closure.is_symlink() or not closure.is_file():
        raise MaintenanceError("V83 closure GOGIT missing")

    receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
    closure_data = json.loads(closure.read_text(encoding="utf-8"))
    results = closure_data.get("results")
    if not (
        receipt_data.get("step") == "V83"
        and receipt_data.get("youtube", {}).get("status") == "PUBLIC"
        and receipt_data.get("linkedin", {}).get("status") == "PUBLISHED"
        and receipt_data.get("github", {}).get("status") == "PUBLISHED"
        and isinstance(results, dict)
        and results.get("FINAL_FLOW") == "PASS"
        and results.get("MEDIA_RECEIPT") == "PASS"
        and "V83 CLOSED" in mini_readme
        and "START-DEV-FLOW V84" in mini_readme
        and "V83 genuine FINAL media flow --> VERIFIED / CLOSED" in youtube_readme
        and "START-DEV-FLOW V84" in youtube_readme
    ):
        raise MaintenanceError("post-V83 local documentation/evidence gate failed")

    return {
        "V83_MEDIA_RECEIPT": "PASS",
        "V83_FINAL_CLOSURE": "PASS",
        "MINI_V83_DOC": "PASS",
        "YOUTUBE_V83_DOC": "PASS",
    }


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    result: dict[str, str] = {}

    result.update(sync_local("YOUTUBE", YOUTUBE, stamp))
    result.update(sync_local("MINI", MINI, stamp))
    result.update(sync_local("KUZAICHAT", KUZAICHAT, stamp))
    result.update(verify_local_state())

    remote = run(
        [*SSH, "bash", "-s", "--", stamp],
        input_text=REMOTE_SCRIPT,
        timeout=240,
    )
    result.update(parse_remote(remote.stdout))

    result.update({
        "MAJ_THEKUZNETWORK": "PASS",
        "KUZAICHAT_CHANGE": "NO_CHANGE",
        "TRAINING_ALLOWED": "0",
        "BLIND_ACCESS": "0",
        "NEXT_BOUNDARY": "START_DEV_FLOW_V84_REQUIRED",
    })

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    for key in sorted(result):
        print(f"{key}={result[key]}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MaintenanceError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"MAJ-THEKUZNETWORK ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
