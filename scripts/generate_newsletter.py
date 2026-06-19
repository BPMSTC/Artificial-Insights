#!/usr/bin/env python3
"""
Generate newsletter HTML from structured markdown notes.
Creates both the issue page and sources page.

Usage:
    python generate_newsletter.py meeting-notes/cop\ 012926.md
"""

import html
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
        'Failure Mode',
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
            for next_section in section_names[i+1:] + ['Follow-up heading', 'Follow-up tasks']:
                next_pattern = rf'^{re.escape(next_section)}:'
                next_match = re.search(next_pattern, content[start:], re.MULTILINE)
                if next_match:
                    end = start + next_match.start()
                    break
            
            section_content = content[start:end].strip()
            items = parse_items(section_content, section_name)
            data['sections'][section_name] = items
    
    data['follow_up_tasks'] = parse_follow_up_tasks(content)
    heading_match = re.search(r'^Follow-up heading:\s*(.+)$', content, re.MULTILINE)
    _fh = heading_match.group(1).strip() if heading_match else ''
    data['follow_up_heading'] = _fh if _fh else 'How can AI help me?'

    return data


def parse_follow_up_tasks(content: str) -> list:
    """Parse bullet list after 'Follow-up tasks:'. Merges URL: or bare https lines into the previous item."""
    tasks = []
    followup_match = re.search(r'^Follow-up tasks:\s*$', content, re.MULTILINE)
    if not followup_match:
        return []
    rest = content[followup_match.end():].strip()
    current = None
    for raw_line in rest.split('\n'):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith('- '):
            if current is not None:
                tasks.append(current.strip())
            current = line[2:].strip()
        elif re.match(r'^URL:\s*', line, re.IGNORECASE):
            url = re.sub(r'^URL:\s*', '', line, count=1, flags=re.IGNORECASE).strip()
            if current is not None:
                current = f'{current} {url}'.strip()
            else:
                current = url
        elif re.match(r'^https?://', line):
            if current is not None:
                current = f'{current} {line}'.strip()
            else:
                current = line
        elif current is not None:
            current = f'{current} {line}'.strip()
        else:
            current = line
    if current is not None:
        tasks.append(current.strip())
    return tasks


def parse_items(section_content: str, section_name: str) -> list:
    """Parse items from a section's content."""
    items = []
    
    # All possible field names
    field_names = [
        'Summary', 'Tags', 'URL', 'Image', 'Caption', 'Instructions',
        'Teaser', 'LinkText', 'TheNews', 'MyTake', 'Analysis', 'TheLesson',
        'Content', 'Intro', 'ThePrompt', 'WhyItWorks',
        'ArticleImage', 'ArticleImageCaption'
    ]
    field_pattern = '|'.join(field_names)
    
    # Split by item markers (- Title:)
    item_blocks = re.split(r'^- Title:', section_content, flags=re.MULTILINE)
    
    for block in item_blocks[1:]:  # Skip first empty split
        item = {'Title': '', 'URLs': []}  # URLs is a list to handle multiple
        
        # First line is the title
        lines = block.strip().split('\n')
        if lines:
            item['Title'] = lines[0].strip()
        
        # Parse other fields
        current_field = None
        current_value = []
        
        for line in lines[1:]:
            # Check for field markers
            field_match = re.match(rf'^\s*({field_pattern}):\s*(.*)$', line)
            if field_match:
                # Save previous field if exists
                if current_field:
                    if current_field == 'URL':
                        url_val = ' '.join(current_value).strip()
                        if url_val:
                            item['URLs'].append(url_val)
                    else:
                        item[current_field] = _join_field_value(current_value).strip()
                
                current_field = field_match.group(1)
                current_value = [field_match.group(2).strip()] if field_match.group(2).strip() else []
            elif current_field and line.strip():
                current_value.append(line.strip())
            elif current_field and not line.strip():
                if current_value and current_value[-1] != '\n\n':
                    current_value.append('\n\n')
        
        # Save last field
        if current_field:
            if current_field == 'URL':
                url_val = ' '.join(current_value).strip()
                if url_val:
                    item['URLs'].append(url_val)
            else:
                item[current_field] = _join_field_value(current_value).strip()
        
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


def format_text(text: str) -> str:
    """Convert markdown formatting to HTML (bold, paragraph breaks)."""
    if not text:
        return text
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return text


def linkify_plain_urls(text: str) -> str:
    """Turn bare http(s) URLs into anchor tags for follow-up and similar plain-text lines."""
    if not text:
        return text
    return re.sub(
        r'(https?://[^\s<>"\'\)]+)',
        r'<a href="\1" target="_blank" rel="noopener">\1</a>',
        text,
    )


def _join_field_value(parts: list) -> str:
    """Join field value parts, preserving blank lines as <br><br>."""
    result = []
    buffer = []
    for part in parts:
        if part == '\n\n':
            if buffer:
                result.append(' '.join(buffer))
            result.append('<br><br>')
            buffer = []
        else:
            buffer.append(part)
    if buffer:
        result.append(' '.join(buffer))
    return ''.join(result)


def _article_image_html(item: dict, issue_date: str) -> str:
    """Return HTML for optional article image (float left) or empty string."""
    img = (item.get('ArticleImage') or '').strip()
    if not img:
        return ''
    if img.startswith(('http://', 'https://', '//')):
        path = img
    else:
        path = f"../assets/article-images/{issue_date}/{img}"
    caption = (item.get('ArticleImageCaption') or '').strip()
    cap_html = f'\n          <figcaption>{caption}</figcaption>' if caption else ''
    return f'''        <figure class="article-image">
          <img src="{path}" alt="{caption or 'Article image'}">{cap_html}
        </figure>
'''


def generate_quick_scan_html(item: dict, issue_date: str) -> str:
    """Generate HTML for Quick Scan items - brief teasers with links."""
    title = item.get('Title', '')
    teaser = item.get('Teaser', '') or item.get('Summary', '')
    link_text = item.get('LinkText', 'Read More')
    urls = item.get('URLs', [])
    article_img = _article_image_html(item, issue_date)

    link_html = ''
    if urls:
        if len(urls) == 1:
            label = link_text if link_text else 'Read More'
            link_html = f'\n        <p class="read-more"><a href="{urls[0]}" target="_blank" rel="noopener">{label} ↗</a></p>'
        else:
            link_parts = []
            for url in urls:
                domain = url.split('/')[2] if '/' in url else url
                domain = domain.replace('www.', '')
                link_parts.append(f'<a href="{url}" target="_blank" rel="noopener">{domain} ↗</a>')
            link_html = f'\n        <p class="source-links">Sources: ' + ' · '.join(link_parts) + '</p>'

    content_inner = f'''        <div class="content-with-article-image">
{article_img}        <p>{format_text(teaser)}</p>{link_html}
        </div>'''
    return f'''      <div class="quick-scan-item">
        <h3>{title}</h3>
{content_inner}
      </div>
'''


def generate_tool_drop_html(item: dict, issue_date: str) -> str:
    """Generate HTML for Tool Drop - The News + My Take format."""
    title = item.get('Title', '')
    the_news = item.get('TheNews', '') or item.get('Summary', '')
    my_take = item.get('MyTake', '')
    urls = item.get('URLs', [])
    article_img = _article_image_html(item, issue_date)
    
    link_html = ''
    if urls:
        link_html = f'\n        <p class="read-more"><a href="{urls[0]}" target="_blank" rel="noopener">Learn More ↗</a></p>'
    
    my_take_html = ''
    if my_take:
        my_take_html = f'\n        <p class="my-take"><strong>My Take:</strong> {format_text(my_take)}</p>'
    
    content_inner = f'''        <div class="content-with-article-image">
{article_img}        <p><strong>The News:</strong> {format_text(the_news)}</p>{my_take_html}{link_html}
        </div>'''
    return f'''      <div class="content-card card-tool-drop">
        <h3><span class="icon">🛠️</span> {title}</h3>
{content_inner}
      </div>
'''


def generate_breakdown_html(item: dict, issue_date: str) -> str:
    """Generate HTML for The Breakdown - Analysis + The Lesson format."""
    title = item.get('Title', '')
    analysis = item.get('Analysis', '') or item.get('Summary', '')
    the_lesson = item.get('TheLesson', '')
    link_text = item.get('LinkText', 'Read More')
    urls = item.get('URLs', [])
    article_img = _article_image_html(item, issue_date)
    
    lesson_html = ''
    if the_lesson:
        lesson_html = f'\n        <div class="the-lesson"><strong>The Lesson:</strong> {format_text(the_lesson)}</div>'
    
    link_html = ''
    if urls:
        link_html = f'\n        <p class="read-more"><a href="{urls[0]}" target="_blank" rel="noopener">{link_text} ↗</a></p>'
    
    content_inner = f'''        <div class="content-with-article-image">
{article_img}        <p>{format_text(analysis)}</p>{lesson_html}{link_html}
        </div>'''
    return f'''      <div class="content-card card-breakdown">
        <h3><span class="icon">🔬</span> {title}</h3>
{content_inner}
      </div>
'''


def generate_ed_pulse_html(item: dict, issue_date: str) -> str:
    """Generate HTML for Ed Pulse items."""
    title = item.get('Title', '')
    content = item.get('Content', '') or item.get('Summary', '')
    link_text = item.get('LinkText', '')
    urls = item.get('URLs', [])
    article_img = _article_image_html(item, issue_date)
    
    link_html = ''
    if urls:
        if len(urls) == 1:
            label = link_text if link_text else 'Read More'
            link_html = f'\n        <p class="read-more"><a href="{urls[0]}" target="_blank" rel="noopener">{label} ↗</a></p>'
        else:
            link_parts = []
            for url in urls:
                domain = url.split('/')[2] if '/' in url else url
                domain = domain.replace('www.', '')
                link_parts.append(f'<a href="{url}" target="_blank" rel="noopener">{domain} ↗</a>')
            link_html = f'\n        <p class="source-links">Sources: ' + ' · '.join(link_parts) + '</p>'
    
    content_inner = f'''        <div class="content-with-article-image">
{article_img}        <p>{format_text(content)}</p>{link_html}
        </div>'''
    return f'''      <div class="content-card card-ed-pulse">
        <h3><span class="icon">🎓</span> {title}</h3>
{content_inner}
      </div>
'''


def generate_card_html(item: dict, card_class: str, icon: str) -> str:
    """Generate HTML for a generic content card (fallback)."""
    title = item.get('Title', '')
    summary = item.get('Summary', '') or item.get('Content', '') or item.get('Teaser', '')
    urls = item.get('URLs', [])
    
    # If URLs exist, make title a link to the first one
    if urls:
        title_html = f'<a href="{urls[0]}" target="_blank" rel="noopener" style="color: inherit; text-decoration: none;">{title} ↗</a>'
    else:
        title_html = title
    
    # Build links section if multiple URLs
    links_html = ''
    if len(urls) > 1:
        links_html = '\n        <p class="source-links">Sources: '
        link_parts = []
        for i, url in enumerate(urls):
            # Extract domain for display
            domain = url.split('/')[2] if '/' in url else url
            domain = domain.replace('www.', '')
            link_parts.append(f'<a href="{url}" target="_blank" rel="noopener">{domain} ↗</a>')
        links_html += ' · '.join(link_parts) + '</p>'
    
    return f'''      <div class="content-card {card_class}">
        <h3><span class="icon">{icon}</span> {title_html}</h3>
        <p>{summary}</p>{links_html}
      </div>
'''


def generate_in_action_html(item: dict, issue_date: str) -> str:
    """Generate HTML for In Action items with optional demo image."""
    title = item.get('Title', '')
    content = item.get('Content', '') or item.get('Summary', '')
    image = item.get('Image', '')
    caption = item.get('Caption', '')
    link_text = item.get('LinkText', '')
    urls = item.get('URLs', [])
    
    link_html = ''
    if urls:
        if len(urls) == 1:
            label = link_text if link_text else 'Learn More'
            link_html = f'\n        <p class="read-more"><a href="{urls[0]}" target="_blank" rel="noopener">{label} ↗</a></p>'
        else:
            link_parts = []
            for url in urls:
                domain = url.split('/')[2] if '/' in url else url
                domain = domain.replace('www.', '')
                link_parts.append(f'<a href="{url}" target="_blank" rel="noopener">{domain} ↗</a>')
            link_html = f'\n        <p class="source-links">Sources: ' + ' · '.join(link_parts) + '</p>'
    
    html = f'''      <div class="content-card card-in-action">
        <h3><span class="icon">🎬</span> {title}</h3>
        <p>{format_text(content)}</p>
'''
    
    if image:
        image_path = f"../assets/demos/{issue_date}/{image}"
        html += f'''        <figure>
          <img src="{image_path}" alt="{caption or title}">
          <figcaption>{caption}</figcaption>
        </figure>
'''
    
    html += link_html
    html += '      </div>\n'
    return html


def generate_failure_mode_html(item: dict, issue_date: str) -> str:
    """Generate HTML for Failure Mode items — a light-hearted 'AI fails' card.

    Uses the same field shape as Ed Pulse (Title, Content, optional LinkText, URL,
    ArticleImage, ArticleImageCaption).
    """
    title = item.get('Title', '')
    content = item.get('Content', '') or item.get('Summary', '')
    link_text = item.get('LinkText', '')
    urls = item.get('URLs', [])
    article_img = _article_image_html(item, issue_date)

    link_html = ''
    if urls:
        if len(urls) == 1:
            label = link_text if link_text else 'Read More'
            link_html = f'\n        <p class="read-more"><a href="{urls[0]}" target="_blank" rel="noopener">{label} ↗</a></p>'
        else:
            link_parts = []
            for url in urls:
                domain = url.split('/')[2] if '/' in url else url
                domain = domain.replace('www.', '')
                link_parts.append(f'<a href="{url}" target="_blank" rel="noopener">{domain} ↗</a>')
            link_html = f'\n        <p class="source-links">Sources: ' + ' · '.join(link_parts) + '</p>'

    content_inner = f'''        <div class="content-with-article-image">
{article_img}        <p>{format_text(content)}</p>{link_html}
        </div>'''
    return f'''      <div class="content-card card-failure-mode">
        <h3><span class="icon">💥</span> {title}</h3>
{content_inner}
      </div>
'''


def generate_try_this_html(item: dict, issue_date: str) -> str:
    """Generate HTML for Try This items with Intro, Prompt, and Why It Works."""
    title = item.get('Title', '')
    intro = item.get('Intro', '') or item.get('Instructions', '')
    the_prompt = item.get('ThePrompt', '')
    why_it_works = item.get('WhyItWorks', '')
    image = (item.get('Image') or '').strip()
    caption = (item.get('Caption') or '').strip()
    urls = item.get('URLs', [])
    article_img = _article_image_html(item, issue_date)
    
    if not title:
        return ''
    
    # Build the content
    intro_html = f'<p>{format_text(intro)}</p>' if intro else ''
    
    demo_html = ''
    if image:
        image_path = f"../assets/demos/{issue_date}/{image}"
        demo_html = f'''        <figure class="try-this-demo">
          <img src="{image_path}" alt="{caption or title}">
          <figcaption>{caption}</figcaption>
        </figure>
'''
    
    prompt_html = ''
    if the_prompt:
        prompt_html = f'''
        <div class="the-prompt">
          <p class="prompt-label">The Prompt:</p>
          <blockquote>"{format_text(the_prompt)}"</blockquote>
        </div>'''
    
    why_html = ''
    if why_it_works:
        why_html = f'\n        <p class="why-it-works"><strong>Why it works:</strong> {format_text(why_it_works)}</p>'
    
    # Add link if URL exists
    url_html = ''
    if urls:
        url_html = f'\n        <p class="read-more"><a href="{urls[0]}" target="_blank" rel="noopener" style="color: var(--try-this);">Learn more ↗</a></p>'
    
    content_inner = f'''        <div class="content-with-article-image">
{article_img}        {intro_html}{demo_html}{prompt_html}{why_html}{url_html}
        </div>'''
    return f'''      <div class="try-this-box">
        <h3>{title}</h3>
{content_inner}
      </div>
'''


def generate_follow_up_html(tasks: list, heading: str = 'How can AI help me?') -> str:
    """Generate HTML for follow-up tasks block (after Try This). Heading comes from Follow-up heading: in markdown."""
    if not tasks:
        return ''
    items_html = ''
    for task in tasks:
        line_html = linkify_plain_urls(format_text(task))
        items_html += f'        <li>{line_html}</li>\n'
    title = html.escape(heading)
    return f'''      <div class="follow-up-block">
        <h3 class="follow-up-heading">{title}</h3>
        <ul class="follow-up-tasks">
{items_html}      </ul>
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
        'Failure Mode': '💥',
        'Try This': '💡'
    }
    
    card_classes = {
        'Quick Scan': 'card-quick-scan',
        'The Feed': 'card-feed',
        'Tool Drop': 'card-tool-drop',
        'The Breakdown': 'card-breakdown',
        'Ed Pulse': 'card-ed-pulse',
        'In Action': 'card-in-action',
        'Failure Mode': 'card-failure-mode'
    }
    
    header_images = {
        'Quick Scan': 'quick_scan_header.webp',
        'The Feed': 'the_feed_header.webp',
        'Tool Drop': 'tool_drop_header.webp',
        'The Breakdown': 'the_breakdown_header.webp',
        'Ed Pulse': 'ed_pulse_header.webp',
        'In Action': 'in_action_header.webp',
        'Failure Mode': 'failure_mode_header.webp',
        'Try This': 'try_this_header.webp'
    }
    
    section_ids = {
        'Quick Scan': 'quick-scan',
        'The Feed': 'the-feed',
        'Tool Drop': 'tool-drop',
        'The Breakdown': 'the-breakdown',
        'Ed Pulse': 'ed-pulse',
        'In Action': 'in-action',
        'Failure Mode': 'failure-mode',
        'Try This': 'try-this'
    }

    # Resolve assets directory so we can fall back to a text divider when
    # a section header image hasn't been created yet.
    assets_images_dir = Path(__file__).parent.parent / 'assets' / 'images'
    
    # Build sections HTML
    sections_html = ''
    
    for section_name in ['Quick Scan', 'The Feed', 'Tool Drop', 'The Breakdown', 'Ed Pulse', 'In Action', 'Failure Mode', 'Try This']:
        items = data['sections'].get(section_name, [])
        if not items:
            continue
        
        section_id = section_ids[section_name]
        header_img = header_images[section_name]
        icon = section_icons.get(section_name, '📌')

        # Prefer the configured filename (.webp), but also accept .png / .jpg / .jpeg
        # so a header banner works even before it has been converted to webp.
        header_stem = Path(header_img).stem
        resolved_header = None
        for ext in (Path(header_img).suffix, '.webp', '.png', '.jpg', '.jpeg'):
            candidate = assets_images_dir / f'{header_stem}{ext}'
            if candidate.exists():
                resolved_header = candidate.name
                break

        if resolved_header:
            sections_html += f'''
      <!-- {section_name.upper()} -->
      <div class="section-header" id="{section_id}">
        <img src="../assets/images/{resolved_header}" alt="{section_name}">
      </div>
'''
        else:
            sections_html += f'''
      <!-- {section_name.upper()} -->
      <div class="section-divider" id="{section_id}">
        <h2><span class="icon">{icon}</span> {section_name}</h2>
        <div class="line"></div>
      </div>
'''
        
        for item in items:
            if section_name == 'Quick Scan':
                sections_html += generate_quick_scan_html(item, data['issue_date'])
            elif section_name == 'Tool Drop':
                sections_html += generate_tool_drop_html(item, data['issue_date'])
            elif section_name == 'The Breakdown':
                sections_html += generate_breakdown_html(item, data['issue_date'])
            elif section_name == 'Ed Pulse':
                sections_html += generate_ed_pulse_html(item, data['issue_date'])
            elif section_name == 'In Action':
                sections_html += generate_in_action_html(item, data['issue_date'])
            elif section_name == 'Failure Mode':
                sections_html += generate_failure_mode_html(item, data['issue_date'])
            elif section_name == 'Try This':
                sections_html += generate_try_this_html(item, data['issue_date'])
            else:
                card_class = card_classes.get(section_name, '')
                sections_html += generate_card_html(item, card_class, icon)
        
        # After Try This items, add "How can AI help me?" block if we have follow-up tasks
        if section_name == 'Try This' and data.get('follow_up_tasks'):
            sections_html += generate_follow_up_html(
                data['follow_up_tasks'],
                data.get('follow_up_heading') or 'How can AI help me?',
            )
    
    # Build overview items (only for sections that have content)
    overview_items = ''
    for section_name in ['Quick Scan', 'The Feed', 'Tool Drop', 'The Breakdown', 'Ed Pulse', 'In Action', 'Failure Mode', 'Try This']:
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
        --failure-mode: #dc2626;
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
        margin: 0;
      }}
      .issue-info .issue-date {{
        color: var(--muted);
        font-size: 15px;
        margin: 0 0 8px;
        font-weight: 600;
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
      .overview a[href="#failure-mode"] {{ background: #fee2e2; color: var(--failure-mode); }}
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
      .card-failure-mode {{ border-left-color: var(--failure-mode); }}
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
      .source-links {{
        font-size: 13px;
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px solid var(--rule);
      }}
      .source-links a {{
        color: var(--accent);
        text-decoration: none;
      }}
      .source-links a:hover {{
        text-decoration: underline;
      }}
      
      /* Quick Scan Items */
      .quick-scan-item {{
        background: var(--card);
        border: 1px solid var(--rule);
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 16px;
        box-shadow: var(--shadow);
        border-left: 5px solid var(--quick-scan);
        transition: all 0.2s ease;
      }}
      .quick-scan-item:hover {{
        transform: translateY(-2px);
        box-shadow: var(--shadow-hover);
      }}
      .quick-scan-item h3 {{
        margin: 0 0 10px;
        font-size: 18px;
        color: var(--text);
      }}
      .quick-scan-item p {{
        margin: 0;
        color: var(--muted);
        font-size: 15px;
      }}
      
      /* Read More Links */
      .read-more {{
        margin-top: 12px !important;
      }}
      .read-more a {{
        color: var(--accent);
        text-decoration: none;
        font-weight: 600;
        font-size: 14px;
      }}
      .read-more a:hover {{
        text-decoration: underline;
      }}
      
      /* My Take styling */
      .my-take {{
        margin-top: 16px !important;
        padding-top: 12px;
        border-top: 1px dashed var(--rule);
        color: var(--text) !important;
      }}
      
      /* The Lesson styling */
      .the-lesson {{
        margin-top: 16px;
        padding: 14px 18px;
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-radius: 8px;
        font-size: 15px;
        color: var(--text);
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
      .try-this-demo {{
        clear: both;
        margin: 16px 0;
      }}
      .try-this-demo img {{
        display: block;
        max-width: 100%;
        border-radius: 10px;
        border: 1px solid var(--rule);
        box-shadow: var(--shadow);
      }}
      .try-this-demo figcaption {{
        color: var(--muted);
        font-size: 13px;
        margin-top: 10px;
        text-align: center;
        font-style: italic;
      }}
      
      /* The Prompt styling */
      .the-prompt {{
        margin: 16px 0;
        padding: 16px 20px;
        background: rgba(13, 148, 136, 0.08);
        border-radius: 10px;
        border-left: 4px solid var(--try-this);
      }}
      .the-prompt .prompt-label {{
        font-weight: 700;
        color: var(--try-this);
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0 0 10px;
      }}
      .the-prompt blockquote {{
        margin: 0;
        font-style: italic;
        color: var(--text);
        font-size: 15px;
        line-height: 1.7;
      }}
      .why-it-works {{
        margin-top: 14px !important;
        font-size: 14px;
        color: var(--muted) !important;
      }}
      
      /* How can AI help me? (follow-up tasks, inside Try This) */
      .follow-up-block {{
        margin: 24px 0 20px;
        padding: 20px 24px;
        background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
        border: 2px solid #8b5cf6;
        border-radius: 14px;
        border-left-width: 6px;
      }}
      .follow-up-block .follow-up-heading {{
        margin: 0 0 12px;
        font-size: 17px;
        color: #6d28d9;
        display: flex;
        align-items: center;
        gap: 8px;
      }}
      .follow-up-block .follow-up-heading::before {{
        content: "🎯";
        font-size: 20px;
      }}
      .follow-up-block .follow-up-tasks {{
        margin: 0;
        padding-left: 22px;
        color: var(--text);
        font-size: 15px;
        line-height: 1.65;
      }}
      .follow-up-block .follow-up-tasks li {{
        margin-bottom: 8px;
      }}
      .follow-up-block .follow-up-tasks li:last-child {{
        margin-bottom: 0;
      }}
      
      /* Article image (float left, text wrap) — optional per item */
      .content-with-article-image {{
        overflow: auto;
      }}
      .content-with-article-image::after {{
        content: "";
        display: table;
        clear: both;
      }}
      .article-image {{
        float: left;
        margin: 0 1.25em 1em 0;
        max-width: 40%;
        width: auto;
      }}
      .article-image img {{
        display: block;
        border-radius: 10px;
        border: 1px solid var(--rule);
        box-shadow: var(--shadow);
      }}
      .article-image figcaption {{
        color: var(--muted);
        font-size: 12px;
        margin-top: 6px;
        font-style: italic;
      }}
      @media (max-width: 600px) {{
        .article-image {{
          float: none;
          max-width: 100%;
          margin: 0 auto 1em;
          display: block;
        }}
      }}
      
      /* Demo Figure (In Action) */
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
        <p class="issue-date">📅 {date_display} · Issue #{issue_num}</p>
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
        'Failure Mode': '💥',
        'Try This': '💡'
    }
    
    # Collect all sources
    sources_html = ''
    for section_name in ['Quick Scan', 'The Feed', 'Tool Drop', 'The Breakdown', 'Ed Pulse', 'In Action', 'Failure Mode', 'Try This']:
        items = data['sections'].get(section_name, [])
        url_entries = []
        for item in items:
            item_urls = item.get('URLs', [])
            label = item.get('Title', '')
            for url in item_urls:
                if url:
                    url_entries.append((url, label))
        
        if url_entries:
            icon = section_icons.get(section_name, '📌')
            sources_html += f'      <h3>{icon} {section_name}</h3>\n      <ul>\n'
            for url, label in url_entries:
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
