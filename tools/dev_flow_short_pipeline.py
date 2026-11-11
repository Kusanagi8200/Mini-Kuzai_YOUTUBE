#!/usr/bin/env python3
"""Run the validated Mini-Kuzai FINAL-DEV-FLOW YouTube Short pipeline.

Current STEP-07 implementation is intentionally publication-disabled:
- validate Short brief and FINAL provenance
- render canonical V8 video
- generate Piper narration
- mix canonical audio
- audit final media
- run YouTube uploader preflight
- never upload media
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_dev_flow_short_brief.py"
RENDERER = ROOT / "app" / "render_short.py"
NARRATOR = ROOT / "app" / "generate_narration.py"
MIXER = ROOT / "app" / "mix_audio.py"
MEDIA_AUDIT = ROOT / "tools" / "audits" / "step04_final_media_check.py"
UPLOADER = ROOT / "app" / "youtube_upload.py"
PYTHON = ROOT / ".venv" / "bin" / "python"
WORK = ROOT / "work"


class PipelineError(RuntimeError):
    pass


def run(args: list[str], *, timeout: int = 300) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise PipelineError(
            f"Command failed: {Path(args[0]).name}"
            + (f" -- {detail}" if detail else "")
        )

    return result.stdout.strip()


def parse_results(output: str) -> dict[str, str]:
    values: dict[str, str] = {}

    for line in output.splitlines():
        if "=" not in line:
            continue

        key, value = line.split("=", 1)

        if re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            values[key] = value.strip()

    return values


def require(values: dict[str, str], key: str, expected: str) -> None:
    actual = values.get(key)

    if actual != expected:
        raise PipelineError(
            f"{key} expected {expected!r}, got {actual!r}"
        )


def load_brief(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise PipelineError("Short brief is missing or unsafe")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PipelineError("Short brief is invalid JSON") from exc

    if not isinstance(data, dict):
        raise PipelineError("Short brief must be a JSON object")

    return data


def materialize(brief: dict, prefix: Path) -> tuple[Path, Path]:
    timeline = {
        "schema_version": 1,
        "id": brief["video_id"],
        "test_only": True,
        "duration_seconds": brief["timeline"]["duration_seconds"],
        "segments": brief["timeline"]["segments"],
    }

    timeline_path = prefix.with_name(prefix.name + "-timeline.json")
    narration_path = prefix.with_name(prefix.name + "-narration.txt")

    timeline_path.write_text(
        json.dumps(timeline, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    narration_path.write_text(
        brief["narration"].strip() + "\n",
        encoding="utf-8",
    )

    return timeline_path, narration_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument(
        "--prefix",
        default=None,
        help="Work-file prefix. Defaults to step-derived name.",
    )
    args = parser.parse_args()

    if not PYTHON.is_file():
        raise PipelineError("Project Python environment is unavailable")

    brief_path = args.brief.resolve()
    brief = load_brief(brief_path)

    step = brief.get("step", "")
    if not re.fullmatch(r"V[0-9]+", step):
        raise PipelineError("Invalid Short step")

    WORK.mkdir(parents=True, exist_ok=True)

    prefix_name = args.prefix or f"step07-{step.lower()}-pipeline"
    if not re.fullmatch(r"[A-Za-z0-9._-]+", prefix_name):
        raise PipelineError("Unsafe work prefix")

    prefix = WORK / prefix_name

    validation_output = run([
        str(PYTHON),
        str(VALIDATOR),
        "--brief",
        str(brief_path),
    ])

    validation = parse_results(validation_output)
    require(validation, "BRIEF_VALIDATION", "PASS")

    timeline_path, narration_text_path = materialize(
        brief,
        prefix,
    )

    visual = prefix.with_name(prefix.name + "-visual.mp4")
    narration_wav = prefix.with_name(prefix.name + "-narration.wav")
    final_video = prefix.with_name(prefix.name + "-final.mp4")
    mix_metadata = prefix.with_name(prefix.name + "-mix.json")

    render_output = run([
        str(PYTHON),
        str(RENDERER),
        "--timeline",
        str(timeline_path),
        "--output",
        str(visual),
    ])

    render = parse_results(render_output)
    require(render, "DURATION_SECONDS", "60")

    narration_output = run([
        str(PYTHON),
        str(NARRATOR),
        "--text-file",
        str(narration_text_path),
        "--output",
        str(narration_wav),
    ])

    narration = parse_results(narration_output)

    if "DURATION_SECONDS" not in narration:
        raise PipelineError("Narration duration was not reported")

    run([
        str(PYTHON),
        str(MIXER),
        "--video",
        str(visual),
        "--narration",
        str(narration_wav),
        "--output",
        str(final_video),
        "--metadata",
        str(mix_metadata),
    ])

    audit_output = run([
        str(PYTHON),
        str(MEDIA_AUDIT),
        str(final_video),
        "--mix-metadata",
        str(mix_metadata),
    ])

    audit = parse_results(audit_output)
    require(audit, "STEP_STATUS", "PASS")
    require(audit, "DURATION_MS", "60000")

    youtube = brief["youtube"]

    upload_args = [
        str(PYTHON),
        str(UPLOADER),
        "--video",
        str(final_video),
        "--title",
        youtube["title"],
        "--description",
        youtube["description"],
    ]

    for tag in youtube["tags"]:
        upload_args.extend(["--tag", tag])

    # Deliberately no --execute in STEP-07 dry-run orchestrator.
    preflight_output = run(upload_args)
    preflight = parse_results(preflight_output)

    require(preflight, "PREFLIGHT", "PASS")
    require(preflight, "TARGET_CHANNEL_MATCH", "1")
    require(preflight, "UPLOAD_PERFORMED", "0")

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print("STEP_STATUS=PASS")
    print(f"SHORT_STEP={step}")
    print("BRIEF_VALIDATION=PASS")
    print("RENDER=PASS")
    print("NARRATION=PASS")
    print("AUDIO_MIX=PASS")
    print("MEDIA_AUDIT=PASS")
    print(f"DURATION_MS={audit['DURATION_MS']}")
    print(
        "NARRATION_SOURCE_DURATION_MS="
        + audit["NARRATION_SOURCE_DURATION_MS"]
    )
    print(
        "NARRATION_SPEED_FACTOR="
        + audit["NARRATION_SPEED_FACTOR"]
    )
    print("YOUTUBE_PREFLIGHT=PASS")
    print("TARGET_CHANNEL_MATCH=1")
    print(
        "DUPLICATE_SHA256="
        + preflight.get("DUPLICATE_SHA256", "")
    )
    print("UPLOAD_PERFORMED=0")
    print("PUBLICATION=DISABLED")
    print(f"FINAL_VIDEO={final_video}")
    print(f"VIDEO_SHA256={preflight['VIDEO_SHA256']}")
    print("PIPELINE_ORCHESTRATOR=PASS")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        PipelineError,
        subprocess.TimeoutExpired,
    ) as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
