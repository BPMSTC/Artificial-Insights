#!/usr/bin/env python3
"""
Publish the newsletter to GitHub Pages.

1. Verify (and optionally fix) index.html for the latest issue
2. Push origin master
3. Fast-forward gh-pages from master and push origin gh-pages
4. Return to the original branch

Usage:
    python scripts/publish_newsletter.py
    python scripts/publish_newsletter.py --fix-index
    python scripts/publish_newsletter.py --dry-run
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from newsletter_index import get_latest_issue, update_index, verify_index

PROJECT_ROOT = SCRIPT_DIR.parent


def run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print('>', ' '.join(cmd))
    kwargs = {'cwd': PROJECT_ROOT, 'text': True, 'check': check}
    if capture:
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
    return subprocess.run(cmd, **kwargs)


def current_branch() -> str:
    result = run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture=True)
    return (result.stdout or '').strip()


def has_uncommitted_changes() -> bool:
    result = run(['git', 'status', '--porcelain'], capture=True)
    return bool((result.stdout or '').strip())


def remote_contains_commit(branch: str, commit: str) -> bool:
    result = run(['git', 'branch', '-r', '--contains', commit], check=False, capture=True)
    needle = f'origin/{branch}'
    return needle in (result.stdout or '')


def main() -> int:
    parser = argparse.ArgumentParser(description='Publish newsletter to master and gh-pages.')
    parser.add_argument(
        '--fix-index',
        action='store_true',
        help='Update index.html for the latest issue before publishing.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Verify only; do not push.',
    )
    args = parser.parse_args()

    latest = get_latest_issue(PROJECT_ROOT)
    if latest is None:
        print('Error: could not determine the latest issue from meeting-notes/.')
        return 1

    issue_date, issue_number = latest
    print(f'Latest issue: #{issue_number} ({issue_date})')

    if args.fix_index:
        if update_index(PROJECT_ROOT, issue_date, issue_number):
            print('Updated index.html for the latest issue.')
            if has_uncommitted_changes():
                print('Commit index.html (and any regenerated HTML) before publishing.')
                return 1

    errors = verify_index(PROJECT_ROOT)
    if errors:
        print('index.html is not ready to publish:')
        for error in errors:
            print(f'  - {error}')
        print('Run: python scripts/new_newsletter.py YYYY-MM-DD for a new issue,')
        print('or:  python scripts/publish_newsletter.py --fix-index')
        return 1

    print('index.html, issue page, and sources page look correct.')

    if args.dry_run:
        print('Dry run complete. No pushes performed.')
        return 0

    if has_uncommitted_changes():
        print('Error: uncommitted changes remain. Commit or stash before publishing.')
        return 1

    start_branch = current_branch()
    if start_branch != 'master':
        print(f'Warning: publishing from branch "{start_branch}" instead of master.')

    head = run(['git', 'rev-parse', 'HEAD'], capture=True).stdout.strip()

    run(['git', 'push', '--no-verify', 'origin', 'master'])

    run(['git', 'checkout', 'gh-pages'])
    try:
        run(['git', 'merge', 'master', '--ff-only'])
        run(['git', 'push', 'origin', 'gh-pages'])
    finally:
        run(['git', 'checkout', start_branch])

    if remote_contains_commit('gh-pages', head):
        print('Published to origin/master and origin/gh-pages.')
    else:
        print('Warning: gh-pages push finished, but remote verification was inconclusive.')

    print('Live site: https://bpmstc.github.io/Artificial-Insights/')
    return 0


if __name__ == '__main__':
    sys.exit(main())
