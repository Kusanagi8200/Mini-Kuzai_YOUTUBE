#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "tools" / "dev_flow_short_worker.py"

spec = importlib.util.spec_from_file_location(
    "dev_flow_short_worker",
    WORKER,
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class WorkerTests(unittest.TestCase):

    def write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )

    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()

    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)

        mini = root / "Mini-Kuzai"
        briefs = root / "briefs"
        journal = root / "state" / "journal.json"
        pipeline = root / "fake_pipeline.py"

        mini.mkdir(parents=True)

        self.git(mini, "init", "-b", "main")
        self.git(mini, "config", "user.name", "Mini-Kuzai Test")
        self.git(
            mini,
            "config",
            "user.email",
            "mini-kuzai-test@example.invalid",
        )

        receipt = (
            mini
            / "automation"
            / "dev-flow"
            / "receipts"
            / "V80-final.json"
        )

        self.write_json(
            receipt,
            {
                "schema_version": 1,
                "command": "FINAL-DEV-FLOW",
                "step": "V80",
                "status": "PUBLISHED",
            },
        )

        self.git(mini, "add", ".")
        self.git(mini, "commit", "-m", "add FINAL receipt")

        brief = briefs / "V80-final.json"

        self.write_json(
            brief,
            {
                "schema_version": 1,
                "step": "V80",
                "video_id": "VIDEO-V80-FINAL",
            },
        )

        pipeline.write_text(
            """#!/usr/bin/env python3
print("##### SECTION RESULTS FOR ASSISTANT ######")
print("PIPELINE_ORCHESTRATOR=PASS")
print("UPLOAD_PERFORMED=1")
print("UPLOAD_PRIVACY=public")
print("PUBLICATION=PUBLIC")
print("YOUTUBE_VIDEO_ID=AbCdEf12345")
print("VIDEO_SHA256=" + "a" * 64)
""",
            encoding="utf-8",
        )
        pipeline.chmod(0o755)

        return temporary, mini, briefs, journal, pipeline

    def test_pending_candidate(self):
        temporary, mini, briefs, journal, _ = self.fixture()
        self.addCleanup(temporary.cleanup)

        data = module.load_journal(journal)

        step, _, state = module.inspect_candidate(
            briefs / "V80-final.json",
            mini_root=mini,
            journal=data,
            require_committed=False,
        )

        self.assertEqual(step, "V80")
        self.assertEqual(state, "PENDING")

    def test_process_and_idempotence(self):
        temporary, mini, briefs, journal, pipeline = self.fixture()
        self.addCleanup(temporary.cleanup)

        result = module.process_candidate(
            briefs / "V80-final.json",
            mini_root=mini,
            journal_path=journal,
            pipeline=pipeline,
            python=Path(os.sys.executable),
            require_committed=False,
        )

        self.assertEqual(result["state"], "PUBLIC_PUBLISHED")
        self.assertEqual(result["processed"], "1")

        result2 = module.process_candidate(
            briefs / "V80-final.json",
            mini_root=mini,
            journal_path=journal,
            pipeline=pipeline,
            python=Path(os.sys.executable),
            require_committed=False,
        )

        self.assertEqual(result2["state"], "ALREADY_VERIFIED")
        self.assertEqual(result2["processed"], "0")

    def test_conflicting_replay_is_blocked(self):
        temporary, mini, briefs, journal, pipeline = self.fixture()
        self.addCleanup(temporary.cleanup)

        module.process_candidate(
            briefs / "V80-final.json",
            mini_root=mini,
            journal_path=journal,
            pipeline=pipeline,
            python=Path(os.sys.executable),
            require_committed=False,
        )

        path = briefs / "V80-final.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["changed"] = True
        self.write_json(path, data)

        with self.assertRaises(module.WorkerError):
            module.process_candidate(
                path,
                mini_root=mini,
                journal_path=journal,
                pipeline=pipeline,
                python=Path(os.sys.executable),
                require_committed=False,
            )

    def test_nonpublished_receipt_is_blocked(self):
        temporary, mini, briefs, journal, _ = self.fixture()
        self.addCleanup(temporary.cleanup)

        receipt = (
            mini
            / "automation"
            / "dev-flow"
            / "receipts"
            / "V80-final.json"
        )

        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["status"] = "FAILED"
        self.write_json(receipt, data)

        self.git(mini, "add", ".")
        self.git(mini, "commit", "-m", "change FINAL receipt status")

        with self.assertRaises(module.WorkerError):
            module.inspect_candidate(
                briefs / "V80-final.json",
                mini_root=mini,
                journal=module.load_journal(journal),
                require_committed=False,
            )


if __name__ == "__main__":
    unittest.main()
