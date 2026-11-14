#!/usr/bin/env python3
"""Production reconciler for the Mini-Kuzai FINAL media flow.

For V83+ one service invocation may advance the complete idempotent chain:

FINAL receipt -> Short brief -> YouTube -> LinkedIn native video ->
GitHub media fallback -> committed cross-channel receipt -> GOGIT closure.

The loop is deliberately bounded. It retries only known state transitions whose
publishers are independently idempotent. Unknown failures stop the service.
The scientific Mini-Kuzai FINAL remains authoritative and independent.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"
SHORT_WORKER = ROOT / "tools" / "dev_flow_short_worker.py"
ORCHESTRATOR = ROOT / "tools" / "cross_channel_media_orchestrator.py"
CLOSURE_AUDIT = ROOT / "tools" / "final_dev_flow_closure_audit.py"
GOGIT = ROOT / "tools" / "gogit_publish.py"
JOURNAL = Path(
    "/root/.local/state/mini-kuzai-youtube/dev-flow-short-worker.json"
)
RECEIPT_DIR = ROOT / "automation" / "publication-receipts"
GOGIT_HISTORY_DIR = ROOT / "reports" / "assistant-results" / "history"

STEP_RE = re.compile(r"V([0-9]+)\Z")
RECEIPT_RE = re.compile(r"(V([0-9]+))-final\.json\Z")
MAX_RECONCILE_PASSES = 8
AUTO_CLOSURE_MIN_VERSION = 83


class MediaFlowWorkerError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise MediaFlowWorkerError(message)


def run(
    args: list[str],
    *,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaFlowWorkerError(
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
        raise MediaFlowWorkerError(f"{label} is invalid JSON") from exc
    if not isinstance(data, dict):
        fail(f"{label} must be a JSON object")
    return data


def load_journal(path: Path) -> dict:
    if path.is_symlink():
        fail("Worker journal is unsafe")
    if not path.exists():
        return {"schema_version": 1, "steps": {}}

    data = load_json(path, "Worker journal")
    if data.get("schema_version") != 1:
        fail("Unsupported worker journal schema")
    if not isinstance(data.get("steps"), dict):
        fail("Worker journal steps missing")
    return data


def downstream_candidates(
    journal_path: Path,
    receipt_dir: Path,
) -> list[str]:
    journal = load_journal(journal_path)
    found: list[tuple[int, str]] = []

    for step, row in journal["steps"].items():
        match = STEP_RE.fullmatch(step)
        if match is None:
            continue

        version = int(match.group(1))
        if version < 81:
            continue
        if not isinstance(row, dict):
            fail(f"Invalid worker journal row for {step}")
        if row.get("status") != "PUBLIC_PUBLISHED":
            continue

        receipt = receipt_dir / f"{step}-final.json"
        if receipt.exists() or receipt.is_symlink():
            continue

        found.append((version, step))

    return [step for _, step in sorted(found)]


def closure_step_id(step: str) -> str:
    return f"{step}-FINAL-DEV-FLOW-AUTO-VERIFY-001"


def closure_report_path(step: str, history_dir: Path) -> Path:
    return history_dir / f"{closure_step_id(step)}.json"


def closure_verified(step: str, history_dir: Path) -> bool:
    path = closure_report_path(step, history_dir)
    if not path.exists():
        return False

    report = load_json(path, "FINAL closure GOGIT")
    results = report.get("results")
    if (
        report.get("schema_version") != 1
        or report.get("step_id") != closure_step_id(step)
        or not isinstance(results, dict)
        or results.get("FINAL_FLOW") != "PASS"
        or results.get("MEDIA_RECEIPT") != "PASS"
    ):
        fail(f"Existing FINAL closure GOGIT is invalid for {step}")
    return True


def closure_candidates(
    receipt_dir: Path,
    history_dir: Path,
) -> list[str]:
    if not receipt_dir.exists():
        return []
    if receipt_dir.is_symlink() or not receipt_dir.is_dir():
        fail("Publication receipt directory is unsafe")

    found: list[tuple[int, str]] = []
    for path in receipt_dir.glob("V*-final.json"):
        match = RECEIPT_RE.fullmatch(path.name)
        if match is None:
            continue
        step = match.group(1)
        version = int(match.group(2))
        if version < AUTO_CLOSURE_MIN_VERSION:
            continue
        if path.is_symlink() or not path.is_file():
            fail(f"Unsafe publication receipt for {step}")
        if not closure_verified(step, history_dir):
            found.append((version, step))

    return [step for _, step in sorted(found)]


def run_short_worker() -> dict[str, str]:
    if not PYTHON.is_file():
        fail("Project Python unavailable")
    if SHORT_WORKER.is_symlink() or not SHORT_WORKER.is_file():
        fail("Short worker unavailable")

    result = run(
        [str(PYTHON), str(SHORT_WORKER)],
        timeout=1200,
    )
    values = parse_results(result.stdout)

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise MediaFlowWorkerError(
            "Short worker failed"
            + (f": {detail}" if detail else "")
        )

    worker = values.get("WORKER", "")
    if worker not in {"BRIEF_GENERATED", "PASS", "IDLE"}:
        fail("Short worker returned an unexpected state")

    return values


def run_downstream(
    step: str,
    *,
    journal_path: Path,
    publish: bool,
) -> dict[str, str]:
    if ORCHESTRATOR.is_symlink() or not ORCHESTRATOR.is_file():
        fail("Cross-channel orchestrator unavailable")

    args = [
        str(PYTHON),
        str(ORCHESTRATOR),
        "--step",
        step,
        "--journal",
        str(journal_path),
    ]

    env = None
    if publish:
        args.append("--publish")
        env = os.environ.copy()
        env["KUZAI_CROSS_CHANNEL_MEDIA_ENABLED"] = "YES"

    result = run(args, timeout=900, env=env)
    values = parse_results(result.stdout)

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise MediaFlowWorkerError(
            "Cross-channel orchestrator failed"
            + (f": {detail}" if detail else "")
        )

    state = values.get("MEDIA_ORCHESTRATOR", "")
    if publish:
        if state != "PASS":
            fail("Cross-channel live orchestration did not report PASS")
        if values.get("RECEIPT_COMMITTED") != "1":
            fail("Cross-channel publication returned no committed receipt")
    elif state not in {"DRY_RUN_PASS", "PASS"}:
        fail("Cross-channel preflight did not report PASS")

    return values


def run_closure_gogit(
    step: str,
    *,
    journal_path: Path,
    history_dir: Path,
) -> dict[str, str]:
    if closure_verified(step, history_dir):
        return {"STATE": "ALREADY_VERIFIED"}

    for tool in (CLOSURE_AUDIT, GOGIT):
        if tool.is_symlink() or not tool.is_file():
            fail(f"Closure tool unavailable: {tool.name}")

    audit = run(
        [
            str(PYTHON),
            str(CLOSURE_AUDIT),
            "--step",
            step,
            "--journal",
            str(journal_path),
        ],
        timeout=360,
    )
    audit_values = parse_results(audit.stdout)
    if audit.returncode != 0 or audit_values.get("FINAL_FLOW") != "PASS":
        fail("FINAL closure audit did not report PASS")

    fd, temporary = tempfile.mkstemp(
        prefix=f".{step.lower()}-final-closure-",
        suffix=".txt",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(audit.stdout)
            if not audit.stdout.endswith("\n"):
                handle.write("\n")

        gogit = run(
            [
                str(PYTHON),
                str(GOGIT),
                "--step",
                closure_step_id(step),
                "--input",
                temporary,
            ],
            timeout=180,
        )
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

    values = parse_results(gogit.stdout)
    if gogit.returncode != 0 or values.get("GOGIT") != "READY":
        fail("Automatic FINAL closure GOGIT failed")
    if not closure_verified(step, history_dir):
        fail("Automatic FINAL closure GOGIT verification failed")

    return {
        "STATE": "PUBLISHED",
        "GOGIT_COMMIT": values.get("COMMIT", ""),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path, default=JOURNAL)
    parser.add_argument("--receipt-dir", type=Path, default=RECEIPT_DIR)
    parser.add_argument(
        "--gogit-history-dir",
        type=Path,
        default=GOGIT_HISTORY_DIR,
        help="Tests only when overridden.",
    )
    parser.add_argument(
        "--skip-short-worker",
        action="store_true",
        help="Tests only.",
    )
    args = parser.parse_args()

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print("MEDIA_FLOW_WORKER=START")
    print(f"RECONCILE_LIMIT={MAX_RECONCILE_PASSES}")

    live = os.environ.get("KUZAI_CROSS_CHANNEL_MEDIA_ENABLED") == "YES"
    completed_step: str | None = None
    last_stage = "IDLE"
    publication_performed = False

    for pass_number in range(1, MAX_RECONCILE_PASSES + 1):
        progressed = False

        if not args.skip_short_worker:
            short = run_short_worker()
            short_state = short.get("WORKER", "")
            print(f"PASS_{pass_number}_SHORT={short_state}")

            if short_state == "BRIEF_GENERATED":
                last_stage = "BRIEF_GENERATED"
                progressed = True
                continue

            if short.get("PROCESSED") == "1":
                last_stage = "YOUTUBE_PUBLISHED"
                publication_performed = True
                progressed = True
                continue

        candidates = downstream_candidates(args.journal, args.receipt_dir)
        print(f"PASS_{pass_number}_DOWNSTREAM={len(candidates)}")
        if candidates:
            step = candidates[0]
            values = run_downstream(
                step,
                journal_path=args.journal,
                publish=live,
            )
            print(f"DOWNSTREAM_STEP={step}")
            print(f"DOWNSTREAM_LIVE={int(live)}")

            if not live:
                print("MEDIA_FLOW_STAGE=CROSS_CHANNEL_PREFLIGHT")
                print("PUBLICATION_PERFORMED=0")
                print("MEDIA_FLOW_WORKER=PASS")
                return 0

            completed_step = step
            last_stage = "CROSS_CHANNEL_PUBLISHED"
            publication_performed = True
            progressed = True
            if "RECEIPT_COMMIT" in values:
                print(f"RECEIPT_COMMIT={values['RECEIPT_COMMIT']}")
            continue

        closures = closure_candidates(
            args.receipt_dir,
            args.gogit_history_dir,
        )
        print(f"PASS_{pass_number}_CLOSURES={len(closures)}")
        if closures:
            step = closures[0]
            result = run_closure_gogit(
                step,
                journal_path=args.journal,
                history_dir=args.gogit_history_dir,
            )
            completed_step = step
            last_stage = "GOGIT_VERIFIED"
            progressed = result.get("STATE") == "PUBLISHED"
            if "GOGIT_COMMIT" in result:
                print(f"GOGIT_COMMIT={result['GOGIT_COMMIT']}")
            if progressed:
                continue

        if not progressed:
            if completed_step and closure_verified(
                completed_step,
                args.gogit_history_dir,
            ):
                print("MEDIA_FLOW_STAGE=FINAL_CLOSED_GOGIT")
                print(f"FINAL_STEP={completed_step}")
                print("FINAL_FLOW_CLOSED=1")
            else:
                print(f"MEDIA_FLOW_STAGE={last_stage}")
                print("FINAL_FLOW_CLOSED=0")
            print(f"PUBLICATION_PERFORMED={int(publication_performed)}")
            print(f"RECONCILE_PASSES={pass_number}")
            print("MEDIA_FLOW_WORKER=PASS")
            return 0

    fail("Bounded FINAL media reconciliation limit exceeded")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MediaFlowWorkerError as exc:
        print("##### SECTION RESULTS FOR ASSISTANT ######")
        print("MEDIA_FLOW_WORKER=BLOCKED")
        print(f"ERROR={exc}")
        raise SystemExit(1)
