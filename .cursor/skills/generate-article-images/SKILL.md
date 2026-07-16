---
name: generate-article-images
description: >-
  Generate Grok Imagine article images for Artificial Insights newsletter
  stories, save them under assets/article-images/YYYY-MM-DD/, and fill
  ArticleImage plus ArticleImageCaption in meeting-notes markdown. Use when
  the user asks to generate article images, fill ArticleImage fields, create
  story images with Grok, or prepare images for a newsletter issue.
---

# Generate Article Images

For each story that needs a float-left article image, create a Grok Imagine image, store it in the issue's article-images folder, and update the meeting-notes fields.

## When to run

Use after the meeting-notes markdown for an issue is filled in, and before (or alongside) final HTML generation.

Requires `XAI_API_KEY` in a repo-root `.env` file (gitignored) or in the environment.
See `.env.example`.

## Scope

Generate images only for items in:

- Quick Scan
- Tool Drop
- The Breakdown
- Ed Pulse
- Try This

Skip **In Action** and **Failure Mode** — those use `Image:` files in `assets/demos/YYYY-MM-DD/`.

Default: only fill items where `ArticleImage:` is empty. If the user asks to regenerate, overwrite the named files and captions.

## Workflow

Copy this checklist and track progress:

```
Article images:
- [ ] Identify issue date + notes file
- [ ] List stories missing ArticleImage
- [ ] For each story: prompt → generate → save → update markdown
- [ ] Confirm files exist on disk
- [ ] (Optional) regenerate HTML
```

### 1. Identify the issue

- Notes file: `meeting-notes/YYYY-MM-DD.md`
- Image folder: `assets/article-images/YYYY-MM-DD/`
- Create the folder if missing

If the user does not name a date, use the newest non-template file in `meeting-notes/`.

### 2. Find stories that need images

Parse items under the in-scope sections. For each `- Title:` block, treat it as needing an image when `ArticleImage:` is missing or blank.

Use the item's `Title` plus the main body field for context:

| Section | Body fields |
|---------|-------------|
| Quick Scan | Teaser |
| Tool Drop | TheNews, MyTake |
| The Breakdown | Analysis, TheLesson |
| Ed Pulse | Content |
| Try This | Intro, ThePrompt |

### 3. For each story

1. **Filename** — short kebab-case slug + `.png`  
   Examples: `neo-robot-hand.png`, `data-center-delays.png`, `chatgpt-work.png`  
   Must be unique within the issue folder.

2. **Caption** — one plain sentence for `ArticleImageCaption:` (newsletter voice; no trailing period required if matching nearby style).

3. **Image prompt** — editorial newsletter illustration, not a screenshot fake:
   - Concrete visual tied to the story (not generic "AI brain")
   - Clean composition suitable as a small float-left thumbnail
   - No readable text, logos, watermarks, or UI chrome unless essential
   - Prefer photoreal or restrained editorial illustration
   - Square-friendly subject (saved at 1:1)

4. **Generate and save** with the helper script:

```bash
python scripts/generate_article_image.py \
  --prompt "YOUR PROMPT HERE" \
  --out "assets/article-images/YYYY-MM-DD/slug.png"
```

5. **Update markdown** for that item:

```markdown
  ArticleImage: slug.png
  ArticleImageCaption: Your one-sentence caption
```

Keep spacing consistent with neighboring fields (`ArticleImage: filename` with one space after the colon).

### 4. Finish

- Verify every targeted story has both a non-empty `ArticleImage` / `ArticleImageCaption` and a real file on disk.
- Summarize what was generated (filename + caption per story).
- Only run `python scripts/generate_newsletter.py "meeting-notes/YYYY-MM-DD.md"` if the user asked to regenerate HTML.

## Helper script

`scripts/generate_article_image.py` calls xAI Grok Imagine (`grok-imagine-image`), downloads the image, and writes `--out`.

- Auth: `XAI_API_KEY` from `.env` or the environment
- Default aspect ratio: `1:1`
- If the key is missing, stop and tell the user to add it to `.env` (from `.env.example`) — do not invent images or use a different image tool unless the user explicitly redirects.
- Never commit `.env` or paste the key into markdown/skill files.

## Do not

- Do not put generated files in `assets/demos/`
- Do not use remote `https://` URLs for newly generated article images — save local files
- Do not change story titles, teasers, or other fields while filling images
- Do not generate images for In Action / Failure Mode unless the user explicitly asks
