Artificial Insights

Goal
Produce a bi-weekly internal AI newsletter for coworkers (generalist to mid-level)
with concise highlights at the top and deeper details below.

Folder layout
- meeting-notes/        Raw meeting notes per issue (source input)
- issues/               Published HTML issues (one file per issue)
- sources/              Source pages per issue (one file per issue)
- templates/            Reusable HTML templates
- assets/images/        Images used in issues

Issue naming
Use ISO dates for filenames:
- issues/YYYY-MM-DD.html
- sources/YYYY-MM-DD.html

Recommended sections
- Highlights (short paragraphs with headings)
- News
- New Tools
- Analysis
- Education Impact
- Demonstrations (images + captions)

Workflow (draft)
1) Capture meeting notes in meeting-notes/.
2) Add links to the issue's sources page in sources/.
3) Auto-generate a draft from notes/links (future automation).
4) Review and edit the HTML issue in issues/.
5) Publish the HTML and share the link.
