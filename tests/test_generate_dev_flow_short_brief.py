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
TOOL = ROOT / "tools" / "generate_dev_flow_short_brief.py"

spec = importlib.util.spec_from_file_location("brief_generator", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class FinalTrainingReportTests(unittest.TestCase):

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
        repo = Path(temporary.name) / "Mini-Kuzai"
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

        metrics = {
            "SEMANTIC_VALIDATION_COMPLETE": 0,
            "TRAINING_AUTHORIZED": 0,
            "TRAINING_STARTED": 1,
            "V81_FINAL_PASS": 1,
            "V81_FINAL_BLIND_ACCESS": 0,
            "V81_FINAL_WINDOW_CLOSED": int(closed),
            "V81_FINAL_FURTHER_TRAINING_AUTHORIZED": 0,
        }

        report = {
            "project": "Mini-Kuzai",
            "phase": "03",
            "status": "PUBLIC_AGGREGATE_REVIEW_ONLY",
            "private_conversation_data_included": False,
            "semantic_validation_complete": False,
            "step_id": "PHASE03-SMOLTALK-V81-FINAL-CLOSURE-001",
            "metrics": metrics,
            "source": "Mini-Kuzai V81 final closure review",
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

        return temporary, repo

    def test_closed_training_final_is_accepted(self):
        temporary, repo = self.fixture(closed=True)
        self.addCleanup(temporary.cleanup)

        receipt, request, report, source_commit = module.validate_provenance(
            "V81",
            repo,
        )

        self.assertEqual(receipt["status"], "PUBLISHED")
        self.assertEqual(request["step"], "V81")
        self.assertEqual(report["metrics"]["V81_FINAL_PASS"], 1)
        self.assertEqual(len(source_commit), 40)

    def test_training_final_without_closed_window_is_rejected(self):
        temporary, repo = self.fixture(closed=False)
        self.addCleanup(temporary.cleanup)

        with self.assertRaises(module.BriefGeneratorError):
            module.validate_provenance("V81", repo)

    def test_training_final_narration_is_extended_for_voice_window(self):
        temporary, repo = self.fixture(closed=True)
        self.addCleanup(temporary.cleanup)

        receipt, request, report, source_commit = module.validate_provenance(
            "V81",
            repo,
        )
        brief = module.build_brief(
            "V81",
            receipt,
            request,
            report,
            source_commit,
        )

        narration = brief["narration"]
        self.assertGreaterEqual(len(narration), 600)
        self.assertIn("training window is now closed", narration)
        self.assertIn("new protocol and explicit approval", narration)

    def test_diagnostic_final_narration_is_extended_for_voice_window(self):
        report = {
            "source": "Mini-Kuzai V82 post-continuation context-order replication control",
            "step_id": (
                "PHASE03-SMOLTALK-V82-POST-CONTINUATION-"
                "CONTEXT-ORDER-REPLICATION-001"
            ),
            "metrics": {
                "SEMANTIC_VALIDATION_COMPLETE": 0,
                "TRAINING_AUTHORIZED": 0,
                "TRAINING_STARTED": 0,
                "V82_PASS": 1,
                "V82_BLIND_ACCESS": 0,
                "V82_BASELINE_PRED_CHANGED": 5,
                "V82_FINAL_PRED_CHANGED": 38,
                "V82_BASELINE_SIGN_CHANGED": 5,
            },
        }
        receipt = {"status": "PUBLISHED"}
        request = {
            "report": (
                "reports/assistant-results/history/"
                + report["step_id"]
                + ".json"
            )
        }

        brief = module.build_brief(
            "V82",
            receipt,
            request,
            report,
            "a" * 40,
        )

        narration = brief["narration"]
        self.assertGreaterEqual(len(narration), 650)
        self.assertIn("read-only control", narration)
        self.assertIn("controlled numerical observation", narration)
        self.assertIn("not a semantic evaluation", narration)

    def test_selected_metrics_excludes_pass_metric(self):
        metrics = {
            "V81_FINAL_PASS": 1,
            "V81_FINAL_EXPOSURE": 1181302,
            "V81_FINAL_STEPS": 136,
            "V81_FINAL_BEST_LOSS_X1E6": 4030447,
            "SEMANTIC_VALIDATION_COMPLETE": 0,
            "TRAINING_AUTHORIZED": 0,
            "TRAINING_STARTED": 1,
        }

        chosen = module.selected_metrics("V81", metrics)
        names = {name for name, _ in chosen}
        self.assertNotIn("V81_FINAL_PASS", names)


if __name__ == "__main__":
    unittest.main()
