#!/usr/bin/env python3
"""
Generate sources HTML page from meeting notes markdown.
Usage: python generate_sources.py <notes_file> <output_file> [issue_date] [issue_number]
Example: python generate_sources.py "../meeting-notes/cop 012926.md" "../sources/2026-01-29.html" "Jan 29, 2026" "1"
"""

import sys
import re
from pathlib import Path


def parse_sources(content: str) -> dict:
    """Parse the Sources section from markdown content."""
    sources = {
        "News": [],
        "New Tools": [],
        "Analysis": [],
        "Education Impact": [],
        "Demonstrations": []
    }
    
    # Find the Sources section
    sources_match = re.search(r'^Sources:\s*$', content, re.MULTILINE)
    if not sources_match:
        return sources
    
    sources_text = content[sources_match.end():]
    
    # Stop at Follow-up tasks or end of file
    followup_match = re.search(r'^Follow-up tasks:', sources_text, re.MULTILINE)
    if followup_match:
        sources_text = sources_text[:followup_match.start()]
    
    current_section = None
    current_url = None
    current_label = None
    
    for line in sources_text.split('\n'):
        line_stripped = line.strip()
        
        # Check for section headers
        for section in sources.keys():
            if line_stripped == f"{section}:" or line_stripped == section:
                current_section = section
                current_url = None
                current_label = None
                break
        
        # Check for URL line
        url_match = re.match(r'^-?\s*URL:\s*(.*)$', line_stripped, re.IGNORECASE)
        if url_match:
            # Save previous entry if exists
            if current_url and current_label and current_section:
                sources[current_section].append({
                    "url": current_url.strip(),
                    "label": current_label.strip()
                })
            current_url = url_match.group(1).strip()
            current_label = None
            continue
        
        # Check for Label line
        label_match = re.match(r'^-?\s*Label:\s*(.*)$', line_stripped, re.IGNORECASE)
        if label_match:
            current_label = label_match.group(1).strip()
            # Save entry if we have both URL and label
            if current_url and current_label and current_section:
                sources[current_section].append({
                    "url": current_url.strip(),
                    "label": current_label.strip()
                })
                current_url = None
                current_label = None
            continue
    
    # Don't forget last entry
    if current_url and current_label and current_section:
        sources[current_section].append({
            "url": current_url.strip(),
            "label": current_label.strip()
        })
    
    return sources


def generate_html(sources: dict, issue_date: str, issue_number: str, issue_url: str) -> str:
    """Generate the sources HTML page."""
    
    section_classes = {
        "News": "section-news",
        "New Tools": "section-tools",
        "Analysis": "section-analysis",
        "Education Impact": "section-education",
        "Demonstrations": "section-demos"
    }
    
    def generate_section(name: str, items: list) -> str:
        if not items:
            return ""
        
        css_class = section_classes.get(name, "")
        links = "\n".join(
            f'          <li><a href="{item["url"]}">{item["label"]}</a></li>'
            for item in items if item["url"] and item["label"]
        )
        
        if not links:
            return ""
        
        return f'''
      <section class="section {css_class}">
        <h2>{name}</h2>
        <ul>
{links}
        </ul>
      </section>'''
    
    sections_html = "".join(
        generate_section(name, items) 
        for name, items in sources.items()
    )
    
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Artificial Insights — {issue_date} - Sources</title>
    <style>
      :root {{
        --text: #0f172a;
        --muted: #475569;
        --rule: #e2e8f0;
        --accent: #2563eb;
        --accent-hover: #1d4ed8;
        --accent-soft: #dbeafe;
        --card: #ffffff;
        --shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
        --news: #0891b2;
        --tools: #059669;
        --analysis: #d97706;
        --education: #db2777;
        --demos: #7c3aed;
      }}
      body {{
        font-family: "Segoe UI", Arial, Helvetica, sans-serif;
        color: var(--text);
        margin: 0;
        background: #f8fafc;
      }}
      main {{
        max-width: 960px;
        margin: 0 auto;
        padding: 28px 20px 40px;
      }}
      .back-link {{
        margin-bottom: 16px;
      }}
      .back-link a {{
        color: var(--accent);
        text-decoration: none;
        font-size: 14px;
        font-weight: 600;
        transition: color 0.15s ease;
      }}
      .back-link a:hover {{
        color: var(--accent-hover);
      }}
      .back-link a::before {{
        content: "← ";
      }}
      header {{
        display: flex;
        align-items: center;
        gap: 16px;
      }}
      header img {{
        width: 48px;
        height: 48px;
        object-fit: contain;
      }}
      header h1 {{
        margin: 0 0 6px;
        font-size: 28px;
        letter-spacing: 0.2px;
      }}
      header p {{
        margin: 0;
        color: var(--muted);
      }}
      .banner {{
        margin: 18px 0 8px;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: var(--shadow);
      }}
      .banner img {{
        width: 100%;
        display: block;
      }}
      .section {{
        margin-top: 22px;
        background: var(--card);
        border: 1px solid var(--rule);
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: var(--shadow);
        border-left: 4px solid var(--accent);
      }}
      .section-news {{ border-left-color: var(--news); }}
      .section-tools {{ border-left-color: var(--tools); }}
      .section-analysis {{ border-left-color: var(--analysis); }}
      .section-education {{ border-left-color: var(--education); }}
      .section-demos {{ border-left-color: var(--demos); }}
      .section h2 {{
        margin: 0 0 10px;
        font-size: 20px;
      }}
      ul {{
        margin: 0;
        padding-left: 18px;
      }}
      li {{
        margin: 6px 0;
      }}
      a {{
        color: var(--accent);
        text-decoration: none;
        transition: color 0.15s ease;
      }}
      a:hover {{
        color: var(--accent-hover);
      }}
      footer {{
        margin-top: 40px;
        padding: 20px 0;
        border-top: 1px solid var(--rule);
        text-align: center;
        color: var(--muted);
        font-size: 14px;
      }}
      footer a {{
        color: var(--accent);
        text-decoration: none;
        transition: color 0.15s ease;
      }}
      footer a:hover {{
        color: var(--accent-hover);
      }}
      @media (max-width: 600px) {{
        main {{
          padding: 20px 16px 32px;
        }}
        header {{
          gap: 12px;
        }}
        header img {{
          width: 40px;
          height: 40px;
        }}
        header h1 {{
          font-size: 22px;
        }}
        .banner {{
          margin: 14px 0 6px;
          border-radius: 12px;
        }}
        .section {{
          padding: 14px 16px;
          border-radius: 12px;
        }}
      }}
    </style>
  </head>
  <body>
    <main>
      <div class="back-link">
        <a href="{issue_url}">Back to issue</a>
      </div>

      <header>
        <img src="../assets/images/artificial_insights_logo.webp" alt="Artificial Insights logo">
        <div>
          <h1>Artificial Insights — {issue_date}</h1>
          <p>Sources · Issue #{issue_number}</p>
        </div>
      </header>

      <div class="banner">
        <img src="../assets/images/artificial_insights_banner.webp" alt="Artificial Insights banner">
      </div>
{sections_html}

      <footer>
        <p>Artificial Insights · Issue #{issue_number} · {issue_date}<br>
        <a href="../index.html">View all issues</a> · <a href="{issue_url}">Read this issue</a></p>
      </footer>
    </main>
  </body>
</html>
'''


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_sources.py <notes_file> <output_file> [issue_date] [issue_number]")
        sys.exit(1)
    
    notes_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    issue_date = sys.argv[3] if len(sys.argv) > 3 else "Date TBD"
    issue_number = sys.argv[4] if len(sys.argv) > 4 else "X"
    
    # Derive issue URL from output filename
    issue_filename = output_file.stem + ".html"
    issue_url = f"../issues/{issue_filename}"
    
    if not notes_file.exists():
        print(f"Error: Notes file not found: {notes_file}")
        sys.exit(1)
    
    content = notes_file.read_text(encoding="utf-8")
    sources = parse_sources(content)
    
    # Count total sources
    total = sum(len(items) for items in sources.values())
    print(f"Found {total} sources across {sum(1 for items in sources.values() if items)} sections")
    
    html = generate_html(sources, issue_date, issue_number, issue_url)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding="utf-8")
    print(f"Generated: {output_file}")


if __name__ == "__main__":
    main()
