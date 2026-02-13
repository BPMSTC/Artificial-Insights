# Artificial Insights

A bi-weekly AI newsletter for coworkers (generalist to mid-level AI experts) featuring concise highlights, deep-dive analysis, and practical tips.

## Overview

This newsletter uses a two-tier editorial format:
- **Quick Scan**: Brief teasers (2 sentences) with links for quick reading
- **Deep Dives**: Detailed sections with personal analysis and lessons learned

## Project Structure

```
newsletter/
├── meeting-notes/          # Structured markdown files (your content source)
│   ├── meeting-notes-template.md
│   └── 2026-01-29.md      # Named YYYY-MM-DD to match issue date
├── issues/                 # Generated HTML newsletter issues
│   └── YYYY-MM-DD.html
├── sources/                # Generated source/reference pages
│   └── YYYY-MM-DD.html
├── assets/
│   ├── images/            # Banner, logo, section headers (webp format)
│   └── demos/             # Demo GIFs organized by issue date
│       └── YYYY-MM-DD/
├── scripts/
│   ├── new_newsletter.py       # Create new issue (run this first)
│   └── generate_newsletter.py  # Markdown → HTML generator
└── .git/hooks/
    └── pre-commit         # Auto-regenerates on commit
```

## Newsletter Sections

1. **Quick Scan**: 2-sentence teasers with "Read More" links
2. **Tool Drop**: "The News" + "My Take" format for tool reviews
3. **The Breakdown**: Analysis with highlighted "The Lesson" callouts
4. **Ed Pulse**: Education impact and pedagogy insights
5. **In Action**: Demonstrations with GIFs and guides
6. **Try This**: Actionable prompts with "Why it works" explanations

## Creating a New Newsletter

Run one command with the meeting/newsletter date:

```bash
python scripts/new_newsletter.py 2026-02-14
```

Or run without arguments to be prompted for the date:

```bash
python scripts/new_newsletter.py
# Enter issue date (YYYY-MM-DD): 2026-02-14
```

**This automatically:**
1. Creates `meeting-notes/YYYY-MM-DD.md` from the template (with date and issue number filled in)
2. Creates `assets/demos/YYYY-MM-DD/` folder for demo GIFs
3. Generates `issues/YYYY-MM-DD.html` and `sources/YYYY-MM-DD.html`
4. Adds the new issue card to `index.html`

**Then you:**
1. Edit `meeting-notes/YYYY-MM-DD.md` with your content
2. Add demo GIFs to `assets/demos/YYYY-MM-DD/` (if needed)
3. Update the description in `index.html` for the new issue card (optional)
4. Commit and push

---

## Workflow

### 1. Create Meeting Notes (or edit existing)

```markdown
Issue Date: 2026-01-29
Issue Number: 1
Title: Artificial Insights

Quick Scan:
- Title: Claude Embeds in Excel
  Teaser: Paid users can now run Claude directly inside Excel...
  LinkText: Read Tutorial
  URL: https://example.com

Tool Drop:
- Title: Deep Dive on Claude in Excel
  TheNews: Claude can now generate complex spreadsheets...
  MyTake: While the "paid version" requirement is a hurdle...
  URL: https://example.com
```

See `meeting-notes/meeting-notes-template.md` for the complete structure.

### 2. Create Demos Folder and Add Assets (if needed)

Create the folder `assets/demos/YYYY-MM-DD/` (the date must match your `Issue Date:` in the markdown). Place GIFs there; filenames must match the `Image:` field in your markdown:

```markdown
In Action:
- Title: The Recurring Task
  Content: ChatGPT is the endlessly patient colleague...
  Image: recurring-tasks.gif    # Goes in assets/demos/2026-01-29/
  Caption: Setting up a recurring task
  URL: https://example.com
```

### 3. Generate Newsletter (when editing existing content)

**Option A: Manual generation**
```bash
python scripts/generate_newsletter.py "meeting-notes/2026-01-29.md"
```

**Option B: Automatic (recommended)**
```bash
git add meeting-notes/2026-01-29.md
git commit -m "Update newsletter content"
# Pre-commit hook automatically regenerates HTML
```

### 4. Push to GitHub Pages

```bash
git push
# Also push to gh-pages branch:
git checkout gh-pages && git merge master && git push && git checkout master
```

Live site: https://bpmstc.github.io/Artificial-Insights/

## Markdown Format Reference

### Quick Scan Fields
- `Title`: Headline
- `Teaser`: 2-sentence summary
- `LinkText`: Custom link text (e.g., "Read Tutorial")
- `URL`: Source link

### Tool Drop Fields
- `Title`: Tool name
- `TheNews`: Brief description
- `MyTake`: Your analysis/opinion
- `URL`: Reference link

### The Breakdown Fields
- `Title`: Topic
- `Analysis`: Main discussion
- `TheLesson`: Key takeaway (displayed in highlighted box)
- `LinkText`: Custom link text
- `URL`: Reference link

### Ed Pulse Fields
- `Title`: Topic
- `Content`: Discussion
- `LinkText`: Optional custom link text
- `URL`: Optional reference link

### In Action Fields
- `Title`: Demo name
- `Content`: Description
- `Image`: Filename of GIF in `assets/demos/YYYY-MM-DD/`
- `Caption`: Image caption
- `LinkText`: Optional custom link text
- `URL`: Optional guide link

### Try This Fields
- `Title`: Prompt name
- `Intro`: Context/setup
- `ThePrompt`: The actual prompt text (displayed in special box)
- `WhyItWorks`: Explanation
- `URL`: Optional reference link

## Features

- **Automated generation**: Pre-commit hook regenerates newsletter on markdown changes
- **Multiple URLs**: Add multiple `URL:` lines for items with multiple sources
- **Responsive design**: Mobile-friendly layout
- **WebP optimization**: All images converted to WebP for performance
- **GitHub Pages hosting**: Automatic deployment to gh-pages branch

## Repository

- **GitHub**: https://github.com/BPMSTC/Artificial-Insights
- **Live Site**: https://bpmstc.github.io/Artificial-Insights/

## Notes

- Always use ISO date format `YYYY-MM-DD` for issue dates
- Demo GIFs should be optimized for web (< 500 KB recommended)
- Pre-commit hook handles both `issues/` and `sources/` generation automatically
- Section header images are in `assets/images/` as webp files
- **Naming:** Meeting notes use `YYYY-MM-DD.md` (e.g., `2026-01-29.md`)
- **Issue numbers** auto-increment when you run `new_newsletter.py`
