#!/usr/bin/env python3
"""Production wrapper for the Mini-Kuzai FINAL media flow.

One bounded transaction per invocation:

1. Run the existing FINAL Short worker.
2. If it generated a brief, stop.
3. If it published a YouTube Short, stop.
4. If the Short worker is idle, find one V81+ YouTube-published step without a
   committed cross-channel receipt and run the downstream media orchestrator.

Default mode keeps downstream publication in preflight. Automatic live
LinkedIn/GitHub publication requires:
KUZAI_CROSS_CHANNEL_MEDIA_ENABLED=YES

The scientific Mini-Kuzai FINAL remains authoritative and independent.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python"
SHORT_WORKER = ROOT / "tools" / "dev_flow_short_worker.py"
ORCHESTRATOR = ROOT / "tools" / "cross_channel_media_orchestrator.py"
JOURNAL = Path(
    "/root/.local/state/mini-kuzai-youtube/dev-flow-short-worker.json"
)
RECEIPT_DIR = ROOT / "automation" / "publication-receipts"

STEP_RE = re.compile(r"V([0-9]+)\Z")


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


def load_journal(path: Path) -> dict:
    if path.is_symlink():
        fail("Worker journal is unsafe")
    if not path.exists():
        return {"schema_version": 1, "steps": {}}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise MediaFlowWorkerError("Worker journal is invalid JSON") from exc

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

    return [
        step
        for _, step in sorted(found, key=lambda item: item[0])
    ]


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

    result = run(
        args,
        timeout=900,
        env=env,
    )
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
    else:
        if state not in {"DRY_RUN_PASS", "PASS"}:
            fail("Cross-channel preflight did not report PASS")

    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path, default=JOURNAL)
    parser.add_argument(
        "--receipt-dir",
        type=Path,
        default=RECEIPT_DIR,
    )
    parser.add_argument(
        "--skip-short-worker",
        action="store_true",
        help="Tests only.",
    )
    args = parser.parse_args()

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print("MEDIA_FLOW_WORKER=START")

    if not args.skip_short_worker:
        short = run_short_worker()
        short_state = short.get("WORKER", "")
        print(f"SHORT_WORKER_STATE={short_state}")

        if short_state == "BRIEF_GENERATED":
            print("MEDIA_FLOW_STAGE=BRIEF_GENERATED")
            print("PUBLICATION_PERFORMED=0")
            print("MEDIA_FLOW_WORKER=PASS")
            return 0

        if short.get("PROCESSED") == "1":
            print("MEDIA_FLOW_STAGE=YOUTUBE_PUBLISHED")
            print("PUBLICATION_PERFORMED=1")
            print("MEDIA_FLOW_WORKER=PASS")
            return 0

        if short_state != "IDLE":
            # PASS with only already-verified historical briefs is equivalent
            # to idle for downstream selection.
            print("MEDIA_FLOW_STAGE=SHORT_WORKER_COMPLETE")

    candidates = downstream_candidates(
        args.journal,
        args.receipt_dir,
    )
    print(f"DOWNSTREAM_CANDIDATES={len(candidates)}")

    if not candidates:
        print("MEDIA_FLOW_STAGE=IDLE")
        print("PUBLICATION_PERFORMED=0")
        print("MEDIA_FLOW_WORKER=PASS")
        return 0

    step = candidates[0]
    live = os.environ.get("KUZAI_CROSS_CHANNEL_MEDIA_ENABLED") == "YES"

    values = run_downstream(
        step,
        journal_path=args.journal,
        publish=live,
    )

    print(f"DOWNSTREAM_STEP={step}")
    print(f"DOWNSTREAM_LIVE={int(live)}")

    if live:
        print("MEDIA_FLOW_STAGE=CROSS_CHANNEL_PUBLISHED")
        print("PUBLICATION_PERFORMED=1")
    else:
        print("MEDIA_FLOW_STAGE=CROSS_CHANNEL_PREFLIGHT")
        print("PUBLICATION_PERFORMED=0")

    if "RECEIPT_COMMIT" in values:
        print(f"RECEIPT_COMMIT={values['RECEIPT_COMMIT']}")

    print("MEDIA_FLOW_WORKER=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MediaFlowWorkerError as exc:
        print("##### SECTION RESULTS FOR ASSISTANT ######")
        print("MEDIA_FLOW_WORKER=BLOCKED")
        print(f"ERROR={exc}")
        raise SystemExit(1)
