# reports/

*Last updated: 2026-05-03*

Frozen deliverables and current rendered drafts - PDFs and PPTXs that have been
submitted, emailed, or otherwise "shipped" should not be edited after the fact.
Files marked `*_draft.*` at the top level are active working cuts until they are
replaced by a final shipped artifact or invalidated. Living documentation
(domain guides, architecture, setup) lives in [../docs/](../docs/); planning
artifacts (roadmap, meeting agendas, working notes) live in
[../planning/](../planning/). This directory is for durable rendered outputs,
not source-of-truth prose.

## Current Deliverables and Active Drafts

| File | Date | What it is |
|---|---|---|
| `2026-04-02_proposal.pdf` | Apr 2, 2026 | Team 13 research proposal (MCP standardization + Smart Grid scenario generation), emailed to mentor Dr. Dhaval Patel. A frozen cut from the team Overleaf project. |
| `2026-04-06_midpoint_submission.pdf` | Apr 6, 2026 | HPML mid-point report submitted to Courseworks. 5 slides: title, project summary, current progress, work in progress, blockers and limitations. |
| `2026-05-03_final_presentation_smartgridbench_draft.pptx` | May 3, 2026 | Current editable #44 final-presentation PowerPoint draft; scenario, mitigation, and dry-run gates remain open before final submission. |

## Archive

`archive/` holds superseded or invalid local draft artifacts that were replaced by later deliverables. It is not for current working exports. Kept for provenance and in case a reviewer needs to trace how the project evolved:

| File | Superseded by |
|---|---|
| `archive/2026-04-01_proposal_draft.pdf` | `2026-04-02_proposal.pdf` |
| `archive/2026-04-02_midpoint_draft.pdf` | `2026-04-06_midpoint_submission.pdf` |
| `archive/2026-04-02_midpoint_draft.pptx` | `2026-04-06_midpoint_submission.pdf` |

## Build Notes

| Artifact | Build note |
|---|---|
| `2026-05-03_final_presentation_smartgridbench_draft.pptx` | [build_notes/2026-05-03_final_presentation_smartgridbench_build.md](build_notes/2026-05-03_final_presentation_smartgridbench_build.md) |

## Conventions

- **Naming:** `YYYY-MM-DD_<what>.<ext>` — date-prefixed so `ls` orders them chronologically.
- **No edits after the fact.** If a shipped deliverable needs a correction, create a new dated file — don't overwrite history. Files ending `*_draft.*` may be edited until replaced by a final shipped artifact.
- **Active drafts stay at the top level** while they are the current working cut. Move them to `archive/` only after they are superseded or invalidated.
- **Source files (LaTeX, Markdown, Keynote) live elsewhere** - [../docs/data_pipeline.tex](../docs/data_pipeline.tex) for paper-ready LaTeX sections, [../planning/archive/mid_report_slides.md](../planning/archive/mid_report_slides.md) for the archived midpoint slide source. `reports/` only holds the rendered outputs.
