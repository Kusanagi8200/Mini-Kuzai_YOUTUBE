#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import os
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / "tools" / "github_media_fallback.py"

spec = importlib.util.spec_from_file_location(
    "github_media_fallback",
    PUBLISHER,
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class GitHubMediaFallbackTests(unittest.TestCase):

    def state(self) -> dict[str, str]:
        return {
            "discussion_number": "81",
            "youtube_video_id": "AbCdEf12345",
            "youtube_url": "https://www.youtube.com/watch?v=AbCdEf12345",
            "video_sha256": "a" * 64,
        }

    def test_media_body_contains_verified_fallback(self):
        body = module.media_body("V81", self.state())
        self.assertIn("MEDIA PUBLICATION // V81 FINAL", body)
        self.assertIn("YOUTUBE_PUBLIC_LINK_FALLBACK", body)
        self.assertIn("AbCdEf12345", body)
        self.assertIn("NO", "NO")

    def test_existing_identical_comment_is_idempotent(self):
        body = module.media_body("V81", self.state())
        comment = {
            "id": "DC_test",
            "url": "https://github.com/example/comment",
            "body": body,
        }
        found = module.existing_media_comment(
            [comment],
            "V81",
            body,
        )
        self.assertEqual(found["id"], "DC_test")

    def test_conflicting_existing_comment_is_blocked(self):
        comment = {
            "id": "DC_test",
            "url": "https://github.com/example/comment",
            "body": (
                "MEDIA PUBLICATION // V81 FINAL\n\n"
                "conflicting content"
            ),
        }
        with self.assertRaises(module.GitHubMediaError):
            module.existing_media_comment(
                [comment],
                "V81",
                module.media_body("V81", self.state()),
            )

    def test_preflight_never_publishes(self):
        state = self.state()
        with patch.object(module, "github_actor", return_value="Kusanagi8200"),              patch.object(
                 module,
                 "discussion_comments",
                 return_value=(
                     "D_kwDO_test",
                     "https://github.com/Kusanagi8200/Mini-Kuzai/discussions/81",
                     [],
                 ),
             ),              patch.object(module, "graphql") as graphql_mock:
            result = module.publish(
                "V81",
                state,
                allow_publish=False,
            )

        self.assertEqual(result["state"], "READY_TO_COMMENT")
        graphql_mock.assert_not_called()

    def test_live_gate_blocks_by_default(self):
        state = self.state()
        with patch.object(module, "github_actor", return_value="Kusanagi8200"),              patch.object(
                 module,
                 "discussion_comments",
                 return_value=(
                     "D_kwDO_test",
                     "https://github.com/Kusanagi8200/Mini-Kuzai/discussions/81",
                     [],
                 ),
             ),              patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(module.GitHubMediaError):
                module.publish(
                    "V81",
                    state,
                    allow_publish=True,
                )


if __name__ == "__main__":
    unittest.main()
