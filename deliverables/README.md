# CourseWorks Deliverables

This directory holds the final files intended for the COMS E6998 CourseWorks submission.

> **Status note 2026-05-10:** the presentation PPTX and PDF in this directory are
> currently **non-canonical pending further formatting edits**. Do not
> treat them as the final submitted artifacts until this notice is removed and
> the regeneration steps below have been re-run. The IEEE final report PDF is
> built from a separately versioned source and is current.

## Contents

- `Team13_HPML_Final_Presentation.pptx` — presentation deck source (currently non-canonical pending user formatting edits).
- `Team13_HPML_Final_Presentation.pdf` — PDF export of the deck (currently non-canonical pending re-export after the formatting edits land).
- `Team13_HPML_Final_Report.pdf` — IEEE-format final report (current).

## Provenance and regeneration

Each artifact is a one-shot export from a separately versioned source. Re-export after content changes; CourseWorks reviewers should treat the PDFs as exports of the listed sources at the export time below, not as independently authored documents.

### `Team13_HPML_Final_Presentation.pptx`

Currently non-canonical (see status note above). Editable source maintained outside this repo by the release owner; the file in this directory is the working copy committed into the team repo for grader access once the formatting pass is complete. Edited in PowerPoint / Keynote / LibreOffice Impress.

### `Team13_HPML_Final_Presentation.pdf`

Currently non-canonical (see status note above). One-shot export from the PPTX above. To regenerate after a PPTX content change:

1. Open `Team13_HPML_Final_Presentation.pptx` in PowerPoint (or Keynote, or LibreOffice Impress).
2. File → Export → PDF → 4:3, embed fonts, "best for printing" quality.
3. Save over `Team13_HPML_Final_Presentation.pdf` in this directory.
4. Verify with `pdftotext deliverables/Team13_HPML_Final_Presentation.pdf - | grep -E "scenario|36 |61 "` that any scenario-count claims match `README.md` and `docs/final_presentation_deck.md`.

A scriptable PPTX → PDF conversion via LibreOffice headless mode is available on systems with `soffice` installed:

```bash
soffice --headless --convert-to pdf --outdir deliverables/ deliverables/Team13_HPML_Final_Presentation.pptx
```

The output may differ slightly from PowerPoint's native exporter (font fallback, slide-master rendering); for the submitted artifact prefer the PowerPoint export path above.

### `Team13_HPML_Final_Report.pdf`

Built from an IEEE LaTeX source maintained outside this repo by the release owner. To regenerate, the release owner re-runs `pdflatex` (twice, for refs) on the source and copies the resulting `main.pdf` over `deliverables/Team13_HPML_Final_Report.pdf` in this directory.

Verify the resulting PDF (run from the repo root):

```bash
pdfinfo deliverables/Team13_HPML_Final_Report.pdf | grep -E "Pages|Producer"
pdftotext deliverables/Team13_HPML_Final_Report.pdf - | grep -iE "claude|codex|chatgpt"
```

The AI-disclosure block must list Claude and Codex only (no ChatGPT). Page count should be within the IEEE class submission limit; verify with `pdfinfo` after each recompile (the literal page count rotates per .tex revision).

## Submission checklist

Before each export, confirm scenario-count claims are consistent across `README.md`, `docs/final_presentation_deck.md`, the report PDF, and the presentation PDF:

- Paper-grade canonical: 36 scenarios (31 hand-authored + 5 promoted generated) + 5 negative fixtures. This is the evaluated corpus, frozen at NeurIPS submission (2026-05-07).
- Repo current: 61 scenario files in `data/scenarios/` because PR #199 added 25 post-submission stretch scenarios. These are deliberately excluded from paper/CourseWorks evaluation claims.

Last regenerated: see `git log -1 --format=%ci -- deliverables/Team13_HPML_Final_Presentation.pdf` and equivalent for the report PDF.
