#!/usr/bin/env python3
"""Build the non-scientific FLOW-PRESENTATION-001 media package.

This tool renders and audits the presentation video only.
It never publishes to YouTube, LinkedIn or GitHub.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "flow-presentation-001.json"
RENDERER = ROOT / "app" / "render_short.py"
NARRATOR = ROOT / "app" / "generate_narration.py"
MIXER = ROOT / "app" / "mix_audio.py"
MEDIA_AUDIT = ROOT / "tools" / "audits" / "step04_final_media_check.py"


class FlowPresentationError(RuntimeError):
    pass


def run(args: list[str], *, timeout: int = 900) -> str:
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
        raise FlowPresentationError(
            f"Command failed: {Path(args[0]).name}"
            + (f" -- {detail}" if detail else "")
        )
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_config(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise FlowPresentationError("Presentation config missing or unsafe")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise FlowPresentationError("Unsupported presentation schema")
    if data.get("publication_id") != "FLOW-PRESENTATION-001":
        raise FlowPresentationError("Unexpected publication ID")
    if data.get("purpose") != "NON_SCIENTIFIC_PUBLICATION_FLOW_TEST":
        raise FlowPresentationError("Presentation purpose is not non-scientific")
    timeline = data.get("timeline")
    if not isinstance(timeline, dict):
        raise FlowPresentationError("Timeline missing")
    segments = timeline.get("segments")
    if timeline.get("duration_seconds") != 60 or not isinstance(segments, list):
        raise FlowPresentationError("Invalid 60-second timeline")
    if len(segments) != 5:
        raise FlowPresentationError("Presentation requires exactly five segments")
    if sum(item.get("duration_seconds", 0) for item in segments) != 60:
        raise FlowPresentationError("Timeline segment total is not 60 seconds")
    narration = data.get("narration")
    if not isinstance(narration, str) or len(narration.strip()) < 200:
        raise FlowPresentationError("Narration is missing or too short")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--prefix",
        default="flow-presentation-001",
        help="Work-file prefix",
    )
    args = parser.parse_args()

    data = load_config(args.config)
    work = ROOT / "work"
    work.mkdir(parents=True, exist_ok=True)

    prefix = work / args.prefix
    timeline = prefix.with_name(prefix.name + "-timeline.json")
    narration_txt = prefix.with_name(prefix.name + "-narration.txt")
    visual = prefix.with_name(prefix.name + "-visual.mp4")
    narration_wav = prefix.with_name(prefix.name + "-narration.wav")
    final_video = prefix.with_name(prefix.name + "-final.mp4")
    mix_metadata = prefix.with_name(prefix.name + "-mix.json")
    media_manifest = prefix.with_name(prefix.name + "-media.json")

    timeline.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": data["publication_id"],
                "test_only": True,
                "duration_seconds": data["timeline"]["duration_seconds"],
                "segments": data["timeline"]["segments"],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    narration_txt.write_text(
        data["narration"].strip() + "\n",
        encoding="utf-8",
    )

    render_output = run([
        sys.executable,
        str(RENDERER),
        "--timeline",
        str(timeline),
        "--output",
        str(visual),
    ])
    narration_output = run([
        sys.executable,
        str(NARRATOR),
        "--text-file",
        str(narration_txt),
        "--output",
        str(narration_wav),
    ])
    mix_output = run([
        sys.executable,
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
        sys.executable,
        str(MEDIA_AUDIT),
        str(final_video),
        "--mix-metadata",
        str(mix_metadata),
    ])

    if "STEP_STATUS=PASS" not in audit_output:
        raise FlowPresentationError("Final media audit did not report PASS")

    metadata = json.loads(mix_metadata.read_text(encoding="utf-8"))
    digest = sha256_file(final_video)

    manifest = {
        "schema_version": 1,
        "publication_id": data["publication_id"],
        "purpose": data["purpose"],
        "media": {
            "path": str(final_video),
            "sha256": digest,
            "duration_ms": 60000,
            "voice_start_ms": metadata["voice_start_ms"],
            "voice_end_ms": metadata["voice_end_ms"],
            "voice_window_ms": metadata["voice_window_ms"],
            "narration_source_duration_ms": metadata[
                "narration_source_duration_ms"
            ],
            "narration_speed_factor": metadata["narration_speed_factor"],
        },
        "youtube": data["youtube"],
        "linkedin": data["linkedin"],
        "github": data["github"],
        "publication": {
            "youtube": "NOT_STARTED",
            "linkedin": "NOT_STARTED",
            "github": "NOT_STARTED",
        },
    }
    media_manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("##### SECTION RESULTS FOR ASSISTANT ######")
    print("FLOW_PRESENTATION_BUILD=PASS")
    print(f"PUBLICATION_ID={data['publication_id']}")
    print("PURPOSE=NON_SCIENTIFIC_PUBLICATION_FLOW_TEST")
    print("PUBLICATION_PERFORMED=0")
    print(f"FINAL_VIDEO={final_video}")
    print(f"VIDEO_SHA256={digest}")
    print(f"MEDIA_MANIFEST={media_manifest}")
    print(f"VOICE_START_MS={metadata['voice_start_ms']}")
    print(f"VOICE_END_MS={metadata['voice_end_ms']}")
    print(f"VOICE_WINDOW_MS={metadata['voice_window_ms']}")
    print(
        "NARRATION_SOURCE_DURATION_MS="
        + str(metadata["narration_source_duration_ms"])
    )
    print(
        "NARRATION_SPEED_FACTOR="
        + str(metadata["narration_speed_factor"])
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        FlowPresentationError,
        subprocess.TimeoutExpired,
        json.JSONDecodeError,
        OSError,
    ) as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
