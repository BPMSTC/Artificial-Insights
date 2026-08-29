#!/usr/bin/env python3
"""Install repo git hooks from scripts/hooks/."""

from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = PROJECT_ROOT / 'scripts' / 'hooks'
TARGET_DIR = PROJECT_ROOT / '.git' / 'hooks'


def main() -> None:
    if not TARGET_DIR.parent.is_dir():
        raise SystemExit('Error: .git directory not found. Run this from the repo root.')

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    installed = []

    for hook in SOURCE_DIR.iterdir():
        if not hook.is_file():
            continue
        target = TARGET_DIR / hook.name
        shutil.copy2(hook, target)
        target.chmod(0o755)
        installed.append(hook.name)

    if not installed:
        raise SystemExit('No hooks found in scripts/hooks/.')

    print('Installed git hooks:')
    for name in installed:
        print(f'  - {name}')


if __name__ == '__main__':
    main()
