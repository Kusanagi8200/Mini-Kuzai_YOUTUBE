#!/usr/bin/env python3
"""Validate a Mini-Kuzai FINAL-DEV-FLOW Short brief and its provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "config" / "dev-flow-short-brief.schema.json"
DEFAULT_MINI_KUZAI = Path("/root/GitHub-Mini-Kuzai/Mini-Kuzai")

sys.path.insert(0, str(ROOT / "app"))
from youtube_upload import normalize_description, validate_title  # noqa: E402


class BriefValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise BriefValidationError(message)


def read_json(path: Path, label: str) -> tuple[dict, str]:
    if path.is_symlink() or not path.is_file():
        fail(f"{label} is missing or unsafe")

    text = path.read_text(encoding="utf-8")

    try:
        data = json.loads(text)
    except (OSError, ValueError) as exc:
        raise BriefValidationError(f"{label} is not valid JSON") from exc

    if not isinstance(data, dict):
        fail(f"{label} must be a JSON object")

    return data, text


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    if check and result.returncode != 0:
        fail(f"Git command failed: {' '.join(args)}")

    return result.stdout


def ensure_committed(repo: Path, relative: str) -> str:
    path = repo / relative

    if path.is_symlink() or not path.is_file():
        fail(f"Source file missing or unsafe: {relative}")

    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        fail(f"Source file is not committed: {relative}")

    current = path.read_text(encoding="utf-8")
    committed = git(repo, "show", f"HEAD:{relative}")

    if current != committed:
        fail(f"Source file differs from committed HEAD: {relative}")

    return current


def ensure_commit(repo: Path, commit: str) -> None:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        fail("Source commit does not exist in Mini-Kuzai repository")


def ensure_source_snapshot(
    repo: Path,
    commit: str,
    relative: str,
    expected: str,
) -> None:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        fail(f"Source file absent from source commit: {relative}")

    if result.stdout != expected:
        fail(f"Source file changed after FINAL source commit: {relative}")


def validate_schema(brief: dict, schema_path: Path) -> None:
    schema, _ = read_json(schema_path, "Schema")

    Draft202012Validator.check_schema(schema)

    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(brief),
        key=lambda item: list(item.absolute_path),
    )

    if errors:
        error = errors[0]
        location = ".".join(str(item) for item in error.absolute_path)
        if not location:
            location = "<root>"
        fail(f"Schema validation failed at {location}: {error.message}")


def validate_brief(
    brief_path: Path,
    mini_kuzai_root: Path = DEFAULT_MINI_KUZAI,
    schema_path: Path = DEFAULT_SCHEMA,
) -> dict:
    brief, _ = read_json(brief_path, "Short brief")
    validate_schema(brief, schema_path)

    step = brief["step"]

    if brief["video_id"] != f"VIDEO-{step}-FINAL":
        fail("Video ID does not match step")

    source = brief["source"]

    expected_receipt = f"automation/dev-flow/receipts/{step}-final.json"
    expected_request = f"automation/dev-flow/requests/{step}-final.json"

    if source["final_receipt"] != expected_receipt:
        fail("FINAL receipt path does not match step")

    receipt_text = ensure_committed(
        mini_kuzai_root,
        source["final_receipt"],
    )
    request_text = ensure_committed(
        mini_kuzai_root,
        expected_request,
    )
    report_text = ensure_committed(
        mini_kuzai_root,
        source["gogit_report"],
    )

    receipt = json.loads(receipt_text)
    request = json.loads(request_text)
    report = json.loads(report_text)

    if receipt.get("schema_version") != 1:
        fail("Unsupported FINAL receipt schema")
    if receipt.get("command") != "FINAL-DEV-FLOW":
        fail("Receipt is not FINAL-DEV-FLOW")
    if receipt.get("step") != step:
        fail("Receipt step mismatch")
    if receipt.get("status") != "PUBLISHED":
        fail("FINAL receipt is not PUBLISHED")

    if request.get("schema_version") != 1:
        fail("Unsupported FINAL request schema")
    if request.get("command") != "FINAL-DEV-FLOW":
        fail("Request is not FINAL-DEV-FLOW")
    if request.get("step") != step:
        fail("Request step mismatch")
    if request.get("report") != source["gogit_report"]:
        fail("Brief GOGIT report does not match FINAL request")

    request_sha256 = hashlib.sha256(
        request_text.encode("utf-8")
    ).hexdigest()

    if receipt.get("request_sha256") != request_sha256:
        fail("FINAL request SHA256 does not match receipt")

    source_commit = source["source_commit"]

    if receipt.get("source_commit") != source_commit:
        fail("Brief source commit does not match FINAL receipt")

    if source.get("final_status") != receipt.get("status"):
        fail("Brief FINAL status does not match receipt")

    ensure_commit(mini_kuzai_root, source_commit)

    ensure_source_snapshot(
        mini_kuzai_root,
        source_commit,
        expected_request,
        request_text,
    )
    ensure_source_snapshot(
        mini_kuzai_root,
        source_commit,
        source["gogit_report"],
        report_text,
    )

    if report.get("project") != "Mini-Kuzai":
        fail("Unexpected GOGIT project")
    if report.get("phase") != "03":
        fail("Unexpected GOGIT phase")
    if report.get("status") != "PUBLIC_AGGREGATE_REVIEW_ONLY":
        fail("Unexpected GOGIT publication status")
    if report.get("private_conversation_data_included") is not False:
        fail("GOGIT report contains or does not explicitly exclude private data")

    step_id = report.get("step_id", "")
    if not isinstance(step_id, str):
        fail("Invalid GOGIT step ID")
    if not step_id.startswith(f"PHASE03-SMOLTALK-{step}-"):
        fail("GOGIT step ID does not match Short step")

    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        fail("GOGIT metrics are missing")

    if metrics.get(f"{step}_PASS") != 1:
        fail(f"{step}_PASS is not 1")

    if metrics.get("SEMANTIC_VALIDATION_COMPLETE") != 0:
        fail("Unexpected semantic validation state")

    if report.get("semantic_validation_complete") is not False:
        fail("Unexpected semantic validation metadata")

    blind_metrics = [
        value
        for name, value in metrics.items()
        if name.endswith("_BLIND_ACCESS")
    ]

    if not blind_metrics or any(value != 0 for value in blind_metrics):
        fail("BLIND access safety invariant failed")

    timeline = brief["timeline"]

    if timeline["duration_seconds"] != 60:
        fail("Timeline duration is not 60 seconds")

    if sum(item["duration_seconds"] for item in timeline["segments"]) != 60:
        fail("Timeline segment duration total is not 60 seconds")

    title = brief["youtube"]["title"]
    description = brief["youtube"]["description"]

    validate_title(title)

    normalized = normalize_description(description)
    if normalized != description:
        fail("YouTube description is not in canonical normalized form")

    if brief["youtube"]["publication_mode"] != "private":
        fail("Publication mode must remain private")

    return {
        "step": step,
        "video_id": brief["video_id"],
        "source_commit": source_commit,
        "report_step_id": step_id,
        "segment_count": len(timeline["segments"]),
        "timeline_seconds": timeline["duration_seconds"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument(
        "--mini-kuzai-root",
        type=Path,
        default=DEFAULT_MINI_KUZAI,
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
    )
    args = parser.parse_args()

    result = validate_brief(
        brief_path=args.brief,
        mini_kuzai_root=args.mini_kuzai_root,
        schema_path=args.schema,
    )

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print("BRIEF_VALIDATION=PASS")
    print(f"STEP={result['step']}")
    print(f"VIDEO_ID={result['video_id']}")
    print("FINAL_RECEIPT_CHECK=PASS")
    print("FINAL_REQUEST_CHECK=PASS")
    print("GOGIT_REPORT_CHECK=PASS")
    print("SOURCE_SNAPSHOT_CHECK=PASS")
    print("METADATA_POLICY=PASS")
    print(f"SEGMENT_COUNT={result['segment_count']}")
    print(f"TIMELINE_SECONDS={result['timeline_seconds']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BriefValidationError as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
