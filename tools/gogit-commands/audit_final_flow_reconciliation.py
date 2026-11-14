#!/usr/bin/env python3
"""Safe aggregate audit for the V83+ FINAL publication reconciler."""

from __future__ import annotations

import py_compile
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = (
    ROOT / "tools" / "dev_flow_media_worker.py",
    ROOT / "tools" / "final_dev_flow_closure_audit.py",
    ROOT / "tools" / "linkedin_video_handoff.py",
    ROOT / "tools" / "generate_dev_flow_short_brief.py",
    ROOT / "tools" / "cross_channel_media_orchestrator.py",
)
PATTERNS = (
    "test_dev_flow_media_worker.py",
    "test_final_dev_flow_closure_audit.py",
    "test_linkedin_video_handoff.py",
    "test_generate_dev_flow_short_brief.py",
    "test_cross_channel_media_orchestrator.py",
    "test_dev_flow_short_worker.py",
    "test_github_media_fallback.py",
)


def run_pattern(pattern: str) -> tuple[int, int, int, bool]:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            pattern,
            "-v",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=240,
    )
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    match = re.search(r"Ran\s+([0-9]+)\s+tests?", output)
    total = int(match.group(1)) if match else 0
    failures = len(re.findall(r"^FAIL:", output, flags=re.M))
    errors = len(re.findall(r"^ERROR:", output, flags=re.M))
    return total, failures, errors, proc.returncode == 0 and total > 0


def main() -> None:
    compile_pass = 1
    for path in FILES:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError:
            compile_pass = 0

    tests = failures = errors = 0
    test_pass = 1
    for pattern in PATTERNS:
        count, fail_count, error_count, ok = run_pattern(pattern)
        tests += count
        failures += fail_count
        errors += error_count
        if not ok:
            test_pass = 0

    worker = (ROOT / "tools" / "dev_flow_media_worker.py").read_text(
        encoding="utf-8"
    )
    handoff = (ROOT / "tools" / "linkedin_video_handoff.py").read_text(
        encoding="utf-8"
    )
    generator = (ROOT / "tools" / "generate_dev_flow_short_brief.py").read_text(
        encoding="utf-8"
    )
    service = (ROOT / "deploy" / "systemd" / "mini-kuzai-youtube-final.service").read_text(
        encoding="utf-8"
    )

    bounded = int(
        "MAX_RECONCILE_PASSES = 8" in worker
        and "AUTO_CLOSURE_MIN_VERSION = 83" in worker
    )
    auto_gogit = int(
        "run_closure_gogit" in worker
        and "FINAL-DEV-FLOW-AUTO-VERIFY-001" in worker
    )
    safe_sync = int(
        "git merge-base --is-ancestor" in handoff
        and "backup/auto-media-pre-sync-" in handoff
        and "git merge --ff-only" in handoff
    )
    adaptive_voice = int(
        "fit_narration_to_voice_window" in generator
        and "measure_narration_seconds" in generator
    )
    timeout_aligned = int("TimeoutStartSec=30min" in service)

    audit_pass = int(
        compile_pass
        and test_pass
        and failures == 0
        and errors == 0
        and bounded
        and auto_gogit
        and safe_sync
        and adaptive_voice
        and timeout_aligned
    )

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print(f"AUDIT_PASS={audit_pass}")
    print(f"COMPILE_PASS={compile_pass}")
    print(f"TEST_PASS={test_pass}")
    print(f"TESTS_RUN={tests}")
    print(f"TEST_FAILURES={failures}")
    print(f"TEST_ERRORS={errors}")
    print(f"BOUNDED_RECONCILIATION={bounded}")
    print(f"AUTO_GOGIT_CLOSURE={auto_gogit}")
    print(f"SAFE_KUZDIN_SYNC={safe_sync}")
    print(f"ADAPTIVE_VOICE_TIMING={adaptive_voice}")
    print(f"SYSTEMD_TIMEOUT_ALIGNED={timeout_aligned}")
    print("PUBLICATION_PERFORMED=0")


if __name__ == "__main__":
    main()
