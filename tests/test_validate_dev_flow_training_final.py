#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "validate_dev_flow_short_brief.py"
SCHEMA = ROOT / "config" / "dev-flow-short-brief.schema.json"

spec = importlib.util.spec_from_file_location("brief_validator", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class TrainingFinalBriefValidatorTests(unittest.TestCase):

    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()

    def write_json(self, path: Path, data: dict) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=2, sort_keys=True) + "\n"
        path.write_text(text, encoding="utf-8")
        return text

    def fixture(self, *, closed: bool = True):
        temporary = tempfile.TemporaryDirectory()
        base = Path(temporary.name)
        repo = base / "Mini-Kuzai"
        repo.mkdir()

        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Mini-Kuzai Test")
        self.git(repo, "config", "user.email", "test@example.invalid")

        step = "V81"
        report_rel = (
            "reports/assistant-results/history/"
            "PHASE03-SMOLTALK-V81-FINAL-CLOSURE-001.json"
        )
        request_rel = "automation/dev-flow/requests/V81-final.json"
        receipt_rel = "automation/dev-flow/receipts/V81-final.json"

        report = {
            "project": "Mini-Kuzai",
            "phase": "03",
            "status": "PUBLIC_AGGREGATE_REVIEW_ONLY",
            "private_conversation_data_included": False,
            "semantic_validation_complete": False,
            "step_id": "PHASE03-SMOLTALK-V81-FINAL-CLOSURE-001",
            "metrics": {
                "SEMANTIC_VALIDATION_COMPLETE": 0,
                "TRAINING_AUTHORIZED": 0,
                "TRAINING_STARTED": 1,
                "V81_FINAL_PASS": 1,
                "V81_FINAL_BLIND_ACCESS": 0,
                "V81_FINAL_WINDOW_CLOSED": int(closed),
                "V81_FINAL_FURTHER_TRAINING_AUTHORIZED": 0,
            },
        }

        request = {
            "schema_version": 1,
            "command": "FINAL-DEV-FLOW",
            "step": step,
            "report": report_rel,
        }

        request_text = self.write_json(repo / request_rel, request)
        self.write_json(repo / report_rel, report)

        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "test FINAL source")
        source_commit = self.git(repo, "rev-parse", "HEAD")

        receipt = {
            "schema_version": 1,
            "command": "FINAL-DEV-FLOW",
            "step": step,
            "request_sha256": hashlib.sha256(
                request_text.encode("utf-8")
            ).hexdigest(),
            "source_commit": source_commit,
            "github_url": (
                "https://github.com/Kusanagi8200/Mini-Kuzai/"
                "discussions/13#discussioncomment-1"
            ),
            "published_at_utc": "2026-11-14T12:00:00+00:00",
            "status": "PUBLISHED",
        }

        self.write_json(repo / receipt_rel, receipt)
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "test FINAL receipt")

        brief = {
            "schema_version": 1,
            "step": step,
            "video_id": "VIDEO-V81-FINAL",
            "source": {
                "final_receipt": receipt_rel,
                "gogit_report": report_rel,
                "source_commit": source_commit,
                "final_status": "PUBLISHED",
            },
            "timeline": {
                "duration_seconds": 60,
                "segments": [
                    {
                        "duration_seconds": 12,
                        "badge": step,
                        "headline": f"TEST {index}",
                        "body": "VALIDATED FINAL TRAINING RESULT",
                    }
                    for index in range(1, 6)
                ],
            },
            "narration": (
                "Mini-Kuzai V81 completed a bounded training continuation. "
                "The training window is closed and no further training is "
                "authorized. BLIND evaluation remains closed."
            ),
            "youtube": {
                "title": "MINI-KUZAI V81 // FINAL CLOSURE REVIEW",
                "description": (
                    "Mini-Kuzai V81 final closure review.\n\n"
                    "BUILD LOCAL. KEEP CONTROL. OWN THE STACK."
                ),
                "tags": [
                    "Mini-Kuzai",
                    "THE KUZ NETWORK",
                    "LLM From Scratch",
                ],
                "publication_mode": "public",
            },
        }

        brief_path = base / "brief.json"
        self.write_json(brief_path, brief)

        return temporary, repo, brief_path

    def test_closed_training_final_is_valid(self):
        temporary, repo, brief_path = self.fixture(closed=True)
        self.addCleanup(temporary.cleanup)

        result = module.validate_brief(
            brief_path,
            mini_kuzai_root=repo,
            schema_path=SCHEMA,
        )

        self.assertEqual(result["step"], "V81")
        self.assertEqual(result["timeline_seconds"], 60)

    def test_open_training_final_is_rejected(self):
        temporary, repo, brief_path = self.fixture(closed=False)
        self.addCleanup(temporary.cleanup)

        with self.assertRaises(module.BriefValidationError):
            module.validate_brief(
                brief_path,
                mini_kuzai_root=repo,
                schema_path=SCHEMA,
            )


if __name__ == "__main__":
    unittest.main()
