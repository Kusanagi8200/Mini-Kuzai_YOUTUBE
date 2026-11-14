#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "tools" / "dev_flow_media_worker.py"

spec = importlib.util.spec_from_file_location(
    "dev_flow_media_worker",
    WORKER,
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class DevFlowMediaWorkerTests(unittest.TestCase):

    def write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_downstream_candidates_only_published_without_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journal = root / "journal.json"
            receipts = root / "receipts"

            self.write_json(
                journal,
                {
                    "schema_version": 1,
                    "steps": {
                        "V80": {"status": "PUBLIC_PUBLISHED"},
                        "V81": {"status": "PUBLIC_PUBLISHED"},
                        "V82": {"status": "PUBLIC_PUBLISHED"},
                        "V83": {"status": "DRY_RUN_VERIFIED"},
                    },
                },
            )
            receipts.mkdir()
            self.write_json(
                receipts / "V82-final.json",
                {"schema_version": 1},
            )

            self.assertEqual(
                module.downstream_candidates(journal, receipts),
                ["V81"],
            )

    def test_auto_closure_starts_at_v83(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipts = root / "receipts"
            history = root / "history"
            receipts.mkdir()
            history.mkdir()
            self.write_json(receipts / "V82-final.json", {"schema_version": 1})
            self.write_json(receipts / "V83-final.json", {"schema_version": 1})

            with patch.object(module, "closure_verified", return_value=False):
                self.assertEqual(
                    module.closure_candidates(receipts, history),
                    ["V83"],
                )

    def test_existing_valid_closure_gogit_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            history = Path(tmp)
            step = "V83"
            self.write_json(
                module.closure_report_path(step, history),
                {
                    "schema_version": 1,
                    "step_id": module.closure_step_id(step),
                    "results": {
                        "FINAL_FLOW": "PASS",
                        "MEDIA_RECEIPT": "PASS",
                    },
                },
            )
            self.assertTrue(module.closure_verified(step, history))

    def test_v83_reconciles_all_stages_in_one_invocation(self):
        short_states = [
            {"WORKER": "BRIEF_GENERATED", "PROCESSED": "0"},
            {"WORKER": "PASS", "PROCESSED": "1"},
            {"WORKER": "IDLE", "PROCESSED": "0"},
            {"WORKER": "IDLE", "PROCESSED": "0"},
            {"WORKER": "IDLE", "PROCESSED": "0"},
        ]

        with patch.object(
            module,
            "run_short_worker",
            side_effect=short_states,
        ), patch.object(
            module,
            "downstream_candidates",
            side_effect=[["V83"], [], []],
        ), patch.object(
            module,
            "run_downstream",
            return_value={
                "MEDIA_ORCHESTRATOR": "PASS",
                "RECEIPT_COMMITTED": "1",
                "RECEIPT_COMMIT": "a" * 40,
            },
        ) as downstream, patch.object(
            module,
            "closure_candidates",
            side_effect=[["V83"], []],
        ), patch.object(
            module,
            "run_closure_gogit",
            return_value={
                "STATE": "PUBLISHED",
                "GOGIT_COMMIT": "b" * 40,
            },
        ) as closure, patch.object(
            module,
            "closure_verified",
            return_value=True,
        ), patch.dict(
            os.environ,
            {"KUZAI_CROSS_CHANNEL_MEDIA_ENABLED": "YES"},
            clear=True,
        ), patch(
            "sys.argv",
            ["dev_flow_media_worker.py"],
        ):
            rc = module.main()

        self.assertEqual(rc, 0)
        self.assertTrue(downstream.call_args.kwargs["publish"])
        closure.assert_called_once()
        self.assertEqual(closure.call_args.args[0], "V83")

    def test_cross_channel_default_remains_preflight_only(self):
        with patch.object(
            module,
            "run_short_worker",
            return_value={"WORKER": "IDLE", "PROCESSED": "0"},
        ), patch.object(
            module,
            "downstream_candidates",
            return_value=["V83"],
        ), patch.object(
            module,
            "run_downstream",
            return_value={"MEDIA_ORCHESTRATOR": "DRY_RUN_PASS"},
        ) as downstream, patch.object(
            module,
            "run_closure_gogit",
        ) as closure, patch.dict(
            os.environ,
            {},
            clear=True,
        ), patch(
            "sys.argv",
            ["dev_flow_media_worker.py"],
        ):
            rc = module.main()

        self.assertEqual(rc, 0)
        self.assertFalse(downstream.call_args.kwargs["publish"])
        closure.assert_not_called()


if __name__ == "__main__":
    unittest.main()
