# reports/

*Last updated: 2026-04-21*

Frozen deliverables — PDFs and PPTXs that have been submitted, emailed, or otherwise "shipped" and should not be edited after the fact. Living documentation (domain guides, architecture, setup) lives in [`../docs/`](../docs/); planning artifacts (roadmap, meeting agendas, working notes) live in [`../planning/`](../planning/). This directory is for the immutable outputs.

## Current deliverables

| File | Date | What it is |
|---|---|---|
| `2026-04-02_proposal.pdf` | Apr 2, 2026 | Team 13 research proposal (MCP standardization + Smart Grid scenario generation), emailed to mentor Dr. Dhaval Patel. A frozen cut from the team Overleaf project. |
| `2026-04-06_midpoint_submission.pdf` | Apr 6, 2026 | HPML mid-point report submitted to Courseworks. 5 slides: title, project summary, current progress, work in progress, blockers and limitations. |

## Archive

`archive/` holds superseded drafts and working-version exports that were replaced by later deliverables. Kept for provenance and in case a reviewer needs to trace how the project evolved:

| File | Superseded by |
|---|---|
| `archive/2026-04-01_proposal_draft.pdf` | `2026-04-02_proposal.pdf` |
| `archive/2026-04-02_midpoint_draft.pdf` | `2026-04-06_midpoint_submission.pdf` |
| `archive/2026-04-02_midpoint_draft.pptx` | `2026-04-06_midpoint_submission.pdf` |

## Conventions

- **Naming:** `YYYY-MM-DD_<what>.<ext>` — date-prefixed so `ls` orders them chronologically.
- **No edits after the fact.** If a shipped deliverable needs a correction, create a new dated file — don't overwrite history.
- **Drafts and working versions go to `archive/`** at the time the final version is created, so the top-level only ever shows what's currently authoritative.
- **Source files (LaTeX, Markdown, Keynote) live elsewhere** - [`../docs/data_pipeline.tex`](../docs/data_pipeline.tex) for paper-ready LaTeX sections, [`../planning/archive/mid_report_slides.md`](../planning/archive/mid_report_slides.md) for the archived midpoint slide source. `reports/` only holds the rendered outputs.
