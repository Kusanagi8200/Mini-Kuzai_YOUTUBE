#!/usr/bin/env python3
"""Validate frozen STEP-02 overlay geometry."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "overlay-layout.json"
MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"


def intersects(a: dict[str, int], b: dict[str, int]) -> bool:
    return not (
        a["x"] + a["width"] <= b["x"]
        or b["x"] + b["width"] <= a["x"]
        or a["y"] + a["height"] <= b["y"]
        or b["y"] + b["height"] <= a["y"]
    )


def inside(inner: dict[str, int], outer: dict[str, int]) -> bool:
    return (
        inner["x"] >= outer["x"]
        and inner["y"] >= outer["y"]
        and inner["x"] + inner["width"] <= outer["x"] + outer["width"]
        and inner["y"] + inner["height"] <= outer["y"] + outer["height"]
    )


def main() -> int:
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    canvas = payload["canvas"]
    reserved = payload["reserved_zones"]
    dynamic = payload["dynamic_zones"]

    canvas_box = {"x": 0, "y": 0, "width": canvas["width"], "height": canvas["height"]}
    primary = dynamic["primary_panel"]

    bounds_ok = all(
        inside(zone, canvas_box)
        for zone in list(reserved.values()) + list(dynamic.values())
    )
    children_ok = all(
        inside(dynamic[name], primary)
        for name in ("badge", "headline", "body")
    )

    forbidden = (
        "fixed_logo",
        "character_protection",
        "fixed_branding",
        "shorts_right_ui_conservative",
        "shorts_bottom_ui_conservative",
    )
    reserved_clear = all(not intersects(primary, reserved[name]) for name in forbidden)

    passed = bounds_ok and children_ok and reserved_clear

    print(MARKER)
    print(f"STEP_STATUS={'PASS' if passed else 'FAIL'}")
    print(f"CANVAS_WIDTH={canvas['width']}")
    print(f"CANVAS_HEIGHT={canvas['height']}")
    print(f"ALL_ZONES_IN_BOUNDS={int(bounds_ok)}")
    print(f"DYNAMIC_CHILDREN_IN_PRIMARY={int(children_ok)}")
    print(f"PRIMARY_RESERVED_CLEAR={int(reserved_clear)}")
    print(f"PRIMARY_X={primary['x']}")
    print(f"PRIMARY_Y={primary['y']}")
    print(f"PRIMARY_WIDTH={primary['width']}")
    print(f"PRIMARY_HEIGHT={primary['height']}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
