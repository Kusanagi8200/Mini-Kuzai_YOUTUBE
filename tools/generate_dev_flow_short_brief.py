#!/usr/bin/env python3
"""Generate one deterministic Mini-Kuzai FINAL media brief.

This tool is intentionally publication-free. It derives a Short brief only
from committed Mini-Kuzai FINAL provenance:

FINAL receipt -> FINAL request -> immutable GOGIT report -> validated brief.

It never starts training, never accesses BLIND data, and never publishes to
YouTube, LinkedIn, or GitHub Discussions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MINI_KUZAI = Path("/root/GitHub-Mini-Kuzai/Mini-Kuzai")
BRIEF_DIR = ROOT / "automation" / "dev-flow" / "short-briefs"
VALIDATOR = ROOT / "tools" / "validate_dev_flow_short_brief.py"
PYTHON = ROOT / ".venv" / "bin" / "python"

sys.path.insert(0, str(ROOT / "app"))
from youtube_upload import normalize_description  # noqa: E402

STEP_RE = re.compile(r"V([0-9]+)\Z")
REPORT_RE = re.compile(
    r"reports/assistant-results/history/"
    r"PHASE03-SMOLTALK-(V[0-9]+)-.+\.json\Z"
)

SAFETY_KEYS = {
    "SEMANTIC_VALIDATION_COMPLETE",
    "TRAINING_AUTHORIZED",
    "TRAINING_STARTED",
}

PRIORITY_TERMS = (
    "PRED_CHANGED",
    "SIGN_CHANGED",
    "CORRECT",
    "PREFIXES",
    "COUNT",
    "TOTAL",
    "MEAN",
    "MAX",
    "MIN",
    "RATIO",
    "SHARE",
)


class BriefGeneratorError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise BriefGeneratorError(message)


def run(
    args: list[str],
    *,
    cwd: Path,
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
        raise BriefGeneratorError(
            f"Command failed to execute: {args[0]}"
        ) from exc


def git(repo: Path, *args: str) -> str:
    result = run(["git", *args], cwd=repo)
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
        fail(f"{repo.name} must be synchronized with origin/main")

    return local


def read_committed(repo: Path, relative: str, label: str) -> tuple[dict, str]:
    if (
        relative.startswith("/")
        or "\\" in relative
        or ".." in Path(relative).parts
    ):
        fail(f"Unsafe {label} path")

    path = repo / relative
    if path.is_symlink() or not path.is_file():
        fail(f"{label} missing or unsafe")

    tracked = run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=repo,
    )
    if tracked.returncode != 0:
        fail(f"{label} is not committed")

    text = path.read_text(encoding="utf-8")
    committed = git(repo, "show", f"HEAD:{relative}")

    if text.rstrip("\n") != committed:
        fail(f"{label} differs from committed HEAD")

    try:
        data = json.loads(text)
    except (OSError, ValueError) as exc:
        raise BriefGeneratorError(f"{label} is invalid JSON") from exc

    if not isinstance(data, dict):
        fail(f"{label} must be a JSON object")

    return data, text


def verify_snapshot(
    repo: Path,
    commit: str,
    relative: str,
    current_text: str,
    label: str,
) -> None:
    check = run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=repo,
    )
    if check.returncode != 0:
        fail("FINAL source commit does not exist")

    result = run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=repo,
    )
    if result.returncode != 0:
        fail(f"{label} absent from FINAL source commit")

    if result.stdout.rstrip("\n") != current_text.rstrip("\n"):
        fail(f"{label} changed after FINAL source commit")


def validate_provenance(
    step: str,
    mini_root: Path,
) -> tuple[dict, dict, dict, str]:
    receipt_rel = f"automation/dev-flow/receipts/{step}-final.json"
    request_rel = f"automation/dev-flow/requests/{step}-final.json"

    receipt, receipt_text = read_committed(
        mini_root,
        receipt_rel,
        "FINAL receipt",
    )
    request, request_text = read_committed(
        mini_root,
        request_rel,
        "FINAL request",
    )

    if receipt.get("schema_version") != 1:
        fail("Unsupported FINAL receipt schema")
    if receipt.get("command") != "FINAL-DEV-FLOW":
        fail("Receipt is not FINAL-DEV-FLOW")
    if receipt.get("step") != step:
        fail("FINAL receipt step mismatch")
    if receipt.get("status") != "PUBLISHED":
        fail("FINAL receipt is not PUBLISHED")

    if request.get("schema_version") != 1:
        fail("Unsupported FINAL request schema")
    if request.get("command") != "FINAL-DEV-FLOW":
        fail("Request is not FINAL-DEV-FLOW")
    if request.get("step") != step:
        fail("FINAL request step mismatch")

    report_rel = request.get("report")
    if not isinstance(report_rel, str):
        fail("FINAL request has no GOGIT report")

    match = REPORT_RE.fullmatch(report_rel)
    if match is None or match.group(1) != step:
        fail("FINAL request GOGIT report path is invalid")

    request_digest = hashlib.sha256(
        request_text.encode("utf-8")
    ).hexdigest()
    if receipt.get("request_sha256") != request_digest:
        fail("FINAL request SHA256 does not match receipt")

    report, report_text = read_committed(
        mini_root,
        report_rel,
        "GOGIT report",
    )

    if report.get("project") != "Mini-Kuzai":
        fail("Unexpected GOGIT project")
    if report.get("phase") != "03":
        fail("Unexpected GOGIT phase")
    if report.get("status") != "PUBLIC_AGGREGATE_REVIEW_ONLY":
        fail("Unexpected GOGIT report status")
    if report.get("private_conversation_data_included") is not False:
        fail("GOGIT privacy invariant failed")
    if report.get("semantic_validation_complete") is not False:
        fail("Unexpected semantic-validation metadata")

    step_id = report.get("step_id")
    if (
        not isinstance(step_id, str)
        or not step_id.startswith(f"PHASE03-SMOLTALK-{step}-")
    ):
        fail("GOGIT step ID does not match FINAL step")

    metrics = report.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        fail("GOGIT metrics missing")
    if any(type(value) is not int or value < 0 for value in metrics.values()):
        fail("GOGIT metrics must be nonnegative integers")
    if metrics.get(f"{step}_PASS") != 1:
        fail(f"{step}_PASS is not 1")
    if metrics.get("SEMANTIC_VALIDATION_COMPLETE") != 0:
        fail("Semantic validation safety invariant failed")
    if metrics.get("TRAINING_AUTHORIZED") != 0:
        fail("Training authorization must remain disabled")
    if metrics.get("TRAINING_STARTED") != 0:
        fail("Training must not have started")

    blind = [
        value
        for name, value in metrics.items()
        if name.endswith("_BLIND_ACCESS")
    ]
    if not blind or any(value != 0 for value in blind):
        fail("BLIND access safety invariant failed")

    source_commit = receipt.get("source_commit")
    if not isinstance(source_commit, str) or not re.fullmatch(
        r"[a-f0-9]{40}",
        source_commit,
    ):
        fail("Invalid FINAL source commit")

    verify_snapshot(
        mini_root,
        source_commit,
        request_rel,
        request_text,
        "FINAL request",
    )
    verify_snapshot(
        mini_root,
        source_commit,
        report_rel,
        report_text,
        "GOGIT report",
    )

    return receipt, request, report, source_commit


def clip(text: str, limit: int) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    if limit <= 3:
        return clean[:limit]
    return clean[: limit - 3].rstrip() + "..."


def subject_from_report(step: str, report: dict) -> str:
    source = report.get("source")
    if not isinstance(source, str) or not source.strip():
        fail("GOGIT report source is missing")

    subject = re.sub(
        rf"^Mini-Kuzai\s+{re.escape(step)}\s*",
        "",
        source.strip(),
        flags=re.IGNORECASE,
    )
    subject = re.sub(r"\s+", " ", subject).strip(" -:")
    if not subject:
        subject = "scientific control"

    return subject


def metric_score(name: str) -> tuple[int, str]:
    score = 0
    for index, term in enumerate(PRIORITY_TERMS):
        if term in name:
            score += len(PRIORITY_TERMS) - index
    return (-score, name)


def selected_metrics(step: str, metrics: dict[str, int]) -> list[tuple[str, int]]:
    excluded = {
        f"{step}_PASS",
        *SAFETY_KEYS,
    }

    candidates = [
        (name, value)
        for name, value in metrics.items()
        if name.startswith(step + "_")
        and name not in excluded
        and not name.endswith("_BLIND_ACCESS")
    ]

    candidates.sort(key=lambda item: metric_score(item[0]))

    if len(candidates) < 3:
        fallback = [
            (name, value)
            for name, value in metrics.items()
            if name not in excluded
            and not name.endswith("_BLIND_ACCESS")
            and (name, value) not in candidates
        ]
        fallback.sort(key=lambda item: item[0])
        candidates.extend(fallback)

    return candidates[:3]


def metric_label(step: str, name: str) -> str:
    prefix = step + "_"
    if name.startswith(prefix):
        name = name[len(prefix):]
    return name.replace("_", " ").strip()


def build_brief(
    step: str,
    receipt: dict,
    request: dict,
    report: dict,
    source_commit: str,
) -> dict:
    subject = subject_from_report(step, report)
    subject_upper = clip(subject.upper(), 96)

    chosen = selected_metrics(step, report["metrics"])

    segments: list[dict] = [
        {
            "duration_seconds": 12,
            "badge": step,
            "headline": "FINAL VERIFIED",
            "body": subject_upper,
        }
    ]

    for name, value in chosen:
        segments.append(
            {
                "duration_seconds": 12,
                "badge": step,
                "headline": clip(metric_label(step, name).upper(), 64),
                "body": clip(f"MEASURED VALUE: {value:,}", 96),
            }
        )

    while len(segments) < 4:
        segments.append(
            {
                "duration_seconds": 12,
                "badge": step,
                "headline": "GOGIT VERIFIED",
                "body": "IMMUTABLE PUBLIC AGGREGATE REPORT PASSED",
            }
        )

    segments.append(
        {
            "duration_seconds": 12,
            "badge": step,
            "headline": "SAFETY BOUNDARY",
            "body": "NO NEW TRAINING / BLIND CLOSED / NO SEMANTIC CLAIM",
        }
    )

    narration_metrics = "; ".join(
        f"{metric_label(step, name).lower()} {value:,}"
        for name, value in chosen
    )
    if not narration_metrics:
        narration_metrics = "the immutable aggregate verification passed"

    narration = (
        f"Mini-Kuzai {step} has completed the {subject}. "
        "The FINAL DEV-FLOW receipt is published and the immutable GOGIT "
        f"report passed. Key measurements include {narration_metrics}. "
        "This media summary does not authorize new training, does not open "
        "BLIND evaluation, and does not claim semantic competence or reasoning."
    )
    narration = clip(narration, 900)

    title = clip(
        f"MINI-KUZAI {step} // {subject.upper()}",
        100,
    )

    description = (
        f"Mini-Kuzai {step} FINAL media summary for {subject}.\n\n"
        f"Verified immutable report: {report['step_id']}\n"
        "No new training. BLIND evaluation remains closed. "
        "This publication does not claim semantic competence.\n\n"
        "BUILD LOCAL. KEEP CONTROL. OWN THE STACK."
    )
    description = normalize_description(description)

    return {
        "schema_version": 1,
        "step": step,
        "video_id": f"VIDEO-{step}-FINAL",
        "source": {
            "final_receipt": (
                f"automation/dev-flow/receipts/{step}-final.json"
            ),
            "gogit_report": request["report"],
            "source_commit": source_commit,
            "final_status": receipt["status"],
        },
        "timeline": {
            "duration_seconds": 60,
            "segments": segments,
        },
        "narration": narration,
        "youtube": {
            "title": title,
            "description": description,
            "tags": [
                "Mini-Kuzai",
                "THE KUZ NETWORK",
                "LLM From Scratch",
                "Local AI",
                step,
            ],
            "publication_mode": "public",
        },
    }


def write_brief(path: Path, brief: dict) -> None:
    if path.exists() or path.is_symlink():
        fail(f"Output already exists: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            brief,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )


def validate_generated(path: Path, mini_root: Path) -> None:
    if not PYTHON.is_file():
        fail("Project Python environment unavailable")
    if VALIDATOR.is_symlink() or not VALIDATOR.is_file():
        fail("Brief validator unavailable")

    result = run(
        [
            str(PYTHON),
            str(VALIDATOR),
            "--brief",
            str(path),
            "--mini-kuzai-root",
            str(mini_root),
        ],
        cwd=ROOT,
        timeout=120,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        try:
            path.unlink()
        except OSError:
            pass
        fail(
            "Generated brief failed validation"
            + (f": {detail}" if detail else "")
        )

    if "BRIEF_VALIDATION=PASS" not in result.stdout.splitlines():
        try:
            path.unlink()
        except OSError:
            pass
        fail("Brief validator did not report PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", required=True)
    parser.add_argument(
        "--mini-kuzai-root",
        type=Path,
        default=DEFAULT_MINI_KUZAI,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output path. Defaults to "
            "automation/dev-flow/short-briefs/Vxx-final.json"
        ),
    )
    args = parser.parse_args()

    if STEP_RE.fullmatch(args.step) is None:
        fail("Invalid step")

    verify_repo(ROOT)
    verify_repo(args.mini_kuzai_root)

    receipt, request, report, source_commit = validate_provenance(
        args.step,
        args.mini_kuzai_root,
    )

    brief = build_brief(
        args.step,
        receipt,
        request,
        report,
        source_commit,
    )

    output = (
        args.output.resolve()
        if args.output is not None
        else BRIEF_DIR / f"{args.step}-final.json"
    )

    write_brief(output, brief)
    validate_generated(output, args.mini_kuzai_root)

    try:
        relative_output = output.relative_to(ROOT).as_posix()
    except ValueError:
        relative_output = str(output)

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print("BRIEF_GENERATOR=PASS")
    print(f"STEP={args.step}")
    print(f"OUTPUT={relative_output}")
    print(f"SOURCE_COMMIT={source_commit}")
    print(f"REPORT_STEP_ID={report['step_id']}")
    print("SEGMENT_COUNT=5")
    print("TIMELINE_SECONDS=60")
    print("TRAINING_ALLOWED=0")
    print("BLIND_ACCESS=0")
    print("PUBLICATION_PERFORMED=0")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BriefGeneratorError as exc:
        print("##### SECTION RESULTS FOR ASSISTANT ######")
        print("BRIEF_GENERATOR=BLOCKED")
        print(f"ERROR={exc}")
        raise SystemExit(1)
