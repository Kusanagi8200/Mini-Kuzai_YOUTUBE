#!/usr/bin/env python3
"""Normalize Markdown headings and footer for Mini-Kuzai YouTube documentation."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUPS = ROOT / "backups"
FOOTER_TEXT = "THE KUZ NETWORK - KUSANAGI8200 - @2026"
FOOTER = f"**`{FOOTER_TEXT}`**"
MARKER = "##### SECTION RESULTS FOR ASSISTANT ######"


def markdown_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.md")
        if ".git" not in path.parts and "backups" not in path.parts
    )


def backup(path: Path, backup_root: Path) -> Path:
    relative = path.relative_to(ROOT)
    target = backup_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    return target


def normalize(content: str) -> str:
    lines = content.replace("\r\n", "\n").split("\n")
    output: list[str] = []
    fenced = False
    fence_token = ""

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```") or stripped.startswith("~~~"):
            token = stripped[:3]
            if not fenced:
                fenced = True
                fence_token = token
            elif token == fence_token:
                fenced = False
                fence_token = ""
            output.append(line)
            continue

        if not fenced:
            if FOOTER_TEXT in stripped and stripped in {
                FOOTER_TEXT,
                f"**{FOOTER_TEXT}**",
                f"`{FOOTER_TEXT}`",
                FOOTER,
            }:
                continue

            if line.startswith("#"):
                hashes, separator, title = line.partition(" ")
                if (
                    separator
                    and 1 <= len(hashes) <= 6
                    and set(hashes) == {"#"}
                    and title.strip()
                ):
                    clean = title.strip()
                    if clean.startswith("`") and clean.endswith("`"):
                        clean = clean[1:-1]
                    clean = clean.replace("`", "")
                    line = f"{hashes} `{clean}`"

        output.append(line)

    while output and not output[-1].strip():
        output.pop()

    if output and output[-1].strip() == "---":
        output.pop()
        while output and not output[-1].strip():
            output.pop()

    output.extend(["", "---", "", FOOTER, ""])
    return "\n".join(output)


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = BACKUPS / f"doc-style-{stamp}"
    changed = 0
    backed_up = 0

    for path in markdown_files():
        original = path.read_text(encoding="utf-8")
        updated = normalize(original)
        if updated == original:
            continue
        backup(path, backup_root)
        backed_up += 1
        path.write_text(updated, encoding="utf-8")
        changed += 1

    print(MARKER)
    print("DOC_STYLE=PASS")
    print(f"FILES_CHANGED={changed}")
    print(f"BACKUPS_CREATED={backed_up}")
    print(f"BACKUP_ROOT={backup_root.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
