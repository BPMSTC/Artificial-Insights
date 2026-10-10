---
name: generate-article-images
description: >-
  Generate Grok Imagine article images for Artificial Insights newsletter
  stories, save them under assets/article-images/YYYY-MM-DD/, and fill
  ArticleImage plus ArticleImageCaption in the issue's meeting-notes markdown.
  Use when Brent asks to generate article images, fill ArticleImage fields,
  create story images with Grok, or prepare images for a newsletter issue.
---

# Generate Article Images

Each in-scope story gets a small square editorial illustration that floats left beside its text. This skill finds the stories that need one, agrees on a visual style with Brent, generates the images with Grok Imagine, checks them, and fills in the markdown fields.

Run it after the issue's meeting notes are filled in, before or alongside final HTML generation.

## Setup

`scripts/generate_article_image.py` reads `XAI_API_KEY` from the repo-root `.env` file (gitignored) or from the environment. You never handle the key directly. If the script reports the key missing, stop and tell Brent. Don't fall back to a different image tool, because the newsletter's look depends on consistent Grok output. Never copy the key into markdown, skill files, or commits.

## Scope

In scope: **Quick Scan, Tool Drop, The Breakdown, Field Notes, Ed Pulse, Try This.**

Out of scope: **In Action** and **Failure Mode**. Those use real screenshots from `assets/demos/YYYY-MM-DD/` through their `Image:` fields, and an illustration would replace evidence with decoration. Generate for them only if Brent explicitly asks.

By default, fill only items whose `ArticleImage:` is missing or blank. Overwrite existing images and captions only when Brent asks to regenerate specific ones.

## Workflow

```
Article images:
- [ ] Find the issue and list stories missing images
- [ ] Read the issue, propose 2–3 styles, wait for Brent's choice
- [ ] For each story: prompt → generate → check → update markdown
- [ ] Verify and summarize
```

### 1. Find the issue and the stories

- Notes file: `meeting-notes/YYYY-MM-DD.md`. If Brent doesn't name a date, use the newest non-template file in `meeting-notes/`.
- Image folder: `assets/article-images/YYYY-MM-DD/`. Create it if missing.

Each `- Title:` block under an in-scope section is one story. Use its title plus its body fields to understand what it's about:

| Section | Body fields |
|---------|-------------|
| Quick Scan | Teaser |
| Tool Drop | TheNews, MyTake |
| The Breakdown | Analysis, TheLesson |
| Field Notes | Content |
| Ed Pulse | Content |
| Try This | Intro, ThePrompt |

### 2. Propose styles and wait for a choice

Read the whole issue, not only the stories that need images, and get a sense of its themes and mood. Is it heavy on hardware and robotics, campus policy, hands-on tools? Is the tone cautionary, playful, practical?

If the previous issue's `assets/article-images/` folder exists, look at one or two of its images first. Avoid proposing the same style again unless it clearly suits this issue better, so consecutive issues don't all look alike.

Then send Brent one message with:

- **The stories that will get images** (section and title), so he can drop any.
- **2–3 style options suited to this issue.** For each, give a short name and one sentence on why it fits these particular stories. Make the options genuinely different from each other (for example, one painterly, one graphic, one moody), not three shades of the same look.
- **An invitation to name his own style** instead of any of these.
- **Any Field Notes inline image you think would help** (see "Field Notes inline images" below), as a yes/no option.

Wait for his answer before writing any prompt or generating any image. Each generation costs money, and the style has to stay consistent across the issue.

Exception: if Brent already named a style when he asked for the images, skip the proposal and use his style.

One style applies to every image in the run unless Brent names a different style for a specific story.

### 3. For each story

1. **Filename.** Short kebab-case slug plus `.png`, unique within the issue folder. Examples: `neo-robot-hand.png`, `data-center-delays.png`, `chatgpt-work.png`.

2. **Caption.** One plain sentence for `ArticleImageCaption:` in the newsletter's voice. Match the punctuation of neighboring captions in the file.

3. **Prompt.** An editorial illustration, not a fake screenshot. Every prompt includes:
   - The chosen style, named explicitly.
   - A concrete subject from this story: a specific object, setting, person, or moment. Avoid generic "AI" imagery like glowing brains or circuit boards, which say nothing about the story.
   - A simple, centered composition that still reads as a small square thumbnail.
   - No readable text, logos, watermarks, or UI chrome. Image models garble lettering, and it looks sloppy at thumbnail size. If a story is about an app or a screen, show a person or object in context instead of the interface.

4. **Generate.** Save as a local file in the issue folder, never as a remote `https://` URL, so the newsletter doesn't depend on links that can break:

   ```bash
   python scripts/generate_article_image.py \
     --prompt "YOUR PROMPT HERE" \
     --out "assets/article-images/YYYY-MM-DD/slug.png"
   ```

   The script saves at 1:1 by default, which matches the float-left thumbnail.

5. **Check.** Open the saved PNG and look at it. If it has garbled text, doesn't read as the story, or drifts from the chosen style, adjust the prompt and regenerate once. If the second attempt also misses, keep the better of the two and flag it in the summary.

   If the script errors out or the request is refused, retry once with a reworded prompt. If it fails again, leave that story's fields blank, note it, and move on to the next story.

6. **Update the markdown** for that item, matching the spacing of neighboring fields:

   ```markdown
     ArticleImage: slug.png
     ArticleImageCaption: Your one-sentence caption
   ```

Touch only `ArticleImage`, `ArticleImageCaption`, and any inline image lines Brent approved. Leave titles, teasers, and all other fields exactly as they are.

### Field Notes inline images

A Field Notes piece can hold a second, centered image partway through the explainer, such as a concept diagram or a sentence split into tokens. Don't make these by default. If a piece explains a concept that a picture would clearly help, offer it in the step 2 message, and generate it only if Brent says yes.

When approved:

- Save it in the same `assets/article-images/YYYY-MM-DD/` folder with an `-inline` suffix (for example `token-split-inline.png`), so it's distinct from the float-left opener.
- Add it on its own indented line inside `Content`, where the illustration belongs:

  ```markdown
      ![A sentence broken into the tokens a model actually reads](token-split-inline.png)
  ```

- Don't use an `Image:` line inside `Content`. It ends the Content field.

The generator renders this as a centered `.inline-figure`, not a float. See also README "Field Notes mid-piece images" and `meeting-notes-template.md`.

### 4. Verify and finish

- Confirm every targeted story has a non-empty `ArticleImage` and `ArticleImageCaption`, and that each file exists on disk.
- Summarize for Brent: the style used, then filename and caption per story, plus anything skipped or flagged.
- Regenerate the HTML only if Brent asked for it:

  ```bash
  python scripts/generate_newsletter.py "meeting-notes/YYYY-MM-DD.md"
  ```
