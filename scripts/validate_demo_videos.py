#!/usr/bin/env python3
"""
Validate demo media for browser-friendly playback.

Warns (and exits non-zero) when .mov / QuickTime files are present under
assets/demos/ or referenced from meeting-notes Image: fields.

Usage:
    python scripts/validate_demo_videos.py
    python scripts/validate_demo_videos.py --strict   # same as default (non-zero exit)
    python scripts/validate_demo_videos.py --warn-only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMOS_ROOT = PROJECT_ROOT / "assets" / "demos"
NOTES_ROOT = PROJECT_ROOT / "meeting-notes"
MOV_SUFFIXES = {".mov"}


def find_mov_files() -> list[Path]:
    if not DEMOS_ROOT.is_dir():
        return []
    return sorted(
        p for p in DEMOS_ROOT.rglob("*")
        if p.is_file() and p.suffix.lower() in MOV_SUFFIXES
    )


def find_mov_references() -> list[tuple[Path, int, str]]:
    refs: list[tuple[Path, int, str]] = []
    if not NOTES_ROOT.is_dir():
        return refs
    pattern = re.compile(r"^\s*Image:\s*(.+\.mov)\s*$", re.IGNORECASE)
    for notes_path in sorted(NOTES_ROOT.glob("*.md")):
        if "template" in notes_path.name.lower():
            continue
        for i, line in enumerate(notes_path.read_text(encoding="utf-8").splitlines(), start=1):
            match = pattern.match(line)
            if match:
                refs.append((notes_path, i, match.group(1).strip()))
    return refs


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate demo videos for browser playback.")
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print warnings but always exit 0",
    )
    args = parser.parse_args()

    mov_files = find_mov_files()
    mov_refs = find_mov_references()

    if not mov_files and not mov_refs:
        print("Demo video check: OK (no .mov / QuickTime files found).")
        return 0

    print("=" * 72)
    print("DEMO VIDEO WARNING: .mov / QuickTime files are not reliable in browsers.")
    print("Convert them to H.264 + AAC .mp4 before publishing.")
    print()
    print("Example:")
    print(
        '  ffmpeg -i "assets/demos/YYYY-MM-DD/clip.MOV" '
        '-c:v libx264 -c:a aac -movflags +faststart '
        '"assets/demos/YYYY-MM-DD/clip.mp4"'
    )
    print("Then update the meeting-notes Image: field to the .mp4 filename.")
    print("=" * 72)

    if mov_files:
        print("\n.mov files under assets/demos/:")
        for path in mov_files:
            print(f"  - {path.relative_to(PROJECT_ROOT)}")

    if mov_refs:
        print("\n.mov references in meeting-notes:")
        for path, line_no, filename in mov_refs:
            print(f"  - {path.relative_to(PROJECT_ROOT)}:{line_no} -> Image: {filename}")

    print()
    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
