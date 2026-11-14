#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR = ROOT / "tools" / "cross_channel_media_orchestrator.py"

spec = importlib.util.spec_from_file_location(
    "cross_channel_media_orchestrator",
    ORCHESTRATOR,
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class CrossChannelMediaOrchestratorTests(unittest.TestCase):

    def test_linkedin_preflight_contract(self):
        values = {
            "HANDOFF_PREFLIGHT": "PASS",
            "PUBLICATION_PERFORMED": "0",
        }
        self.assertEqual(
            module.require_linkedin(values, publish=False),
            {},
        )

    def test_linkedin_live_contract(self):
        values = {
            "HANDOFF_PREFLIGHT": "PASS",
            "HANDOFF": "PASS",
            "LINKEDIN_VIDEO_URN": "urn:li:video:ABC_def-123",
            "LINKEDIN_POST_URN": "urn:li:ugcPost:123456789",
        }
        result = module.require_linkedin(values, publish=True)
        self.assertEqual(
            result["video_urn"],
            "urn:li:video:ABC_def-123",
        )
        self.assertEqual(
            result["post_urn"],
            "urn:li:ugcPost:123456789",
        )

    def test_github_preflight_contract(self):
        values = {
            "GITHUB_MEDIA_PREFLIGHT": "PASS",
            "MEDIA_MODE": "YOUTUBE_PUBLIC_LINK_FALLBACK",
            "PUBLICATION_STATE": "READY_TO_COMMENT",
            "DISCUSSION_URL": (
                "https://github.com/Kusanagi8200/"
                "Mini-Kuzai/discussions/81"
            ),
            "PUBLICATION_PERFORMED": "0",
        }
        result = module.require_github(values, publish=False)
        self.assertEqual(
            result["discussion_url"],
            values["DISCUSSION_URL"],
        )

    def test_child_propagates_journal(self):
        journal = Path("/tmp/test-journal.json")
        fake = type(
            "Result",
            (),
            {
                "returncode": 0,
                "stdout": (
                    "HANDOFF_PREFLIGHT=PASS\n"
                    "PUBLICATION_PERFORMED=0\n"
                ),
                "stderr": "",
            },
        )()

        with patch.object(module, "run", return_value=fake) as mocked:
            values = module.child(
                module.LINKEDIN,
                "V81",
                journal_path=journal,
                publish=False,
            )

        called_args = mocked.call_args.args[0]
        self.assertIn("--journal", called_args)
        index = called_args.index("--journal")
        self.assertEqual(called_args[index + 1], str(journal))
        self.assertEqual(values["HANDOFF_PREFLIGHT"], "PASS")

    def test_receipt_preserves_scientific_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_dir = module.RECEIPT_DIR
            module.RECEIPT_DIR = Path(tmp)
            self.addCleanup(setattr, module, "RECEIPT_DIR", old_dir)

            state = {
                "scientific_final_receipt": (
                    "automation/dev-flow/receipts/V81-final.json"
                ),
                "scientific_source_commit": "a" * 40,
                "scientific_gogit_report": (
                    "reports/assistant-results/history/"
                    "PHASE03-SMOLTALK-V81-TEST-001.json"
                ),
                "brief_path": (
                    "automation/dev-flow/short-briefs/V81-final.json"
                ),
                "brief_sha256": "b" * 64,
                "video_sha256": "c" * 64,
                "youtube_video_id": "AbCdEf12345",
            }
            linkedin = {
                "video_urn": "urn:li:video:ABC_def-123",
                "post_urn": "urn:li:ugcPost:123456789",
            }
            github = {
                "discussion_url": (
                    "https://github.com/Kusanagi8200/"
                    "Mini-Kuzai/discussions/81"
                ),
                "comment_url": (
                    "https://github.com/Kusanagi8200/"
                    "Mini-Kuzai/discussions/81"
                    "#discussioncomment-123456"
                ),
            }

            path = module.write_receipt(
                "V81",
                state,
                linkedin,
                github,
            )
            data = json.loads(path.read_text(encoding="utf-8"))

        boundary = data["scientific_boundary"]
        self.assertFalse(boundary["media_is_scientific_evidence"])
        self.assertFalse(boundary["training_authorized"])
        self.assertFalse(boundary["blind_access_authorized"])
        self.assertEqual(data["youtube"]["status"], "PUBLIC")
        self.assertEqual(data["linkedin"]["status"], "PUBLISHED")
        self.assertEqual(data["github"]["status"], "PUBLISHED")


if __name__ == "__main__":
    unittest.main()
