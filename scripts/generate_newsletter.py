#!/usr/bin/env python3
"""
Generate newsletter HTML from structured markdown notes.
Creates both the issue page and sources page.

Usage:
    python generate_newsletter.py meeting-notes/cop\ 012926.md
"""

import re
import sys
import os
from datetime import datetime
from pathlib import Path


def parse_markdown(content: str) -> dict:
    """Parse structured markdown into a dictionary of sections and items."""
    data = {
        'issue_date': '',
        'issue_number': '',
        'title': 'Artificial Insights',
        'sections': {}
    }
    
    # Extract header info
    date_match = re.search(r'^Issue Date:\s*(.+)$', content, re.MULTILINE)
    if date_match:
        data['issue_date'] = date_match.group(1).strip()
    
    number_match = re.search(r'^Issue Number:\s*(.+)$', content, re.MULTILINE)
    if number_match:
        data['issue_number'] = number_match.group(1).strip()
    
    title_match = re.search(r'^Title:\s*(.+)$', content, re.MULTILINE)
    if title_match:
        data['title'] = title_match.group(1).strip()
    
    # Define section names to look for
    section_names = [
        'Quick Scan',
        'The Feed', 
        'Tool Drop',
        'The Breakdown',
        'Ed Pulse',
        'In Action',
        'Try This'
    ]
    
    # Split content into sections
    for i, section_name in enumerate(section_names):
        pattern = rf'^{re.escape(section_name)}:\s*$'
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            start = match.end()
            # Find the end (next section or end of relevant content)
            end = len(content)
            for next_section in section_names[i+1:] + ['Follow-up tasks']:
                next_pattern = rf'^{re.escape(next_section)}:'
                next_match = re.search(next_pattern, content[start:], re.MULTILINE)
                if next_match:
                    end = start + next_match.start()
                    break
            
            section_content = content[start:end].strip()
            items = parse_items(section_content, section_name)
            data['sections'][section_name] = items
    
    return data


def parse_items(section_content: str, section_name: str) -> list:
    """Parse items from a section's content."""
    items = []
    
    # Split by item markers (- Title:)
    item_blocks = re.split(r'^- Title:', section_content, flags=re.MULTILINE)
    
    for block in item_blocks[1:]:  # Skip first empty split
        item = {'Title': ''}
        
        # First line is the title
        lines = block.strip().split('\n')
        if lines:
            item['Title'] = lines[0].strip()
        
        # Parse other fields
        current_field = None
        current_value = []
        
        for line in lines[1:]:
            # Check for field markers
            field_match = re.match(r'^\s*(Summary|Tags|URL|Image|Caption|Instructions):\s*(.*)$', line)
            if field_match:
                # Save previous field if exists
                if current_field:
                    item[current_field] = ' '.join(current_value).strip()
                current_field = field_match.group(1)
                current_value = [field_match.group(2).strip()] if field_match.group(2).strip() else []
            elif current_field and line.strip():
                # Continuation of previous field (for multi-line summaries)
                current_value.append(line.strip())
        
        # Save last field
        if current_field:
            item[current_field] = ' '.join(current_value).strip()
        
        # Only add items with a title
        if item['Title']:
            items.append(item)
    
    return items


def format_date_display(date_str: str) -> str:
    """Convert YYYY-MM-DD to 'Jan 29, 2026' format."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%b %d, %Y')
    except:
        return date_str


def generate_card_html(item: dict, card_class: str, icon: str) -> str:
    """Generate HTML for a content card."""
    title = item.get('Title', '')
    summary = item.get('Summary', '')
    url = item.get('URL', '')
    
    # If URL exists, make title a link
    if url:
        title_html = f'<a href="{url}" target="_blank" rel="noopener" style="color: inherit; text-decoration: none;">{title} ↗</a>'
    else:
        title_html = title
    
    return f'''      <div class="content-card {card_class}">
        <h3><span class="icon">{icon}</span> {title_html}</h3>
        <p>{summary}</p>
      </div>
'''


def generate_in_action_html(item: dict, issue_date: str) -> str:
    """Generate HTML for In Action items with optional demo image."""
    title = item.get('Title', '')
    summary = item.get('Summary', '')
    image = item.get('Image', '')
    caption = item.get('Caption', '')
    url = item.get('URL', '')
    
    # If URL exists, make title a link
    if url:
        title_html = f'<a href="{url}" target="_blank" rel="noopener" style="color: inherit; text-decoration: none;">{title} ↗</a>'
    else:
        title_html = title
    
    html = f'''      <div class="content-card card-in-action">
        <h3><span class="icon">🎬</span> {title_html}</h3>
        <p>{summary}</p>
'''
    
    if image:
        image_path = f"../assets/demos/{issue_date}/{image}"
        html += f'''        <figure>
          <img src="{image_path}" alt="{caption or title}">
          <figcaption>{caption}</figcaption>
        </figure>
'''
    
    html += '      </div>\n'
    return html


def generate_try_this_html(item: dict) -> str:
    """Generate HTML for Try This items."""
    title = item.get('Title', '')
    instructions = item.get('Instructions', '')
    url = item.get('URL', '')
    
    if not title:
        return ''
    
    # Add link if URL exists
    url_html = ''
    if url:
        url_html = f' <a href="{url}" target="_blank" rel="noopener" style="color: var(--try-this);">Learn more ↗</a>'
    
    return f'''      <div class="try-this-box">
        <h3>{title}</h3>
        <p>{instructions}{url_html}</p>
      </div>
'''


def generate_issue_html(data: dict) -> str:
    """Generate the complete issue HTML."""
    date_display = format_date_display(data['issue_date'])
    issue_num = data['issue_number']
    
    # Section icons mapping
    section_icons = {
        'Quick Scan': '⚡',
        'The Feed': '📰',
        'Tool Drop': '🛠️',
        'The Breakdown': '🔬',
        'Ed Pulse': '🎓',
        'In Action': '🎬',
        'Try This': '💡'
    }
    
    card_classes = {
        'Quick Scan': 'card-quick-scan',
        'The Feed': 'card-feed',
        'Tool Drop': 'card-tool-drop',
        'The Breakdown': 'card-breakdown',
        'Ed Pulse': 'card-ed-pulse',
        'In Action': 'card-in-action'
    }
    
    header_images = {
        'Quick Scan': 'quick_scan_header.webp',
        'The Feed': 'the_feed_header.webp',
        'Tool Drop': 'tool_drop_header.webp',
        'The Breakdown': 'the_breakdown_header.webp',
        'Ed Pulse': 'ed_pulse_header.webp',
        'In Action': 'in_action_header.webp',
        'Try This': 'try_this_header.webp'
    }
    
    section_ids = {
        'Quick Scan': 'quick-scan',
        'The Feed': 'the-feed',
        'Tool Drop': 'tool-drop',
        'The Breakdown': 'the-breakdown',
        'Ed Pulse': 'ed-pulse',
        'In Action': 'in-action',
        'Try This': 'try-this'
    }
    
    # Build sections HTML
    sections_html = ''
    
    for section_name in ['Quick Scan', 'The Feed', 'Tool Drop', 'The Breakdown', 'Ed Pulse', 'In Action', 'Try This']:
        items = data['sections'].get(section_name, [])
        if not items:
            continue
        
        section_id = section_ids[section_name]
        header_img = header_images[section_name]
        
        sections_html += f'''
      <!-- {section_name.upper()} -->
      <div class="section-header" id="{section_id}">
        <img src="../assets/images/{header_img}" alt="{section_name}">
      </div>
'''
        
        for item in items:
            if section_name == 'In Action':
                sections_html += generate_in_action_html(item, data['issue_date'])
            elif section_name == 'Try This':
                sections_html += generate_try_this_html(item)
            else:
                icon = section_icons.get(section_name, '📌')
                card_class = card_classes.get(section_name, '')
                sections_html += generate_card_html(item, card_class, icon)
    
    # Build overview items (only for sections that have content)
    overview_items = ''
    for section_name in ['Quick Scan', 'The Feed', 'Tool Drop', 'The Breakdown', 'Ed Pulse', 'In Action', 'Try This']:
        if data['sections'].get(section_name):
            section_id = section_ids[section_name]
            icon = section_icons[section_name]
            overview_items += f'          <li><a href="#{section_id}">{icon} {section_name}</a></li>\n'
    
    html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Artificial Insights — {date_display}</title>
    <style>
      :root {{
        --text: #0f172a;
        --muted: #64748b;
        --rule: #e2e8f0;
        --accent: #2563eb;
        --accent-hover: #1d4ed8;
        --accent-soft: #dbeafe;
        --card: #ffffff;
        --bg: #f8fafc;
        --shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
        --shadow-hover: 0 8px 30px rgba(15, 23, 42, 0.12);
        --quick-scan: #8b5cf6;
        --feed: #0891b2;
        --tool-drop: #059669;
        --breakdown: #d97706;
        --ed-pulse: #db2777;
        --in-action: #7c3aed;
        --try-this: #0d9488;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
        color: var(--text);
        margin: 0;
        background: var(--bg);
        line-height: 1.6;
      }}
      
      /* Top Bar */
      .top-bar {{
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #fff;
        padding: 12px 20px;
        font-size: 13px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
      }}
      .top-bar a {{
        color: #94a3b8;
        text-decoration: none;
        transition: color 0.15s;
      }}
      .top-bar a:hover {{ color: #fff; }}
      .top-bar .date {{ color: #94a3b8; }}
      
      /* Container */
      .container {{
        max-width: 720px;
        margin: 0 auto;
        padding: 0 20px;
      }}
      
      /* Header */
      .header {{
        text-align: center;
        padding: 32px 0 24px;
      }}
      .header img {{
        max-width: 100%;
        border-radius: 16px;
        box-shadow: var(--shadow);
      }}
      
      /* Nav Links */
      .nav-links {{
        display: flex;
        justify-content: center;
        gap: 24px;
        padding: 16px 0;
        border-bottom: 2px solid var(--rule);
        margin-bottom: 24px;
        flex-wrap: wrap;
      }}
      .nav-links a {{
        color: var(--muted);
        text-decoration: none;
        font-size: 14px;
        font-weight: 600;
        padding: 6px 12px;
        border-radius: 6px;
        transition: all 0.15s;
      }}
      .nav-links a:hover {{ 
        color: var(--accent);
        background: var(--accent-soft);
      }}
      
      /* Issue Info */
      .issue-info {{
        text-align: center;
        margin-bottom: 32px;
      }}
      .issue-info h1 {{
        font-size: 36px;
        margin: 0 0 8px;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, var(--text) 0%, var(--muted) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }}
      .issue-info .meta {{
        color: var(--muted);
        font-size: 15px;
      }}
      .issue-info .meta .icon {{ margin-right: 6px; }}
      
      /* Issue Overview */
      .overview {{
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid var(--rule);
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 32px;
        box-shadow: var(--shadow);
      }}
      .overview h2 {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--muted);
        margin: 0 0 14px;
        display: flex;
        align-items: center;
        gap: 8px;
      }}
      .overview h2::before {{
        content: "📑";
        font-size: 14px;
      }}
      .overview ul {{
        margin: 0;
        padding: 0;
        list-style: none;
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }}
      .overview li {{
        padding: 0;
      }}
      .overview a {{
        color: var(--text);
        text-decoration: none;
        font-weight: 600;
        font-size: 13px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 14px;
        border-radius: 8px;
        transition: all 0.2s;
      }}
      .overview a:hover {{ 
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      }}
      .overview a[href="#quick-scan"] {{ background: #f3e8ff; color: var(--quick-scan); }}
      .overview a[href="#the-feed"] {{ background: #cffafe; color: var(--feed); }}
      .overview a[href="#tool-drop"] {{ background: #d1fae5; color: var(--tool-drop); }}
      .overview a[href="#the-breakdown"] {{ background: #fef3c7; color: var(--breakdown); }}
      .overview a[href="#ed-pulse"] {{ background: #fce7f3; color: var(--ed-pulse); }}
      .overview a[href="#in-action"] {{ background: #ede9fe; color: var(--in-action); }}
      .overview a[href="#try-this"] {{ background: #ccfbf1; color: var(--try-this); }}
      
      /* Section Header Image */
      .section-header {{
        margin: 48px 0 20px;
        border-radius: 12px;
        overflow: hidden;
      }}
      .section-header img {{
        width: 100%;
        height: auto;
        display: block;
      }}
      
      /* Section Divider (fallback for no image) */
      .section-divider {{
        display: flex;
        align-items: center;
        gap: 16px;
        margin: 48px 0 20px;
      }}
      .section-divider h2 {{
        margin: 0;
        font-size: 26px;
        white-space: nowrap;
        display: flex;
        align-items: center;
        gap: 10px;
      }}
      .section-divider .line {{
        flex: 1;
        height: 4px;
        border-radius: 2px;
        background: linear-gradient(90deg, var(--tool-drop) 0%, transparent 100%);
      }}
      
      /* Content Card */
      .content-card {{
        background: var(--card);
        border: 1px solid var(--rule);
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 16px;
        box-shadow: var(--shadow);
        border-left: 5px solid var(--accent);
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
      }}
      .content-card:hover {{
        transform: translateY(-2px);
        box-shadow: var(--shadow-hover);
      }}
      .content-card::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
        opacity: 0;
        transition: opacity 0.2s;
      }}
      .content-card:hover::before {{
        opacity: 1;
      }}
      .card-quick-scan {{ border-left-color: var(--quick-scan); }}
      .card-feed {{ border-left-color: var(--feed); }}
      .card-tool-drop {{ border-left-color: var(--tool-drop); }}
      .card-breakdown {{ border-left-color: var(--breakdown); }}
      .card-ed-pulse {{ border-left-color: var(--ed-pulse); }}
      .card-in-action {{ border-left-color: var(--in-action); }}
      .content-card h3 {{
        margin: 0 0 10px;
        font-size: 18px;
        display: flex;
        align-items: center;
        gap: 8px;
      }}
      .content-card h3 .icon {{
        font-size: 20px;
      }}
      .content-card h3 a {{
        transition: opacity 0.15s;
      }}
      .content-card h3 a:hover {{
        opacity: 0.7;
      }}
      .content-card p {{
        margin: 0;
        color: var(--muted);
        font-size: 15px;
      }}
      .content-card p + p {{
        margin-top: 12px;
      }}
      
      /* Try This Box */
      .try-this-box {{
        background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%);
        border: 2px solid var(--try-this);
        border-radius: 14px;
        padding: 22px 26px;
        margin: 20px 0;
        position: relative;
        overflow: hidden;
      }}
      .try-this-box::before {{
        content: "💡";
        position: absolute;
        top: -10px;
        right: 20px;
        font-size: 48px;
        opacity: 0.15;
      }}
      .try-this-box h3 {{
        color: var(--try-this);
        margin: 0 0 12px;
        font-size: 17px;
        display: flex;
        align-items: center;
        gap: 8px;
      }}
      .try-this-box h3::before {{
        content: "→";
        font-weight: bold;
      }}
      .try-this-box p {{
        margin: 0;
        color: var(--text);
        font-size: 15px;
      }}
      .try-this-box code {{
        background: rgba(13, 148, 136, 0.15);
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 14px;
        font-family: "Consolas", monospace;
      }}
      
      /* Demo Figure */
      figure {{
        margin: 16px 0;
      }}
      figure img {{
        max-width: 100%;
        border-radius: 10px;
        border: 1px solid var(--rule);
        box-shadow: var(--shadow);
      }}
      figcaption {{
        color: var(--muted);
        font-size: 13px;
        margin-top: 10px;
        text-align: center;
        font-style: italic;
      }}
      
      /* Share Section */
      .share-section {{
        text-align: center;
        padding: 36px 28px;
        margin: 48px 0;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border: 1px solid var(--rule);
        border-radius: 16px;
      }}
      .share-section h3 {{
        margin: 0 0 8px;
        font-size: 20px;
        color: var(--text);
      }}
      .share-section p {{
        margin: 0 0 20px;
        color: var(--muted);
        font-size: 15px;
      }}
      .share-link {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: var(--accent);
        color: #fff;
        padding: 12px 24px;
        border-radius: 10px;
        text-decoration: none;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.2s;
      }}
      .share-link:hover {{
        background: var(--accent-hover);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
      }}
      .share-link::before {{
        content: "✉️";
      }}
      
      /* Footer */
      footer {{
        border-top: 2px solid var(--rule);
        padding: 36px 0;
        text-align: center;
        color: var(--muted);
        font-size: 13px;
      }}
      footer a {{
        color: var(--muted);
        text-decoration: none;
        transition: color 0.15s;
      }}
      footer a:hover {{ color: var(--accent); }}
      footer .footer-links {{
        margin-bottom: 16px;
        display: flex;
        justify-content: center;
        gap: 24px;
        flex-wrap: wrap;
      }}
      footer .brand {{
        font-weight: 700;
        color: var(--text);
        font-size: 14px;
      }}
      
      /* Responsive */
      @media (max-width: 600px) {{
        .top-bar {{
          justify-content: center;
          text-align: center;
        }}
        .nav-links {{
          gap: 12px;
        }}
        .issue-info h1 {{
          font-size: 28px;
        }}
        .section-divider h2 {{
          font-size: 22px;
        }}
        .content-card, .overview, .try-this-box {{
          padding: 18px 20px;
        }}
        .overview a {{
          padding: 6px 10px;
          font-size: 12px;
        }}
      }}
      
      @media print {{
        .top-bar, .nav-links, .share-section {{ display: none; }}
        body {{ background: #fff; }}
        .content-card, .overview {{ box-shadow: none; }}
      }}
    </style>
  </head>
  <body>
    <div class="top-bar">
      <span class="date">📅 {date_display} · Issue #{issue_num}</span>
      <a href="#">🔗 Read Online</a>
    </div>
    
    <div class="container">
      <div class="header">
        <img src="../assets/images/artificial_insights_banner.webp" alt="Artificial Insights">
      </div>
      
      <nav class="nav-links">
        <a href="../index.html">📚 All Issues</a>
        <a href="../sources/{data['issue_date']}.html">🔍 Sources</a>
        <a href="#share">📤 Share</a>
      </nav>
      
      <div class="issue-info">
        <h1>Artificial Insights</h1>
        <p class="meta"><span class="icon">⏱️</span> Your bi-weekly AI briefing · 5 min read</p>
      </div>
      
      <div class="overview">
        <h2>In This Issue</h2>
        <ul>
{overview_items}        </ul>
      </div>
{sections_html}
      <!-- SHARE -->
      <div class="share-section" id="share">
        <h3>Found this useful?</h3>
        <p>Share Artificial Insights with a colleague who might benefit.</p>
        <a href="mailto:?subject=Check%20out%20Artificial%20Insights&body=I%20thought%20you%20might%20find%20this%20AI%20newsletter%20useful%3A%20https%3A%2F%2Fbpmstc.github.io%2FArtificial-Insights%2F" class="share-link">Share via Email</a>
      </div>
      
      <footer>
        <div class="footer-links">
          <a href="../index.html">📚 All Issues</a>
          <a href="../sources/{data['issue_date']}.html">🔍 Sources</a>
          <a href="mailto:">✉️ Contact</a>
        </div>
        <p><span class="brand">Artificial Insights</span> · Issue #{issue_num} · {date_display}</p>
      </footer>
    </div>
  </body>
</html>
'''
    return html


def generate_sources_html(data: dict) -> str:
    """Generate the sources HTML page."""
    date_display = format_date_display(data['issue_date'])
    issue_num = data['issue_number']
    issue_url = f"../issues/{data['issue_date']}.html"
    
    section_icons = {
        'Quick Scan': '⚡',
        'The Feed': '📰',
        'Tool Drop': '🛠️',
        'The Breakdown': '🔬',
        'Ed Pulse': '🎓',
        'In Action': '🎬',
        'Try This': '💡'
    }
    
    # Collect all sources
    sources_html = ''
    for section_name in ['Quick Scan', 'The Feed', 'Tool Drop', 'The Breakdown', 'Ed Pulse', 'In Action', 'Try This']:
        items = data['sections'].get(section_name, [])
        urls = []
        for item in items:
            url = item.get('URL', '').strip()
            if url:
                label = item.get('Title', url)
                urls.append((url, label))
        
        if urls:
            icon = section_icons.get(section_name, '📌')
            sources_html += f'      <h3>{icon} {section_name}</h3>\n      <ul>\n'
            for url, label in urls:
                sources_html += f'        <li><a href="{url}" target="_blank" rel="noopener">{label} ↗</a></li>\n'
            sources_html += '      </ul>\n'
    
    html = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Sources — Artificial Insights #{issue_num}</title>
    <style>
      :root {{
        --text: #0f172a;
        --muted: #64748b;
        --rule: #e2e8f0;
        --accent: #2563eb;
        --accent-hover: #1d4ed8;
        --accent-soft: #dbeafe;
        --card: #ffffff;
        --bg: #f8fafc;
        --shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
        color: var(--text);
        margin: 0;
        background: var(--bg);
        line-height: 1.7;
      }}
      .top-bar {{
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #fff;
        padding: 12px 20px;
        font-size: 13px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
      }}
      .top-bar a {{
        color: #94a3b8;
        text-decoration: none;
        transition: color 0.15s;
      }}
      .top-bar a:hover {{ color: #fff; }}
      .top-bar .date {{ color: #94a3b8; }}
      .container {{
        max-width: 720px;
        margin: 0 auto;
        padding: 0 20px 60px;
      }}
      .header {{
        text-align: center;
        padding: 32px 0 24px;
      }}
      .header img {{
        max-width: 100%;
        border-radius: 16px;
        box-shadow: var(--shadow);
      }}
      .nav-links {{
        display: flex;
        justify-content: center;
        gap: 24px;
        padding: 16px 0;
        border-bottom: 2px solid var(--rule);
        margin-bottom: 24px;
        flex-wrap: wrap;
      }}
      .nav-links a {{
        color: var(--muted);
        text-decoration: none;
        font-size: 14px;
        font-weight: 600;
        padding: 6px 12px;
        border-radius: 6px;
        transition: all 0.15s;
      }}
      .nav-links a:hover {{
        color: var(--accent);
        background: var(--accent-soft);
      }}
      h1 {{
        font-size: 32px;
        margin: 32px 0 8px;
        letter-spacing: -0.5px;
      }}
      .meta {{
        color: var(--muted);
        font-size: 15px;
        margin-bottom: 32px;
      }}
      h3 {{
        font-size: 18px;
        margin: 28px 0 12px;
        display: flex;
        align-items: center;
        gap: 8px;
      }}
      ul {{
        margin: 0 0 20px;
        padding-left: 24px;
      }}
      li {{
        margin-bottom: 8px;
      }}
      a {{
        color: var(--accent);
        text-decoration: none;
        transition: color 0.15s;
      }}
      a:hover {{
        color: var(--accent-hover);
        text-decoration: underline;
      }}
      footer {{
        border-top: 2px solid var(--rule);
        padding: 36px 0;
        text-align: center;
        color: var(--muted);
        font-size: 13px;
        margin-top: 48px;
      }}
      footer a {{
        color: var(--muted);
      }}
      footer a:hover {{ color: var(--accent); }}
      footer .footer-links {{
        margin-bottom: 16px;
        display: flex;
        justify-content: center;
        gap: 24px;
        flex-wrap: wrap;
      }}
      footer .brand {{
        font-weight: 700;
        color: var(--text);
        font-size: 14px;
      }}
      @media (max-width: 600px) {{
        h1 {{ font-size: 26px; }}
        h3 {{ font-size: 16px; }}
      }}
    </style>
  </head>
  <body>
    <div class="top-bar">
      <span class="date">📅 {date_display} · Issue #{issue_num}</span>
      <a href="{issue_url}">← Back to Issue</a>
    </div>
    
    <div class="container">
      <div class="header">
        <img src="../assets/images/artificial_insights_banner.webp" alt="Artificial Insights">
      </div>
      
      <nav class="nav-links">
        <a href="../index.html">📚 All Issues</a>
        <a href="{issue_url}">📰 This Issue</a>
      </nav>
      
      <h1>🔍 Sources</h1>
      <p class="meta">References and links from Issue #{issue_num}</p>
      
{sources_html}
      <footer>
        <div class="footer-links">
          <a href="../index.html">📚 All Issues</a>
          <a href="{issue_url}">📰 This Issue</a>
        </div>
        <p><span class="brand">Artificial Insights</span> · Issue #{issue_num} · {date_display}</p>
      </footer>
    </div>
  </body>
</html>
'''
    return html


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_newsletter.py <markdown_file>")
        sys.exit(1)
    
    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"Error: File not found: {md_path}")
        sys.exit(1)
    
    # Read and parse markdown
    content = md_path.read_text(encoding='utf-8')
    data = parse_markdown(content)
    
    if not data['issue_date']:
        print("Error: Could not find 'Issue Date:' in markdown file")
        sys.exit(1)
    
    # Determine output paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    issue_path = project_root / 'issues' / f"{data['issue_date']}.html"
    sources_path = project_root / 'sources' / f"{data['issue_date']}.html"
    
    # Generate and write files
    issue_html = generate_issue_html(data)
    sources_html = generate_sources_html(data)
    
    issue_path.write_text(issue_html, encoding='utf-8')
    sources_path.write_text(sources_html, encoding='utf-8')
    
    print(f"Generated: {issue_path}")
    print(f"Generated: {sources_path}")


if __name__ == '__main__':
    main()
