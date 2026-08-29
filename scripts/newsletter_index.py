#!/usr/bin/env python3
"""Shared helpers for index.html and latest-issue verification."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def format_date_display(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%b %d, %Y')
    except ValueError:
        return date_str


def get_latest_issue(project_root: Path) -> tuple[str, int] | None:
    """Return (issue_date, issue_number) for the highest-numbered meeting notes file."""
    notes_dir = project_root / 'meeting-notes'
    latest: tuple[str, int] | None = None

    for md_file in notes_dir.glob('*.md'):
        if 'template' in md_file.name.lower():
            continue
        try:
            content = md_file.read_text(encoding='utf-8')
        except OSError:
            continue

        date_match = re.search(r'^Issue Date:\s*(.+)$', content, re.MULTILINE)
        number_match = re.search(r'^Issue Number:\s*(\d+)', content, re.MULTILINE)
        if not date_match or not number_match:
            continue

        issue_date = date_match.group(1).strip()
        issue_number = int(number_match.group(1))
        if latest is None or issue_number > latest[1]:
            latest = (issue_date, issue_number)

    return latest


def verify_index(project_root: Path) -> list[str]:
    """Return human-readable problems with index.html vs the latest issue."""
    errors: list[str] = []
    latest = get_latest_issue(project_root)
    if latest is None:
        return ['No meeting notes with Issue Date and Issue Number were found.']

    issue_date, issue_number = latest
    index_path = project_root / 'index.html'
    if not index_path.is_file():
        return [f'Missing {index_path}']

    content = index_path.read_text(encoding='utf-8')
    date_display = format_date_display(issue_date)
    expected_latest = f'{date_display} · Issue #{issue_number}'

    latest_match = re.search(
        r'<span class="date">📅 Latest Issue: (.+?)</span>',
        content,
    )
    if not latest_match or latest_match.group(1).strip() != expected_latest:
        errors.append(
            f'Latest Issue bar should be "{expected_latest}" '
            f'but found "{latest_match.group(1).strip() if latest_match else "nothing"}".'
        )

    latest_link = f'href="issues/{issue_date}.html">Read Latest'
    if latest_link not in content:
        errors.append(f'Latest Issue link should point to issues/{issue_date}.html.')

    card_marker = f'<span class="issue-number">Issue #{issue_number}</span>'
    if card_marker not in content:
        errors.append(f'All Issues is missing a card for Issue #{issue_number} ({issue_date}).')

    issue_html = project_root / 'issues' / f'{issue_date}.html'
    sources_html = project_root / 'sources' / f'{issue_date}.html'
    if not issue_html.is_file():
        errors.append(f'Missing generated issue page: {issue_html}')
    if not sources_html.is_file():
        errors.append(f'Missing generated sources page: {sources_html}')

    return errors


def update_index(project_root: Path, issue_date: str, issue_number: int) -> bool:
    """Ensure index.html points at the issue and has an All Issues card. Returns True if modified."""
    index_path = project_root / 'index.html'
    content = index_path.read_text(encoding='utf-8')
    original = content
    date_display = format_date_display(issue_date)

    content = re.sub(
        r'(<span class="date">📅 Latest Issue: ).*?(</span>)',
        rf'\1{date_display} · Issue #{issue_number}\2',
        content,
        count=1,
    )
    content = re.sub(
        r'(<a href=")issues/[^"]+\.html(">Read Latest)',
        rf'\1issues/{issue_date}.html\2',
        content,
        count=1,
    )

    if f'<span class="issue-number">Issue #{issue_number}</span>' not in content:
        new_card = f'''      <article class="issue-card">
        <div class="issue-header">
          <h3>{date_display}</h3>
          <span class="issue-number">Issue #{issue_number}</span>
        </div>
        <p>Add a brief description of this issue.</p>
        <div class="links">
          <a href="issues/{issue_date}.html">Read Issue</a>
          <a href="sources/{issue_date}.html">Sources</a>
        </div>
      </article>
      
      '''
        marker = '      <article class="issue-card">'
        if marker in content:
            content = content.replace(marker, new_card.rstrip() + '\n\n' + marker, 1)

    if content != original:
        index_path.write_text(content, encoding='utf-8')
        return True
    return False
