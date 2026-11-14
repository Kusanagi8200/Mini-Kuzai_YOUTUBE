#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "tools" / "linkedin_video_handoff.py"

spec = importlib.util.spec_from_file_location(
    "linkedin_video_handoff",
    HANDOFF,
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class LinkedInVideoHandoffTests(unittest.TestCase):

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.temp_root = Path(self.temporary.name)
        self.original_root = module.ROOT
        module.ROOT = self.temp_root
        self.addCleanup(self.restore_root)

    def restore_root(self):
        module.ROOT = self.original_root

    def write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )

    def fixture(self):
        video = self.temp_root / "work" / "worker-v81-final.mp4"
        video.parent.mkdir(parents=True)
        video.write_bytes(b"verified-video")
        digest = hashlib.sha256(video.read_bytes()).hexdigest()

        brief = (
            self.temp_root
            / "automation"
            / "dev-flow"
            / "short-briefs"
            / "V81-final.json"
        )
        self.write_json(
            brief,
            {
                "schema_version": 1,
                "step": "V81",
                "video_id": "VIDEO-V81-FINAL",
                "youtube": {
                    "title": "MINI-KUZAI V81 // TEST CONTROL",
                    "description": (
                        "Mini-Kuzai V81 deterministic media summary.\n\n"
                        "BUILD LOCAL. KEEP CONTROL. OWN THE STACK."
                    ),
                },
            },
        )

        journal = self.temp_root / "journal.json"
        self.write_json(
            journal,
            {
                "schema_version": 1,
                "steps": {
                    "V81": {
                        "status": "PUBLIC_PUBLISHED",
                        "video_sha256": digest,
                        "youtube_video_id": "AbCdEf12345",
                        "final_video_path": "work/worker-v81-final.mp4",
                    }
                },
            },
        )

        return video, brief, journal, digest

    def test_validate_local_state(self):
        _video, brief, journal, digest = self.fixture()

        with patch.object(
            module,
            "run",
            return_value=type("R", (), {
                "returncode": 0,
                "stdout": "",
                "stderr": "",
            })(),
        ), patch.object(
            module,
            "git",
            return_value=brief.read_text(encoding="utf-8").rstrip("\n"),
        ):
            state = module.validate_local_state("V81", journal)

        self.assertEqual(state["video_sha256"], digest)
        self.assertEqual(state["youtube_video_id"], "AbCdEf12345")
        self.assertEqual(state["publication_id"], "MINI-KUZAI-V81-FINAL")
        self.assertIn("FLOW V81 OK", state["linkedin_text"])

    def test_sha_mismatch_is_blocked(self):
        _video, brief, journal, _digest = self.fixture()
        data = json.loads(journal.read_text(encoding="utf-8"))
        data["steps"]["V81"]["video_sha256"] = "a" * 64
        self.write_json(journal, data)

        with patch.object(
            module,
            "run",
            return_value=type("R", (), {
                "returncode": 0,
                "stdout": "",
                "stderr": "",
            })(),
        ), patch.object(
            module,
            "git",
            return_value=brief.read_text(encoding="utf-8").rstrip("\n"),
        ):
            with self.assertRaises(module.HandoffError):
                module.validate_local_state("V81", journal)

    def test_live_gate_blocks_by_default(self):
        state = {
            "publication_id": "MINI-KUZAI-V81-FINAL",
            "video_sha256": "a" * 64,
        }
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(module.HandoffError):
                module.publish(
                    "V81",
                    state,
                    host="83.228.192.116",
                    key=Path("/nonexistent"),
                    remote_root="/opt/kuz-din",
                    remote_media_root="/var/lib/kuz-din/mini-kuzai-media",
                )


if __name__ == "__main__":
    unittest.main()
