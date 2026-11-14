#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tools" / "final_dev_flow_closure_audit.py"

spec = importlib.util.spec_from_file_location(
    "final_dev_flow_closure_audit",
    AUDIT,
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class FinalDevFlowClosureAuditTests(unittest.TestCase):

    def test_child_is_read_only(self):
        fake = type(
            "R",
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
                "V83",
                Path("/tmp/journal.json"),
            )

        args = mocked.call_args.args[0]
        self.assertNotIn("--publish", args)
        self.assertEqual(values["PUBLICATION_PERFORMED"], "0")

    def test_scientific_final_requires_matching_source_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_root = module.MINI_KUZAI
            module.MINI_KUZAI = Path(tmp)
            self.addCleanup(setattr, module, "MINI_KUZAI", old_root)

            relative = "automation/dev-flow/receipts/V83-final.json"
            path = module.MINI_KUZAI / relative
            path.parent.mkdir(parents=True)
            path.write_text(
                (
                    '{"schema_version":1,"command":"FINAL-DEV-FLOW",'
                    '"step":"V83","status":"PUBLISHED",'
                    '"source_commit":"' + "a" * 40 + '"}\n'
                ),
                encoding="utf-8",
            )
            media = {
                "source": {
                    "scientific_final_receipt": relative,
                    "scientific_source_commit": "b" * 40,
                }
            }

            fake = type(
                "R",
                (),
                {"returncode": 0, "stdout": "", "stderr": ""},
            )()
            with patch.object(module, "run", return_value=fake):
                with self.assertRaises(module.ClosureAuditError):
                    module.verify_scientific_final("V83", media)


if __name__ == "__main__":
    unittest.main()
