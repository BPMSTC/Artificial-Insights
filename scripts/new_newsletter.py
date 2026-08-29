#!/usr/bin/env python3
"""
Create a new newsletter issue. Run this with a date (YYYY-MM-DD) to:
1. Create meeting-notes/YYYY-MM-DD.md from template
2. Create assets/demos/YYYY-MM-DD/ folder
3. Generate issues/ and sources/ HTML
4. Add the issue to index.html

Usage:
    python scripts/new_newsletter.py 2026-02-14
    python scripts/new_newsletter.py    # prompts for date
"""

import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from newsletter_index import update_index


def get_next_issue_number(project_root: Path) -> int:
    """Find the highest issue number from meeting notes and add 1."""
    notes_dir = project_root / 'meeting-notes'
    max_num = 0
    
    for md_file in notes_dir.glob('*.md'):
        if 'template' in md_file.name.lower():
            continue
        try:
            content = md_file.read_text(encoding='utf-8')
            match = re.search(r'^Issue Number:\s*(\d+)', content, re.MULTILINE)
            if match:
                max_num = max(max_num, int(match.group(1)))
        except (OSError, ValueError):
            continue
    
    return max_num + 1


def create_meeting_notes(project_root: Path, issue_date: str, issue_number: int) -> Path:
    """Create meeting notes file from template."""
    template_path = project_root / 'meeting-notes' / 'meeting-notes-template.md'
    notes_path = project_root / 'meeting-notes' / f'{issue_date}.md'
    
    if notes_path.exists():
        print(f"Warning: {notes_path} already exists. Skipping creation.")
        return notes_path
    
    content = template_path.read_text(encoding='utf-8')
    content = content.replace('Issue Date: YYYY-MM-DD', f'Issue Date: {issue_date}')
    content = content.replace('Issue Number: X', f'Issue Number: {issue_number}')
    
    notes_path.write_text(content, encoding='utf-8')
    print(f"Created: {notes_path}")
    return notes_path


def create_demos_folder(project_root: Path, issue_date: str) -> Path:
    """Create demos folder for the issue date."""
    demos_path = project_root / 'assets' / 'demos' / issue_date
    
    if demos_path.exists():
        print(f"Demo folder already exists: {demos_path}")
        return demos_path
    
    demos_path.mkdir(parents=True, exist_ok=True)
    # Add .gitkeep so empty folder gets committed
    (demos_path / '.gitkeep').touch()
    print(f"Created: {demos_path}/")
    return demos_path


def create_article_images_folder(project_root: Path, issue_date: str) -> Path:
    """Create article-images folder for the issue date (optional images per item)."""
    img_path = project_root / 'assets' / 'article-images' / issue_date
    
    if img_path.exists():
        print(f"Article images folder already exists: {img_path}")
        return img_path
    
    img_path.mkdir(parents=True, exist_ok=True)
    (img_path / '.gitkeep').touch()
    print(f"Created: {img_path}/")
    return img_path


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Get date from argument or prompt
    if len(sys.argv) >= 2:
        issue_date = sys.argv[1].strip()
    else:
        issue_date = input("Enter issue date (YYYY-MM-DD): ").strip()
    
    # Validate date format
    try:
        datetime.strptime(issue_date, '%Y-%m-%d')
    except ValueError:
        print(f"Error: Invalid date format. Use YYYY-MM-DD (e.g., 2026-02-14)")
        sys.exit(1)
    
    print(f"\nCreating newsletter for {issue_date}...\n")
    
    # 1. Get next issue number
    issue_number = get_next_issue_number(project_root)
    print(f"Issue number: {issue_number}")
    
    # 2. Create meeting notes
    notes_path = create_meeting_notes(project_root, issue_date, issue_number)
    
    # 3. Create demos folder
    create_demos_folder(project_root, issue_date)
    
    # 4. Create article-images folder
    create_article_images_folder(project_root, issue_date)
    
    # 5. Generate newsletter HTML
    import subprocess
    result = subprocess.run(
        [sys.executable, str(script_dir / 'generate_newsletter.py'), str(notes_path)],
        cwd=str(project_root)
    )
    if result.returncode != 0:
        print("Error: Newsletter generation failed.")
        sys.exit(1)
    
    # 6. Update index.html
    if update_index(project_root, issue_date, issue_number):
        print(f"Updated: {project_root / 'index.html'}")
    else:
        print(f"Latest Issue bar already current in {project_root / 'index.html'}")
    
    print(f"\nDone! Edit meeting-notes/{issue_date}.md with your content,")
    print(f"add demo GIFs to assets/demos/{issue_date}/ and optional article images to assets/article-images/{issue_date}/, then commit and push.")


if __name__ == '__main__':
    main()
