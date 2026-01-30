# Demo Assets

Place demonstration images and GIFs in folders named by issue date.

## Structure

```
demos/
  2026-01-29/           ← folder matches issue date
    excel-claude-demo.gif
    gemini-video.png
  2026-02-12/
    another-demo.gif
```

## Naming Convention

Use descriptive kebab-case names:
- `tool-name-action.gif` (e.g., `claude-excel-spreadsheet.gif`)
- `tool-name-feature.png` (e.g., `copilot-email-summary.png`)

## Supported Formats

- `.png` - screenshots
- `.gif` - short animations
- `.webp` - optimized images
- `.jpg` - photos

## Referencing in Meeting Notes

```
Demonstrations:
- Title: Claude building a spreadsheet
  Summary: Watch Claude generate a multi-tab budget tracker.
  Image: claude-excel-spreadsheet.gif
  Caption: Claude creating formulas automatically
```

The generator will look for the image in `assets/demos/{issue-date}/`.
