#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "build_flow_presentation.py"
CONFIG = ROOT / "config" / "flow-presentation-001.json"

spec = importlib.util.spec_from_file_location("flow_presentation", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class FlowPresentationTests(unittest.TestCase):

    def test_config_is_non_scientific_and_complete(self):
        data = module.load_config(CONFIG)
        self.assertEqual(
            data["purpose"],
            "NON_SCIENTIFIC_PUBLICATION_FLOW_TEST",
        )
        self.assertEqual(data["timeline"]["duration_seconds"], 60)
        self.assertEqual(len(data["timeline"]["segments"]), 5)
        self.assertEqual(
            sum(x["duration_seconds"] for x in data["timeline"]["segments"]),
            60,
        )
        self.assertIn("youtube", data)
        self.assertIn("linkedin", data)
        self.assertIn("github", data)

    def test_builder_has_no_external_publication_call(self):
        source = TOOL.read_text(encoding="utf-8")
        forbidden = (
            "youtube_upload.py",
            "api.linkedin.com",
            "github.com/graphql",
            "--execute",
        )
        for item in forbidden:
            self.assertNotIn(item, source)

    def test_voice_contract_is_5_to_55_seconds(self):
        mix_path = ROOT / "app" / "mix_audio.py"
        spec = importlib.util.spec_from_file_location(
            "mix_audio_contract",
            mix_path,
        )
        mix = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mix)
        self.assertEqual(mix.VOICE_START, 5.0)
        self.assertEqual(mix.VOICE_END, 55.0)
        self.assertEqual(mix.VOICE_WINDOW, 50.0)

    def test_publication_copy_is_channel_specific(self):
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertIn("DEVELOPMENT DOCUMENTATION FLOW", data["linkedin"]["title"])
        self.assertIn("AUTOMATED DEVELOPMENT DOCUMENTATION FLOW", data["youtube"]["title"])
        self.assertIn("non-scientific", data["github"]["body"].lower())


if __name__ == "__main__":
    unittest.main()
