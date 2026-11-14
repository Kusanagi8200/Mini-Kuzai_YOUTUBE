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

    def test_downstream_candidates_only_v81_plus_without_receipt(self):
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

    def test_short_worker_brief_stage_stops_loop(self):
        with patch.object(
            module,
            "run_short_worker",
            return_value={
                "WORKER": "BRIEF_GENERATED",
                "PROCESSED": "0",
            },
        ), patch.object(
            module,
            "downstream_candidates",
        ) as downstream:
            with patch(
                "sys.argv",
                ["dev_flow_media_worker.py"],
            ):
                rc = module.main()

        self.assertEqual(rc, 0)
        downstream.assert_not_called()

    def test_short_worker_youtube_stage_stops_loop(self):
        with patch.object(
            module,
            "run_short_worker",
            return_value={
                "WORKER": "PASS",
                "PROCESSED": "1",
            },
        ), patch.object(
            module,
            "downstream_candidates",
        ) as downstream:
            with patch(
                "sys.argv",
                ["dev_flow_media_worker.py"],
            ):
                rc = module.main()

        self.assertEqual(rc, 0)
        downstream.assert_not_called()

    def test_cross_channel_default_is_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journal = root / "journal.json"
            receipts = root / "receipts"
            self.write_json(
                journal,
                {
                    "schema_version": 1,
                    "steps": {
                        "V81": {"status": "PUBLIC_PUBLISHED"},
                    },
                },
            )
            receipts.mkdir()

            with patch.object(
                module,
                "run_downstream",
                return_value={
                    "MEDIA_ORCHESTRATOR": "DRY_RUN_PASS",
                },
            ) as downstream, patch.dict(
                os.environ,
                {},
                clear=True,
            ), patch(
                "sys.argv",
                [
                    "dev_flow_media_worker.py",
                    "--skip-short-worker",
                    "--journal",
                    str(journal),
                    "--receipt-dir",
                    str(receipts),
                ],
            ):
                rc = module.main()

        self.assertEqual(rc, 0)
        self.assertFalse(downstream.call_args.kwargs["publish"])

    def test_cross_channel_live_requires_explicit_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journal = root / "journal.json"
            receipts = root / "receipts"
            self.write_json(
                journal,
                {
                    "schema_version": 1,
                    "steps": {
                        "V81": {"status": "PUBLIC_PUBLISHED"},
                    },
                },
            )
            receipts.mkdir()

            with patch.object(
                module,
                "run_downstream",
                return_value={
                    "MEDIA_ORCHESTRATOR": "PASS",
                    "RECEIPT_COMMIT": "a" * 40,
                },
            ) as downstream, patch.dict(
                os.environ,
                {"KUZAI_CROSS_CHANNEL_MEDIA_ENABLED": "YES"},
                clear=True,
            ), patch(
                "sys.argv",
                [
                    "dev_flow_media_worker.py",
                    "--skip-short-worker",
                    "--journal",
                    str(journal),
                    "--receipt-dir",
                    str(receipts),
                ],
            ):
                rc = module.main()

        self.assertEqual(rc, 0)
        self.assertTrue(downstream.call_args.kwargs["publish"])


if __name__ == "__main__":
    unittest.main()
