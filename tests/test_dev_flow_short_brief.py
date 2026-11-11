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


class BriefValidatorTests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()

    def write_json(self, path: Path, data: dict) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=2, sort_keys=True) + "\n"
        path.write_text(text, encoding="utf-8")
        return text

    def build_fixture(self):
        temporary = tempfile.TemporaryDirectory()
        base = Path(temporary.name)
        repo = base / "Mini-Kuzai"
        repo.mkdir()

        self.git(repo, "init", "-b", "main")
        self.git(repo, "config", "user.name", "Mini-Kuzai Test")
        self.git(repo, "config", "user.email", "test@example.invalid")

        step = "V80"
        report_rel = (
            "reports/assistant-results/history/"
            "PHASE03-SMOLTALK-V80-TEST-001.json"
        )
        request_rel = "automation/dev-flow/requests/V80-final.json"
        receipt_rel = "automation/dev-flow/receipts/V80-final.json"

        report = {
            "project": "Mini-Kuzai",
            "phase": "03",
            "status": "PUBLIC_AGGREGATE_REVIEW_ONLY",
            "private_conversation_data_included": False,
            "semantic_validation_complete": False,
            "step_id": "PHASE03-SMOLTALK-V80-TEST-001",
            "metrics": {
                "V80_PASS": 1,
                "V80_BLIND_ACCESS": 0,
                "SEMANTIC_VALIDATION_COMPLETE": 0,
                "TRAINING_STARTED": 0,
                "TRAINING_AUTHORIZED": 0,
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
        self.git(repo, "commit", "-m", "test source")
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
                "discussions/11#discussioncomment-1"
            ),
            "published_at_utc": "2026-11-11T12:00:00+00:00",
            "status": "PUBLISHED",
        }

        self.write_json(repo / receipt_rel, receipt)
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "test receipt")

        brief = {
            "schema_version": 1,
            "step": step,
            "video_id": "VIDEO-V80-FINAL",
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
                        "badge": "V80",
                        "headline": f"TEST {index}",
                        "body": "VALIDATED DEVELOPMENT RESULT",
                    }
                    for index in range(1, 6)
                ],
            },
            "narration": (
                "Mini-Kuzai V80 completed a validated development control. "
                "This synthetic narration exists only for validator testing. "
                "No training or blind evaluation is authorized by this test."
            ),
            "youtube": {
                "title": "MINI-KUZAI V80 // VALIDATED DEVELOPMENT STEP",
                "description": (
                    "Mini-Kuzai V80 validated development milestone.\n\n"
                    "BUILD LOCAL. KEEP CONTROL. OWN THE STACK."
                ),
                "tags": [
                    "Mini-Kuzai",
                    "THE KUZ NETWORK",
                    "LLM From Scratch",
                ],
                "publication_mode": "private",
            },
        }

        brief_path = base / "brief.json"
        self.write_json(brief_path, brief)

        return temporary, repo, brief_path, brief

    def test_valid_brief(self):
        temporary, repo, brief_path, _ = self.build_fixture()
        self.addCleanup(temporary.cleanup)

        result = module.validate_brief(
            brief_path,
            mini_kuzai_root=repo,
            schema_path=SCHEMA,
        )

        self.assertEqual(result["step"], "V80")
        self.assertEqual(result["timeline_seconds"], 60)

    def test_report_mismatch_is_rejected(self):
        temporary, repo, brief_path, brief = self.build_fixture()
        self.addCleanup(temporary.cleanup)

        brief["source"]["gogit_report"] = (
            "reports/assistant-results/history/"
            "PHASE03-SMOLTALK-V80-OTHER-001.json"
        )
        self.write_json(brief_path, brief)

        with self.assertRaises(module.BriefValidationError):
            module.validate_brief(
                brief_path,
                mini_kuzai_root=repo,
                schema_path=SCHEMA,
            )

    def test_non_published_receipt_is_rejected(self):
        temporary, repo, brief_path, _ = self.build_fixture()
        self.addCleanup(temporary.cleanup)

        receipt_path = (
            repo / "automation/dev-flow/receipts/V80-final.json"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["status"] = "FAILED"
        self.write_json(receipt_path, receipt)
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "change receipt")

        with self.assertRaises(module.BriefValidationError):
            module.validate_brief(
                brief_path,
                mini_kuzai_root=repo,
                schema_path=SCHEMA,
            )

    def test_noncanonical_description_is_rejected(self):
        temporary, repo, brief_path, brief = self.build_fixture()
        self.addCleanup(temporary.cleanup)

        brief["youtube"]["description"] = "Result: validated"
        self.write_json(brief_path, brief)

        with self.assertRaises(module.BriefValidationError):
            module.validate_brief(
                brief_path,
                mini_kuzai_root=repo,
                schema_path=SCHEMA,
            )


if __name__ == "__main__":
    unittest.main()
